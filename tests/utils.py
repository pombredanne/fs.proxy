# coding: utf-8
from __future__ import unicode_literals
from __future__ import absolute_import

try:
    from tlz import itertoolz
except ImportError:
    itertoolz = None

try:
    from unittest import mock
except ImportError:
    import mock
