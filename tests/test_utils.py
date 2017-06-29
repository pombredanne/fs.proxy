# coding: utf-8
from __future__ import unicode_literals
from __future__ import absolute_import

import sys
import unittest
import importlib

import fs.proxy._utils

from . import utils


class TestUnique(unittest.TestCase):

    def _test_unique(self, unique):
        self.assertEqual(list(unique('AAABBCCCCDD')), list('ABCD'))
        self.assertEqual(list(unique('AaAABbCCCDd')), list('AaBbCDd'))
        self.assertEqual(list(unique('AaBbcCDd', key=str.lower)), list('ABcD'))

    def setUp(self):
        sys.modules.pop('fs.proxy._utils')
        if utils.itertoolz is not None:
            sys.modules.pop('tlz.itertoolz')

    @unittest.skipIf(utils.itertoolz is None, "itertoolz not available")
    def test_tlz_unique(self):
        "Test the behaviour of (cy)toolz.itertoolz.unique function."
        unique = importlib.import_module('fs.proxy._utils').unique
        self.assertTrue(unique.__module__.endswith('toolz.itertoolz'))
        self._test_unique(unique)

    def test_itertools_unique(self):
        "Test the behaviour of the itertools unique_everseen recipe."
        sys.modules['tlz.itertoolz'] = None
        unique = importlib.import_module('fs.proxy._utils').unique
        self.assertEqual(unique.__module__, 'fs.proxy._utils')
        self._test_unique(unique)
