fs.proxy
========

|Source| |PyPI| |Travis| |Codecov| |Codacy| |Format| |License|

.. |Codacy| image:: https://img.shields.io/codacy/grade/6c923611c7fd49809cfe58a4d2e131ce/master.svg?style=flat-square&maxAge=300
   :target: https://www.codacy.com/app/althonos/fs.proxy/dashboard

.. |Travis| image:: https://img.shields.io/travis/althonos/fs.proxy/master.svg?style=flat-square&maxAge=300
   :target: https://travis-ci.org/althonos/fs.proxy/branches

.. |Codecov| image:: https://img.shields.io/codecov/c/github/althonos/fs.proxy/master.svg?style=flat-square&maxAge=300
   :target: https://codecov.io/gh/althonos/fs.proxy

.. |PyPI| image:: https://img.shields.io/pypi/v/fs.proxy.svg?style=flat-square&maxAge=300
   :target: https://pypi.python.org/pypi/fs.proxy

.. |Format| image:: https://img.shields.io/pypi/format/fs.proxy.svg?style=flat-square&maxAge=300
   :target: https://pypi.python.org/pypi/fs.proxy

.. |Versions| image:: https://img.shields.io/pypi/pyversions/fs.proxy.svg?style=flat-square&maxAge=300
   :target: https://travis-ci.org/althonos/fs.proxy

.. |License| image:: https://img.shields.io/pypi/l/fs.proxy.svg?style=flat-square&maxAge=300
   :target: https://choosealicense.com/licenses/mit/

.. |Source| image:: https://img.shields.io/badge/source-GitHub-303030.svg?maxAge=300&style=flat-square
   :target: https://github.com/althonos/fs.proxy


Requirements
------------

+-------------------+-----------------+-------------------+--------------------+
| **pyfilesystem2** | |PyPI fs|       | |Source fs|       | |License fs|       |
+-------------------+-----------------+-------------------+--------------------+
| **six**           | |PyPI six|      | |Source six|      | |License six|      |
+-------------------+-----------------+-------------------+--------------------+
| **psutil**        | |PyPI psutil|   | |Source psutil|   | |License psutil|   |
+-------------------+-----------------+-------------------+--------------------+

.. |License six| image:: https://img.shields.io/pypi/l/six.svg?maxAge=300&style=flat-square
   :target: https://choosealicense.com/licenses/mit/

.. |Source six| image:: https://img.shields.io/badge/source-GitHub-303030.svg?maxAge=300&style=flat-square
   :target: https://github.com/benjaminp/six

.. |PyPI six| image:: https://img.shields.io/pypi/v/six.svg?maxAge=300&style=flat-square
   :target: https://pypi.python.org/pypi/six

.. |License fs| image:: https://img.shields.io/badge/license-MIT-blue.svg?maxAge=300&style=flat-square
   :target: https://choosealicense.com/licenses/mit/

.. |Source fs| image:: https://img.shields.io/badge/source-GitHub-303030.svg?maxAge=300&style=flat-square
   :target: https://github.com/PyFilesystem/pyfilesystem2

.. |PyPI fs| image:: https://img.shields.io/pypi/v/fs.svg?maxAge=300&style=flat-square
   :target: https://pypi.python.org/pypi/fs

.. |License psutil| image:: https://img.shields.io/pypi/l/psutil.svg?maxAge=300&style=flat-square
   :target: https://choosealicense.com/licenses/bsd-3-clause/

.. |Source psutil| image:: https://img.shields.io/badge/source-GitHub-303030.svg?maxAge=300&style=flat-square
   :target: https://github.com/giampaolo/psutil

.. |PyPI psutil| image:: https://img.shields.io/pypi/v/psutil.svg?maxAge=300&style=flat-square
   :target: https://pypi.python.org/pypi/psutil


Installation
------------

Install directly from PyPI, using `pip <https://pip.pypa.io/>`_ ::

    pip install fs.proxy


Usage
-----

This module revolves around the notion of proxy filesystems, akin to wrapper
filesystems from the core library, but using a *proxy* in combination with the
*delegate* filesystem used by ``WrapFS``. They also make it easier to create generic
wrappers, as ``fs.proxy.base.Proxy`` subclasses will use the ``fs.base.FS`` method
implementation, while actually deriving from ``WrapFS`` !

This extension includes a base ``fs.proxy.base.Proxy`` class, that requires only the
`essential filesystem methods
<https://pyfilesystem2.readthedocs.io/en/latest/implementers.html#essential-methods>`_
to be implemented.

The ``fs.proxy.writer`` package also declares two classes that can be used to make
any read-only filesystem *writeable*, using a secondary writeable filesystem:
``fs.proxy.writer.ProxyWriter`` and ``fs.proxy.writer.SwapWriter``. ``ProxyWriter``
will always write modifications to the secondary filesystem (often a ``MemoryFS`` or
a ``TempFS``), while ``SwapWriter`` will use a third *backup* filesystem in case
the memory footprint of the proxy filesystem becomes too large (swapping from a
``MemoryFS`` to an ``OSFS``, etc.). For instance, let's pretend we can write to
the root:

.. code:: python

   >>> import fs.proxy.writer

   >>> read_only_fs = fs.open_fs(u'/') # this is not actually read-only ;)
   >>> writeable_fs = fs.proxy.writer.ProxyWriter(read_only_fs)
   >>> writeable_fs.setbytes(u'/root.txt', b'I am writing in root !')

   >>> writeable_fs.exists(u'/root.txt')
   True
   >>> read_only_fs.exists(u'/root.txt')
   False


See also
--------

* `fs <https://github.com/Pyfilesystem/pyfilesystem2>`_, the core pyfilesystem2 library
* `fs.archive <https://github.com/althonos/fs.archive>`_, enhanced archive filesystems
  for pyfilesystem2
* `fs.sshfs <https://github.com/althonos/fs.sshfs>`_, a SFTP/SSH implementation for
  pyfilesystem2 using `paramiko <https://github.com/paramiko/paramiko>`_
