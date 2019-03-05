# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the PathStorage class."""
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
)
from pyretis.inout.formats import (
    OrderPathFormatter,
    EnergyPathFormatter,
    PathExtFormatter,
)
from .help import create_external_path

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


class TestPathStorage(unittest.TestCase):
    """Test the PathStorage class."""

    def test_write_fail(self):
        """Test that the write method give an error."""
        storage = PathStorage()
        with self.assertRaises(NotImplementedError):
            storage.write('test')

    def test_output(self):
        """Test that we can output to the storage."""
        storage = PathStorage()
        path, _ = create_external_path()
        with tempfile.TemporaryDirectory() as tempdir:
            ensemble = PathEnsemble(1, [0.0, 1.0, 2.0], exe_dir=tempdir)
            create_dirs_and_files(ensemble, path)
            for j, (status, tarbase) in enumerate(zip(('ACC', 'REJ'),
                                                      (storage.tar_acc,
                                                       storage.tar_rej))):
                files = storage.output(10 + j, (path, status, ensemble))
                # Check if we got the files in the tar-files:
                tar_file = os.path.join(ensemble.directory['traj'],
                                        tarbase)
                with tarfile.open(tar_file, 'r') as tar:
                    members = [i.name for i in tar.getmembers()]
                    self.assertEqual(len(members), len(files))
                    for _, i in files:
                        self.assertIn(i, members)

    def test_output_recreate(self):
        """Test that the backup of archives does work."""
        storage = PathStorage()
        path, _ = create_external_path()
        with tempfile.TemporaryDirectory() as tempdir:
            ensemble = PathEnsemble(1, [0.0, 1.0, 2.0], exe_dir=tempdir)
            create_dirs_and_files(ensemble, path)
            storage.output(10, (path, 'ACC', ensemble))
            tar_file = os.path.join(ensemble.directory['traj'],
                                    storage.tar_acc)
            with open(tar_file, 'w') as tar:
                tar.write('Some Men Just Want to Watch The World Burn')
            storage.output(11, (path, 'ACC', ensemble))
            expected = [storage.tar_acc, '{}_000'.format(storage.tar_acc)]
            files = []
            for i in os.scandir(ensemble.directory['traj']):
                if i.is_file():
                    files.append(i.name)
            self.assertEqual(len(expected), len(files))
            for i in expected:
                self.assertIn(i, files)

    def test_formatter_info(self):
        """Test that we get correct info about formatters."""
        storage = PathStorage()
        info = storage.formatter_info()
        correct = [OrderPathFormatter, EnergyPathFormatter, PathExtFormatter]
        self.assertEqual(len(info), len(correct))
        for i in correct:
            self.assertIn(i, info)


if __name__ == '__main__':
    unittest.main()
