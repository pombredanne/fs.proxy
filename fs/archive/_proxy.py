
import abc
import six
import psutil
import itertools
import functools

from .. import errors
from .. import iotools

from ..base import FS
from ..mode import Mode
from ..copy import copy_file, copy_dir, copy_fs
from ..path import dirname, relpath, join
from ..tools import get_intermediate_dirs
from ..opener import open_fs
from ..tempfs import TempFS
from ..wrapfs import WrapFS
from ..memoryfs import MemoryFS

from . import _utils


class WrapProxyWriterMeta(abc.ABCMeta):
    """Prevent the wrapped class from using `WrapFS` implementations.

    With this metaclass, the `WrapProxyWriter` methods use any other
    available implementation , falling back to `WrapFS` in last resort.
    This prevents the wrapper from directly using the delegate filesystem
    methods, and instead forces it to use `FS` implementations that rely
    on the *essential* methods, which have been implemented.
    """

    def __new__(cls, name, bases, attrs):
        _bases = bases + (FS,)
        for base in _bases:
            if base is not WrapFS:
                for k,v in vars(base).items():
                    if callable(v):
                        attrs.setdefault(k, v)
        return super(WrapProxyWriterMeta, cls).__new__(cls, name, bases, attrs)



@six.add_metaclass(WrapProxyWriterMeta)
class WrapProxyWriter(WrapFS):
    """A wrapper that makes a read-only FS writable with a proxy filesystem.

    Uses a temporary filesystem to handle the changes within the
    read-only filesystem, without copying the whole read-only filesystem
    to the temporary one.

    """

    def __init__(self, wrap_fs=None, proxy=None, close=True):
        """Create a new WrapProxyWriter instance.

        Parameters:
            wrap_fs (FS): The read_only filesystem to wrap. If None given,
                the wrapper will behave exactly as its proxy filesystem alone.
            proxy (FS): The proxy filesystem. If None given, uses a
                `TempFS` instance. *Must be writable.*
            close (bool): Close the read_only filesystem when the wrapper
                is closed.
        """
        super(WrapProxyWriter, self).__init__(wrap_fs or MemoryFS())
        self._proxy = open_fs(proxy or 'temp://__proxy__', writeable=True)
        self._removed = set()
        self._close_ro = close

        self._meta = self.delegate_fs().getmeta().copy()
        self._meta.setdefault('invalid_path_chars', '\0')
        self._meta['read_only'] = False

    def __repr__(self):
        return "{}(r={!r}|w={!r})".format(
            self.__class__.__name__,
            self.delegate_fs(),
            self._proxy
        )

    def __str__(self):
        return "<{} '{}'>".format(
            self.__class__.__name__.lower(),
            self.delegate_fs()
        )

    def _on_wrapped_only(self, path):
        """Return True if given ``path`` is present only on the wrapped FS.

        The path is considered present only on the wrapped filesystem if:
            * it has never been modified
            * it has not been removed
        """
        return self.delegate_fs().exists(path) \
           and not self._proxy.exists(path) \
           and not path in self._removed

    def _relocate(self, path):
        """Move the entry at the given ``path`` to the proxy FS.

        Note:
            Uses `fs.copy.copy_file`, although since the copy is
            always done across different filesystems, there is limited
            chances the copy will be more optimized than reading/writing
            two file objects.
        """
        self._proxy.makedirs(dirname(path), recreate=True)
        copy_file(self.delegate_fs(), path, self._proxy, path)
        self._removed.add(path)

    def exists(self, path):
        _path = self.validatepath(path)
        if self._proxy.exists(_path):
            return True
        elif self.delegate_fs().exists(_path):
            return not _path in self._removed
        else:
            return False

    def makedir(self, path, permissions=None, recreate=False):
        _path = relpath(self.validatepath(path))

        if self.exists(_path) and not recreate:
            raise errors.DirectoryExists(path)

        parent = dirname(_path)
        if not self.exists(parent) and parent not in '/':
            raise errors.ResourceNotFound(path)

        self._proxy.makedirs(_path, recreate=True)

        return self._proxy.opendir(_path)

    def remove(self, path):
        _path = self.validatepath(path)

        if not self.exists(_path):
            raise errors.ResourceNotFound(path)

        if self._proxy.exists(_path):
            self._proxy.remove(_path)

        self._removed.add(_path)

    def removedir(self, path):
        _path = self.validatepath(path)

        if _path in '/':
            raise errors.RemoveRootError()
        elif not self.isempty(_path):
            raise errors.DirectoryNotEmpty(path)

        if self._proxy.exists(_path):
            self._proxy.removedir(_path)

        self._removed.add(_path)

    def openbin(self, path, mode='r', buffering=-1, **options):
        _path = self.validatepath(path)
        _mode = Mode(mode)

        if _mode.exclusive and self.exists(_path):
            raise errors.FileExists(path)

        if not _mode.create:
            if not self.exists(_path):
                raise errors.ResourceNotFound(path)

            if not self._proxy.exists(_path):
                return self.delegate_fs().openbin(_path, mode, buffering, **options)

        elif not _mode.truncate:
            if self._on_wrapped_only(_path):
                self._relocate(_path)

        if self.delegate_fs().exists(dirname(_path)):
            self._proxy.makedirs(dirname(_path), recreate=True)

        return self._proxy.openbin(_path, mode, buffering, **options)

    def setinfo(self, path, info):
        _path = self.validatepath(path)
        if not self.exists(_path):
            raise errors.ResourceNotFound(path)

        if self._proxy.exists(_path):
            self._proxy.setinfo(_path, info)
        elif self.delegate_fs().exists(_path):
            self._proxy.makedirs(dirname(_path), recreate=True)
            copy_file(self.delegate_fs(), _path, self._proxy, _path)
            self._proxy.setinfo(_path, info)

    def listdir(self, path):
        _path = self.validatepath(path)
        content = []

        if not self.exists(_path):
            raise errors.ResourceNotFound(path)

        if not self.isdir(_path):
            raise errors.DirectoryExpected(path)

        if self._proxy.exists(_path):
            content.extend(self._proxy.listdir(_path))

        if self.delegate_fs().exists(_path):
            content.extend(f for f in self.delegate_fs().listdir(_path)
                           if not join(_path, f) in self._removed)

        return list(_utils.unique(content))

    def getinfo(self, path, namespaces=None):
        _path = self.validatepath(path)
        if not self.exists(_path):
            raise errors.ResourceNotFound(_path)
        elif self._proxy.exists(_path):
            return self._proxy.getinfo(_path, namespaces)
        else:
            return self.delegate_fs().getinfo(_path, namespaces)

    def close(self):
        if not self.isclosed():
            super(WrapProxyWriter, self).close()
            self._proxy.close()
            if self._close_ro:
                self.delegate_fs().close()

    def validatepath(self, path):
        self.check()
        return super(WrapFS, self).validatepath(path)


