# coding: utf-8
from __future__ import absolute_import
from __future__ import unicode_literals

import os
import io
import zipfile
import tempfile
import unittest

import fs.test
import fs.wrap
import fs.errors
import fs.memoryfs
import fs.archive.zipfs

from fs.path import relpath, join, forcedir, abspath
from fs.archive.test import ArchiveTestCases


class TestZipFS(fs.test.FSTestCases, unittest.TestCase):

    def make_fs(self):
        self.tempfile = tempfile.mktemp()
        return fs.archive.zipfs.ZipFS(self.tempfile)

    def destroy_fs(self, fs):
        fs.close()
        if os.path.exists(self.tempfile):
            os.remove(self.tempfile)
        del self.tempfile


class TestZipReadFS(ArchiveTestCases, unittest.TestCase):

    def compress(self, handle, source_fs):
        with zipfile.ZipFile(handle, 'w') as zipf:
            for base, dirs, files in source_fs.walk():
                # Create entry only for empty directories
                if not files:
                    zipf.writestr(relpath(forcedir(base)), '')
                # Directly create file entries
                for f in files:
                    filename = relpath(join(base, f.name)).rstrip('/')
                    zipf.writestr(filename, source_fs.gettext(filename))

    def load_archive(self, handle):
        return fs.archive.zipfs.ZipReadFS(handle)

    def setUp(self):
        self.handle = io.BytesIO()
        super(TestZipReadFS, self).setUp()

    def remove_archive(self, handle):
        handle.close()

    def test_create_failed(self):
        self.assertRaises(fs.errors.CreateFailed, fs.archive.zipfs.ZipFS, 1)

    def test_getinfo_errors(self):
        self.assertRaises(fs.errors.ResourceNotFound, self.fs.getinfo, 'boom.txt')

    def test_getbytes_errors(self):
        self.assertRaises(fs.errors.ResourceNotFound, self.fs.getbytes, 'boom.txt')
        self.assertRaises(fs.errors.FileExpected, self.fs.getbytes, 'foo')



class TestZipFSIO(unittest.TestCase):

    def make_archive(self, handle):
        with zipfile.ZipFile(handle, 'w') as z:
            z.writestr('foo.txt', 'Hello World !')
            z.writestr('egg/', '')
            z.writestr('baz/bar.txt', 'Savy ?')

        if hasattr(handle, 'seek') and handle.seekable():
            handle.seek(0)

        return handle

    def list_files(self, handle):
        if hasattr(handle, 'seek') and handle.seekable():
            handle.seek(0)
        with zipfile.ZipFile(handle) as z:
            return {abspath(name).rstrip('/') for name in z.namelist()}

    def _test_read(self, fs):
        self.assertEqual(set(fs.listdir('/')), {'foo.txt', 'egg', 'baz'})
        self.assertEqual(fs.gettext('foo.txt'), 'Hello World !')
        self.assertTrue(fs.isdir('egg'))

    def _test_read_write(self, fs):
        self._test_read(fs)
        self._test_write(fs)

    def _test_write(self, fs):
        fs.touch('ham.txt')
        fs.makedirs('/spam/qux')
        fs.touch('/spam/boom.txt')

        if fs.isfile('foo.txt'):
            fs.remove('foo.txt')
        if fs.isdir('egg'):
            fs.removedir('egg')

        self.assertTrue(fs.isdir('spam/qux'))
        self.assertTrue(fs.isfile('spam/boom.txt'))
        self.assertFalse(fs.isdir('egg') or fs.exists('egg'))

    def test_read_stream(self):
        stream = self.make_archive(io.BytesIO())
        with fs.archive.zipfs.ZipFS(io.BufferedReader(stream)) as zipfs:
            self._test_read(zipfs)
        self.assertEqual(self.list_files(stream),
            {'/egg', '/foo.txt', '/baz/bar.txt'})

    def test_read_write_stream(self):
        stream = self.make_archive(io.BytesIO())
        with fs.archive.zipfs.ZipFS(stream) as zipfs:
            self._test_read_write(zipfs)
        self.assertEqual(self.list_files(stream),
            {'/ham.txt', '/spam/boom.txt', '/spam/qux', '/baz/bar.txt'})

    def test_write_stream(self):
        stream = io.BytesIO()
        stream.readable = lambda: False   # mock a write-only stream

        with fs.archive.zipfs.ZipFS(stream) as zipfs:
            self._test_write(zipfs)

        self.assertEqual(self.list_files(stream),
             {'/ham.txt', '/spam/boom.txt', '/spam/qux'})

    def test_read_file(self):
        filename = self.make_archive(tempfile.mktemp())
        with fs.archive.zipfs.ZipFS(filename) as zipfs:
            self._test_read(zipfs)
        self.assertEqual(self.list_files(filename),
            {'/egg', '/foo.txt', '/baz/bar.txt'})

    def test_read_write_file(self):
        filename = self.make_archive(tempfile.mktemp())
        with fs.archive.zipfs.ZipFS(filename) as zipfs:
            self._test_read_write(zipfs)
        self.assertEqual(self.list_files(filename),
            {'/ham.txt', '/spam/boom.txt', '/spam/qux', '/baz/bar.txt'})

    def test_write_file(self):
        filename = tempfile.mktemp()
        with fs.archive.zipfs.ZipFS(filename) as zipfs:
            self._test_write(zipfs)
        self.assertEqual(self.list_files(filename),
             {'/ham.txt', '/spam/boom.txt', '/spam/qux'})
