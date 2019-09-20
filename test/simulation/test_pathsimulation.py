# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the path simulation classes."""
from io import StringIO
import unittest
from unittest.mock import patch
import logging
import tempfile
import os
import copy
from shutil import copyfile
from pyretis.simulation.path_simulation import (
    PathSimulation,
    SimulationRETIS,
)
from pyretis.inout.settings import add_default_settings
from pyretis.inout.setup import (
    create_force_field,
    create_engine,
    create_orderparameter,
)
from pyretis.inout.setup.createsystem import create_system_from_settings
from pyretis.inout.setup.createsimulation import create_path_ensembles
from pyretis.orderparameter import Position
from pyretis.engines.internal import Langevin, VelocityVerlet
from pyretis.core.random_gen import (
    MockRandomGenerator,
    create_random_generator,
)
from pyretis.core.units import units_from_settings
from .test_helpers import TEST_SETTINGS


logging.disable(logging.CRITICAL)


HERE = os.path.abspath(os.path.dirname(__file__))


SETTINGS1 = {
    'simulation': {
        'task': 'tis',
        'steps': 10,
        'interfaces': [-0.9, -0.9, 1.0],
    },
    'system': {'units': 'lj', 'temperature': 0.1, 'dimensions': 1},
    'engine': {
        'class': 'Langevin',
        'gamma': 0.3,
        'high_friction': False,
        'seed': 321,
        'timestep': 0.002
    },
    'potential': [{'a': 1.0, 'b': 2.0, 'c': 0.0, 'class': 'DoubleWell'}],
    'orderparameter': {
        'class': 'Position',
        'dim': 'x',
        'index': 0,
        'name': 'Position',
        'periodic': False
    },
    'initial-path': {'method': 'kick'},
    'particles': {'position': {'file': 'initial.xyz'}},
    'retis': {
        'swapfreq': 0.5,
        'nullmoves': True,
        'swapsimul': True,
    },
    'tis': {
        'freq': 0.5,
        'maxlength': 2000,
        'aimless': True,
        'allowmaxlength': False,
        'sigma_v': -1,
        'seed': 1,
        'rgen': 'mock',
        'zero_momentum': False,
        'rescale_energy': False,
    },
}


def create_variables(stochastic=False, exe_path=None):
    """Create system, engine, order parameter etc."""
    settings = {key: copy.deepcopy(val) for key, val in TEST_SETTINGS.items()}
    add_default_settings(settings)
    if exe_path is not None:
        settings['simulation']['exe-path'] = exe_path
    units_from_settings(settings)
    if stochastic:
        engine = Langevin(0.002, 1.0)
        engine.rgen = MockRandomGenerator(seed=2)
    else:
        engine = VelocityVerlet(0.002)
    system = create_system_from_settings(settings, engine)
    system.forcefield = create_force_field(settings)
    order_function = Position(0)
    ensembles, _ = create_path_ensembles(
        [-1.0, 0.0, 1.0, 2.0],
        'internal',
        include_zero=True,
        exe_dir=exe_path
    )
    rgen = MockRandomGenerator(seed=1)
    return settings, engine, system, order_function, ensembles, rgen


def create_variables1(exe_path=None):
    """Create system, engine, order parameter etc."""
    settings = {key: copy.deepcopy(val) for key, val in SETTINGS1.items()}
    add_default_settings(settings)
    if exe_path is not None:
        settings['simulation']['exe-path'] = exe_path
        source = os.path.join(
            HERE, settings['particles']['position']['file']
        )
        target = os.path.join(
            exe_path, settings['particles']['position']['file']
        )
        copyfile(source, target)
    units_from_settings(settings)
    engine = create_engine(settings)
    system = create_system_from_settings(settings, engine)
    system.forcefield = create_force_field(settings)
    order_function = create_orderparameter(settings)
    ensembles, _ = create_path_ensembles(
        settings['simulation']['interfaces'],
        'internal',
        include_zero=True,
        exe_dir=exe_path
    )
    rgen = create_random_generator(settings)
    return settings, engine, system, order_function, ensembles, rgen


