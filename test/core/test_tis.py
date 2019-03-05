# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test methods for doing TIS."""
from io import StringIO
import logging
import unittest
from unittest.mock import patch
import numpy as np
from pyretis.core import System, create_box, Particles
from pyretis.initiation import initiate_path_simulation
from pyretis.inout.setup import (
    create_force_field,
    create_engine,
    create_simulation
)
from pyretis.core.tis import (
    time_reversal,
    shoot,
)
from pyretis.inout.setup.createsimulation import create_path_ensembles
from pyretis.core.random_gen import MockRandomGenerator
from .help import (
    make_internal_path,
    MockEngine,
    MockEngine2,
    MockOrder,
    MockOrder2,
    SameOrder,
    NegativeOrder,
)

logging.disable(logging.CRITICAL)

TISMOL_001 = [[262, 'ACC', 'ki', -0.903862, 1.007330, 1, 262],
              [262, 'BWI', 'tr', -0.903862, 1.007330, 262, 1],
              [12, 'BWI', 'sh', 0.957091, 1.002750, 12, 1],
              [262, 'BWI', 'tr', -0.903862, 1.007330, 262, 1],
              [262, 'BWI', 'tr', -0.903862, 1.007330, 262, 1],
              [262, 'BWI', 'tr', -0.903862, 1.007330, 262, 1],
              [77, 'BWI', 'sh', 0.522609, 1.003052, 77, 1],
              [262, 'BWI', 'tr', -0.903862, 1.007330, 262, 1],
              [262, 'BWI', 'tr', -0.903862, 1.007330, 262, 1],
              [262, 'BWI', 'tr', -0.903862, 1.007330, 262, 1],
              [262, 'BWI', 'tr', -0.903862, 1.007330, 262, 1]]


def create_ensembles_and_paths():
    """Return some test data we can use."""
    interfaces = [-1., 0., 1., 2., 10]
    ensembles, _ = create_path_ensembles(interfaces, 'internal',
                                         include_zero=False)
    # Make some paths for the ensembles.
    starts = [(0, -1.1), (0, -1.05), (0, -1.123), (0, -1.01)]
    ends = [(100, -1.2), (100, -1.3), (100, -1.01),
            (100, 10.01)]
    maxs = [(50, -0.2), (50, 0.5), (50, 2.5), (100, 10.01)]
    for i, j, k, ens in zip(starts, ends, maxs, ensembles):
        path = make_internal_path(i, j, k, ens.interfaces[1])
        ens.add_path_data(path, 'ACC')
    return ensembles


def prepare_test_simulation():
    """Prepare a small system we can integrate."""
    settings = {}
    # Basic settings for the simulation:
    settings['simulation'] = {'task': 'tis',
                              'steps': 10,
                              'exe-path': '',
                              'interfaces': [-0.9, -0.9, 1.0]}
    settings['system'] = {'units': 'lj', 'temperature': 0.07}
    # Basic settings for the Langevin integrator:
    settings['engine'] = {'class': 'Langevin',
                          'gamma': 0.3,
                          'high_friction': False,
                          'seed': 1,
                          'rgen': 'mock-borg',
                          'timestep': 0.002}
    # Potential parameters:
    # The potential is: `V_\text{pot} = a x^4 - b (x - c)^2`
    settings['potential'] = [{'a': 1.0, 'b': 2.0, 'c': 0.0,
                              'class': 'DoubleWell'}]
    # Settings for the order parameter:
    settings['orderparameter'] = {'class': 'Position',
                                  'dim': 'x', 'index': 0, 'name': 'Position',
                                  'periodic': False}
    # TIS specific settings:
    settings['tis'] = {'freq': 0.5,
                       'maxlength': 20000,
                       'aimless': True,
                       'allowmaxlength': False,
                       'sigma_v': -1,
                       'seed': 1,
                       'rgen': 'mock-borg',
                       'zero_momentum': False,
                       'rescale_energy': False}
    settings['initial-path'] = {'method': 'kick'}

    box = create_box(periodic=[False])
    system = System(temperature=settings['system']['temperature'],
                    units=settings['system']['units'], box=box)
    system.particles = Particles(dim=system.get_dim())
    system.forcefield = create_force_field(settings)
    system.add_particle(np.array([-1.0]), mass=1, name='Ar', ptype=0)
    engine = create_engine(settings)
    kwargs = {'system': system, 'engine': engine}
    simulation = create_simulation(settings, kwargs)
    system.particles.vel = np.array([[0.78008019924163818]])
    return simulation, settings


