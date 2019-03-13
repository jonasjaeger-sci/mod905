# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the PathStorage classes."""
import logging
import os
import unittest
import tempfile
import tarfile
import pathlib
from pyretis.inout.common import make_dirs
from pyretis.core.pathensemble import PathEnsemble
from pyretis.inout.archive import (
    add_to_tar_file,
    generate_traj_names,
    PathStorage,
    PathStorageTar,
)
from pyretis.inout.formats import (
    OrderPathFormatter,
    EnergyPathFormatter,
    PathExtFormatter,
)
from .help import create_external_path, turn_on_logging

logging.disable(logging.CRITICAL)
HERE = os.path.abspath(os.path.dirname(__file__))


def create_dirs_and_files(ensemble, path):
    """Create some directories and files for the testing."""
    for i in ensemble.directories():
        make_dirs(i)
    new_pos = []
    for i in path.phasepoints:
        filename = os.path.join(
            ensemble.directory['generate'], i.particles.get_pos()[0]
        )
        new_pos.append((filename, i.particles.get_pos()[1]))
        pathlib.Path(filename).touch()
    for phasepoint, pos in zip(path.phasepoints, new_pos):
        phasepoint.particles.set_pos(pos)


def generate_file_names(start, stop, dirname, paths):
    """Just generate some fake file names."""
    files = []
    for i in range(start, stop):
        filename = os.path.join(dirname, 'file-{}.txt'.format(i))
        pathlib.Path(filename).touch()
        files.append(
            (filename, os.path.join(*paths, 'file-{}.txt'.format(i)))
        )
    return files


def look_for_files_and_dirs(dirname):
    """Return files or directories found in the given path."""
    files = []
    dirs = []
    for i in os.scandir(dirname):
        if i.is_file():
            files.append(i.name)
        elif i.is_dir():
            dirs.append(i.name)
    return files, dirs


class TestArchiveMethods(unittest.TestCase):
    """Test methods defined in the module."""

    def test_add_to_tar(self):
        """Test adding files."""
        with tempfile.TemporaryDirectory() as tempdir:
            tar_file = os.path.join(tempdir, 'test.tar')
            # Create some files to add:
            files = generate_file_names(0, 5, tempdir, ['aaa', 'bbb', 'ccc'])
            add = add_to_tar_file(tar_file, files, file_mode='w')
            self.assertTrue(add)
            with tarfile.open(tar_file, 'r') as tar:
                members = [i.name for i in tar.getmembers()]
                self.assertEqual(len(members), len(files))
                for _, i in files:
                    self.assertIn(i, members)
            # Append to the file:
            files2 = generate_file_names(5, 10, tempdir, ['123', '456', '689'])
            add = add_to_tar_file(tar_file, files2, file_mode='a')
            self.assertTrue(add)
            files += files2
            with tarfile.open(tar_file, 'r') as tar:
                members = [i.name for i in tar.getmembers()]
                self.assertEqual(len(members), len(files))
                for (_, i) in files:
                    self.assertIn(i, members)
            # Check if we can get an read error:
            with open(tar_file, 'w') as tar:
                tar.write('Some Men Just Want to Watch The World Burn')
            add = add_to_tar_file(tar_file, files, file_mode='a')
            self.assertFalse(add)

    def test_generate_names(self):
        """Test the generation of trajectory names for the archive."""
        path, _ = create_external_path()
        files = generate_traj_names(path, 'traj')
        for (src, trg) in files:
            self.assertEqual(
                trg,
                os.path.join('traj', src)
            )