class WrapSwapProxyWriter(WrapProxyWriter):
    """Similar to `WrapProxyWriter`, but with a dynamic proxy.

    The wrapper starts with a MemoryFS, but if the available memory
    on the system becomes low, it will swap automatically to a
    TempFS to free some space.

    Attributes:
        MEMORY_USAGE_LIMIT (int): the maximum size of the RAM proxy.
            If the memory filesystem occupies more than that, the
            wrapper swaps to the backup filesystem. Defaults to half
            of the total memory the system.
        memory_usage (int): the cumulated size of all files in the
            proxy filesystem.

    Todo:
        Make the swap dynamic, so that the wrapper bounces between
        the intial proxy and the swapped proxy instead of always
        using the swapped proxy after the swap.

    """
    MEMORY_USAGE_LIMIT = psutil.virtual_memory().total / 2

    def __init__(self, wrap_fs=None, swap_fs=None, close=True):
        super(WrapSwapProxyWriter, self).__init__(
            wrap_fs or MemoryFS(),
            proxy=MemoryFS(),
            close=close,
        )
        self._swap_fs = open_fs(swap_fs or 'temp://__swap__', writeable=True)

    @property
    def memory_usage(self):
        """The sum of the proxy filesystem files sizes.
        """
        memory_usage = 0
        for _, info in self._proxy.walk.info(namespaces=("details")):
            memory_usage += info.size or 0
        return memory_usage

    def check(self):
        super(WrapSwapProxyWriter, self).check()

        if self.memory_usage > self.MEMORY_USAGE_LIMIT:
            self.swap()

    def swap(self):
        """Replace the current proxy with the backup proxy.

        The in-memory proxy filesystem is closed after the copy.
        """
        if self._proxy is not self._swap_fs:
            _proxy, self._proxy = self._proxy, self._swap_fs
            copy_fs(_proxy, self._proxy)
            _proxy.close()
            del _proxy

    def close(self):
        if not self.isclosed():
            super(WrapProxyWriter, self).close()
            self._proxy.close()
            self._swap_fs.close()
            if self._close_ro:
                self.delegate_fs().close()
