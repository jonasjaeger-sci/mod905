# -*- coding: utf-8 -*-
# Copyright (c) 2026, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test functionality for the PathEnsemble classes."""
from io import StringIO
import logging
import os
import numpy as np
import tempfile
import unittest
from pyretis.core.particles import Particles, ParticlesExt
from pyretis.core.path import Path
from pyretis.core.pathensemble import (
    _generate_file_names,
    get_path_ensemble_class,
    PathEnsemble,
    PathEnsembleExt,
    generate_ensemble_name,
)
from pyretis.core.random_gen import (MockRandomGenerator,
                                     create_random_generator)
from pyretis.core.system import System
from pyretis.inout.common import make_dirs
from unittest.mock import patch
from .help import PATHTEST0, PATHTEST1, turn_on_logging
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


def make_system(order, pos, vel, vpot, ekin, internal=True):
    """Create a system for testing."""
    system = System()
    if internal:
        system.particles = Particles(dim=3)
    else:
        system.particles = ParticlesExt(dim=3)
    system.order = order
    system.particles.set_pos(pos)
    system.particles.set_vel(vel)
    system.particles.vpot = vpot
    system.particles.ekin = ekin
    return system


def make_fake_extpath(length=10):
    """Just return a fake path for testing."""
    rgen = MockRandomGenerator(seed=0)
    path = Path(rgen)
    for i in range(length):
        filename = os.path.join(DIR_NAME, FILE_NAME.format(i))
        path.append(
            make_system([i], (filename, i), False, 0.0, 0.0, internal=False)
        )
    return path


def make_fake_path(length=10):
    """Just return a fake path for testing."""
    rgen = MockRandomGenerator(seed=0)
    path = Path(rgen)
    for i in range(length):
        path.append(
            make_system([i], np.ones((5, 3)) * i,
                        np.ones((5, 3)) * i, 0.0, 0.0)
        )
    path.generated = ('fake',)
    return path


def make_fake_path_files(dirname):
    """Return a fake path and generate files for it."""
    rgen = MockRandomGenerator(seed=0)
    path = Path(rgen)
    for name in ('fake_path_1', 'fake_path_2'):
        filename = os.path.join(dirname, name)
        with open(filename, 'w', encoding='utf-8') as output:
            output.write('Ibsens ripsbusker og andre buskevekster\n')
            output.write(filename)
    for i in range(10):
        if i < 5:
            filename = os.path.join(dirname, 'fake_path_1')
        else:
            filename = os.path.join(dirname, 'fake_path_2')
        path.append(
            make_system([i], (filename, i), False, 0.0, 0.0, internal=False)
        )
    path.generated = ('fake',)
    return path


def remove_path_files(path):
    """Remove the files for a trajectory."""
    # Just remove the files:
    names = set()
    for i in path.phasepoints:
        names.add(i.particles.get_pos()[0])
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
        for i, (point, pointn) in enumerate(zip(path.phasepoints, new_pos)):
            self.assertEqual(i, pointn[1])
            self.assertEqual(point.particles.get_pos()[1], pointn[1])
            path1 = os.path.dirname(point.particles.get_pos()[0])
            path2 = os.path.dirname(pointn[0])
            self.assertEqual(path1, DIR_NAME)
            self.assertEqual(path2, new_dir)
            self.assertTrue(point.particles.get_pos()[0] in source)
            target = source[point.particles.get_pos()[0]]
            self.assertEqual(target, pointn[0])
        new_pos2, _ = _generate_file_names(path, new_dir, prefix='prefix-')
        for i, point in enumerate(new_pos2):
            self.assertEqual(
                os.path.basename(point[0]),
                f'prefix-{FILE_NAME.format(i)}',
            )

    def test_get_class(self):
        """Test that we get the correct class."""
        klass1 = get_path_ensemble_class('internal')
        self.assertTrue(klass1 is PathEnsemble)
        klass2 = get_path_ensemble_class('external')
        self.assertTrue(klass2 is PathEnsembleExt)
        with self.assertRaises(ValueError):
            get_path_ensemble_class('Pretty fly for a whity guy')

    def test_generate_ensemble_name(self):
        """Test that we can generate names for directories."""
        name = generate_ensemble_name(5, zero_pad=3)
        self.assertEqual(name, '005')
        name = generate_ensemble_name(2, zero_pad=6)
        self.assertEqual(name, '000002')
        for i in (-1, 0, 1, 2):
            name = generate_ensemble_name(1, zero_pad=i)
            self.assertEqual(name, '001')


