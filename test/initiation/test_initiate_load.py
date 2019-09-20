# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test initiate load methods."""
import logging
from io import StringIO
import unittest
from unittest.mock import patch
import os
import tempfile
import pathlib
import shutil
import numpy as np
from pyretis.initiation.initiate_load import (
    clean_path,
    read_path_files,
    read_path_files_ext,
    reorderframes,
    _check_path,
    _do_the_dirty_load_job,
)
from pyretis.engines.gromacs import GromacsEngine
from pyretis.engines.internal import Langevin
from pyretis.core.box import create_box
from pyretis.core.system import System
from pyretis.core.path import Path
from pyretis.core.particles import Particles, ParticlesExt
from pyretis.core.pathensemble import PathEnsemble, PathEnsembleExt
from pyretis.core.units import units_from_settings
from pyretis.core.random_gen import RandomGenerator
from pyretis.inout.common import make_dirs
from pyretis.inout.formats.path import PathExtFile, PathIntFile
from pyretis.inout.formats.order import OrderPathFile
from pyretis.inout.formats.energy import EnergyPathFile
from pyretis.orderparameter import Position, PositionVelocity
from pyretis.inout.setup import (
    create_simulation,
    create_force_field,
    create_system,
    create_engine,
)
from pyretis.inout.settings import parse_settings_file
from pyretis.inout.setup.createsimulation import create_path_ensembles

logging.disable(logging.CRITICAL)
HERE = os.path.abspath(os.path.dirname(__file__))
CP2K = os.path.join(HERE, 'mockcp2k.py')
GMX = os.path.join(HERE, 'mockgmx.py')
MDRUN = os.path.join(HERE, 'mockmdrun.py')
CP2K_DIR = os.path.join(HERE, 'cp2k', 'cp2k_input')
CP2K_LOAD = os.path.join(HERE, 'cp2k', 'load')
GMX_DIR = os.path.join(HERE, 'gromacs', 'gmx_input')
GMX_LOAD = os.path.join(HERE, 'gromacs', 'load')
GMX_LOAD_TRJ = os.path.join(HERE, 'gromacs', 'load-trj')
INTERNAL_LOAD = os.path.join(HERE, 'internal', 'tis', 'load')
INTERNAL_LOAD_2 = os.path.join(HERE, 'internal', 'retis-load', 'load-sparse')


def remove_file(filename):
    """Remove a file."""
    if os.path.isfile(filename):
        try:
            os.remove(filename)
        except OSError:
            pass


def set_up_system(order, pos, vel, vpot=None, ekin=None, internal=True):
    """Create a system for testing."""
    system = System()
    if internal:
        system.particles = Particles(dim=3)
        for posi, veli in zip(pos, vel):
            system.add_particle(posi, vel=veli)
    else:
        system.particles = ParticlesExt(dim=3)
        system.add_particle(pos, vel=vel)
    system.order = order
    system.particles.vpot = vpot
    system.particles.ekin = ekin
    return system


def fill_path(path=None, npoints=20, scale=1):
    """Fill in data for a arbitrary path."""
    if path is None:
        path = Path()
    for i in range(npoints):
        path.append(
            set_up_system([(-20.0 + 2.5 * i) * scale],
                          [np.ones(3) * i],
                          [np.ones(3) * i],
                          vpot=i, ekin=i,
                          internal=True)
        )
    return path


def find_files_in_dir(dirname):
    """Return a list of files in the given directory."""
    return [i.name for i in os.scandir(dirname) if i.is_file()]


def read_traj_order_energy(dirname, path_reader):
    """Read trajectory, order parameter and energy files."""
    traj, order, energy = [], [], []
    traj_file_name = os.path.join(dirname, 'traj.txt')
    with path_reader(traj_file_name, 'r') as trajfile:
        traj = [i for i in next(trajfile.load())['data']]
    order_file_name = os.path.join(dirname, 'order.txt')
    with OrderPathFile(order_file_name, 'r') as orderfile:
        order = [i for i in next(orderfile.load())['data']]
    energy_file_name = os.path.join(dirname, 'energy.txt')
    with EnergyPathFile(energy_file_name, 'r') as energyfile:
        for i in energyfile.load():
            energy = i['data']
            break
    return traj, order, energy


def path_traj_order_energy(path):
    """Get trajectory, order parameters and energies from a path."""
    traj, order, energy = [], [], {'time': [], 'vpot': [], 'ekin': []}
    for i, phasepoint in enumerate(path.phasepoints):
        vel = -1 if phasepoint.particles.get_vel() else 1
        traj.append([i, os.path.basename(phasepoint.particles.get_pos()[0]),
                     phasepoint.particles.get_pos()[1], vel])
        order.append(np.array([i, phasepoint.order], dtype=np.float))
        energy['time'].append(i)
        energy['vpot'].append(phasepoint.particles.vpot)
        energy['ekin'].append(phasepoint.particles.ekin)
    for key, val in energy.items():
        energy[key] = np.array(val)
    return traj, order, energy


def path_traj_order_energy_int(path):
    """Get trajectory, order parameters and energies from a path."""
    traj, order, energy = [], [], {'time': [], 'vpot': [], 'ekin': []}
    for i, phasepoint in enumerate(path.phasepoints):
        traj.append({'pos': phasepoint.particles.get_pos(),
                     'vel': phasepoint.particles.get_vel()})
        order.append(np.array([i, *phasepoint.order]))
        energy['time'].append(i)
        energy['vpot'].append(phasepoint.particles.vpot)
        energy['ekin'].append(phasepoint.particles.ekin)
    for key, val in energy.items():
        energy[key] = np.array(val)
    return traj, order, energy


