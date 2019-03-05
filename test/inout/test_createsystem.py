# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the methods in pyretis.inout.setup.createsystem"""
import os
import logging
import unittest
import numpy as np
from pyretis.core.units import create_conversion_factors
from pyretis.core.box import RectangularBox, TriclinicBox
from pyretis.core.system import System
from pyretis.core.particles import Particles, ParticlesExt
from pyretis.engines.internal import MDEngine
from pyretis.engines.external import ExternalMDEngine
from pyretis.inout.setup.createsystem import (
    list_get,
    guess_particle_mass,
    initial_positions_lattice,
    initial_positions_file,
    create_initial_positions,
    set_up_box,
    create_velocities,
    create_system_from_restart,
    create_system_from_settings,
    create_system,
)
logging.disable(logging.CRITICAL)


HERE = os.path.abspath(os.path.dirname(__file__))


def create_test_system():
    """Create a system we can use for testing."""
    settings = {
        'system': {'dimensions': 3, 'units': 'lj'},
        'particles': {
            'position': {
                'generate': 'fcc',
                'repeat': [1, 2, 3],
                'density': 0.9
            }
        }
    }
    create_conversion_factors(settings['system']['units'])
    particles, boxs = initial_positions_lattice(settings)
    box = set_up_box({}, boxs)
    system = System(units='lj', box=box, temperature=1.0)
    system.particles = particles
    return system, settings


class DummyExternal(ExternalMDEngine):
    """A dummy external engine. Only useful for testing!"""

    def __init__(self, input_path, timestep, subcycles):
        """Initialise the dummy engine."""
        super().__init__('External engine for testing!', timestep,
                         subcycles)
        self.input_path = os.path.abspath(input_path)
        self.input_files = {
            'conf': os.path.join(self.input_path, 'dummy_config'),
            'template': os.path.join(self.input_path, 'dummy_template'),
        }

    def step(self, system, name):
        pass

    def _read_configuration(self, filename):
        pass

    def _reverse_velocities(self, filename, outfile):
        pass

    def _extract_frame(self, traj_file, idx, out_file):
        pass

    def _propagate_from(self, name, path, system, order_function, interfaces,
                        msg_file, reverse=False):
        # pylint: disable=too-many-arguments
        pass

    def modify_velocities(self, system, rgen, sigma_v=None, aimless=True,
                          momentum=False, rescale=None):
        # pylint: disable=too-many-arguments
        pass


