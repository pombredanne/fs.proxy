# coding: utf-8
"""A collection of wrapper filesystems.

These classes inherit from `fs.wrapfs.WrapFS`, and allow wrapping a
filesystem without relying only the delegate filesystem method
implementations. In other terms, filesystem inheriting from `fs.proxy.Proxy`
will have access to the ``delegate_fs`` of `fs.wrapfs.WrapFS`, but other
than that will behave like `fs.base.FS`. Implementing a `fs.proxy.Proxy`
is only as tough as implementing a plain filesystem.
"""

__license__ = "MIT"
__copyright__ = "Copyright (c) 2017 Martin Larralde"
__author__ = "Martin Larralde <martin.larralde@ens-cachan.fr>"
__version__ = 'dev'

# Dynamically get the version of the installed module
try:
    import pkg_resources
    __version__ = pkg_resources.get_distribution(__name__).version
except Exception:
    pkg_resources = None
finally:
    del pkg_resources
