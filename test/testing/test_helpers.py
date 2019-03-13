# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test common methods that are used in testing."""
import os
import pathlib
import tempfile
import unittest
from pyretis.inout.common import make_dirs
from pyretis.testing.helpers import search_for_files, clean_dir
from pyretis.testing.systemhelp import create_system_ext


class TestSearchForFiles(unittest.TestCase):
    """Test that we can search for files."""

    def test_search(self):
        """Test the search for files method."""
        dirs = ['these', 'are', 'directories']
        files = ['test1.txt', 'test2.txt', 'test3.txt']
        created_files = []
        created_files_match = []
        with tempfile.TemporaryDirectory() as tempdir:
            # Make some files in the root directory:
            for i in files:
                filename = pathlib.Path().joinpath(tempdir, i)
                pathlib.Path(filename).touch()
                created_files.append(filename)
            # Make some folders with files:
            for i, j in zip(dirs, files):
                dirname = pathlib.Path().joinpath(tempdir, i)
                make_dirs(dirname)
                filename = pathlib.Path().joinpath(dirname, j)
                pathlib.Path(filename).touch()
                created_files.append(filename)
            # Test searching for all files:
            found_files = search_for_files(tempdir)
            self.assertEqual(
                sorted(found_files),
                sorted([str(i) for i in created_files])
            )
            # Test searching for a specific file name:
            found_files = search_for_files(tempdir, match='test4.txt')
            self.assertEqual(len(found_files), 0)
            found_files = search_for_files(tempdir, match='test3.txt')
            created_files_match = [
                str(i) for i in created_files if i.name == 'test3.txt'
            ]
            self.assertEqual(sorted(found_files), sorted(created_files_match))

    def test_clean_dir(self):
        """Test the search for files method."""
        created_files = []
        with tempfile.TemporaryDirectory() as tempdir:
            # Make some files in the root directory:
            for i in range(11):
                filename = pathlib.Path().joinpath(tempdir, 'file{}'.format(i))
                pathlib.Path(filename).touch()
                created_files.append(filename)
            files = [i for i in os.scandir(tempdir) if i.is_file]
            self.assertEqual(len(files), len(created_files))
            # Remove the files:
            clean_dir(tempdir)
            files = [i for i in os.scandir(tempdir) if i.is_file]
            self.assertEqual(len(files), 0)


class TestSystemHelp(unittest.TestCase):
    """Test the System helpers."""

    def test_create(self):
        """Test that we can create systems."""
        cases = [
            (None, False),
            (None, True),
            (('file.txt', 1), False),
            (('file.txt', 2), True),
        ]
        for case in cases:
            system = create_system_ext(pos=case[0], vel=case[1])
            if case[0] is None:
                self.assertEqual(system.particles.get_pos(), (None, None))
            else:
                self.assertEqual(system.particles.get_pos(), case[0])
            self.assertEqual(system.particles.get_vel(), case[1])


if __name__ == '__main__':
    unittest.main()