class TISTest(unittest.TestCase):
    """Run a test for the TIS algorithm.

    This test will compare with results obtained by the old
    FORTRAN TISMOL program.
    """

    def test_tis_001(self):
        """Test a TIS simulation for 001."""
        simulation, in_settings = prepare_test_simulation()
        ensemble = simulation.path_ensemble
        with patch('sys.stdout', new=StringIO()):
            for i in range(10):
                if i == 0:
                    for _ in initiate_path_simulation(simulation, in_settings):
                        pass
                else:
                    simulation.step()
                path = ensemble.paths[-1]
                path_data = [
                    path['length'],
                    path['status'],
                    path['generated'][0],
                    path['ordermin'][0],
                    path['ordermax'][0]
                ]
                for j in (0, 1, 2):
                    self.assertEqual(path_data[j], TISMOL_001[i][j])
                self.assertAlmostEqual(path_data[3], TISMOL_001[i][3],
                                       places=6)
                self.assertAlmostEqual(path_data[4], TISMOL_001[i][4],
                                       places=6)


class TISTestMethod(unittest.TestCase):
    """Test the various TIS methods."""

    def test_time_reversal(self):
        """Test the time reversal move."""
        ensembles = create_ensembles_and_paths()
        status = ('ACC', 'ACC', 'ACC', 'BWI')
        accept = (True, True, True, False)
        for ens, acc, stat in zip(ensembles, accept, status):
            path = ens.last_path
            accept, new_path, status = time_reversal(
                path, SameOrder(), ens.interfaces, 'L'
            )
            for i, j in zip(path.phasepoints,
                            reversed(new_path.phasepoints)):
                parti = i.particles
                partj = j.particles
                # Check that positions are the same:
                self.assertTrue(np.allclose(parti.pos, partj.pos))
                # Check that velocities are reversed:
                self.assertTrue(np.allclose(parti.vel, -1.0 * partj.vel))
                # Check that energies are the same:
                self.assertAlmostEqual(parti.ekin, partj.ekin)
                self.assertAlmostEqual(parti.vpot, partj.vpot)
                # Check that order parameters are the same:
                self.assertAlmostEqual(i.order[0], j.order[0])
            self.assertEqual(accept, acc)
            self.assertEqual(status, stat)
            self.assertEqual(new_path.get_move(), 'tr')
            # Check that the ld move is not altered:
            path.set_move('ld')
            accept, new_path, status = time_reversal(
                path, SameOrder(), ens.interfaces, 'L'
            )
            self.assertEqual(new_path.get_move(), 'ld')
            # Check that order parameters are reversed:
            accept, new_path, status = time_reversal(
                path, NegativeOrder(), ens.interfaces, 'L'
            )
            for i, j in zip(path.phasepoints,
                            reversed(new_path.phasepoints)):
                self.assertAlmostEqual(i.order[0], -1 * j.order[0])

    def test_shoot1(self):
        """Test the shooting move, vol 1."""
        ensembles = create_ensembles_and_paths()
        order = MockOrder()
        engine = MockEngine(1.0)
        tis_settings = {
            'maxlength': 1000,
            'sigma_v': -1,
            'aimless': True,
            'zero_momentum': False,
            'rescale_energy': False,
            'allowmaxlength': False
        }
        # Generate BTL:
        ens = ensembles[0]
        rgen = MockRandomGenerator(seed=1)
        accept, _, status = shoot(ens.last_path, order,
                                  ens.interfaces, engine,
                                  rgen, tis_settings, 'L')
        self.assertEqual(status, 'BTL')
        self.assertFalse(accept)
        # Generate BTX:
        tis_settings['allowmaxlength'] = True
        accept, _, status = shoot(ens.last_path, order,
                                  ens.interfaces, engine,
                                  rgen, tis_settings, 'L')
        self.assertEqual(status, 'BTX')
        self.assertFalse(accept)
        # Generate BWI:
        tis_settings['allowmaxlength'] = True
        engine.total_eclipse = float('inf')
        engine.delta_v = 1
        accept, _, status = shoot(ens.last_path, order,
                                  ens.interfaces, engine,
                                  rgen, tis_settings, 'L')
        self.assertEqual(status, 'BWI')
        self.assertFalse(accept)
        # Generate ACC:
        tis_settings['allowmaxlength'] = False
        engine.total_eclipse = float('inf')
        engine.delta_v = -0.01
        accept, _, status = shoot(ens.last_path, order,
                                  ens.interfaces, engine,
                                  rgen, tis_settings, 'L')
        self.assertEqual(status, 'ACC')
        self.assertTrue(accept)

    def test_shoot2(self):
        """Test the shooting move, vol 2."""
        ensembles = create_ensembles_and_paths()
        order = MockOrder()
        engine = MockEngine(1.0)
        tis_settings = {
            'maxlength': 1000,
            'sigma_v': -1,
            'aimless': True,
            'zero_momentum': False,
            'rescale_energy': False,
            'allowmaxlength': False,
        }
        # Generate NCR:
        ens = ensembles[2]
        path = ens.last_path
        rgen = MockRandomGenerator(seed=1)
        tis_settings['allowmaxlength'] = False
        engine.total_eclipse = float('inf')
        engine.delta_v = -0.1
        ens.interfaces = (-1., 9., 10.)
        accept, _, status = shoot(ens.last_path, order,
                                  (-1., 9., 10.), engine,
                                  rgen, tis_settings, 'L')
        self.assertEqual(status, 'NCR')
        self.assertFalse(accept)
        # Generate FTL:
        ens = ensembles[2]
        engine = MockEngine2(1.0, ens.interfaces)
        tis_settings['allowmaxlength'] = False
        engine.delta_v = -0.1
        accept, _, status = shoot(ens.last_path, order,
                                  ens.interfaces, engine,
                                  rgen, tis_settings, 'L')
        self.assertEqual(status, 'FTL')
        self.assertFalse(accept)
        # Generate FTX:
        engine = MockEngine2(1.0, ens.interfaces)
        tis_settings['allowmaxlength'] = True
        engine.delta_v = -0.01
        accept, _, status = shoot(path, order,
                                  ens.interfaces, engine,
                                  rgen, tis_settings, 'L')
        self.assertEqual(status, 'FTX')
        self.assertFalse(accept)
        # re Generate FTX, test move 'ld' option:
        engine = MockEngine2(1.0, ens.interfaces)
        tis_settings['allowmaxlength'] = False
        path.set_move('ld')
        engine.delta_v = -0.01
        accept, _, status = shoot(path, order,
                                  ens.interfaces, engine,
                                  rgen, tis_settings, 'L')
        self.assertEqual(status, 'FTX')
        self.assertFalse(accept)

    def test_shoot_kob(self):
        """Test the shooting move when we get a KOB."""
        ensembles = create_ensembles_and_paths()
        order = MockOrder2()
        engine = MockEngine(1.0)
        tis_settings = {
            'maxlength': 1000,
            'sigma_v': -1,
            'aimless': True,
            'zero_momentum': False,
            'rescale_energy': False,
            'allowmaxlength': False,
        }
        # Generate BTL:
        ens = ensembles[0]
        rgen = MockRandomGenerator(seed=1)
        accept, _, status = shoot(ens.last_path, order,
                                  ens.interfaces, engine,
                                  rgen, tis_settings, 'L')
        self.assertEqual(status, 'KOB')
        self.assertFalse(accept)

    def test_shoot_aiming(self):
        """Test the non aimless shooting move."""
        ensembles = create_ensembles_and_paths()
        order = MockOrder()
        engine = MockEngine(1.0)
        tis_settings = {
            'maxlength': 1000,
            'sigma_v': -1,
            'aimless': False,
            'zero_momentum': False,
            'rescale_energy': False,
            'allowmaxlength': False,
        }
        # Generate ACC:
        tis_settings['allowmaxlength'] = True
        engine.total_eclipse = float('inf')
        engine.delta_v = -0.01
        ens = ensembles[2]
        rgen = MockRandomGenerator(seed=1)
        accept, _, status = shoot(ens.last_path, order,
                                  ens.interfaces, engine,
                                  rgen, tis_settings, 'L')
        self.assertEqual(status, 'ACC')
        self.assertTrue(accept)
        # Generate MCR:
        accept, _, status = shoot(ens.last_path, order,
                                  ens.interfaces, engine,
                                  rgen, tis_settings, 'L')
        self.assertEqual(status, 'MCR')
        self.assertFalse(accept)


if __name__ == '__main__':
    unittest.main()