def compare_trajs(ensemble_load, path):
    """Compare loaded trajectory with source."""

    traj, order, energy = read_traj_order_energy(ensemble_load, PathExtFile)
    trajp, orderp, energyp = path_traj_order_energy(path)

    if not (len(order) == len(orderp)
            or len(traj) == len(trajp)):
        return False
    for i, j in zip(order, orderp):
        if not np.allclose(i, j):
            return False
    for traji, trajj in zip(traj, trajp):
        trajjj = [str(i) for i in trajj]
        for i, j in zip(traji, trajjj):
            if not i == j:
                return False
    for term in ('time', 'ekin', 'vpot'):
        if not len(energy[term]) == len(energyp[term]):
            return False
        if not np.allclose(energy[term], energyp[term]):
            return False
    return True


def compare_trajs_int(ensemble_load, path):
    """Compare internal trajectory with source."""

    traj, order, energy = read_traj_order_energy(ensemble_load, PathIntFile)
    trajp, orderp, energyp = path_traj_order_energy_int(path)
    if not (len(order) == len(orderp)
            or len(traj) == len(trajp)):
        return False
    for i, j in zip(order, orderp):
        if not np.allclose(i, j, atol=1e-6):
            return False
    for traji, trajj in zip(traj, trajp):
        for i in ('pos', 'vel'):
            if not np.allclose(traji[i], trajj[i]):
                return False
    term = 'time'
    if not len(energy[term]) == len(energyp[term]):
        return False
    if not np.allclose(energy[term], energyp[term]):
        return False
    for term in ('ekin', 'vpot'):
        if not len(energy[term]) == len(energyp[term]):
            return False
        try:
            if not np.allclose(energy[term], energyp[term]):
                return False
        except TypeError:  # Infinite errors are ok
            pass
    return True


