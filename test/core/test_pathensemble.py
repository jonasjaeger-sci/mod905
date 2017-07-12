# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test functionality for the path classes."""
import logging
import os
import unittest
import tarfile
import numpy as np
from pyretis.core.path import PathExt, Path
from pyretis.core.pathensemble import (
    _generate_file_names,
    get_path_ensemble_class,
    PathEnsemble,
    PathEnsembleExt,
)
from pyretis.core.random_gen import MockRandomGenerator
from pyretis.inout.common import make_dirs
logging.disable(logging.CRITICAL)


FILE_NAME = 'file{:03d}.xyz'
DIR_NAME = os.path.abspath(os.path.join('path', 'to'))
HERE = os.path.abspath(os.path.dirname(__file__))
DIRS = [
    os.path.join(HERE, '001'),
    os.path.join(HERE, '001', 'accepted'),
    os.path.join(HERE, '001', 'accepted', 'not-needed'),
    os.path.join(HERE, '001', 'generate'),
    os.path.join(HERE, '001', 'traj'),
]


def create_dirs():
    """Just create some dirs we need for testing."""
    for i in DIRS:
        make_dirs(i)


def remove_dirs():
    """Remove the dirs we created."""
    for i in DIRS:
        try:
            os.removedirs(i)
        except OSError:
            pass


def make_fake_extpath(length=10):
    """Just return a fake path for testing."""
    rgen = MockRandomGenerator(seed=0)
    path = PathExt(rgen)
    for i in range(length):
        filename = os.path.join(DIR_NAME, FILE_NAME.format(i))
        phasepoint = {
            'order': [i],
            'pos': (filename, i),
            'vel': False,
            'vpot': 0.0,
            'ekin': 0.0
        }
        path.append(phasepoint)
    return path


def make_fake_path(length=10):
    """Just return a fake path for testing."""
    rgen = MockRandomGenerator(seed=0)
    path = Path(rgen)
    for i in range(length):
        phasepoint = {
            'order': [i],
            'pos': np.ones((5, 3)) * i,
            'vel': np.ones((5, 3)) * i,
            'vpot': 0.0,
            'ekin': 0.0
        }
        path.append(phasepoint)
    path.generated = ('fake',)
    return path


def make_fake_path_files():
    """Return a fake path and set up some files for it."""
    rgen = MockRandomGenerator(seed=0)
    path = PathExt(rgen)
    for name in (os.path.join(HERE, 'fake_path_1'),
                 os.path.join(HERE, 'fake_path_2')):
        with open(name, 'w') as output:
            output.write('Ibsens ripsbusker og andre buskevekster\n')
            output.write(name)
    for i in range(10):
        if i < 5:
            filename = os.path.join(HERE, 'fake_path_1')
        else:
            filename = os.path.join(HERE, 'fake_path_2')
        phasepoint = {
            'order': [i],
            'pos': (filename, i),
            'vel': False, 'vpot': 0.0, 'ekin': 0.0,
        }
        path.append(phasepoint)
    path.generated = ('fake',)
    return path


def remove_path_files(path):
    """Remove the files for a trajectory."""
    # Just remove the files:
    names = set()
    for i in path.trajectory():
        names.add(i['pos'][0])
    for name in names:
        _remove_file(name)


def _remove_file(name):
    """Silently remove file."""
    try:
        os.remove(name)
    except OSError:
        pass


