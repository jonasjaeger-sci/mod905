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
from pyretis.core.pathensemble import PathEnsemble
from pyretis.core.tis import (
    make_tis_step_ensemble,
    time_reversal,
    web_throwing,
    stone_skipping,
    extender,
    select_shoot,
    ss_wt_acceptance,
    shoot,
    paste_paths,
    make_path,
)
from pyretis.engines.internal import VelocityVerlet, RandomWalk
from pyretis.initiation import initiate_path_simulation
from pyretis.inout.setup import (
    create_force_field,
    create_engine,
    create_simulation
)
from pyretis.orderparameter import Position
from pyretis.inout.setup.createsimulation import create_path_ensembles
from pyretis.core.random_gen import MockRandomGenerator, RandomGenerator
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

    This painful test will compare with results obtained by the old
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
        order_f = MockOrder()
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
        accept, _, status = shoot(ens.last_path, order_f,
                                  ens.interfaces, engine,
                                  rgen, tis_settings, 'L')
        self.assertEqual(status, 'BTL')
        self.assertFalse(accept)
        # Generate BTX:
        tis_settings['allowmaxlength'] = True
        accept, _, status = shoot(ens.last_path, order_f,
                                  ens.interfaces, engine,
                                  rgen, tis_settings, 'L')
        self.assertEqual(status, 'BTX')
        self.assertFalse(accept)
        # Generate BWI:
        tis_settings['allowmaxlength'] = True
        engine.total_eclipse = float('inf')
        engine.delta_v = 1
        accept, _, status = shoot(ens.last_path, order_f,
                                  ens.interfaces, engine,
                                  rgen, tis_settings, 'L')
        self.assertEqual(status, 'BWI')
        self.assertFalse(accept)
        # Generate ACC:
        tis_settings['allowmaxlength'] = False
        engine.total_eclipse = float('inf')
        engine.delta_v = -0.01
        accept, _, status = shoot(ens.last_path, order_f,
                                  ens.interfaces, engine,
                                  rgen, tis_settings, 'L')
        self.assertEqual(status, 'ACC')
        self.assertTrue(accept)

    def test_shoot2(self):
        """Test the shooting move, vol 2."""
        ensembles = create_ensembles_and_paths()
        order_f = MockOrder()
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
        accept, _, status = shoot(ens.last_path, order_f,
                                  (-1., 9., 10.), engine,
                                  rgen, tis_settings, 'L')
        self.assertEqual(status, 'NCR')
        self.assertFalse(accept)
        # Generate FTL:
        ens = ensembles[2]
        engine = MockEngine2(1.0, ens.interfaces)
        tis_settings['allowmaxlength'] = False
        engine.delta_v = -0.1
        accept, _, status = shoot(ens.last_path, order_f,
                                  ens.interfaces, engine,
                                  rgen, tis_settings, 'L')
        self.assertEqual(status, 'FTL')
        self.assertFalse(accept)
        # Generate FTX:
        engine = MockEngine2(1.0, ens.interfaces)
        tis_settings['allowmaxlength'] = True
        engine.delta_v = -0.01
        accept, _, status = shoot(path, order_f,
                                  ens.interfaces, engine,
                                  rgen, tis_settings, 'L')
        self.assertEqual(status, 'FTX')
        self.assertFalse(accept)
        # re Generate FTL, test move 'ld' option:
        engine = MockEngine2(1.0, ens.interfaces)
        tis_settings['allowmaxlength'] = True
        path.set_move('ld')
        engine.delta_v = -0.01
        accept, _, status = shoot(path, order_f,
                                  ens.interfaces, engine,
                                  rgen, tis_settings, 'L')
        self.assertEqual(status, 'FTX')
        self.assertFalse(accept)

    def test_shoot_kob(self):
        """Test the shooting move when we get a KOB."""
        ensembles = create_ensembles_and_paths()
        order_f = MockOrder2()
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
        accept, _, status = shoot(ens.last_path, order_f,
                                  ens.interfaces, engine,
                                  rgen, tis_settings, 'L')
        self.assertEqual(status, 'KOB')
        self.assertFalse(accept)

    def test_shoot_aiming(self):
        """Test the non aimless shooting move."""
        ensembles = create_ensembles_and_paths()
        order_f = MockOrder()
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
        accept, _, status = shoot(ens.last_path, order_f,
                                  ens.interfaces, engine,
                                  rgen, tis_settings, 'L')
        self.assertEqual(status, 'ACC')
        self.assertTrue(accept)
        # Generate MCR:
        accept, _, status = shoot(ens.last_path, order_f,
                                  ens.interfaces, engine,
                                  rgen, tis_settings, 'L')
        self.assertEqual(status, 'MCR')
        self.assertFalse(accept)

    def test_web_throwing_real(self):
        """Test web_throwing shooting move with real dynamics."""
        tis_settings = {
            'maxlength': 1000,
            'sigma_v': -1,
            'aimless': False,
            'zero_momentum': False,
            'rescale_energy': False,
            'allowmaxlength': True,
            'n_jumps': 22,
            'interface_sour': -1.95
        }

        interfaces = [-3, -1.4, 2.3]
        order_f = Position(index=0)
        engine = VelocityVerlet(0.01)
        rgen = RandomGenerator(seed=0)

        trial_path = make_internal_path((-5, 2.1), (5, 2.2), (1, -1))
        shooting_point = trial_path.phasepoints[4]
        shooting_point.idx = 4

        _, path, _ = make_path(trial_path, order_f, interfaces, engine,
                               tis_settings, maxlen=1000,
                               shooting_point=shooting_point, start_cond='L')

        interfaces = [-20, -1, 10]
        accept, new_path, status = web_throwing(path, order_f,
                                                interfaces, engine,
                                                rgen, tis_settings)

        self.assertEqual(status, 'NSG')
        self.assertFalse(accept)

        interfaces = [-3, -1.4, 2.3]
        accept, new_path, status = select_shoot(path, order_f,
                                                interfaces, engine,
                                                rgen, tis_settings,
                                                shooting_move='wt',
                                                start_cond='L')

        self.assertEqual(status, 'ACC')
        self.assertTrue(accept)

        tis_settings['n_jumps'] = 0
        path.generated = ('ld', 0, 0, 0)
        accept, trial_path, status = web_throwing(path, order_f,
                                                  interfaces, engine,
                                                  rgen, tis_settings)

        # With No jumps, the final path has to be equal to the initial
        for ps1, ps2 in zip(trial_path.phasepoints, path.phasepoints):
            self.assertTrue(ps1 == ps2)  # This is a ESSENTIAL test
        self.assertEqual(status, 'ACC')
        self.assertTrue(accept)
        self.assertEqual(path.generated[0], 'ld')

        tis_settings['interface_sour'] = 10
        with self.assertRaises(ValueError):
            web_throwing(path_old=path, order_function=order_f,
                         interfaces=[-100., 1., 100.], engine=engine,
                         rgen=rgen, tis_settings=tis_settings)

    def test_web_throwing(self):
        """Test web_throwing shooting move with rnd dynamics."""
        tis_settings = {
            'maxlength': 10000,
            'sigma_v': 10,
            'aimless': True,
            'zero_momentum': False,
            'rescale_energy': False,
            'allowmaxlength': False,
            'n_jumps': 16,
            'interface_sour': 0.
        }
        interfaces = [-1., 2., 9.]
        order_f = Position(index=0)
        engine = RandomWalk(timestep=0.5)
        rgen = RandomGenerator(seed=16)

        path = make_internal_path((-5, 2.1), (5, 2.2), (1, -1))
        _, trial_path, _ = shoot(path, order_f, interfaces, engine, rgen,
                                 tis_settings, 'L')
        trial_path.generated = ('ld', 0, 0, 0)

        # Generate ACC:
        accept, path, status = web_throwing(trial_path, order_f,
                                            interfaces, engine,
                                            rgen, tis_settings)
        self.assertEqual(path.generated[0], 'wt')
        self.assertEqual(status, 'ACC')
        self.assertTrue(accept)

        # iF No jumps, the extension on this absurd interfaces
        # should get lost (BTX)
        tis_settings['n_jumps'] = 0
        interfaces = [-300000, 2, 30000]
        accept, path, status = select_shoot(trial_path, order_f,
                                            interfaces, engine,
                                            rgen, tis_settings,
                                            shooting_move='wt',
                                            start_cond='L')

        self.assertEqual(status, 'BTX')
        self.assertFalse(accept)

        # should generate a B to B (thus a 'BWI')
        interfaces = [-3000000, 2, 9]
        engine = RandomWalk(timestep=1)
        accept, path, status = select_shoot(trial_path, order_f,
                                            interfaces, engine,
                                            rgen, tis_settings,
                                            shooting_move='wt',
                                            start_cond='L')

        self.assertEqual(status, 'BWI')
        self.assertFalse(accept)

    def test_stone_skipping(self):
        """Test stone skipping shooting move."""
        tis_settings = {
            'maxlength': 1000,
            'sigma_v': -1,
            'aimless': True,
            'zero_momentum': False,
            'rescale_energy': False,
            'allowmaxlength': False,
            'n_jumps': 0,
        }
        # Generate ACC:
        order_f = Position(index=0)
        engine = MockEngine(16.0)
        rgen = RandomGenerator(seed=1)  # The seed helps the coverage.
        path = make_internal_path((-5, 2.1), (5, 2.2), (1, -1))

        tis_settings['n_jumps'] = 16
        accept, path, status = stone_skipping(path, order_f,
                                              [0.7, 2., 2.5], engine,
                                              rgen, tis_settings, 'L')
        self.assertEqual(status, 'ACC')
        self.assertTrue(accept)

        engine = VelocityVerlet(0.001)
        accept, path, status = stone_skipping(path, order_f,
                                              [0.7, 2., 1234.5], engine,
                                              rgen, tis_settings, 'L')
        self.assertEqual(status, 'NSS')
        self.assertFalse(accept)

        # Not extendable
        accept, path, status = stone_skipping(path, order_f,
                                              [-100., 3., 100.], engine,
                                              rgen, tis_settings, 'L')
        self.assertEqual(status, 'NCR')
        self.assertFalse(accept)

    def test_stone_skipping_real(self):
        """Test stone skipping with real dynamics."""
        tis_settings = {
            'maxlength': 1000,
            'sigma_v': -1,
            'aimless': True,
            'zero_momentum': False,
            'rescale_energy': False,
            'allowmaxlength': True,
            'n_jumps': 16,
        }
        # Generate ACC:
        interfaces = [-3, -1.4, 2.3]
        order_f = Position(index=0)
        engine = VelocityVerlet(0.01)
        rgen = RandomGenerator(seed=0)

        trial_path = make_internal_path((-5, 2.1), (5, 2.2), (1, -1))
        shooting_point = trial_path.phasepoints[4]
        empty = trial_path.empty_path(rgen=RandomGenerator(seed=0),
                                      maxlen=1000)
        engine.propagate(empty, shooting_point,
                         order_f, interfaces,
                         reverse=False)

        path = empty.reverse(order_f)
        path.set_move('ss')
        accept, path, status = select_shoot(path, order_f,
                                            interfaces, engine,
                                            rgen, tis_settings,
                                            shooting_move='ss',
                                            start_cond='L')

        self.assertEqual(status, 'ACC')
        self.assertTrue(accept)

    def test_stone_skipping_full_version(self):
        """Test stone skipping with real dynamics."""
        tis_settings = {
            'maxlength': 1000,
            'sigma_v': -1,
            'aimless': True,
            'zero_momentum': False,
            'rescale_energy': False,
            'allowmaxlength': False,
            'n_jumps': 16,
            'high_accept': True,
        }
        # Generate ACC:
        interfaces = [-3, -1.4, 2.3]
        order_f = Position(index=0)
        engine = VelocityVerlet(0.01)
        rgen = RandomGenerator(seed=0)

        trial_path = make_internal_path((-5, 2.1), (5, 2.2), (1, -1))
        shooting_point = trial_path.phasepoints[4]
        empty = trial_path.empty_path(rgen=RandomGenerator(seed=0),
                                      maxlen=1000)
        engine.propagate(empty, shooting_point,
                         order_f, interfaces,
                         reverse=False)

        path = empty.reverse(order_f)
        path.set_move('ss')
        accept, path, status = select_shoot(path, order_f,
                                            interfaces, engine,
                                            rgen, tis_settings,
                                            shooting_move='ss',
                                            start_cond='L')

        self.assertEqual(status, 'ACC')
        self.assertTrue(accept)

        # Generate XSS - failed to do one stone skipping jump:
        tis_settings['maxlength'] = 10
        empty = trial_path.empty_path(rgen=RandomGenerator(seed=0),
                                      maxlen=1000)
        engine.propagate(empty, shooting_point,
                         order_f, interfaces,
                         reverse=False)

        path = empty.reverse(order_f)
        path.set_move('ss')
        accept, path, status = select_shoot(path, order_f,
                                            interfaces, engine,
                                            rgen, tis_settings,
                                            shooting_move='ss',
                                            start_cond='L')

        self.assertEqual(status, 'XSS')
        self.assertFalse(accept)

        # Generate NSS - failed to do one step crossing:
        engine = VelocityVerlet(0.0000001)
        accept, path, status = select_shoot(path, order_f,
                                            interfaces, engine,
                                            rgen, tis_settings,
                                            shooting_move='ss',
                                            start_cond='L')

        self.assertEqual(status, 'NSS')
        self.assertFalse(accept)

    def test_extender(self):
        """Test extender of paths."""
        path = make_internal_path((-5, 2.1), (5, 2.2), (1, -1))
        path.status = 'ACC'
        order_f = Position(index=0)
        engine = MockEngine(2.0)
        interfaces = [-1, 0., 2.]
        tis_settings = {
            'maxlength': 1000,
            'sigma_v': -1,
            'aimless': False,
            'zero_momentum': False,
            'rescale_energy': False,
            'allowmaxlength': False,
        }
        # Check that nothing changes, the path is already good
        accept, new_path, status = extender(path, order_f,
                                            interfaces, engine,
                                            tis_settings)
        self.assertTrue(new_path == path)
        self.assertTrue(accept)

        # Check that the forward expansion works, and it can fail
        path = make_internal_path((-5, 2.1), (5, 2.2), (1, -1))
        path.status = 'ACC'
        order_f = Position(index=0)
        engine = MockEngine(2.0)
        interfaces = [-1, 0., 2.7]
        tis_settings = {
            'maxlength': 1000,
            'sigma_v': -1,
            'aimless': False,
            'zero_momentum': False,
            'rescale_energy': False,
            'allowmaxlength': False,
        }
        accept, new_path, status = extender(path, order_f,
                                            interfaces, engine,
                                            tis_settings)
        self.assertEqual(status, 'ACC')
        self.assertTrue(accept)

        interfaces = [-1, 0., 3.]
        accept, new_path, status = extender(new_path, order_f,
                                            interfaces, engine,
                                            tis_settings)
        self.assertEqual(status, 'FTX')
        self.assertFalse(accept)

        interfaces = [2., 2.5, 3.]
        accept, new_path, status = extender(new_path, order_f,
                                            interfaces, engine,
                                            tis_settings)
        self.assertEqual(status, 'FTX')
        self.assertFalse(accept)

    def test_ss_wt_acceptance_base(self):
        """Test ss_wt_acceptance is working properly (part 0)."""

        order_f = Position(index=0)

        # Generate a B to A path
        rgen = RandomGenerator(seed=0)
        interfaces = [-4, -2., -1.]
        lol_path = make_internal_path((5, 5), (-5, -5), (5, 5))
        new_path = lol_path.copy()
        new_path.status = 'REJ'
        lol_path.set_move('ss')
        succ = ss_wt_acceptance(path_old=lol_path, path_new=new_path,
                                interfaces=interfaces,
                                rgen=rgen, order_function=order_f,
                                tis_settings={'high_accept': True})
        self.assertTrue(succ)
        self.assertEqual(new_path.status, 'ACC')

    def test_ss_wt_acceptance(self):
        """Test ss_wt_acceptance is working properly."""

        order_f = Position(index=0)
        engine = RandomWalk(timestep=0.1)
        tis_settings = {
            'maxlength': 1000,
            'sigma_v': -1,
            'aimless': False,
            'zero_momentum': False,
            'rescale_energy': False,
            'allowmaxlength': False
        }
        # Test segment direction
        # (just wrong orientation but still connecting B to A)
        path = make_internal_path((-5, 2.1), (5, 2.2), (1, -1))

        shooting_point = path.phasepoints[12]
        shooting_point.idx = 12
        interfaces = [-1, 0., 1]
        rgen = RandomGenerator(seed=0)

        success, _, status = make_path(path, order_f, interfaces, engine,
                                       tis_settings, maxlen=1000,
                                       shooting_point=shooting_point,
                                       start_cond='L')
        self.assertEqual(status, 'KOB')
        self.assertFalse(success)

        # Generate a B to A path
        path = make_internal_path((5, 5), (-5, -5), (5, 5))

        # Fix it and accept it
        interfaces = [-4, -2., -1]
        path2 = make_internal_path((-5, -5), (-5, -5), (5, 5))
        old_path = paste_paths(path2, path)
        old_path.set_move('ss')
        succ = ss_wt_acceptance(old_path, path, interfaces,
                                rgen=rgen, order_function=None,
                                tis_settings={})
        self.assertTrue(succ)
        self.assertEqual(path.status, 'ACC')

        rgen = RandomGenerator(seed=0)
        path.set_move('ss')
        succ = ss_wt_acceptance(path, old_path, interfaces,
                                rgen=rgen, order_function=None,
                                tis_settings={})
        self.assertFalse(succ)
        self.assertEqual(old_path.status, 'SSA')

        path.set_move('wt')
        succ = ss_wt_acceptance(path, old_path, interfaces,
                                rgen=rgen, order_function=None,
                                tis_settings={'interface_sour': -2.})
        self.assertFalse(succ)
        self.assertEqual(old_path.status, 'WTA')

        path.set_move('ss')
        succ = ss_wt_acceptance(path, old_path, interfaces,
                                rgen=rgen, order_function=None,
                                tis_settings={'high_accept': True})
        self.assertTrue(succ)
        self.assertEqual(old_path.status, 'ACC')

    def test_extender_1(self):
        """Test extender behaviour in special circumstances."""
        path = make_internal_path((-1, 2.1), (-2, 2.2), (-1, -1))
        path.status = 'ACC'
        order_f = Position(index=0)
        engine = MockEngine(2.0)
        # Test extension in the 000^- ensemble
        interfaces = [-9999., 0., 0.]
        tis_settings = {
            'maxlength': 1000,
            'sigma_v': -1,
            'aimless': False,
            'zero_momentum': False,
            'rescale_energy': False,
            'allowmaxlength': False,
            'n_jumps': 16,
            'interface_sour': 1.5
        }
        # Check that nothing changes, the path is already good
        accept, new_path, status = extender(path, order_f,
                                            interfaces, engine,
                                            tis_settings)
        self.assertEqual(status, 'ACC')
        self.assertTrue(accept)

        # Test segment direction
        # (just wrong orientation but still connecting B to A)
        path = make_internal_path((-5, 2.1), (5, 2.2), (1, -1))
        path_new = path.reverse(order_f)
        path_new.maxlen = 1000
        interfaces = [-1, 0., 2.4]
        accept, path, status = extender(path_new, order_f,
                                        interfaces, engine,
                                        tis_settings)
        self.assertEqual(status, 'ACC')
        self.assertTrue(accept)

        accept, path, status = extender(path, order_f,
                                        interfaces, engine,
                                        tis_settings)
        self.assertEqual(status, 'ACC')
        self.assertTrue(accept)

        tis_settings['maxlength'] = 10
        accept, path, status = extender(path, order_f,
                                        interfaces, engine,
                                        tis_settings)
        self.assertEqual(status, 'FTX')
        self.assertFalse(accept)

        # Test segment direction, shall fail
        path = make_internal_path((-5, 2.1), (5, 2.2), (1, -1))
        path_new = path.reverse(order_f)
        path_new.maxlen = 1000
        accept, path, status = extender(path_new, order_f,
                                        interfaces, engine,
                                        tis_settings)
        self.assertEqual(status, 'BTX')
        self.assertFalse(accept)

    def test_0_min_L(self):
        """Test that a path that ends up at the left interface of the
        {0-} ensemble is rejected"""
        ens = PathEnsemble(ensemble_number=0, interfaces=(0, 1, 2))
        path = make_internal_path((0, 2.1), (100, 2.2), (50, -1),
                                  ens.interfaces[1])
        ens.add_path_data(path, status='ACC')
        order_f = MockOrder()
        tis_settings = {'freq': 0, 'maxlength': 1000, 'sigma_v': -1,
                        'shooting_moves': ['sh', 'sh', 'sh'],
                        'aimless': True, 'zero_momentum': False,
                        'rescale_energy': False, 'allowmaxlength': False}
        eng = MockEngine(10)
        out = make_tis_step_ensemble(path_ensemble=ens,
                                     order_function=order_f,
                                     engine=eng,
                                     rgen=path.rgen,
                                     tis_settings=tis_settings,
                                     cycle=1)

        # Make sure this generated an L to R path
        self.assertGreater(out[1].phasepoints[0].order[0], 2)
        self.assertLess(out[1].phasepoints[-1].order[0], 0)

        # Assert if this was rejected with the right status
        self.assertFalse(out[0])
        self.assertEqual(out[2], '0-L')

    def test_0_min_R(self):
        """Test that a path that ends up at the right interface of the
        {0-} ensemble is accepted"""
        ens = PathEnsemble(ensemble_number=0, interfaces=(0, 1, 2))
        path = make_internal_path((0, 2.1), (100, 2.2), (50, -1),
                                  ens.interfaces[1])
        ens.add_path_data(path, status='ACC')
        order_f = MockOrder()
        eng = MockEngine(10, turn_around=2000)
        out = make_tis_step_ensemble(path_ensemble=ens,
                                     order_function=order_f,
                                     engine=eng,
                                     rgen=path.rgen,
                                     tis_settings={'freq': 0,
                                                   'maxlength': 1000,
                                                   'sigma_v': -1,
                                                   'aimless': True,
                                                   'zero_momentum': False,
                                                   'rescale_energy': False,
                                                   'allowmaxlength': False},
                                     cycle=1)

        # Make sure this generated an R to R path
        self.assertGreater(out[1].phasepoints[0].order[0], 2)
        self.assertGreater(out[1].phasepoints[-1].order[0], 2)

        # Assert if this was accepted with the right status
        self.assertTrue(out[0])
        self.assertEqual(out[2], 'ACC')


if __name__ == '__main__':
    unittest.main()
