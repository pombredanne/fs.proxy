# coding: utf-8
from __future__ import absolute_import
from __future__ import unicode_literals

import io
import os
import abc
import six
import sys

# Have to use absolute imports in
# case the module is not installed
# locally (issue in import order,
# as fs.archive.test is mistaken
# for fs.test ?!)
from fs import open_fs
from fs import walk
from fs import errors
from fs.test import UNICODE_TEXT


@six.add_metaclass(abc.ABCMeta)
class ArchiveTestCases(object):

    @abc.abstractmethod
    def compress(self, handle, fs):
        pass

    @abc.abstractmethod
    def load_archive(self, handle):
        pass

    @abc.abstractmethod
    def remove_archive(self, handle):
        pass

    def make_source_fs(self):
        return open_fs('temp://')

    def build_source(self, fs):
        fs.makedirs('foo/bar/baz')
        fs.makedir('tmp')
        fs.settext('top.txt', 'Hello, World')
        fs.settext('top2.txt', 'Hello, World')
        fs.settext('foo/bar/egg', 'foofoo')
        fs.makedir('unicode')
        fs.settext('unicode/text.txt', UNICODE_TEXT)

    def setUp(self):
        self.source_fs = source_fs = self.make_source_fs()
        self.build_source(source_fs)
        self.compress(self.handle, source_fs)
        self.fs = self.load_archive(self.handle)

    def tearDown(self):
        self.source_fs.close()
        self.fs.close()
        self.remove_archive(self.handle)

    def test_repr(self):
        repr(self.fs)

    def test_str(self):
        self.assertIsInstance(six.text_type(self.fs), six.text_type)

    def test_scandir(self):

        dirsize = self.fs.getdetails('foo').size
        if dirsize is None:
            self.skipTest("Filesystem does not support 'details' namespace")

        for entry in self.fs.scandir('/', namespaces=('details',)):
            if entry.is_dir:
                self.assertEqual(entry.size, dirsize)
            else:
                self.assertEqual(entry.size, len(self.fs.getbytes(entry.name)))

        with self.assertRaises(errors.ResourceNotFound):
            _ = next(self.fs.scandir('what'))
        with self.assertRaises(errors.DirectoryExpected):
            _ = next(self.fs.scandir('top.txt'))



    def test_readonly(self):
        if not self.fs._meta.get('read_only', False):
            self.skipTest("Filesystem is not read-only")

        with self.assertRaises(errors.ResourceReadOnly):
            self.fs.makedir('newdir')
        with self.assertRaises(errors.ResourceReadOnly):
            self.fs.remove('top.txt')
        with self.assertRaises(errors.ResourceReadOnly):
            self.fs.removedir('foo/bar/baz')
        with self.assertRaises(errors.ResourceReadOnly):
            self.fs.create('foo.txt')
        with self.assertRaises(errors.ResourceReadOnly):
            self.fs.setinfo('foo.txt', {})

    def test_getinfo(self):
        root = self.fs.getinfo('/')
        self.assertEqual(root.name, '')
        self.assertTrue(root.is_dir)

        top = self.fs.getinfo('top.txt', 'details')
        self.assertEqual(top.size, 12)
        self.assertFalse(top.is_dir)

    def test_listdir(self):
        self.assertEqual(
            sorted(self.source_fs.listdir('/')),
            sorted(self.fs.listdir('/'))
        )
        with self.assertRaises(errors.DirectoryExpected):
            self.fs.listdir('top.txt')
        with self.assertRaises(errors.ResourceNotFound):
            self.fs.listdir('nothere')

    def test_open(self):
        with self.fs.open('top.txt') as f:
            chars = []
            while True:
                c = f.read(2)
                if not c:
                    break
                chars.append(c)
            self.assertEqual(
                ''.join(chars),
                'Hello, World'
            )
        with self.assertRaises(errors.ResourceNotFound):
            with self.fs.open('nothere.txt') as f:
                pass
        with self.assertRaises(errors.FileExpected):
            with self.fs.open('foo') as f:
                pass

    def test_gettext(self):
        self.assertEqual(self.fs.gettext('top.txt'), 'Hello, World')
        self.assertEqual(self.fs.gettext('foo/bar/egg'), 'foofoo')
        self.assertRaises(errors.ResourceNotFound, self.fs.getbytes, 'what.txt')
        self.assertRaises(errors.FileExpected, self.fs.gettext, 'foo')

    def test_getbytes(self):
        self.assertEqual(self.fs.getbytes('top.txt'), b'Hello, World')
        self.assertEqual(self.fs.getbytes('foo/bar/egg'), b'foofoo')
        self.assertRaises(errors.ResourceNotFound, self.fs.gettext, 'what.txt')
        self.assertRaises(errors.FileExpected, self.fs.getbytes, 'foo')

    def test_walk_files(self):
        source_files = sorted(walk.walk_files(self.source_fs))
        archive_files = sorted(walk.walk_files(self.fs))

        self.assertEqual(
            source_files,
            archive_files
        )

    def test_implied_dir(self):
        self.fs.getinfo('foo/bar')
        self.fs.getinfo('foo')