class TestMethods(unittest.TestCase):
    """Test some of the methods from .createsystem"""

    def test_list_get(self):
        """Test the list_get method."""
        lst = [1, 2, 3]
        for idx, i in enumerate(lst):
            item = list_get(lst, idx)
            self.assertEqual(item, i)
        for i in range(3, 10):
            item = list_get(lst, i)
            self.assertEqual(item, lst[-1])

    def test_guess_particle_mass(self):
        """Test the guess_particle_mass method."""
        mass = guess_particle_mass(0, 'He', 'g/mol')
        self.assertAlmostEqual(mass, 4.002602)
        mass = guess_particle_mass(0, 'X', 'g/mol')
        self.assertAlmostEqual(mass, 1.0)

    def test_initial_positions_lattice(self):
        """Test that we can generate positions on a lattice."""
        settings = {'particles': {}, 'system': {'dimensions': 3}}
        settings['particles']['position'] = {
            'generate': 'fcc',
            'repeat': [1, 2, 3],
            'density': 0.9,
        }
        settings['particles']['mass'] = {'X': 1.23}
        settings['particles']['name'] = ['X']
        settings['particles']['type'] = [42]
        particles, box = initial_positions_lattice(settings)
        for i in particles.ptype:
            self.assertEqual(i, 42)
        for i in particles.mass:
            self.assertAlmostEqual(i, 1.23)
        for i in particles.name:
            self.assertEqual(i, 'X')
        lenx, leny, lenz = box['high']
        self.assertAlmostEqual(lenx, 1.64414138)
        self.assertAlmostEqual(leny / lenx, 2.0)
        self.assertAlmostEqual(lenz / lenx, 3.0)

    def test_initial_positions_file(self):
        """Test that we can get initial positions from a file."""
        gro = os.path.join(HERE, 'config.gro')
        settings = {
            'particles': {'position': {'file': gro}},
            'system': {'dimensions': 3, 'units': 'reduced'}
        }
        create_conversion_factors(settings['system']['units'])
        particles, box, vel = initial_positions_file(settings)
        self.assertTrue(vel)
        self.assertEqual(particles.dim, 3)
        for i in box['cell']:
            self.assertAlmostEqual(i, 20.0)
        for i, j in zip(particles.name, ['Ba', 'Hf', 'O', 'O', 'O']):
            self.assertEqual(i, j)
        # Test override particle names:
        settings['particles']['name'] = ['X', 'Y', 'Z']
        particles, _, _ = initial_positions_file(settings)
        for i, j in zip(particles.name, ['X', 'Y', 'Z', 'Z', 'Z']):
            self.assertEqual(i, j)
        # Test override dimensions:
        settings['system']['dimensions'] = 2
        particles, _, _ = initial_positions_file(settings)
        self.assertEqual(particles.dim, 2)
        # Test missing file info:
        settings['particles']['position'] = {}
        with self.assertRaises(ValueError):
            initial_positions_file(settings)
        # Test unknown format:
        settings['particles']['position'] = {'file': 'file.fancy_format'}
        with self.assertRaises(ValueError):
            initial_positions_file(settings)
        # Test .txt format and multiple snapshots:
        settings['particles']['position'] = {
            'file': os.path.join(HERE, 'config.txt')
        }
        logging.disable(logging.INFO)
        with self.assertLogs('pyretis.inout.setup.createsystem',
                             level='WARNING'):
            initial_positions_file(settings)
        logging.disable(logging.CRITICAL)
        # Test empty config:
        settings['particles']['position'] = {
            'file': os.path.join(HERE, 'config_empty.txt')
        }
        with self.assertRaises(ValueError):
            initial_positions_file(settings)

    def test_create_initial_positions(self):
        """Test that we can create initial positions."""
        # On a lattice:
        settings = {
            'particles': {},
            'system': {'dimensions': 3, 'units': 'reduced'}
        }
        create_conversion_factors(settings['system']['units'])
        settings['particles']['position'] = {
            'generate': 'fcc',
            'repeat': [1, 2, 3],
            'density': 0.9,
        }
        create_initial_positions(settings)
        # From a file:
        settings['particles'] = {
            'position': {'file': os.path.join(HERE, 'config.gro')},
        }
        create_initial_positions(settings)
        # And that we fail for other/missing settings:
        settings['particles'] = {
            'position': {'something-else': None},
        }
        with self.assertRaises(ValueError):
            create_initial_positions(settings)

    def test_set_up_box(self):
        """Test that we can set up a box from settings."""
        # From settings:
        settings = {
            'box': {'cell': [1, 2, 3], 'periodic': [True, False, True]}
        }
        box = set_up_box(settings, None)
        self.assertIsInstance(box, RectangularBox)
        for i, j in zip(box.cell, [1., 2., 3.]):
            self.assertAlmostEqual(i, j)
        for i, j in zip(box.periodic, [True, False, True]):
            self.assertEqual(i, j)
        # From dict, with missing settings:
        settings = {}
        boxs = {'cell': [1, 2, 3, 4, 5, 6]}
        box = set_up_box(settings, boxs)
        self.assertIsInstance(box, TriclinicBox)
        mat = np.array([[1., 4., 5.], [0., 2., 6.], [0., 0., 3.]])
        self.assertTrue(np.allclose(box.box_matrix, mat))
        # When we have no settings at all:
        settings = {}
        box = set_up_box(settings, None)
        self.assertIsInstance(box, RectangularBox)
        for i in box.periodic:
            self.assertFalse(i)

    def test_create_velocities(self):
        """Test that we can create velocities."""
        system, settings = create_test_system()
        # If velocities have already be set:
        create_velocities(system, settings, True)
        # If we want to generate them:
        settings['particles']['velocity'] = {
            'generate': 'maxwell',
            'temperature': 4.321,
            'momentum': True,
            'seed': 0
        }
        create_velocities(system, settings, True)
        temp = system.calculate_temperature()
        self.assertAlmostEqual(temp, 4.321)
        # If we want to scale to some energy:
        settings['particles']['velocity'] = {
            'scale': 100.,
        }
        create_velocities(system, settings, True)

    def test_create_system_from_restart(self):
        """Test that we can create from restart settings."""
        system, _ = create_test_system()
        restart = {}
        restart['system'] = system.restart_info()
        system2 = create_system_from_restart(restart)
        self.assertEqual(system.units, system2.units)

    def test_create_system_settings(self):
        """Test creation of system from settings."""
        # On a lattice:
        settings = {
            'particles': {},
            'system': {'dimensions': 3, 'units': 'reduced', 'temperature': 1.0}
        }
        create_conversion_factors(settings['system']['units'])
        settings['particles']['position'] = {
            'generate': 'fcc',
            'repeat': [1, 2, 3],
            'density': 0.9,
        }
        engine = MDEngine(1.0, 'Just for testing')
        system = create_system_from_settings(settings, engine)
        self.assertIsInstance(system.particles, Particles)
        engine = DummyExternal('test', 1.0, 10)
        system = create_system_from_settings(settings, engine)
        self.assertIsInstance(system.particles, ParticlesExt)
        # Test that missing 'particles' in settings combined with
        # an internal engine gives an KeyError:
        del settings['particles']
        engine = MDEngine(1.0, 'Just for testing')
        self.assertRaises(KeyError, lambda: create_system_from_settings(
            settings, engine))

    def test_create_system(self):
        """Test that we can use the create_system method."""
        # With restart:
        system, _ = create_test_system()
        restart = {}
        restart['system'] = system.restart_info()
        system2 = create_system(None, None, restart=restart)
        self.assertEqual(system.units, system2.units)
        # From settings:
        settings = {
            'particles': {},
            'system': {'dimensions': 3, 'units': 'reduced', 'temperature': 1.0}
        }
        create_conversion_factors(settings['system']['units'])
        settings['particles']['position'] = {
            'generate': 'fcc',
            'repeat': [1, 2, 3],
            'density': 0.9,
        }
        engine = MDEngine(1.0, 'Just for testing')
        system3 = create_system(settings, engine)
        self.assertIsInstance(system3.particles, Particles)


if __name__ == '__main__':
    unittest.main()
