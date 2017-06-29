# coding: utf-8
"""Proxy filesystem base class.
"""
import abc
import six

from ..base import FS
from ..wrapfs import WrapFS


class ProxyMeta(abc.ABCMeta):
    """Prevent classes from using `WrapFS` implementations.

    With this metaclass, the `Proxy` methods use any other available
    implementation, falling back to `WrapFS` only in last resort (i.e., for
    `WrapFS.delegate_fs` and `WrapFS.delegate_path` if the derived object does
    not overload those methods). This prevents the wrapper from directly using
    the delegate filesystem methods, and instead forces it to use `FS`
    implementations that rely on the *essential* methods, which must be
    implemented.
    """

    def __new__(cls, name, bases, attrs):
        _bases = bases + (FS,)
        exclude = ('__init__',)
        for base in _bases:
            if base is not WrapFS:
                for k,v in vars(base).items():
                    if callable(v) and k not in exclude:
                        attrs.setdefault(k, v)
        return super(ProxyMeta, cls).__new__(cls, name, bases, attrs)


@six.add_metaclass(ProxyMeta)
class Proxy(WrapFS):
    """A proxy filesystem.

    Proxies are `fs.wrapfs.WrapFS` subclasses that do more than just relying
    on the delegate filesystem internaly. They only require the essential
    filesystem methods to be declared, and can use `fs.base.FS` non-essential
    methods implementation.

    Proxies must implement an additional `proxy_fs` method, that returns the
    secondary filesystem the proxy uses, or None if they do not us any
    (in which case, it should probably be a `WrapFS` instead).

    .. aafig::

        +---------+
        |  Proxy  |
        +----+----+
             |                          self.proxy_fs()
             +-------------------------------+
             |                               |
             | self.delegate_fs()       +----+------+
             |                          |           |
             v                          v           v
        +----+-------+                 None     +---+--------+
        |  Primary   |                          | Secondary  |
        | Filesystem |                          | Filesystem |
        +------------+                          +------------+


    """



    @abc.abstractmethod
    def proxy_fs(self):
        return NotImplemented
