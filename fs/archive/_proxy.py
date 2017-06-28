
import abc
import six
import itertools
import functools

from .. import errors
from .. import iotools

from ..base import FS
from ..mode import Mode
from ..copy import copy_file, copy_dir
from ..path import dirname, relpath, join
from ..tools import get_intermediate_dirs
from ..opener import open_fs
from ..tempfs import TempFS
from ..wrapfs import WrapFS
from ..memoryfs import MemoryFS

from . import _utils


class WrapProxyWriterMeta(abc.ABCMeta):
    """Prevent the wrapped class from using ``WrapFS`` method implementations.
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
    """Makes a read-only Filesystem writable.

    Uses a temporary filesystem to handle the changes within the
    read-only filesystem, without copying the whole read-only filesystem
    to the temporary one.
    """

    def __init__(self, wrap_fs=None, proxy=None, close=True):

        super(WrapProxyWriter, self).__init__(wrap_fs or MemoryFS())
        self._proxy = open_fs(proxy or 'temp://__proxy__')
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
        """
        return self.delegate_fs().exists(path) \
           and not self._proxy.exists(path) \
           and not path in self._removed

    def _relocate(self, path):
        """Move the entry at the given ``path`` to the proxy FS.
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

        if not _mode.writing:
            if not self.exists(_path):
                raise errors.ResourceNotFound(path)

            if not self._proxy.exists(_path):
                return self.delegate_fs().openbin(_path, mode, buffering, **options)

        elif _mode.appending or _mode.updating:
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
