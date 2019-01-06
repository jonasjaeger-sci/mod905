# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the TIS method."""
import logging
import unittest
import numpy as np
from pyretis.core import System, create_box, Particles
from pyretis.initiation import initiate_path_simulation
from pyretis.inout.setup import (
    create_force_field,
    create_engine,
    create_simulation
)
from pyretis.engines.internal import MDEngine
from pyretis.orderparameter import OrderParameter
from pyretis.forcefield import ForceField, PotentialFunction
from pyretis.core.tis import (
    time_reversal,
    shoot,
)
from pyretis.inout.setup.createsimulation import create_path_ensembles
from pyretis.core.random_gen import MockRandomGenerator
from pyretis.core.path import Path
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


class MockEngine(MDEngine):
    """An engine used for testing. It will not do actual dynamics."""

    def __init__(self, timestep, turn_around=20):
        """Just set the time step."""
        super().__init__(timestep, 'Engie McEngineface', dynamics='Fake')
        self.time = 0
        self.turn_around = turn_around  # every now and then
        self.delta_v = 0.0123456

    def integration_step(self, system):
        """Do a fake integration step."""
        self.time += 1
        particles = system.particles
        particles.pos += self.delta_t * self.delta_v
        system.potential_and_force()
        if self.time > self.turn_around:
            self.time = 0
            self.delta_v *= -1.
        return None


class MockEngine2(MDEngine):
    """An engine used for testing. It will not do actual dynamics."""

    def __init__(self, timestep, interfaces):
        """Just set the time step."""
        super().__init__(timestep, 'Engie McEngineface', dynamics='Fake')
        self.time = 0
        self.delta_v = 0.0123456
        self.cross_left = False
        self.interfaces = interfaces

    def integration_step(self, system):
        """Do a fake integration step."""
        self.time += 1
        particles = system.particles
        if not self.cross_left:
            particles.pos += self.delta_t * self.delta_v
            if particles.pos[0][0] < self.interfaces[0]:
                self.cross_left = True
                self.delta_v *= -1.
        system.potential_and_force()
        return None


class MockOrder(OrderParameter):
    """Just return the position as the order parameter."""
    def __init__(self):
        super().__init__(description='Ordey McOrderface')
        self.index = 0
        self.dim = 0

    def calculate(self, system):
        return [system.particles.pos[self.index][self.dim]]


class MockOrder2(OrderParameter):
    """Just return the position as the order parameter."""
    def __init__(self):
        super().__init__(description='Ordey McOrderface')

    def calculate(self, system):
        return [11.]


class MockPotential(PotentialFunction):
    """Set the potential equal to x**2"""
    def __init__(self):
        super().__init__(dim=1, desc='Potey McPotentialface')

    def potential(self, system):
        # pylint: disable=no-self-use,missing-docstring
        pos = system.particles.pos
        vpot = pos**2
        return vpot.sum()

    def force(self, system):
        # pylint: disable=missing-docstring
        pos = system.particles.pos
        forces = pos * 1.0
        virial = np.zeros((self.dim, self.dim))
        return forces, virial

    def potential_and_force(self, system):
        # pylint: disable=missing-docstring
        pot = self.potential(system)
        force, virial = self.force(system)
        return pot, force, virial


def make_internal_path(start, end, maxorder, interface, points=100):
    """Return a dummy path.

    Parameters
    ----------
    start : tuple of floats
        The starting point for the path.
    end : tuple of floats
        The ending point for the path.
    maxorder : tuple of floats
        The maximum order parameter the path should attain.
    interface : integer or None
        The interface can be used to remove points from the path so
        that the path will be valid.
    points : integer, optional
        The number of points to add to the path.
    """
    # pylint: disable=too-many-locals
    x = [start[0], maxorder[0], end[0]]  # pylint: disable=invalid-name
    y = [start[1], maxorder[1], end[1]]  # pylint: disable=invalid-name
    par = np.polyfit(x, y, 2)
    xre = np.linspace(0., x[-1], points)
    yre = np.polyval(par, xre)
    # Delete some points from yre so that the path will be ok:
    if interface is not None:
        idx = [0]
        if yre[0] < interface:
            for i in np.where(yre > interface)[0]:
                idx.append(i)
        else:
            for i in np.where(yre < interface)[0]:
                idx.append(i)
        idx.append(-1)
        yre2 = [yre[i] for i in idx]
    else:
        yre2 = yre
    rgen = MockRandomGenerator(seed=0)
    path = Path(rgen, maxlen=1000)
    previous = None
    for order in yre2:
        if previous is None:
            vel = 0.0
        else:
            vel = order - previous
        ekin = 0.5 * vel**2
        phasepoint = {'order': [order], 'pos': np.array([[order, ]]),
                      'vel': np.array([[vel, ]]),
                      'vpot': order**2, 'ekin': ekin}
        path.append(phasepoint)
        previous = order
    path.generated = ('fake', 0, 0, 0)
    return path


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