class PathEnsembleTest(unittest.TestCase):
    """Run a test for the PathEnsemble class."""

    def test_logic(self):
        """Test eq and ne."""
        path_ensemble1 = PathEnsemble(0, [-1, 0, 1], maxpath=10, exe_dir=None)
        path_ensemble2 = PathEnsemble(0, [-1, 0, 1], maxpath=10, exe_dir=None)
        path_ensemble2.rgen = path_ensemble1.rgen
        self.assertFalse(path_ensemble1 == 'Nonno')
        self.assertTrue(path_ensemble2 == path_ensemble1)

        path_ensemble2 = PathEnsemble(0, [-2, 0, 1], maxpath=10, exe_dir=None)
        with patch('sys.stdout', new=StringIO()):
            self.assertTrue(path_ensemble2 != path_ensemble1)

        path_ensemble2 = PathEnsemble(0, [-1, 0, 1], maxpath=10, exe_dir=None)
        path_ensemble2.ciccio = None
        with patch('sys.stdout', new=StringIO()):
            self.assertTrue(path_ensemble2 != path_ensemble1)

        path_ensemble2 = PathEnsemble(0, [-1, 0, 1], maxpath=10, exe_dir=None)
        path_ensemble2.directory = {'accepted': 'GranaPadano'}
        with patch('sys.stdout', new=StringIO()):
            self.assertTrue(path_ensemble2 != path_ensemble1)

        path_ensemble2 = PathEnsemble(0, [-1, 0, 1], maxpath=16, exe_dir=None)
        with patch('sys.stdout', new=StringIO()):
            self.assertTrue(path_ensemble2 != path_ensemble1)

        path_ensemble2 = PathEnsemble(0, [-1, 0, 1], maxpath=10, exe_dir=None)
        path_ensemble2.last_path = Path()
        with patch('sys.stdout', new=StringIO()):
            self.assertTrue(path_ensemble2 != path_ensemble1)

        path_ensemble1 = PathEnsemble(0, [-1, 0, 1], maxpath=10, exe_dir=None)
        path_ensemble2 = PathEnsemble(0, [-1, 0, 1], maxpath=10, exe_dir=None)
        path_ensemble1.rgen = create_random_generator({'rgen': 'rgen',
                                                       'seed': 123})
        path_ensemble2.rgen = create_random_generator({'rgen': 'rgen',
                                                       'seed': 123})
        path_ensemble2.rgen.rand()
        with patch('sys.stdout', new=StringIO()):
            self.assertTrue(path_ensemble2 != path_ensemble1)
        path_ensemble1.rgen = create_random_generator({'rgen': 'rgen',
                                                       'seed': 132})
        path_ensemble2.rgen = create_random_generator({'rgen': 'rgen',
                                                       'seed': 123})
        with patch('sys.stdout', new=StringIO()):
            self.assertTrue(path_ensemble2 != path_ensemble1)

        path_ensemble2 = PathEnsemble(0, [-1, 0, 1], maxpath=10, exe_dir=None)
        path_ensemble1.rgen = create_random_generator({'rgen': 'mock'})
        path_ensemble2.rgen = create_random_generator({'rgen': 'rgen'})
        with patch('sys.stdout', new=StringIO()):
            self.assertTrue(path_ensemble2 != path_ensemble1)

        path_ensemble1 = PathEnsemble(0, [-1, 0, 1], maxpath=10, exe_dir=None)
        path_ensemble2 = PathEnsemble(0, [-1, 0, 1], maxpath=10, exe_dir=None)

        path_ensemble1.last_path = Path()
        path_ensemble2.last_path = [1, 2]
        with patch('sys.stdout', new=StringIO()):
            self.assertTrue(path_ensemble2 != path_ensemble1)
        path_ensemble1.last_path = PATHTEST0
        path_ensemble2.last_path = PATHTEST1
        with patch('sys.stdout', new=StringIO()):
            self.assertTrue(path_ensemble2 != path_ensemble1)

    def test_init(self):
        """Test initiation."""
        path_ensemble = PathEnsemble(0, [-1, 0, 1], maxpath=10, exe_dir=None)
        self.assertEqual(path_ensemble.start_condition, 'R')
        self.assertEqual(path_ensemble.ensemble_name_simple, '000')
        path_ensemble = PathEnsemble(11, [-1, 0, 1], maxpath=10, exe_dir=None)
        self.assertEqual(path_ensemble.start_condition, 'L')
        self.assertEqual(path_ensemble.ensemble_name_simple, '011')

    def test_directories(self):
        """Test if we get back a directory."""
        path_ensemble1 = PathEnsemble(0, [-1, 0, 1])
        path_ensemble2 = PathEnsemble(0, [-1, 0, 1], exe_dir=DIR_NAME)
        j = 0
        for i in path_ensemble1.directories():
            self.assertTrue(i is None)
            j += 1
        self.assertEqual(j, 4)
        j = 0
        dirs = [i for i in path_ensemble2.directories()]
        self.assertTrue(os.path.join(DIR_NAME, '000') in dirs)
        j += 1
        for i in ('accepted', 'generate', 'traj'):
            testname = os.path.join(DIR_NAME, '000', i)
            self.assertTrue(testname in dirs)
            j += 1
        self.assertEqual(j, 4)

    def test_update_dir(self):
        """Test that we can update directories."""
        path_ensemble = PathEnsemble(1, [-1, 0, 1], exe_dir='test1')
        old = [i for i in path_ensemble.directories()]
        path_ensemble.update_directories(os.path.join('test1', '002'))
        new = [i for i in path_ensemble.directories()]
        for diri, dirj in zip(old, new):
            for i, j in zip(diri, dirj):
                if i != j:
                    self.assertEqual(i, '1')
                    self.assertEqual(j, '2')

    def test_add_path(self):
        """Test adding of paths and reset."""
        path_ensemble = PathEnsemble(1, [-1, 0, 1], maxpath=10)
        # Add a path
        path = make_fake_path(length=10)
        path_ensemble.add_path_data(path, 'ACC', cycle=0)
        self.assertEqual(path_ensemble.nstats['npath'], 1)
        self.assertEqual(path_ensemble.nstats['ACC'], 1)
        self.assertTrue(path is path_ensemble.last_path)
        # Add empty path:
        path_ensemble.add_path_data(None, 'KOB', cycle=1)
        self.assertEqual(path_ensemble.nstats['npath'], 2)
        self.assertEqual(path_ensemble.nstats['KOB'], 1)
        self.assertTrue(path is path_ensemble.last_path)
        # Add for a shooting move:
        path = make_fake_path(length=3)
        path.generated = ('sh', 1, 2, 3)
        path_ensemble.add_path_data(path, 'ACC', cycle=2)
        for _ in range(7):
            path_ensemble.add_path_data(path, 'ACC')
        self.assertEqual(len(path_ensemble.paths), 10)
        path_ensemble.add_path_data(path, 'ACC')
        self.assertEqual(len(path_ensemble.paths), 1)
        path_ensemble.reset_data()
        self.assertEqual(len(path_ensemble.paths), 0)
        for _, val in path_ensemble.nstats.items():
            self.assertEqual(val, 0)

    def test_looping(self):
        """Test adding of paths and looping."""
        path_ensemble = PathEnsemble(1, [-1, 0, 1], maxpath=20)
        correct = []  # For storing the correct lengths.
        for i in range(5):
            correct.append(10 + i)
            path = make_fake_path(length=10+i)
            path_ensemble.add_path_data(path, 'ACC')
        path_ensemble.add_path_data(None, 'KOB')
        correct.append(14)
        path_ensemble.add_path_data(None, 'KOB')
        correct.append(14)
        for i in range(3):
            correct.append(10 + i + 5)
            path = make_fake_path(length=10+i+5)
            path_ensemble.add_path_data(path, 'ACC')
        for _ in range(5):
            path_ensemble.add_path_data(None, 'KOB')
            correct.append(10 + 2 + 5)  # "+2" is from the previous for loop.
        for i, path in enumerate(path_ensemble.get_paths()):
            if i in (5, 6, 10, 11, 12, 13, 14):
                self.assertEqual(path['status'], 'KOB')
            else:
                self.assertEqual(path['status'], 'ACC')
        for i, path in enumerate(path_ensemble.get_accepted()):
            self.assertEqual(path['length'], correct[i])
        self.assertAlmostEqual(path_ensemble.get_acceptance_rate(), 8./15.)

    def test_restart_info1(self):
        """Test that we can make restart info."""
        path_ensemble = PathEnsemble(1, [-1, 0, 1], maxpath=20)
        for i in range(5):
            path = make_fake_path(length=10+i)
            path_ensemble.add_path_data(path, 'ACC')
        path_ensemble.add_path_data(None, 'KOB')
        path_ensemble.add_path_data(None, 'KOB')
        info = path_ensemble.restart_info()
        path_ensemble2 = PathEnsemble(10, [0, 0, 0], maxpath=1)
        path_ensemble2.load_restart_info(info)
        # Note we do not force interfaces when loading restart,
        # here, just check that nstats were correctly loaded:
        for key, val in path_ensemble.nstats.items():
            self.assertEqual(val, path_ensemble2.nstats[key])

    def test_restart_info2(self):
        """Test that we can make restart info."""
        path_ensemble = PathEnsemble(1, [-1, 0, 1])
        for i in range(5):
            path = make_fake_path(length=10+i)
            path_ensemble.add_path_data(path, 'ACC')
        path_ensemble.add_path_data(None, 'KOB')
        path_ensemble.add_path_data(None, 'KOB')
        info = path_ensemble.restart_info()
        path_ensemble2 = PathEnsemble(10, [0, 0, 0])
        path_ensemble2.load_restart_info(info)

        # Note we do not force interfaces when loading restart
        # information, here, just check that nstats were
        # correctly loaded:
        for key, val in path_ensemble.nstats.items():
            self.assertEqual(val, path_ensemble2.nstats[key])


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

    def test_update_dir(self):
        """Test that we can update directories."""
        path_ensemble = PathEnsembleExt(1, [-1, 0, 1], exe_dir='test1')
        old = [i for i in path_ensemble.directories()]
        path_ensemble.update_directories(os.path.join('test1', '002'))
        new = [i for i in path_ensemble.directories()]
        for diri, dirj in zip(old, new):
            for i, j in zip(diri, dirj):
                if i != j:
                    self.assertEqual(i, '1')
                    self.assertEqual(j, '2')

    def test_move_path(self):
        """Test that we can move paths."""
        with tempfile.TemporaryDirectory() as tempdir:
            ens = PathEnsembleExt(1, [-1., 0., 1.], exe_dir=tempdir)
            for i in ens.directories():
                make_dirs(i)
            for name in ens.list_superfluous():
                os.remove(name)
            path = make_fake_path_files(tempdir)
            # Add a file so that we will have to overwrite it:
            target = os.path.join(tempdir, '001', 'accepted', 'fake_path_2')
            with open(target, 'w', encoding='utf-8') as output:
                output.write('Blekkulf, er du der?')
            # And add a file we don't need:
            target = os.path.join(tempdir, '001', 'accepted', 'extra-file')
            with open(target, 'w', encoding='utf-8') as output:
                output.write('Takpapp, veggpapp, gulvpapp, tapet')
            file_paths = []
            for i in path.phasepoints:
                file_paths.append(i.particles.get_pos()[0])
            # Add the file as accepted. This will move it:
            ens.add_path_data(path, 'ACC', cycle=0)
            file_paths2 = []
            for i in path.phasepoints:
                file_paths2.append(i.particles.get_pos()[0])
            for i, j in zip(file_paths, file_paths2):
                # Check that files were moved:
                self.assertNotEqual(i, j)
                self.assertFalse(os.path.isfile(i))
                self.assertTrue(os.path.isfile(j))
                # Check that we did not alter the base name:
                self.assertEqual(os.path.basename(i), os.path.basename(j))
                # Check that files were moved into the accepted folder:
                target = os.path.join(
                    ens.directory['accepted'], os.path.basename(j)
                )
                self.assertEqual(j, target)
            # Force move path, when source and target are the same:
            ens.add_path_data(path, 'ACC', cycle=0)

    def test_move_to_generate(self):
        """Test that we can move a path to the generated folder."""
        with tempfile.TemporaryDirectory() as tempdir:
            ens = PathEnsembleExt(1, [-1., 0., 1.], exe_dir=tempdir)
            for i in ens.directories():
                make_dirs(i)
            path = make_fake_path_files(tempdir)
            # Check that generated files exists:
            for i in path.phasepoints:
                self.assertTrue(os.path.isfile(i.particles.get_pos()[0]))
            # Add to path ensemble (and move to the accepted folder):
            ens.add_path_data(path, 'ACC', cycle=0)
            for i in path.phasepoints:
                target = os.path.join(
                    tempdir, ens.directory['accepted'],
                    os.path.basename(i.particles.get_pos()[0])
                )
                # After the move, these names should be equal:
                self.assertEqual(target, i.particles.get_pos()[0])
            ens.move_path_to_generate(path, prefix='gen_')
            # Check that files were moved to the generated folder:
            for i in path.phasepoints:
                self.assertTrue(os.path.isfile(i.particles.get_pos()[0]))
                target = os.path.join(
                    tempdir, ens.directory['generate'],
                    os.path.basename(i.particles.get_pos()[0])
                )
                self.assertEqual(target, i.particles.get_pos()[0])

    def test_copy_path(self):
        """Test that we can copy a path."""
        with tempfile.TemporaryDirectory() as tempdir:
            ens = PathEnsembleExt(1, [-1., 0., 1.], exe_dir=tempdir)
            for i in ens.directories():
                make_dirs(i)
            path = make_fake_path_files(tempdir)
            ens.add_path_data(path, 'ACC', cycle=0)
            target_dir = ens.directory['path_ensemble']
            path_copy = ens._copy_path(  # pylint: disable=protected-access
                path,
                target_dir,
                prefix='copy_'
            )
            # Check that files were copied:
            for i in path_copy.phasepoints:
                self.assertTrue(os.path.isfile(i.particles.get_pos()[0]))
            # Check that original files remains:
            for i in path.phasepoints:
                self.assertTrue(os.path.isfile(i.particles.get_pos()[0]))
            # Check that original and copy path are different:
            for i, j in zip(path.phasepoints, path_copy.phasepoints):
                self.assertNotEqual(i.particles.get_pos()[0],
                                    j.particles.get_pos()[0])
            # Test that delete then copy function of _copy_path:
            rewrite_file = tempdir + '/001/copy_fake_path_1'
            # Empties file of text:
            open(rewrite_file, 'w', encoding='utf-8').close()
            self.assertEqual(os.path.getsize(rewrite_file), 0)
            ens._copy_path(  # pylint: disable=protected-access
                path,
                target_dir,
                prefix='copy_'
            )
            self.assertNotEqual(os.path.getsize(rewrite_file), 0)
            # Tests copy_path_to_generate():
            ens.copy_path_to_generate(path)
            for i in path.phasepoints:
                i_path = i.particles.get_pos()[0].replace('accepted',
                                                          'generate')
                self.assertTrue(os.path.isfile(i_path))
            # Check that original files remains:
            for i in path.phasepoints:
                self.assertTrue(os.path.isfile(i.particles.get_pos()[0]))

    def test_restart(self):
        """Test that we can write/read restart info."""
        with tempfile.TemporaryDirectory() as tempdir:
            ens = PathEnsembleExt(1, [-1., 0., 1.], exe_dir=tempdir)
            for i in ens.directories():
                make_dirs(i)
            path = make_fake_path_files(tempdir)
            ens.add_path_data(path, 'ACC', cycle=0)
            info = ens.restart_info()
            ens2 = PathEnsembleExt(2, [-1., 0.5, 1.], exe_dir=tempdir)
            for i in ens2.directories():
                make_dirs(i)
            # Note that this will NOT copy any paths, just set some path
            # names. We just check that we get a warning about this:
            with turn_on_logging():
                with self.assertLogs('pyretis.core.pathensemble',
                                     level='CRITICAL'):
                    with self.assertLogs('pyretis.core.random_gen',
                                         level='CRITICAL'):
                        ens2.load_restart_info(info)

    def test_clear_generate(self):
        """Test that we can clear the ens/generate folder."""
        with tempfile.TemporaryDirectory() as tempdir:
            ens = PathEnsembleExt(1, [-1., 0., 1.], exe_dir=tempdir)
            for i in ens.directories():  # creating 001
                make_dirs(i)  # creating traj, generate
            # make two paths in 001/generate
            make_fake_path_files(tempdir+"/001/generate")
            # first assert that the generate folder is not empty
            self.assertTrue(os.listdir(tempdir+"/001/generate"))
            # clear generate folder
            ens.clear_generate()
            # assert that the generate folder is now empty.
            self.assertFalse(os.listdir(tempdir+"/001/generate"))

    def test_print_pe(self):
        """Test that printing path ensemble information does not crash."""
        with tempfile.TemporaryDirectory() as tempdir:
            ens = PathEnsembleExt(1, [-1., 0., 1.], exe_dir=tempdir)
            for i in ens.directories():
                make_dirs(i)
            path = make_fake_path_files(tempdir)
            ens.add_path_data(path, 'ACC', cycle=0)
            txt = str(ens)
            ref = 'Path ensemble: [0^+]\n\tInterfaces: (-1.0, 0.0, 1.0)\n\t'
            ref += 'Number of paths stored: 1\n\tNumber of accepted paths: 1'
            ref += '\n\tRatio accepted/total paths: 1.0'
            self.assertEqual(txt, ref)


if __name__ == '__main__':
    unittest.main()