class TestPathStorageTar(unittest.TestCase):
    """Test the PathStorageTar class."""

    def test_output(self):
        """Test that we can output to the storage."""
        storage = PathStorageTar()
        path, _ = create_external_path()
        with tempfile.TemporaryDirectory() as tempdir:
            ensemble = PathEnsemble(1, [0.0, 1.0, 2.0], exe_dir=tempdir)
            create_dirs_and_files(ensemble, path)
            for j, status in enumerate(('ACC', 'REJ')):
                files = storage.output(10 + j, (path, status, ensemble))
                # Check if we got the files in the tar-files:
                archive = storage.archive_name_from_status(status)
                tar_file = os.path.join(ensemble.directory['traj'], archive)
                with tarfile.open(tar_file, 'r') as tar:
                    members = [i.name for i in tar.getmembers()]
                    self.assertEqual(len(members), len(files))
                    for _, i in files:
                        self.assertIn(i, members)

    def test_output_recreate(self):
        """Test that the backup of archives does work."""
        storage = PathStorageTar()
        path, _ = create_external_path()
        with tempfile.TemporaryDirectory() as tempdir:
            ensemble = PathEnsemble(1, [0.0, 1.0, 2.0], exe_dir=tempdir)
            create_dirs_and_files(ensemble, path)
            storage.output(10, (path, 'ACC', ensemble))
            tar_file = os.path.join(ensemble.directory['traj'],
                                    storage.archive_name_from_status('ACC'))
            # This will overwrite/corrupt the tar archive:
            with open(tar_file, 'w') as tar:
                tar.write('Some Men Just Want to Watch The World Burn')
            # We should be able to create a new archive and backup the old:
            storage.output(11, (path, 'ACC', ensemble))
            expected = [
                storage.archive_name_from_status('ACC'),
                '{}_000'.format(storage.archive_name_from_status('ACC'))
            ]
            files, _ = look_for_files_and_dirs(ensemble.directory['traj'])
            self.assertEqual(len(expected), len(files))
            for i in expected:
                self.assertIn(i, files)


class TestPathStorage(unittest.TestCase):
    """Test the PathStorage class."""

    def test_write_fail(self):
        """Test that the write method give an critical log message."""
        storage = PathStorage()
        with turn_on_logging():
            with self.assertLogs('pyretis.inout.archive', level='CRITICAL'):
                storage.write('test')

    def test_formatter_info(self):
        """Test that we get correct info about formatters."""
        storage = PathStorage()
        info = storage.formatter_info()
        correct = [OrderPathFormatter, EnergyPathFormatter, PathExtFormatter]
        self.assertEqual(len(info), len(correct))
        for i in correct:
            self.assertIn(i, info)

    def test_output(self):
        """Test that we can create output."""
        storage = PathStorage()
        path, _ = create_external_path()
        with tempfile.TemporaryDirectory() as tempdir:
            ensemble = PathEnsemble(1, [0.0, 1.0, 2.0], exe_dir=tempdir)
            create_dirs_and_files(ensemble, path)
            # Now, there should be no output yet:
            files, dirs = look_for_files_and_dirs(ensemble.directory['traj'])
            self.assertEqual(len(files), 0)
            self.assertEqual(len(dirs), 0)
            # Output some trajectories:
            statuses = ('ACC', 'REJ', 'AN USER ERROR')
            files = {}
            for i, status in enumerate(statuses):
                written = storage.output(10 + i, (path, status, ensemble))
                target_dir = os.path.join(
                    storage.archive_name_from_status(status),
                    storage.out_dir_fmt.format(10 + i),
                )
                # Grab path to the files added:
                files[target_dir] = [j[0] for j in written]
            # We now expect to have some files:
            for key, val in files.items():
                dir_name = os.path.join(ensemble.directory['traj'], key)
                self.assertTrue(os.path.isdir(dir_name))
                # Check that the files we claimed to make are present
                # as files:
                for i in val:
                    self.assertTrue(os.path.isfile(i))
                # Just search for all files in the given archive folder
                # to check that we did not create anything extra:
                found_files = []
                for root, _, filei in os.walk(dir_name):
                    found_files += [os.path.join(root, i) for i in filei]
                self.assertEqual(
                    len(val), len(found_files)
                )
                for i in found_files:
                    self.assertIn(i, val)


if __name__ == '__main__':
    unittest.main()