class TestReadPathFilesExt(unittest.TestCase):
    """Run the tests for the reading external trajectories."""

    def test_read_path_ext(self):
        """Test reading of external trajectories."""
        with tempfile.TemporaryDirectory() as tempdir:
            gmx_dir = os.path.join(tempdir, 'gmx_input')
            shutil.copytree(GMX_DIR, gmx_dir)
            load_dir = os.path.join(tempdir, 'load')
            shutil.copytree(GMX_LOAD, load_dir)
            ensemble = PathEnsembleExt(23, (-0.26, 0.02, 0.2),
                                       exe_dir=tempdir)
            ensemble_load = os.path.join(load_dir,
                                         ensemble.ensemble_name_simple)
            for i in ensemble.directories():
                make_dirs(i)
            files = find_files_in_dir(ensemble.directory['accepted'])
            self.assertEqual(0, len(files))
            gmx = GromacsEngine(GMX, MDRUN, gmx_dir, 0.002, 3, maxwarn=1,
                                gmx_format='gro', write_vel=True,
                                write_force=False)
            gmx.exe_dir = ensemble.directory['accepted']
            path = Path(None)
            system = System(box=None)
            system.particles = ParticlesExt()
            with patch('sys.stdout', new=StringIO()):
                path_ok = read_path_files_ext(path, ensemble, ensemble_load,
                                              system, None, gmx)
                self.assertEqual(path_ok, (True, 'ACC'))
            files = find_files_in_dir(ensemble.directory['accepted'])
            self.assertEqual(2, len(files))
            self.assertIn('trajF.trr', files)
            self.assertIn('trajB.trr', files)
            cmpok = compare_trajs(ensemble_load, path)
            self.assertTrue(cmpok)

    def test_read_path_ext_no_order(self):
        """Test reading of external trajectories with missing order.txt."""
        orderparameter = PositionVelocity(1472, dim='x', periodic=True)
        with tempfile.TemporaryDirectory() as tempdir:
            gmx_dir = os.path.join(tempdir, 'gmx_input')
            shutil.copytree(GMX_DIR, gmx_dir)
            load_dir = os.path.join(tempdir, 'load')
            shutil.copytree(GMX_LOAD, load_dir)
            ensemble = PathEnsembleExt(23, (1.78, 1.795, 1.80),
                                       exe_dir=tempdir)
            ensemble_load = os.path.join(load_dir,
                                         ensemble.ensemble_name_simple)
            remove_file(os.path.join(ensemble_load, 'order.txt'))
            for i in ensemble.directories():
                make_dirs(i)
            files = find_files_in_dir(ensemble.directory['accepted'])
            self.assertEqual(0, len(files))
            files = find_files_in_dir(ensemble_load)
            self.assertEqual(2, len(files))
            self.assertIn('energy.txt', files)
            self.assertIn('traj.txt', files)
            self.assertNotIn('order.txt', files)
            gmx = GromacsEngine(GMX, MDRUN, gmx_dir, 0.002, 3, maxwarn=1,
                                gmx_format='gro', write_vel=True,
                                write_force=False)
            gmx.exe_dir = ensemble.directory['accepted']
            path = Path(None)
            system = System(box=None)
            system.particles = ParticlesExt()
            with patch('sys.stdout', new=StringIO()):
                path_ok = read_path_files_ext(path, ensemble, ensemble_load,
                                              system, orderparameter, gmx)
                self.assertEqual(path_ok, (True, 'ACC'))
            files = find_files_in_dir(ensemble.directory['accepted'])
            self.assertEqual(2, len(files))
            self.assertIn('trajF.trr', files)
            self.assertIn('trajB.trr', files)

    def test_read_path_ext_no_energy(self):
        """Test reading of external trajectories with missing order.txt"""
        with tempfile.TemporaryDirectory() as tempdir:
            gmx_dir = os.path.join(tempdir, 'gmx_input')
            shutil.copytree(GMX_DIR, gmx_dir)
            load_dir = os.path.join(tempdir, 'load')
            shutil.copytree(GMX_LOAD, load_dir)
            ensemble = PathEnsembleExt(23, (-0.26, 0.02, 0.2),
                                       exe_dir=tempdir)
            ensemble_load = os.path.join(load_dir,
                                         ensemble.ensemble_name_simple)
            remove_file(os.path.join(ensemble_load, 'energy.txt'))
            for i in ensemble.directories():
                make_dirs(i)
            files = find_files_in_dir(ensemble.directory['accepted'])
            self.assertEqual(0, len(files))
            files = find_files_in_dir(ensemble_load)
            self.assertEqual(2, len(files))
            self.assertNotIn('energy.txt', files)
            self.assertIn('traj.txt', files)
            self.assertIn('order.txt', files)
            gmx = GromacsEngine(GMX, MDRUN, gmx_dir, 0.002, 3, maxwarn=1,
                                gmx_format='gro', write_vel=True,
                                write_force=False)
            gmx.exe_dir = ensemble.directory['accepted']
            path = Path(None)
            system = System(box=None)
            system.particles = ParticlesExt()
            with patch('sys.stdout', new=StringIO()):
                path_ok = read_path_files_ext(path, ensemble, ensemble_load,
                                              system, None, gmx)
                self.assertEqual(path_ok, (True, 'ACC'))
            files = find_files_in_dir(ensemble.directory['accepted'])
            self.assertEqual(2, len(files))
            self.assertIn('trajF.trr', files)
            self.assertIn('trajB.trr', files)
            for i in path.phasepoints:
                self.assertIsNone(i.particles.ekin)
                self.assertIsNone(i.particles.vpot)

    def test_check_path(self):
        """Test checking of the path."""
        with tempfile.TemporaryDirectory() as tempdir:
            gmx_dir = os.path.join(tempdir, 'gmx_input')
            shutil.copytree(GMX_DIR, gmx_dir)
            load_dir = os.path.join(tempdir, 'load')
            shutil.copytree(GMX_LOAD, load_dir)
            ensemble = PathEnsembleExt(23, (-0.26, 0.02, 0.2),
                                       exe_dir=tempdir)
            ensemble_load = os.path.join(load_dir,
                                         ensemble.ensemble_name_simple)
            for i in ensemble.directories():
                make_dirs(i)
            gmx = GromacsEngine(GMX, MDRUN, gmx_dir, 0.002, 3, maxwarn=1,
                                gmx_format='gro', write_vel=True,
                                write_force=False)
            gmx.exe_dir = ensemble.directory['accepted']
            path = Path(None)
            system = System(box=None)
            system.particles = ParticlesExt()
            with patch('sys.stdout', new=StringIO()):
                read_path_files_ext(path, ensemble, ensemble_load,
                                    system, None, gmx)
            accept, status = _check_path(path, ensemble)
            self.assertTrue(accept)
            self.assertEqual(status, 'ACC')
            ensemble = PathEnsembleExt(23, (-0.26, 0.2, 0.4),
                                       exe_dir=tempdir)
            accept, status = _check_path(path, ensemble)
            self.assertFalse(accept)
            self.assertEqual(status, 'EWI')
            path_r = path.reverse(
                Position(0, dim='x', periodic=False)
            )
            ensemble = PathEnsembleExt(23, (-0.26, 0.02, 0.2),
                                       exe_dir=tempdir)
            accept, status = _check_path(path_r, ensemble)
            self.assertFalse(accept)
            self.assertEqual(status, 'SWI')
            path.append(
                set_up_system([-0.26, 0.0], ('somefile.trr', 0), True,
                              internal=False)
            )
            ensemble = PathEnsembleExt(23, (-0.26, 0.3, 0.3),
                                       exe_dir=tempdir)
            accept, status = _check_path(path, ensemble)
            self.assertFalse(accept)
            self.assertEqual(status, 'NCR')