def create_simple_system():
    """Create a simple system for testing."""
    box = create_box(periodic=[False])
    system = System(units='reduced', temperature=1.0, box=box)
    particles = Particles(dim=1)
    particles.add_particle(np.zeros((1, 1)), np.zeros((1, 1)),
                           np.zeros((1, 1)))
    system.particles = particles
    system.forcefield = ForceField('empty force field',
                                   potential=[MockPotential()])
    return system


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
                          'rgen': 'mock',
                          'timestep': 0.002}
    # Potential parameters:
    # The potential is: `V_\text{pot} = a x^4 - b (x - c)^2`
    settings['potential'] = [{'a': 1.0, 'b': 2.0, 'c': 0.0,
                              'class': 'DoubleWell'}]
    # Settings for the order parameter:
    settings['orderparameter'] = {'class': 'OrderParameterPosition',
                                  'dim': 'x', 'index': 0, 'name': 'Position',
                                  'periodic': False}
    # TIS specific settings:
    settings['tis'] = {'freq': 0.5,
                       'maxlength': 20000,
                       'aimless': True,
                       'allowmaxlength': False,
                       'sigma_v': -1,
                       'seed': 1,
                       'rgen': 'mock',
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
    # here we do a hack so that the simulation and langevin integrator
    # both use the same random generator:
    simulation.rgen = simulation.engine.rgen
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
        for i in range(10):
            if i == 0:
                for _ in initiate_path_simulation(simulation, in_settings):
                    logging.debug('Running initialisation')
            else:
                simulation.step()
            path = ensemble.paths[-1]
            path_data = [path['length'], path['status'], path['generated'][0],
                         path['ordermin'][0], path['ordermax'][0]]
            for j in (0, 1, 2):
                self.assertEqual(path_data[j], TISMOL_001[i][j])
            self.assertAlmostEqual(path_data[3], TISMOL_001[i][3], places=6)
            self.assertAlmostEqual(path_data[4], TISMOL_001[i][4], places=6)


class TISTestMethod(unittest.TestCase):
    """Test the various TIS methods."""

    def test_time_reversal(self):
        """Test the time reversal move."""
        ensembles = create_ensembles_and_paths()
        for ens, acc, stat in zip(ensembles,
                                  [True, True, True, False],
                                  ['ACC', 'ACC', 'ACC', 'BWI']):
            path = ens.last_path
            accept, new_path, status = time_reversal(path, ens.interfaces,
                                                     'L')
            for i, j in zip(path.trajectory(),
                            new_path.trajectory(reverse=True)):
                self.assertTrue(np.allclose(i['pos'], j['pos']))
                self.assertTrue(np.allclose(i['vel'], -1.0 * j['vel']))
                self.assertAlmostEqual(i['ekin'], j['ekin'])
                self.assertAlmostEqual(i['vpot'], j['vpot'])
                self.assertAlmostEqual(i['order'][0],
                                       j['order'][0])
            self.assertEqual(accept, acc)
            self.assertEqual(status, stat)

    def test_shoot(self):
        """Test the shooting move."""
        ensembles = create_ensembles_and_paths()
        order = MockOrder()
        engine = MockEngine(1.0)
        system = create_simple_system()
        tis_settings = {
            'maxlength': 1000,
            'sigma_v': -1,
            'aimless': True,
            'zero_momentum': False,
            'rescale_energy': False,
            'allowmaxlength': False,
        }
        # Generate BTL
        ens = ensembles[0]
        path = ens.last_path
        rgen = MockRandomGenerator(seed=1)
        accept, _, status = shoot(ens.last_path, system, order,
                                  ens.interfaces, engine,
                                  rgen, tis_settings, 'L')
        self.assertEqual(status, 'BTL')
        self.assertFalse(accept)
        # Generate BTX:
        tis_settings['allowmaxlength'] = True
        accept, _, status = shoot(ens.last_path, system, order,
                                  ens.interfaces, engine,
                                  rgen, tis_settings, 'L')
        self.assertEqual(status, 'BTX')
        self.assertFalse(accept)
        # Generate BWI
        tis_settings['allowmaxlength'] = True
        engine.turn_around = float('inf')
        engine.delta_v = 1
        accept, _, status = shoot(ens.last_path, system, order,
                                  ens.interfaces, engine,
                                  rgen, tis_settings, 'L')
        self.assertEqual(status, 'BWI')
        self.assertFalse(accept)
        # Generate ACC:
        tis_settings['allowmaxlength'] = False
        engine.turn_around = float('inf')
        engine.delta_v = -0.01
        accept, _, status = shoot(ens.last_path, system, order,
                                  ens.interfaces, engine,
                                  rgen, tis_settings, 'L')
        self.assertEqual(status, 'ACC')
        self.assertTrue(accept)
        # Generate NCR:
        ens = ensembles[2]
        tis_settings['allowmaxlength'] = False
        engine.turn_around = float('inf')
        engine.delta_v = -0.1
        ens.interfaces = (-1., 9., 10.)
        accept, _, status = shoot(ens.last_path, system, order,
                                  (-1., 9., 10.), engine,
                                  rgen, tis_settings, 'L')
        self.assertEqual(status, 'NCR')
        self.assertFalse(accept)
        # Generate FTL:
        ens = ensembles[2]
        engine = MockEngine2(1.0, ens.interfaces)
        tis_settings['allowmaxlength'] = False
        engine.delta_v = -0.1
        accept, _, status = shoot(ens.last_path, system, order,
                                  ens.interfaces, engine,
                                  rgen, tis_settings, 'L')
        self.assertEqual(status, 'FTL')
        self.assertFalse(accept)
        # Generate FTX:
        engine = MockEngine2(1.0, ens.interfaces)
        tis_settings['allowmaxlength'] = True
        engine.delta_v = -0.01
        accept, _, status = shoot(path, system, order,
                                  ens.interfaces, engine,
                                  rgen, tis_settings, 'L')
        self.assertEqual(status, 'FTX')
        self.assertFalse(accept)

    def test_shoot_kob(self):
        """Test the shooting move when we get a KOB."""
        ensembles = create_ensembles_and_paths()
        order = MockOrder2()
        engine = MockEngine(1.0)
        system = create_simple_system()
        tis_settings = {
            'maxlength': 1000,
            'sigma_v': -1,
            'aimless': True,
            'zero_momentum': False,
            'rescale_energy': False,
            'allowmaxlength': False,
        }
        # Generate BTL
        ens = ensembles[0]
        rgen = MockRandomGenerator(seed=1)
        accept, _, status = shoot(ens.last_path, system, order,
                                  ens.interfaces, engine,
                                  rgen, tis_settings, 'L')
        self.assertEqual(status, 'KOB')
        self.assertFalse(accept)

    def test_shoot_aiming(self):
        """Test the non aimless shooting move."""
        ensembles = create_ensembles_and_paths()
        order = MockOrder()
        engine = MockEngine(1.0)
        system = create_simple_system()
        tis_settings = {
            'maxlength': 1000,
            'sigma_v': -1,
            'aimless': False,
            'zero_momentum': False,
            'rescale_energy': False,
            'allowmaxlength': False,
        }
        # Generate ACC
        tis_settings['allowmaxlength'] = True
        engine.turn_around = float('inf')
        engine.delta_v = -0.01
        ens = ensembles[2]
        rgen = MockRandomGenerator(seed=1)
        accept, _, status = shoot(ens.last_path, system, order,
                                  ens.interfaces, engine,
                                  rgen, tis_settings, 'L')
        self.assertEqual(status, 'ACC')
        self.assertTrue(accept)
        # Generate MCR
        accept, _, status = shoot(ens.last_path, system, order,
                                  ens.interfaces, engine,
                                  rgen, tis_settings, 'L')
        self.assertEqual(status, 'MCR')
        self.assertFalse(accept)


if __name__ == '__main__':
    unittest.main()