class TestPathSimulation(unittest.TestCase):
    """Run the tests for the PathSimulation class."""

    def test_init(self):
        """Test that we can create the simulation object."""
        settings, engine, system, order, ensembles, rgen = create_variables()
        simulation = PathSimulation(system, order, engine, ensembles, settings)
        self.assertTrue(hasattr(simulation, 'rgen'))
        simulation = PathSimulation(system, order, engine, ensembles, settings,
                                    rgen=rgen)
        self.assertEqual(len(simulation.path_ensembles), len(ensembles))
        for i, j in zip(simulation.path_ensembles, ensembles):
            self.assertIs(i, j)
        self.assertTrue(simulation.settings['tis']['aimless'])
        settings['tis']['sigma_v'] = 0.1
        simulation = PathSimulation(system, order, engine, ensembles, settings,
                                    rgen=rgen)
        self.assertFalse(simulation.settings['tis']['aimless'])
        del settings['tis']
        with self.assertRaises(ValueError):
            PathSimulation(system, order, engine, ensembles,
                           settings, rgen=rgen)

    def test_restart_info(self):
        """Test generation of restart info."""
        settings, engine, system, order, ensembles, rgen = create_variables(
            stochastic=True
        )
        simulation = PathSimulation(system, order, engine, ensembles, settings,
                                    rgen=rgen)
        info = simulation.restart_info()
        for key in ('cycle', 'rgen'):
            self.assertIn(key, info)
        self.assertEqual(info['rgen'], 1)
        self.assertIn('engine', info)
        self.assertIn('rgen', info['engine'])
        self.assertEqual(info['engine']['rgen'], 2)
        settings, engine, system, order, ensembles, rgen = create_variables()
        simulation = PathSimulation(system, order, engine, ensembles, settings,
                                    rgen=rgen)
        info = simulation.restart_info()
        self.assertNotIn('engine', info)

    def test_write_restart_file(self):
        """Test that we can create the restart files."""
        with tempfile.TemporaryDirectory() as tempdir:
            var = create_variables(exe_path=tempdir)
            settings, engine, system, order, ensembles, rgen = var
            simulation = PathSimulation(system, order, engine, ensembles,
                                        settings, rgen=rgen)
            simulation.set_up_output(settings)
            simulation.write_restart(now=True)
            dirs = [i.name for i in os.scandir(tempdir) if i.is_dir()]
            self.assertEqual(len(dirs), 4)
            for i in ensembles:
                self.assertIn(i.ensemble_name_simple, dirs)
                for j in os.scandir(i.directory['path-ensemble']):
                    if j.is_file():
                        self.assertEqual('ensemble.restart', j.name)
            files = [i.name for i in os.scandir(tempdir) if i.is_file()]
            self.assertEqual(len(files), 1)
            self.assertIn('pyretis.restart', files)

    def test_initiation(self):
        """Test the initiation method."""
        with tempfile.TemporaryDirectory() as tempdir:
            var = create_variables1(exe_path=tempdir)
            settings, engine, system, order, ensembles, rgen = var
            simulation = PathSimulation(system, order, engine,
                                        ensembles, settings, rgen=rgen)
            simulation.set_up_output(settings)
            with patch('sys.stdout', new=StringIO()):
                self.assertTrue(simulation.initiate(settings))
            # Check the soft exit option:
            open(os.path.join(tempdir, 'EXIT'), 'w').close()
            with patch('sys.stdout', new=StringIO()):
                self.assertFalse(simulation.initiate(settings))


class TestSimulationRETIS(unittest.TestCase):
    """Run the tests for the SimulationRETIS class."""

    def test_step(self):
        """Test the initiation method."""
        moves = {'move-0': 'swap', 'move-1': 'swap', 'move-2': 'nullmove'}
        with tempfile.TemporaryDirectory() as tempdir:
            var = create_variables1(exe_path=tempdir)
            settings, engine, system, order, ensembles, rgen = var
            simulation = SimulationRETIS(system, order, engine,
                                         ensembles, settings, rgen)
            simulation.set_up_output(settings)
            with patch('sys.stdout', new=StringIO()):
                self.assertTrue(simulation.initiate(settings))
                result = simulation.step()
                for key, move in moves.items():
                    self.assertIn(key, result)
                    self.assertEqual(move, result[key])


if __name__ == '__main__':
    unittest.main()