class TestReadPathFiles(unittest.TestCase):
    """Run the tests for reading internal trajectories."""

    def test_read_path(self):
        """Test reading of internal trajectories."""
        with tempfile.TemporaryDirectory() as tempdir:
            load_dir = os.path.join(tempdir, 'load')
            shutil.copytree(INTERNAL_LOAD, load_dir)
            ensemble = PathEnsemble(1, (-0.9, -0.8, -0.7),
                                    exe_dir=tempdir)
            ensemble_load = os.path.join(load_dir,
                                         ensemble.ensemble_name_simple)
            path = Path(None)
            engine = Langevin(0.002, 0.3)
            box = create_box(periodic=[False])
            system = System(box=box)
            system.particles = Particles()
            with patch('sys.stdout', new=StringIO()):
                accept, status = read_path_files(path, ensemble,
                                                 ensemble_load, system,
                                                 None, engine)
                self.assertTrue(accept)
                self.assertEqual(status, 'ACC')
            cmpt = compare_trajs_int(ensemble_load, path)
            self.assertTrue(cmpt)

    def test_read_path_noorder(self):
        """Test reading of internal trajectories with missing order.txt."""
        orderparameter = PositionVelocity(0, dim='x', periodic=False)
        with tempfile.TemporaryDirectory() as tempdir:
            load_dir = os.path.join(tempdir, 'load')
            shutil.copytree(INTERNAL_LOAD, load_dir)
            ensemble = PathEnsemble(1, (-0.9, -0.8, -0.7),
                                    exe_dir=tempdir)
            ensemble_load = os.path.join(load_dir,
                                         ensemble.ensemble_name_simple)
            remove_file(os.path.join(ensemble_load, 'order.txt'))
            path = Path(None)
            engine = Langevin(0.002, 0.3)
            box = create_box(periodic=[False])
            system = System(box=box)
            system.particles = Particles(dim=1)
            with patch('sys.stdout', new=StringIO()):
                accept, status = read_path_files(path, ensemble,
                                                 ensemble_load, system,
                                                 orderparameter, engine)
                self.assertTrue(accept)
                self.assertEqual(status, 'ACC')
            shutil.copyfile(
                os.path.join(INTERNAL_LOAD, '001', 'order.txt'),
                os.path.join(ensemble_load, 'order.txt')
            )
            cmpt = compare_trajs_int(ensemble_load, path)
            self.assertTrue(cmpt)

    def test_read_path_noenergy(self):
        """Test reading of internal trajectories with missing energy.txt."""
        with tempfile.TemporaryDirectory() as tempdir:
            load_dir = os.path.join(tempdir, 'load')
            shutil.copytree(INTERNAL_LOAD, load_dir)
            ensemble = PathEnsemble(1, (-0.9, -0.8, -0.7),
                                    exe_dir=tempdir)
            ensemble_load = os.path.join(load_dir,
                                         ensemble.ensemble_name_simple)
            remove_file(os.path.join(ensemble_load, 'energy.txt'))
            path = Path(None)
            engine = Langevin(0.002, 0.3)
            box = create_box(periodic=[False])
            system = System(box=box)
            system.particles = Particles(dim=1)
            with patch('sys.stdout', new=StringIO()):
                accept, status = read_path_files(path, ensemble,
                                                 ensemble_load, system,
                                                 None, engine)
                self.assertTrue(accept)
                self.assertEqual(status, 'ACC')
            for i in path.phasepoints:
                self.assertIsNone(i.particles.ekin)
                self.assertIsNone(i.particles.vpot)


