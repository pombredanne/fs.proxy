# coding: utf-8
from __future__ import absolute_import
from __future__ import unicode_literals

import os

import zipfile
import tempfile
import unittest

import fs.test
import fs.wrap
import fs.memoryfs
import fs.tempfs
import fs.proxy.writer

from .utils import mock


class TestProxyWriter(fs.test.FSTestCases, unittest.TestCase):

    def make_fs(self):
        mem = fs.memoryfs.MemoryFS()
        f = fs.proxy.writer.ProxyWriter(fs.wrap.WrapReadOnly(mem))
        f.mem = mem
        return f

    def test_proxy_view(self):
        # Add some entries in the filesystem
        self.fs.mem.touch('corge.txt')
        self.fs.mem.makedirs('foo/bar/baz')
        self.fs.mem.touch('foo/qux.txt')

        # Check we can see them through both FS
        self.assertEqual(set(self.fs.listdir('/')), {'corge.txt', 'foo'})
        self.assertEqual(set(self.fs.mem.listdir('/')), {'corge.txt', 'foo'})

        # Pretend we removed them from the proxy wrapper
        self.fs.removetree('/')

        # Check that we have a nice, empty root
        self.assertFalse(self.fs.listdir('/'))

        # Attempt to create a file in lieu of a directory
        self.fs.appendbytes('foo', b'abcdef')

        # Check it is still a directory in the wrapped FS
        self.assertTrue(self.fs.mem.isdir('foo'))

        # Check both respective views
        self.assertTrue(self.fs.mem.exists('corge.txt'))
        self.assertTrue(self.fs.mem.exists('foo/qux.txt'))
        self.assertFalse(self.fs.exists('corge.txt'))
        self.assertFalse(self.fs.exists('foo/qux.txt'))

    def test_relocate_on_update(self):
        text1 = 'Hello, I\'m Foo !\n'
        text2 = 'Hi Foo ! I\' Bar.\n'
        self.fs.mem.settext('foo.txt', text1)
        self.assertEqual(self.fs.mem.gettext('foo.txt'), text1)
        self.assertFalse(self.fs.proxy_fs().exists('foo.txt'))
        with self.fs.open('foo.txt', 'a') as f:
            f.write(text2)
        self.assertEqual(self.fs.mem.gettext('foo.txt'), text1)
        self.assertEqual(self.fs.gettext('foo.txt'), text1+text2)
        self.assertTrue(self.fs.proxy_fs().exists('foo.txt'))

        text3 = 'I am grault.\n'
        text4 = 'No, I AM GROOT\n'
        self.fs.mem.settext('grault.txt', text3)
        self.assertEqual(self.fs.mem.gettext('grault.txt'), text3)
        self.assertFalse(self.fs.proxy_fs().exists('grault.txt'))
        with self.fs.open('grault.txt', 'w') as f:
            f.write(text4)
        self.assertEqual(self.fs.mem.gettext('grault.txt'), text3)
        self.assertEqual(self.fs.gettext('grault.txt'), text4)
        self.assertTrue(self.fs.proxy_fs().exists('grault.txt'))

        text5 = 'Egg, bacon and Spam\n'
        self.fs.mem.settext('menu.txt', text5)
        self.assertEqual(self.fs.mem.gettext('menu.txt'), text5)
        self.assertEqual(self.fs.gettext('menu.txt'), text5)
        with self.fs.open('menu.txt') as f:
            self.assertEqual(f.read(), text5)
        self.assertTrue(self.fs.mem.exists('menu.txt'))
        self.assertFalse(self.fs.proxy_fs().exists('menu.txt'))

    def test_relocate_on_setinfo(self):
        self.fs.mem.touch('spam.txt')
        self.assertTrue(self.fs.mem.exists('spam.txt'))
        self.assertFalse(self.fs.proxy_fs().exists('spam.txt'))

        self.fs.setinfo('spam.txt', {'basic': {'is_dir': True}})
        self.assertTrue(self.fs.mem.exists('spam.txt'))
        self.assertTrue(self.fs.proxy_fs().exists('spam.txt'))

    def destroy_fs(self, fs):
        fs.close()
        del fs.mem
        del fs


class TestSwapWriter(TestProxyWriter, unittest.TestCase):

    def make_fs(self):
        mem = fs.memoryfs.MemoryFS()
        f = fs.proxy.writer.SwapWriter(fs.wrap.WrapReadOnly(mem))
        f.mem = mem
        return f

    def test_swap(self):
        self.assertIsInstance(self.fs.proxy_fs(), fs.memoryfs.MemoryFS)
        self.assertIsInstance(self.fs._swap_fs, fs.tempfs.TempFS)

        with mock.patch.object(self.fs, 'MEMORY_USAGE_LIMIT', 512):
            self.fs.setbytes('foo.txt', b'a'*1024)
            self.fs.listdir('/')

        self.assertIs(self.fs.proxy_fs(), self.fs._swap_fs)