class MethodsTest(unittest.TestCase):
    """Run the tests for the PathEnsemble class."""

    def test_generate_file_name(self):
        """Test the generation of file names."""
        path = make_fake_extpath()
        new_dir = os.path.abspath(os.path.join('new', 'target'))
        new_pos, source = _generate_file_names(path, new_dir)
        for i, (point, pointn) in enumerate(zip(path.trajectory(), new_pos)):
            self.assertEqual(i, pointn[1])
            self.assertEqual(point['pos'][1], pointn[1])
            path1 = os.path.dirname(point['pos'][0])
            path2 = os.path.dirname(pointn[0])
            self.assertEqual(path1, DIR_NAME)
            self.assertEqual(path2, new_dir)
            self.assertTrue(point['pos'][0] in source)
            target = source[point['pos'][0]]
            self.assertEqual(target, pointn[0])
        new_pos2, _ = _generate_file_names(path, new_dir, prefix='prefix-')
        for i, point in enumerate(new_pos2):
            file1 = os.path.basename(point[0])
            file2 = 'prefix-{}'.format(FILE_NAME.format(i))
            self.assertEqual(file1, file2)

    def test_get_class(self):
        """Test that we get the correct class."""
        klass1 = get_path_ensemble_class('internal')
        self.assertTrue(klass1 is PathEnsemble)
        klass2 = get_path_ensemble_class('external')
        self.assertTrue(klass2 is PathEnsembleExt)
        with self.assertRaises(ValueError):
            get_path_ensemble_class('Pretty fly for a whity guy')


class PathEnsembleTest(unittest.TestCase):
    """Run a test for the PathEnsemble class."""

    def test_init(self):
        """Test initiation."""
        ensemble = PathEnsemble(0, [-1, 0, 1], detect=0, maxpath=10,
                                exe_dir=None)
        self.assertEqual(ensemble.start_condition, 'R')
        self.assertEqual(ensemble.ensemble_name_simple, '000')
        ensemble = PathEnsemble(11, [-1, 0, 1], detect=0, maxpath=10,
                                exe_dir=None)
        self.assertEqual(ensemble.start_condition, 'L')
        self.assertEqual(ensemble.ensemble_name_simple, '011')

    def test_directories(self):
        """Test if we get back a directory."""
        ensemble1 = PathEnsemble(0, [-1, 0, 1])
        ensemble2 = PathEnsemble(0, [-1, 0, 1], exe_dir=DIR_NAME)
        j = 0
        for i in ensemble1.directories():
            self.assertTrue(i is None)
            j += 1
        self.assertEqual(j, 1)
        j = 0
        for i in ensemble2.directories():
            self.assertEqual(i, os.path.join(DIR_NAME, '000'))
            j += 1
        self.assertEqual(j, 1)

    def test_add_path(self):
        """Test adding of paths and reset."""
        ensemble = PathEnsemble(1, [-1, 0, 1], detect=0, maxpath=10)
        # Add a path
        path = make_fake_path(length=10)
        ensemble.add_path_data(path, 'ACC', cycle=0)
        self.assertEqual(ensemble.nstats['npath'], 1)
        self.assertEqual(ensemble.nstats['ACC'], 1)
        self.assertTrue(path is ensemble.last_path)
        # Add empty path
        ensemble.add_path_data(None, 'KOB', cycle=1)
        self.assertEqual(ensemble.nstats['npath'], 2)
        self.assertEqual(ensemble.nstats['KOB'], 1)
        self.assertTrue(path is ensemble.last_path)
        # Add for shooting move
        path = make_fake_path(length=3)
        path.generated = ('sh', 1, 2, 3)
        ensemble.add_path_data(path, 'ACC', cycle=2)
        for _ in range(7):
            ensemble.add_path_data(path, 'ACC')
        self.assertEqual(len(ensemble.paths), 10)
        ensemble.add_path_data(path, 'ACC')
        self.assertEqual(len(ensemble.paths), 1)
        ensemble.reset_data()
        self.assertEqual(len(ensemble.paths), 0)
        for _, val in ensemble.nstats.items():
            self.assertEqual(val, 0)

    def test_looping(self):
        """Test adding of paths and looping."""
        ensemble = PathEnsemble(1, [-1, 0, 1], detect=0, maxpath=20)
        correct = []  # store correct lengths
        for i in range(5):
            correct.append(10 + i)
            path = make_fake_path(length=10+i)
            ensemble.add_path_data(path, 'ACC')
        ensemble.add_path_data(None, 'KOB')
        correct.append(14)
        ensemble.add_path_data(None, 'KOB')
        correct.append(14)
        for i in range(3):
            correct.append(10 + i + 5)
            path = make_fake_path(length=10+i+5)
            ensemble.add_path_data(path, 'ACC')
        for _ in range(5):
            ensemble.add_path_data(None, 'KOB')
            correct.append(10 + i + 5)
        for i, path in enumerate(ensemble.get_paths()):
            if i in (5, 6, 10, 11, 12, 13, 14):
                self.assertEqual(path['status'], 'KOB')
            else:
                self.assertEqual(path['status'], 'ACC')
        for i, path in enumerate(ensemble.get_accepted()):
            self.assertEqual(path['length'], correct[i])
        self.assertAlmostEqual(ensemble.get_acceptance_rate(), 8./15.)

    def test_restart_info(self):
        """Test that we can make restart info."""
        ensemble = PathEnsemble(1, [-1, 0, 1], detect=0, maxpath=20)
        for i in range(5):
            path = make_fake_path(length=10+i)
            ensemble.add_path_data(path, 'ACC')
        ensemble.add_path_data(None, 'KOB')
        ensemble.add_path_data(None, 'KOB')
        info = ensemble.restart_info()
        ensemble2 = PathEnsemble(10, [0, 0, 0], detect=100, maxpath=1)
        rgen = MockRandomGenerator(seed=0)
        empty_path = Path(rgen)
        ensemble2.load_restart_info(empty_path, info)
        # Note we do not force interfaces when loading restart,
        # here, just check that nstats were correctly loaded:
        for key, val in ensemble.nstats.items():
            self.assertEqual(val, ensemble2.nstats[key])