class TestInitiateLoad(unittest.TestCase):
    """Test the full initiate load for a TIS simulation."""

    @staticmethod
    def _set_up_for_load(settings, tempdir, copy_load=True):
        """Set up a system for testing the initiate load method."""
        settings['simulation']['exe-path'] = tempdir
        load_dir = os.path.join(
            tempdir, settings['initial-path']['load_folder']
        )
        if copy_load:
            shutil.copytree(INTERNAL_LOAD, load_dir)
        shutil.copyfile(
            os.path.join(HERE, 'internal', 'tis', 'initial.xyz'),
            os.path.join(tempdir, 'initial.xyz')
        )
        units_from_settings(settings)
        engine = create_engine(settings)
        system = create_system(settings, engine=engine)
        system.forcefield = create_force_field(settings)
        keyargs = {'system': system, 'engine': engine}
        simulation = create_simulation(settings, keyargs)
        settings['initial-path']['load_folder'] = load_dir
        simulation.set_up_output(settings)
        return simulation

    @staticmethod
    def _set_up_for_load_2(settings, tempdir, copy_load=True):
        """Set up a second system for testing the initiate load method."""
        settings['simulation']['exe-path'] = tempdir
        load_dir = os.path.join(
            tempdir, settings['initial-path']['load_folder']
        )
        if copy_load:
            shutil.copytree(INTERNAL_LOAD_2, load_dir)
        units_from_settings(settings)
        engine = create_engine(settings)
        system = create_system(settings, engine=engine)
        system.forcefield = create_force_field(settings)
        keyargs = {'system': system, 'engine': engine}
        simulation = create_simulation(settings, keyargs)
        settings['initial-path']['load_folder'] = load_dir
        simulation.set_up_output(settings)
        return simulation

    def test_internal_load(self):
        """Test the load initialise for internal trajectories."""
        settings = parse_settings_file(os.path.join(HERE, 'internal', 'tis',
                                                    'tis.rst'))
        load_dir = os.path.join(HERE, 'internal', 'tis', 'load', '001')
        with tempfile.TemporaryDirectory() as tempdir:
            simulation = self._set_up_for_load(settings, tempdir)
            with patch('sys.stdout', new=StringIO()):
                init = simulation.initiate(settings)
                self.assertTrue(init)
            # We expect now that we have loaded for 001:
            self.assertEqual(len(simulation.path_ensembles), 1)
            self.assertEqual(simulation.path_ensembles[0].ensemble_number, 1)
            # Check that the path contains what it should:
            path = simulation.path_ensembles[0].last_path
            self.assertTrue(compare_trajs_int(load_dir, path))
            # Check that we created an ensemble dir:
            ensemble_dir = os.path.join(tempdir, '001')
            self.assertTrue(os.path.isdir(ensemble_dir))
            # Just delete simulation to force closing of files:
            del simulation
            compare_trajs_int(ensemble_dir, path)

    def test_fail_wrong_engine(self):
        """Test that the test fail for an unsupporten engine type."""
        settings = parse_settings_file(os.path.join(HERE, 'internal', 'tis',
                                                    'tis.rst'))
        with tempfile.TemporaryDirectory() as tempdir:
            simulation = self._set_up_for_load(settings, tempdir)
            simulation.engine.engine_type = 'this-should-fail!'
            with patch('sys.stdout', new=StringIO()):
                with self.assertRaises(ValueError):
                    simulation.initiate(settings)

    def test_internal_load_sparse(self):
        """Test the load initialise for internal trajectories."""
        settings = parse_settings_file(os.path.join(HERE, 'internal',
                                                    'retis-load',
                                                    'reload.rst'))
        with tempfile.TemporaryDirectory() as tempdir:
            simulation = self._set_up_for_load_2(settings, tempdir)
            with patch('sys.stdout', new=StringIO()):
                init = simulation.initiate(settings)
                self.assertTrue(init)
            path = []
            for i in range(3):
                path.append(simulation.path_ensembles[i].last_path)
            del simulation
            self.assertTrue(compare_trajs_int(os.path.join(tempdir, '000'),
                                              path[0]))

            self.assertTrue(os.path.exists(os.path.join(tempdir, '000')))
            self.assertTrue(os.path.exists(os.path.join(tempdir, '001',
                                                        'traj')))
            self.assertTrue(os.path.exists(os.path.join(tempdir, '002',
                                                        'generate')))
            self.assertTrue(os.path.exists(os.path.join(tempdir, '001',
                                                        'pathensemble.txt')))
            self.assertTrue(os.path.exists(os.path.join(tempdir, '002',
                                                        'order.txt')))
            self.assertEqual(path[0].status, 'ACC')
            for i in range(1, 2):
                self.assertEqual(path[i].status, 'ACC')

    def test_initiate_load_fail(self):
        """Test that the initiate load fails for non-existing load folder."""
        settings = parse_settings_file(
            os.path.join(HERE, 'internal', 'tis', 'tis.rst')
        )
        with tempfile.TemporaryDirectory() as tempdir:
            simulation = self._set_up_for_load(settings, tempdir,
                                               copy_load=False)
            with patch('sys.stdout', new=StringIO()):
                with self.assertRaises(FileNotFoundError):
                    simulation.initiate(settings)

    def test_initiate_load_fail2(self):
        """Test that the initiate load fails for insufficient file inputs."""
        settings = parse_settings_file(os.path.join(HERE, 'internal',
                                                    'retis-load',
                                                    'reload.rst'))
        with tempfile.TemporaryDirectory() as tempdir:
            with patch('sys.stdout', new=StringIO()):
                simulation = self._set_up_for_load_2(settings, tempdir)
            # Instead to change the inputs, we change the requirements.
            simulation.path_ensembles[0].interfaces = [1, 100, 100000]
            with patch('sys.stdout', new=StringIO()):
                with self.assertRaises(ValueError) as err:
                    _ = simulation.initiate(settings)
                self.assertTrue('000 does not satisfy the relative ensemble'
                                in str(err.exception))

    def test_reorderframes(self):
        """Test the reorder_frames funciton."""
        interfaces = [-18., -10., 1., 2., 60]
        path_ensembles, _ = create_path_ensembles(interfaces, 'internal',
                                                  include_zero=True)

        rgen = RandomGenerator(seed=0)
        path = Path(rgen, maxlen=1000)
        fill_path(path)

        path_ensemble = path_ensembles[0]
        left, _, right = path_ensemble.interfaces
        path_ensemble.start_condition = 'R'

        # Test that the re-order function generated path
        # satisfies the ensemble requirements (R, R case)
        path, _ = reorderframes(path, path_ensemble)

        self.assertEqual(path.get_start_point(left, right), 'R')
        self.assertEqual(path.get_end_point(left, right), 'R')
        self.assertTrue(path.ordermin[0] < interfaces[0])
        self.assertTrue(path.ordermax[0] > interfaces[0])

        path_ensemble = path_ensembles[1]
        left, _, right = path_ensemble.interfaces
        path_ensemble.start_condition = 'L'
        path = Path(rgen, maxlen=1000)
        fill_path(path)
        path, _ = reorderframes(path, path_ensemble)

        self.assertEqual(path.get_start_point(left, right), 'L')
        self.assertEqual(path.get_end_point(left, right), 'L')
        self.assertTrue(path.ordermin[0] < interfaces[0])
        self.assertTrue(path.ordermax[0] > interfaces[0])

        interfaces = [-18., -10., 1., 2., 10]
        path_ensembles, _ = create_path_ensembles(interfaces, 'internal',
                                                  include_zero=True)

        path_ensemble = path_ensembles[2]
        left, _, right = path_ensemble.interfaces
        path_ensemble.start_condition = 'L'
        path = Path(rgen, maxlen=1000)
        fill_path(path)
        path, _ = reorderframes(path, path_ensemble)

        self.assertEqual(path.get_start_point(left, right), 'L')
        self.assertEqual(path.get_end_point(left, right), 'L')

    def test_reorderframes2(self):
        """Test the clean_path function."""
        interfaces = [float('-inf'), -10., -5]
        path_ensemble = PathEnsemble(0, interfaces)
        rgen = RandomGenerator(seed=0)
        path = Path(rgen, maxlen=1000)

        fill_path(path, npoints=20000, scale=0.01)
        clean_path(path, path_ensemble)
        self.assertEqual(path.length, 2)
        self.assertTrue(_check_path(path, path_ensemble))

        interfaces = [-14., -10., 10]
        path_ensemble = PathEnsemble(0, interfaces)
        rgen = RandomGenerator(seed=0)
        path = Path(rgen, maxlen=1000)

        fill_path(path)
        clean_path(path, path_ensemble)
        self.assertEqual(path.length, 11)
        self.assertTrue(_check_path(path, path_ensemble))

        # Same results?
        clean_path(path, path_ensemble)
        self.assertEqual(path.length, 11)
        self.assertTrue(_check_path(path, path_ensemble))

        # Some intuitive numerical checks> Only crossing points
        # shall remain (4 for the 0 interface and one for the B
        # interface.
        path = fill_path(scale=10000)
        interfaces = [-16., 0., 16]
        path_ensemble = PathEnsemble(1, interfaces)
        initial_length = path.length
        path, _ = reorderframes(path, path_ensemble)

        # Numerical checks
        counter_R, counter_L, counter_M = 0, 0, 0
        for i, phasepoint in enumerate(path.phasepoints):
            if phasepoint.order[0] > interfaces[2]:
                counter_R += 1
            if phasepoint.order[0] < interfaces[0]:
                counter_L += 1
            if interfaces[0] < phasepoint.order[0] < interfaces[2]:
                counter_M += 1

        self.assertEqual(path.length, (counter_R + counter_L + counter_M))
        self.assertEqual((counter_R, counter_M, counter_L), (0, 1, 2))
        self.assertTrue(path.length < initial_length)
        self.assertEqual(path.length, 3)
        self.assertTrue(_check_path(path, path_ensemble))

        # Check that it doesn't fix the impossible.

        # Too large interfaces, all should be kept
        interfaces = [-14000., 0., 1000]
        path_ensemble = PathEnsemble(0, interfaces)

        path = fill_path(npoints=1000, scale=0.16)
        path, _ = reorderframes(path, path_ensemble)
        self.assertEqual((_check_path(path, path_ensemble)),
                         (False, 'EWI'))
        self.assertEqual(path.length, 2001)

        # Too large orderp, almost nothing should remain
        interfaces = [-16., 0., 16]
        path_ensemble = PathEnsemble(0, interfaces)
        path = fill_path(npoints=1000, scale=16016)
        path, _ = reorderframes(path, path_ensemble)
        self.assertEqual((_check_path(path, path_ensemble)),
                         (False, 'NCR'))
        self.assertEqual(path.length, 4)

    def test_external_load(self):
        """Test the load initialise for external trajectories."""
        settings = parse_settings_file(
            os.path.join(HERE, 'gromacs', 'tis.rst')
        )
        settings['engine']['gmx'] = GMX
        settings['engine']['mdrun'] = MDRUN
        with tempfile.TemporaryDirectory() as tempdir:
            settings['simulation']['exe-path'] = tempdir
            gmx_dir = os.path.join(tempdir, 'gmx_input')
            shutil.copytree(GMX_DIR, gmx_dir)
            load_dir = os.path.join(tempdir, 'load')
            shutil.copytree(GMX_LOAD, load_dir)
            settings['engine']['input_path'] = gmx_dir
            units_from_settings(settings)
            engine = create_engine(settings)
            system = create_system(settings, engine=engine)
            system.forcefield = create_force_field(settings)
            keyargs = {'system': system, 'engine': engine}
            simulation = create_simulation(settings, keyargs)
            settings['initial-path']['load_folder'] = load_dir
            simulation.set_up_output(settings)
            with patch('sys.stdout', new=StringIO()):
                init = simulation.initiate(settings)
                self.assertTrue(init)
            self.assertTrue(os.path.exists(os.path.join(tempdir, '023',
                                                        'accepted')))
            self.assertTrue(os.path.exists(os.path.join(tempdir, '023',
                                                        'order.txt')))
            self.assertTrue(os.path.exists(os.path.join(tempdir, '023',
                                                        'energy.txt')))
            self.assertTrue(os.path.exists(os.path.join(tempdir, '023',
                                                        'pathensemble.txt')))
            self.assertEqual(simulation.path_ensemble.last_path.status, 'ACC')

    def test_external_load_cp2k(self):
        """Test the load initialise for external trajectories with CP2K."""
        settings = parse_settings_file(
            os.path.join(HERE, 'cp2k', 'retis.rst'))
        settings['engine']['cp2k'] = CP2K

        with tempfile.TemporaryDirectory() as tempdir:
            settings['simulation']['exe-path'] = tempdir
            cp2k_dir = os.path.join(tempdir, 'cp2k_input')
            shutil.copytree(CP2K_DIR, cp2k_dir)
            load_dir = os.path.join(tempdir, 'load')
            shutil.copytree(CP2K_LOAD, load_dir)
            settings['engine']['input_path'] = cp2k_dir
            units_from_settings(settings)
            engine = create_engine(settings)
            system = create_system(settings, engine=engine)
            system.forcefield = create_force_field(settings)
            keyargs = {'system': system, 'engine': engine}
            simulation = create_simulation(settings, keyargs)
            settings['initial-path']['load_folder'] = load_dir
            simulation.set_up_output(settings)
            with patch('sys.stdout', new=StringIO()):
                init = simulation.initiate(settings)
                self.assertTrue(init)
            self.assertTrue(os.path.exists(os.path.join(tempdir, '000')))
            self.assertTrue(os.path.exists(os.path.join(tempdir, '001',
                                                        'traj')))
            self.assertTrue(os.path.exists(os.path.join(tempdir, '002',
                                                        'generate')))
            self.assertTrue(os.path.exists(os.path.join(tempdir, '003',
                                                        'accepted')))
            self.assertTrue(os.path.exists(os.path.join(load_dir, '002',
                                                        'accepted')))
            self.assertTrue(os.path.exists(os.path.join(load_dir, '003',
                                                        'order.txt')))
            self.assertTrue(os.path.exists(os.path.join(tempdir, '000',
                                                        'pathensemble.txt')))
            self.assertTrue(os.path.exists(os.path.join(tempdir, '003',
                                                        'pathensemble.txt')))
            for i in range(3):
                self.assertEqual(
                    simulation.path_ensembles[i].last_path.status, 'ACC')

            for i in range(1, 3):
                path = simulation.path_ensembles[i].last_path
                for j in range(int(path.length/3)):
                    point1 = path.phasepoints[j]
                    point2 = path.phasepoints[-1-j]
                    self.assertEqual(point1.order[0], point2.order[0])

    def test_external_load_mdtraj(self):
        """Test the load initialise for external trajectories."""
        settings = parse_settings_file(
            os.path.join(HERE, 'gromacs', 'auto-load.rst'))
        orderp_file = os.path.join(HERE, 'gromacs', 'orderp.py')
        settings['engine']['gmx'] = GMX
        settings['engine']['mdrun'] = MDRUN
        top_file = settings['initial-path']['top_file']

        with tempfile.TemporaryDirectory() as tempdir:
            settings['simulation']['exe-path'] = tempdir
            gmx_dir = os.path.join(tempdir, 'gmx_input')
            shutil.copytree(GMX_DIR, gmx_dir)
            shutil.copy(orderp_file, tempdir)
            tmp_top_file = os.path.join(tempdir, top_file)
            load_dir = os.path.join(tempdir, 'load')
            shutil.copytree(GMX_LOAD, load_dir)
            settings['engine']['input_path'] = gmx_dir
            units_from_settings(settings)
            engine = create_engine(settings)
            system = create_system(settings, engine=engine)
            system.forcefield = create_force_field(settings)
            keyargs = {'system': system, 'engine': engine}
            simulation = create_simulation(settings, keyargs)
            settings['initial-path']['load_folder'] = load_dir
            settings['initial-path']['top_file'] = tmp_top_file
            simulation.set_up_output(settings)
            with patch('sys.stdout', new=StringIO()):
                init = simulation.initiate(settings)
                self.assertTrue(init)
            self.assertTrue(os.path.exists(os.path.join(tempdir, '000')))
            self.assertTrue(os.path.exists(os.path.join(tempdir, '001',
                                                        'traj')))
            self.assertTrue(os.path.exists(os.path.join(tempdir, '002',
                                                        'generate')))
            self.assertTrue(os.path.exists(os.path.join(tempdir, '003',
                                                        'accepted')))
            self.assertTrue(os.path.exists(os.path.join(load_dir, '002',
                                                        'accepted')))
            self.assertTrue(os.path.exists(os.path.join(load_dir, '004',
                                                        'traj.txt')))
            self.assertTrue(os.path.exists(os.path.join(load_dir, '003',
                                                        'order.txt')))
            self.assertTrue(os.path.exists(os.path.join(tempdir, '000',
                                                        'pathensemble.txt')))
            self.assertTrue(os.path.exists(os.path.join(tempdir, '003',
                                                        'pathensemble.txt')))
            for i in range(4):
                self.assertEqual(
                    simulation.path_ensembles[i].last_path.status, 'ACC')

            self.assertTrue(os.path.exists(os.path.join(load_dir, '004',
                                                        'traj.txt')))

            for i in range(1, 4):
                path = simulation.path_ensembles[i].last_path
                for j in range(path.length-2):
                    point1 = path.phasepoints[j]
                    point2 = path.phasepoints[j+1]
                    self.assertTrue(point1.order[0] < point2.order[0])

    def test_external_load_mdtraj_2(self):
        """Test the load initialise for external trajectories."""
        settings = parse_settings_file(
            os.path.join(HERE, 'gromacs', 'auto-load.rst'))
        orderp_file = os.path.join(HERE, 'gromacs', 'orderp.py')
        settings['simulation']['interfaces'] = [2.78, 2.88, 3.01, 3.80, 14.00]
        settings['engine']['gmx'] = GMX
        settings['engine']['mdrun'] = MDRUN
        top_file = settings['initial-path']['top_file']

        with tempfile.TemporaryDirectory() as tempdir:
            settings['simulation']['exe-path'] = tempdir
            gmx_dir = os.path.join(tempdir, 'gmx_input')
            shutil.copytree(GMX_DIR, gmx_dir)
            shutil.copy(orderp_file, tempdir)
            tmp_top_file = os.path.join(tempdir, top_file)
            load_dir = os.path.join(tempdir, 'load')
            shutil.copytree(GMX_LOAD, load_dir)
            settings['engine']['input_path'] = gmx_dir
            units_from_settings(settings)
            engine = create_engine(settings)
            system = create_system(settings, engine=engine)
            system.forcefield = create_force_field(settings)
            keyargs = {'system': system, 'engine': engine}
            simulation = create_simulation(settings, keyargs)
            settings['initial-path']['load_folder'] = load_dir
            settings['initial-path']['top_file'] = tmp_top_file
            simulation.set_up_output(settings)
            with patch('sys.stdout', new=StringIO()):
                init = simulation.initiate(settings)
                self.assertTrue(init)
            self.assertTrue(os.path.exists(os.path.join(tempdir, '000')))
            self.assertTrue(os.path.exists(os.path.join(tempdir, '001',
                                                        'traj')))
            self.assertTrue(os.path.exists(os.path.join(tempdir, '002',
                                                        'generate')))
            self.assertTrue(os.path.exists(os.path.join(tempdir, '003',
                                                        'accepted')))
            self.assertTrue(os.path.exists(os.path.join(load_dir, '002',
                                                        'accepted')))
            self.assertTrue(os.path.exists(os.path.join(load_dir, '003',
                                                        'order.txt')))
            for i in range(3):
                self.assertEqual(
                    simulation.path_ensembles[i].last_path.status, 'ACC')

            self.assertTrue(os.path.exists(os.path.join(load_dir, '004',
                                                        'traj.txt')))

            for i in range(1, 3):
                path = simulation.path_ensembles[i].last_path
                for j in range(int(path.length/3)):
                    point1 = path.phasepoints[j]
                    point2 = path.phasepoints[-1-j]
                    self.assertEqual(point1.order[0], point2.order[0])

    def test_external_load_mdtraj_trr(self):
        """Test the load initialise for external trajectories."""
        settings = parse_settings_file(
            os.path.join(HERE, 'gromacs', 'auto-load.rst')
        )
        orderp_file = os.path.join(HERE, 'gromacs', 'orderp.py')
        settings['engine']['gmx'] = GMX
        settings['engine']['mdrun'] = MDRUN
        del settings['initial-path']['top_file']

        with tempfile.TemporaryDirectory() as tempdir:
            settings['simulation']['exe-path'] = tempdir
            gmx_dir = os.path.join(tempdir, 'gmx_input')
            shutil.copytree(GMX_DIR, gmx_dir)
            shutil.copy(orderp_file, tempdir)
            load_dir = os.path.join(tempdir, 'load-trj')
            shutil.copytree(GMX_LOAD_TRJ, load_dir)
            settings['engine']['input_path'] = gmx_dir
            units_from_settings(settings)
            engine = create_engine(settings)
            system = create_system(settings, engine=engine)
            system.forcefield = create_force_field(settings)
            keyargs = {'system': system, 'engine': engine}
            simulation = create_simulation(settings, keyargs)
            settings['initial-path']['load_folder'] = load_dir
            simulation.set_up_output(settings)
            with patch('sys.stdout', new=StringIO()):
                init = simulation.initiate(settings)
                self.assertTrue(init)
            self.assertTrue(os.path.exists(os.path.join(tempdir, '000')))
            self.assertTrue(os.path.exists(os.path.join(tempdir, '001',
                                                        'traj')))
            self.assertTrue(os.path.exists(os.path.join(tempdir, '002',
                                                        'generate')))
            self.assertTrue(os.path.exists(os.path.join(tempdir, '003',
                                                        'accepted')))
            self.assertTrue(os.path.exists(os.path.join(load_dir, '002',
                                                        'accepted')))
            self.assertTrue(os.path.exists(os.path.join(load_dir, '004',
                                                        'traj.txt')))
            self.assertTrue(os.path.exists(os.path.join(load_dir, '003',
                                                        'order.txt')))
            for i in range(4):
                self.assertEqual(
                    simulation.path_ensembles[i].last_path.status, 'ACC')

            self.assertTrue(os.path.exists(os.path.join(load_dir, '004',
                                                        'traj.txt')))

            exp_len = [None, 11, 11, 11]
            for i in range(1, 4):
                path = simulation.path_ensembles[i].last_path
                self.assertEqual(path.length, exp_len[i])

    @staticmethod
    def _create_empty_gro_files(tempdir, nfiles):
        """Create a given number of empty .gro files."""
        grofiles = []
        for i in range(nfiles):
            gro = 'conf{:04d}.gro'.format(i)
            grofile = os.path.join(tempdir, gro)
            pathlib.Path(grofile).touch()
            grofiles.append(gro)
        return grofiles

    def test_load_job(self):
        """Test some aspects of the dirty load method."""
        settings = parse_settings_file(os.path.join(HERE, 'internal', 'tis',
                                                    'tis.rst'))
        with tempfile.TemporaryDirectory() as tempdir:
            self._set_up_for_load(settings, tempdir)
            # Remove the ensemble directory to test what happens:
            edir = os.path.join(tempdir, '001')
            shutil.rmtree(edir)
            self.assertFalse(os.path.isdir(edir))
            # And remove the initial.xyz:
            remove_file(os.path.join(tempdir, 'initial.xyz'))
            with self.assertRaises(FileNotFoundError):
                _do_the_dirty_load_job(tempdir, edir)
            # Create some fake .gro files to see what happens next:
            grofiles = self._create_empty_gro_files(tempdir, 3)
            accepted = os.path.join(edir, 'accepted')
            self.assertFalse(os.path.isdir(edir))
            self.assertFalse(os.path.isdir(accepted))
            _do_the_dirty_load_job(tempdir, edir)
            # Check that edir was created:
            self.assertTrue(os.path.isdir(edir))
            # Check that the accepted dir was crated:
            self.assertTrue(os.path.isdir(accepted))
            # And that the gro files were copied:
            for i in grofiles:
                self.assertTrue(os.path.isfile(os.path.join(accepted, i)))
                remove_file(os.path.join(tempdir, i))
            # Remove the accepted dir and see what happens:
            shutil.rmtree(accepted)
            with self.assertRaises(FileNotFoundError):
                _do_the_dirty_load_job(tempdir, edir)
            # Add some files in tempdir and see what happens:
            grofiles = self._create_empty_gro_files(tempdir, 3)
            self.assertFalse(os.path.isdir(accepted))
            _do_the_dirty_load_job(tempdir, edir)
            self.assertTrue(os.path.isdir(accepted))
            # Check that files were copied:
            for i in grofiles:
                self.assertTrue(os.path.isfile(os.path.join(accepted, i)))
                self.assertTrue(os.path.isfile(os.path.join(tempdir, i)))
                remove_file(os.path.join(tempdir, i))
            shutil.rmtree(accepted)
            # Add some files in edir and see what happens:
            grofiles = self._create_empty_gro_files(edir, 3)
            self.assertFalse(os.path.isdir(accepted))
            _do_the_dirty_load_job(tempdir, edir)
            self.assertTrue(os.path.isdir(accepted))
            # Check that files were moved:
            for i in grofiles:
                self.assertTrue(os.path.isfile(os.path.join(accepted, i)))
                self.assertFalse(os.path.isfile(os.path.join(tempdir, i)))


if __name__ == '__main__':
    unittest.main()
