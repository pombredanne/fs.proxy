# coding: utf-8
from __future__ import absolute_import
from __future__ import unicode_literals

import os
import io
import zipfile
import tempfile
import unittest

from six.moves import filterfalse

import fs.test
import fs.wrap
import fs.errors
import fs.memoryfs
import fs.archive.zipfs

from fs.path import relpath, join, forcedir, abspath, recursepath
from fs.archive.test import ArchiveReadTestCases, ArchiveIOTestCases

class TestZipFS(fs.test.FSTestCases, unittest.TestCase):

    def make_fs(self):
        self.tempfile = tempfile.mktemp()
        return fs.archive.zipfs.ZipFS(self.tempfile)

    def destroy_fs(self, fs):
        fs.close()
        if os.path.exists(self.tempfile):
            os.remove(self.tempfile)
        del self.tempfile


class TestZipReadFS(ArchiveReadTestCases, unittest.TestCase):

    def make_source_fs(self):
        return fs.memoryfs.MemoryFS()

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



class TestZipFSIO(unittest.TestCase, ArchiveIOTestCases):

    _archive_fs = fs.archive.zipfs.ZipFS

    @staticmethod
    def make_source_fs():
        return fs.memoryfs.MemoryFS()

    @staticmethod
    def load_archive(handle):
        return fs.archive.zipfs.ZipFS(handle)

    @staticmethod
    def compress(handle, source_fs):
        if hasattr(handle, 'seek') and handle.seekable():
            handle.seek(0)
        saver = fs.archive.zipfs.ZipSaver(handle, False)
        saver.to_stream(source_fs)

    @staticmethod
    def iter_files(handle):
        if hasattr(handle, 'seek') and handle.seekable():
            handle.seek(0)
        with zipfile.ZipFile(handle) as z:
            for name in z.namelist():
                if not name.endswith('/') and name:
                    yield abspath(name)

    @staticmethod
    def iter_dirs(handle):
        zipname = lambda n: abspath(n).rstrip('/')
        seen = set()

        if hasattr(handle, 'seek') and handle.seekable():
            handle.seek(0)

        with zipfile.ZipFile(handle) as z:

            namelist = z.namelist()

            for name in namelist:

                if name.endswith('/'):
                    seen.add(name)
                    yield zipname(name)

                else:

                    for path in recursepath(name):
                        if not path in '/' and path != abspath(name):
                            if not path in seen:
                                seen.add(path)
                                yield zipname(path)


            # for name in name:
            #     for path in recursepath(name):
            #         if not path in '/' and not relpath(path) in namelist:
            #             if not path in seen:
            #                 seen.add(path)
            #                 yield zipname(path)