class PathEnsembleExtTest(unittest.TestCase):
    """Run a test for the PathEnsembleExt class."""

    def setUp(self):
        """Just make sure we create needed directories."""
        create_dirs()

    def tearDown(self):
        """Remove the created directories."""
        remove_dirs()

    def test_init(self):
        """Test initiation."""
        ens = PathEnsembleExt(1, [-1., 0., 1.], exe_dir=DIR_NAME)
        correct_dir = [
            os.path.join(DIR_NAME, '001'),
            os.path.join(DIR_NAME, '001', 'accepted'),
            os.path.join(DIR_NAME, '001', 'generate'),
            os.path.join(DIR_NAME, '001', 'traj'),
        ]
        for dirname, correct in zip(ens.directories(), correct_dir):
            self.assertEqual(dirname, correct)

    def test_move_path(self):
        """Test that we can move paths."""
        ens = PathEnsembleExt(1, [-1., 0., 1.], exe_dir=HERE)
        for name in ens.list_superfluous():
            os.remove(name)
        path = make_fake_path_files()
        # Add a file so that we will have to overwrite it:
        target = os.path.join(HERE, '001', 'accepted', 'fake_path_2')
        with open(target, 'w') as output:
            output.write('Blekkulf, er du der?')
        # And add a file we don't need:
        target = os.path.join(HERE, '001', 'accepted', 'extra-file')
        with open(target, 'w') as output:
            output.write('Takpapp, veggpapp, gulvpapp, tapet')
        file_paths = []
        for i in path.trajectory():
            if not i['pos'][0] in file_paths:
                file_paths.append(i['pos'][0])
        ens.add_path_data(path, 'ACC', cycle=0)
        file_paths2 = []
        for i in path.trajectory():
            if not i['pos'][0] in file_paths2:
                file_paths2.append(i['pos'][0])
        for i, j in zip(file_paths, file_paths2):
            pre = os.path.commonprefix([i, j])
            name = os.path.basename(i)
            self.assertEqual(os.path.basename(i), os.path.basename(j))
            self.assertEqual(os.path.join(pre, '001', 'accepted', name), j)
            self.assertEqual(os.path.join(pre, name), i)
        # Force move path when source and target are the same
        ens.add_path_data(path, 'ACC', cycle=0)
        remove_path_files(path)

    def test_move_to_generated(self):
        """Test that we can move a path to the generated folder."""
        ens = PathEnsembleExt(1, [-1., 0., 1.], exe_dir=HERE)
        path = make_fake_path_files()
        for i in path.trajectory():
            self.assertTrue(os.path.isfile(i['pos'][0]))
        ens.add_path_data(path, 'ACC', cycle=0)
        ens.move_path_to_generated(path, prefix='gen_')
        for i in path.trajectory():
            base = os.path.basename(i['pos'][0])
            name = os.path.join(HERE, '001', 'generate', base)
            self.assertEqual(name, i['pos'][0])
        for i in path.trajectory():
            self.assertTrue(os.path.isfile(i['pos'][0]))
        remove_path_files(path)

    def test_copy_path(self):
        """Test that we can copy a path."""
        ens = PathEnsembleExt(1, [-1., 0., 1.], exe_dir=HERE)
        path = make_fake_path_files()
        ens.add_path_data(path, 'ACC', cycle=0)
        target_dir = ens.directory['path-ensemble']
        path_copy = ens._copy_path(  # pylint: disable=protected-access
            path,
            target_dir,
            prefix='copy_'
        )
        for i in path_copy.trajectory():
            base = os.path.basename(i['pos'][0])
            name = os.path.join(HERE, '001', base)
            self.assertEqual(name, i['pos'][0])
        for i in path_copy.trajectory():
            self.assertTrue(os.path.isfile(i['pos'][0]))
        remove_path_files(path)
        remove_path_files(path_copy)

    def test_restart(self):
        """Test that we can write/read restart info."""
        ens = PathEnsembleExt(1, [-1., 0., 1.], exe_dir=HERE)
        path = make_fake_path_files()
        ens.add_path_data(path, 'ACC', cycle=0)
        info = ens.restart_info()
        rgen = MockRandomGenerator(seed=0)
        empty_path = PathExt(rgen)
        ens2 = PathEnsembleExt(2, [-1., 0.5, 1.], exe_dir=HERE)
        # Note that this will NOT copy any paths, just set some path
        # names. We just check that we get a warning about this:
        logging.disable(logging.INFO)
        with self.assertLogs('pyretis.core.pathensemble', level='CRITICAL'):
            ens2.load_restart_info(empty_path, info, cycle=0)
        logging.disable(logging.CRITICAL)
        remove_path_files(path)
        remove_path_files(empty_path)

    def test_generate_output(self):
        """Test that we can generate output."""
        ens = PathEnsembleExt(1, [-1., 0., 1.], exe_dir=HERE)
        tar = ens._traj_file  # pylint: disable=protected-access
        _remove_file(tar)
        self.assertFalse(os.path.isfile(tar))
        path = make_fake_path_files()
        cycle = {'step': 0}
        ens.generate_output(cycle, path)
        self.assertTrue(os.path.isfile(tar))
        # read the tar
        with tarfile.open(tar, 'r') as traj:
            for entry in traj:
                lines = traj.extractfile(entry)
                line = None
                for line in lines:
                    pass
                self.assertEqual(line[-11:].decode('utf-8'), entry.name[2:])
        # Currupt the tar file and try to write again:
        with open(tar, 'w') as traj:
            traj.write('Some Men Just Want to Watch The World Burn')
        ens.generate_output(cycle, path)
        # Check that we got the back up.
        tar_backup = '{}_000'.format(tar)
        self.assertTrue(os.path.isfile(tar_backup))
        with open(tar_backup, 'r') as traj:
            lines = None
            for lines in traj:
                pass
            self.assertEqual(lines,
                             'Some Men Just Want to Watch The World Burn')
        remove_path_files(path)
        _remove_file(tar)
        _remove_file(tar_backup)


if __name__ == '__main__':
    unittest.main()
