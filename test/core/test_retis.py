# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the RETIS method(s)."""
import logging
import unittest
import numpy as np
from pyretis.core.system import System
from pyretis.core.particles import Particles
from pyretis.core.path import Path
from pyretis.core.random_gen import MockRandomGenerator
from pyretis.inout.setup.createsimulation import create_path_ensembles
from pyretis.orderparameter import OrderParameter
from pyretis.engines.internal import MDEngine
from pyretis.forcefield import ForceField, PotentialFunction
from pyretis.core.retis import (
    retis_swap,
    make_retis_step,
    null_move,
    retis_moves,
    _relative_shoots_select,
)


logging.disable(logging.CRITICAL)


class MockEngine(MDEngine):
    """An engine used for testing. It will not do actual dynamics."""

    def __init__(self, timestep, turn_around=20):
        """Just set the time step."""
        super().__init__(timestep, 'Engie McEngineface', dynamics='Fake')
        self.time = 0
        self.total_eclipse = turn_around  # every now and then
        self.delta_v = 0.0123456

    def integration_step(self, system):
        """Do a fake integration step."""
        self.time += 1
        particles = system.particles
        particles.pos += self.delta_t * self.delta_v
        system.potential_and_force()
        if self.time > self.total_eclipse:
            self.time = 0
            self.delta_v *= -1.
        return None


class MockOrder(OrderParameter):
    """Just return the position as the order parameter."""
    def __init__(self):
        super().__init__(description='Ordey McOrderface')
        self.index = 0
        self.dim = 0

    def calculate(self, system):
        return [system.particles.pos[self.index][self.dim]]


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
    """
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
    path = Path(rgen)
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


def compare_path_attributes(path1, path2, generated=True):
    """Compare if path attributes have the same values."""
    attr = ['length', 'maxlen', 'ordermax', 'ordermin', 'rgen', 'time_origin']
    for att in attr:
        attr1 = getattr(path1, att)
        attr2 = getattr(path2, att)
        equal = attr1 == attr2
        if not equal:
            return False
    attr = ['ekin', 'order', 'pos', 'vel', 'vpot', 'ordermax', 'ordermin']
    if generated:
        attr.append('generated')
    for att in attr:
        attr1 = getattr(path1, att)
        attr2 = getattr(path2, att)
        for i, j in zip(attr1, attr2):
            equal = i == j
            if not equal:
                return False
    return True


def compare_path_attributes_is(path1, path2):
    """Compare some path attributes."""
    attr = ('ekin', 'length', 'maxlen', 'order', 'ordermax', 'ordermin',
            'pos', 'rgen', 'time_origin', 'vel', 'vpot')
    for att in attr:
        attr1 = getattr(path1, att)
        attr2 = getattr(path2, att)
        equal = attr1 is attr2
        if not equal:
            return False
    return True


def compare_phase_points(point1, point2):
    """Compare two phase points."""
    for key, val in point1.items():
        if key not in point2:
            return False
        if not np.allclose(val, point2[key]):
            return False
    return True


def create_ensembles_and_paths():
    """Return some test data we can use."""
    interfaces = [-1., 0., 1., 2., 10]
    ensembles, _ = create_path_ensembles(interfaces, 'internal',
                                         include_zero=True)
    # Make some paths for the ensembles.
    starts = [(0, -0.9), (0, -1.1), (0, -1.05), (0, -1.123), (0, -1.01)]
    ends = [(100, -0.95), (100, -1.2), (100, -1.3), (100, -1.01),
            (100, 10.01)]
    maxs = [(50, -5), (50, -0.2), (50, 0.5), (50, 2.5), (100, 10.01)]
    for i, j, k, ens in zip(starts, ends, maxs, ensembles):
        path = make_internal_path(i, j, k, ens.interfaces[1])
        ens.add_path_data(path, 'ACC')
    return ensembles


class RetisTestSwap(unittest.TestCase):
    """The RETIS specific methods, for Internal simulations"""

    def test_swap_internal(self):
        """Test swapping of paths."""
        ensembles = create_ensembles_and_paths()
        # 1) Try [0^+] with [1^+]:
        # This move should be reject, we here check that
        # the currently accepted paths are not modified.
        path1 = ensembles[1].last_path
        path1c = path1.copy_path()
        path2 = ensembles[2].last_path
        path2c = path2.copy_path()
        accept, (trial1, trial2), status = retis_swap(
            ensembles, 1, None, None, None, None, 0
        )
        self.assertFalse(accept)
        self.assertEqual(status, 'NCR')
        # Check that the return trial paths are identical are identical
        # to the accepted paths, with the exception of the move:
        self.assertTrue(compare_path_attributes_is(path1, trial2))
        self.assertFalse(path1.generated is trial2.generated)
        self.assertTrue(compare_path_attributes_is(path2, trial1))
        self.assertFalse(path2.generated is trial1.generated)
        # Check that paths path1 and path2 did not change:
        self.assertTrue(compare_path_attributes(path1, path1c))
        self.assertTrue(compare_path_attributes(path2, path2c))

        # 2) Try [3^+] with [4^+]
        # This move should be accepted:
        path1 = ensembles[3].last_path
        path1c = path1.copy_path()
        path2 = ensembles[4].last_path
        path2c = path2.copy_path()
        accept, (trial1, trial2), status = retis_swap(
            ensembles, 3, None, None, None, None, 0
        )
        self.assertTrue(accept)
        self.assertEqual(status, 'ACC')
        # Here, path1 and trial2 should be identical
        self.assertTrue(path1 is trial2)
        self.assertTrue(path1 is ensembles[4].last_path)
        # Here, path2 and trial1 should be identical
        self.assertTrue(path2 is trial1)
        self.assertTrue(path2 is ensembles[3].last_path)
        # Copies should be identical with the exception of the
        # generated attribute.
        self.assertTrue(compare_path_attributes(path1, path1c,
                                                generated=False))
        self.assertFalse(path1.generated[0] == path1c.generated[0])
        self.assertTrue(compare_path_attributes(path2, path2c,
                                                generated=False))
        self.assertFalse(path2.generated[0] == path2c.generated[0])

    def test_nullmove_internal(self):
        """Test the null move."""
        ensembles = create_ensembles_and_paths()
        for ens in ensembles:
            path0 = ens.last_path
            before = ens.last_path.copy_path()
            accept, trial, status = null_move(ens, 1)
            self.assertTrue(accept)
            self.assertTrue(path0 is trial)
            self.assertTrue(status == 'ACC')
            self.assertTrue(path0.generated[0] == '00')
            after = ens.last_path
            self.assertTrue(compare_path_attributes(before, after,
                                                    generated=False))

    def test_swap_zero_internal(self):
        """Test the retis swap zero move."""
        ensembles = create_ensembles_and_paths()
        system = System()
        particles = Particles(dim=1)
        particles.add_particle(np.zeros((1, 1)), np.zeros((1, 1)),
                               np.zeros((1, 1)))
        system.particles = particles
        system.forcefield = ForceField('empty force field',
                                       potential=[MockPotential()])
        settings = {'tis': {'maxlength': 1000}}
        order = MockOrder()
        engine = MockEngine(1.0)
        path1 = ensembles[0].last_path
        path1c = path1.copy_path()
        path2 = ensembles[1].last_path
        path2c = path2.copy_path()
        accept, (trial1, trial2), status = retis_swap(
            ensembles, 0, system, order, engine, settings, 0
        )
        # This should be accepted
        self.assertTrue(accept)
        self.assertEqual(status, 'ACC')
        # Check that paths path1 and path2 did not change:
        self.assertTrue(compare_path_attributes(path1, path1c))
        self.assertTrue(compare_path_attributes(path2, path2c))
        # Last point in trial 1 is second in path 2
        self.assertTrue(compare_phase_points(trial1.phasepoint(-1),
                                             path2.phasepoint(1)))
        # Second last point in trial 1 is first in path 2
        self.assertTrue(compare_phase_points(trial1.phasepoint(-2),
                                             path2.phasepoint(0)))
        # First point in trial 2 is second last in path 1
        self.assertTrue(compare_phase_points(trial2.phasepoint(0),
                                             path1.phasepoint(-2)))
        # Second point in trial 2 is last point in path 1
        self.assertTrue(compare_phase_points(trial2.phasepoint(1),
                                             path1.phasepoint(-1)))

    def test_swap_zero_internal_ftx(self):
        """Test the swap zero when we force a FTX"""
        ensembles = create_ensembles_and_paths()
        system = System()
        particles = Particles(dim=1)
        particles.add_particle(np.zeros((1, 1)), np.zeros((1, 1)),
                               np.zeros((1, 1)))
        system.particles = particles
        system.forcefield = ForceField('empty force field',
                                       potential=[MockPotential()])
        settings = {'tis': {'maxlength': 100}}
        order = MockOrder()
        engine = MockEngine(1.0, turn_around=500)
        accept, _, status = retis_swap(
            ensembles, 0, system, order, engine, settings, 0
        )
        self.assertFalse(accept)
        self.assertEqual(status, 'FTX')

    def test_swap_zero_internal_btx(self):
        """Test the swap zero when we force a BTX"""
        ensembles = create_ensembles_and_paths()
        system = System()
        particles = Particles(dim=1)
        particles.add_particle(np.zeros((1, 1)), np.zeros((1, 1)),
                               np.zeros((1, 1)))
        system.particles = particles
        system.forcefield = ForceField('empty force field',
                                       potential=[MockPotential()])
        settings = {'tis': {'maxlength': 3}}
        order = MockOrder()
        engine = MockEngine(1.0, turn_around=500)
        accept, _, status = retis_swap(
            ensembles, 0, system, order, engine, settings, 0
        )
        self.assertFalse(accept)
        self.assertEqual(status, 'BTX')

    def test_swap_zero_internal_bts(self):
        """Test the swap zero when we force a BTS"""
        ensembles = create_ensembles_and_paths()
        system = System()
        particles = Particles(dim=1)
        particles.add_particle(np.zeros((1, 1)), np.zeros((1, 1)),
                               np.zeros((1, 1)))
        system.particles = particles
        system.forcefield = ForceField('empty force field',
                                       potential=[MockPotential()])
        settings = {'tis': {'maxlength': 1000}}
        order = MockOrder()
        engine = MockEngine(200.0)
        # We set up for BTS by making a faulty initial path:
        path = make_internal_path((0, -0.9), (100, -1.2), (50, -0.2), None)
        ensembles[1].add_path_data(path, 'ACC')
        accept, _, status = retis_swap(
            ensembles, 0, system, order, engine, settings, 0
        )
        self.assertFalse(accept)
        self.assertEqual(status, 'BTS')

    def test_swap_zero_internal_fts(self):
        """Test the swap zero when we force a FTS"""
        ensembles = create_ensembles_and_paths()
        system = System()
        particles = Particles(dim=1)
        particles.add_particle(np.zeros((1, 1)), np.zeros((1, 1)),
                               np.zeros((1, 1)))
        system.particles = particles
        system.forcefield = ForceField('empty force field',
                                       potential=[MockPotential()])
        settings = {'tis': {'maxlength': 1000}}
        order = MockOrder()
        engine = MockEngine(1.0)
        # We set up for FTS by making a faulty initial path:
        path = make_internal_path((0, -0.9), (100, -1.2), (50, -5), None)
        ensembles[0].add_path_data(path, 'ACC')
        accept, _, status = retis_swap(
            ensembles, 0, system, order, engine, settings, 0
        )
        self.assertFalse(accept)
        self.assertEqual(status, 'FTS')

    def test_retis_moves(self):
        """Test the retis moves function."""
        ensembles = create_ensembles_and_paths()
        system = System()
        particles = Particles(dim=1)
        particles.add_particle(np.zeros((1, 1)), np.zeros((1, 1)),
                               np.zeros((1, 1)))
        system.particles = particles
        system.forcefield = ForceField('empty force field',
                                       potential=[MockPotential()])
        settings = {'tis': {'maxlength': 1000},
                    'retis': {'swapsimul': False,
                              'nullmoves': True}}
        order = MockOrder()
        engine = MockEngine(1.0)
        rgen = MockRandomGenerator(seed=0)
        path1 = ensembles[3].last_path
        path2 = ensembles[4].last_path
        results = retis_moves(
            ensembles, system, order, engine, rgen, settings, 0
        )
        # We should have done swapping for [2^+] and [3^+] and nullmoves
        # for the rest:
        for idx, resi in enumerate(results):
            if idx not in (3, 4):
                self.assertEqual(resi[0], 'nullmove')
            else:
                self.assertEqual(resi[0], 'swap')
                if idx == 3:
                    self.assertEqual(resi[4], 4)
                    self.assertTrue(path2 is resi[2])
                elif idx == 4:
                    self.assertEqual(resi[4], 3)
                    self.assertTrue(path1 is resi[2])
            self.assertEqual(resi[1], 'ACC')
            self.assertTrue(resi[3])

    def test_retis_moves_simul(self):
        """Test the retis moves function with swap simul."""
        ensembles = create_ensembles_and_paths()
        system = System()
        particles = Particles(dim=1)
        particles.add_particle(np.zeros((1, 1)), np.zeros((1, 1)),
                               np.zeros((1, 1)))
        system.particles = particles
        system.forcefield = ForceField('empty force field',
                                       potential=[MockPotential()])
        settings = {'tis': {'maxlength': 1000},
                    'retis': {'swapsimul': True,
                              'nullmoves': True}}
        order = MockOrder()
        engine = MockEngine(1.0)
        rgen = MockRandomGenerator(seed=0)
        results = retis_moves(
            ensembles, system, order, engine, rgen, settings, 0
        )
        # nullmove for the first, swap for the rest:
        moves = ('nullmove', 'swap', 'swap', 'swap', 'swap')
        for resi, move in zip(results, moves):
            self.assertEqual(resi[0], move)
        # try with even number of ensembles, this should
        # trigger the if len(ensembles) % 2 for a
        # particular scheme, we enforce this scheme by resetting the
        # seed:
        ensembles = ensembles[:-1]
        rgen = MockRandomGenerator(seed=0)
        results = retis_moves(
            ensembles, system, order, engine, rgen, settings, 0
        )
        moves = ('nullmove', 'swap', 'swap', 'nullmove')
        for resi, move in zip(results, moves):
            self.assertEqual(resi[0], move)
        # finally, try with 2 ensembles:
        ensembles = ensembles[0:2]
        results = retis_moves(
            ensembles, system, order, engine, rgen, settings, 0
        )
        for resi in results:
            self.assertEqual(resi[0], 'swap')

    def test_relative_shoots(self):
        """Test the relative shoots selection."""
        ensembles = create_ensembles_and_paths()
        rgen = MockRandomGenerator(seed=0)
        relative = [0.1, 0.1, 0.1, 0.1, 0.6]
        idx, ensemble = _relative_shoots_select(ensembles, rgen, relative)
        self.assertEqual(idx, 4)
        self.assertEqual(ensemble, ensembles[idx])
        relative = [1.0, 0.0, 0.0, 0.0, 0.0]
        idx, ensemble = _relative_shoots_select(ensembles, rgen, relative)
        self.assertEqual(idx, 0)
        self.assertEqual(ensemble, ensembles[idx])
        relative = [0.0, 0.0, 0.0, 0.0, 0.0]
        with self.assertRaises(ValueError):
            _relative_shoots_select(ensembles, rgen, relative)

    def test_make_retis_step(self):
        """Test that we can do the RETIS steps."""
        ensembles = create_ensembles_and_paths()
        system = System()
        particles = Particles(dim=1)
        particles.add_particle(np.zeros((1, 1)), np.zeros((1, 1)),
                               np.zeros((1, 1)))
        system.particles = particles
        system.forcefield = ForceField('empty force field',
                                       potential=[MockPotential()])
        settings = {'tis': {'maxlength': 1000, 'freq': 1.0},
                    'retis': {'swapsimul': True,
                              'nullmoves': True}}
        order = MockOrder()
        engine = MockEngine(1.0)
        rgen = MockRandomGenerator(seed=0)

        # Check that we can do RETIS
        settings['retis']['swapfreq'] = 1.0
        results = make_retis_step(ensembles, system, order, engine, rgen,
                                  settings, 0)
        moves = ('swap', 'swap', 'swap', 'swap', 'nullmove')
        for resi, move in zip(results, moves):
            self.assertEqual(resi[0], move)
        # Check that we can select TIS moves:
        settings['retis']['swapfreq'] = 0.0
        results = make_retis_step(ensembles, system, order, engine, rgen,
                                  settings, 1)
        for resi in results:
            self.assertEqual(resi[0], 'tis')
            tis_move = resi[2].generated[0]
            self.assertEqual(tis_move, 'tr')
        # Check that we can do relative shoots:
        settings['retis']['relative_shoots'] = [0.1, 0.1, 0.1, 0.1, 0.6]
        results = make_retis_step(ensembles, system, order, engine, rgen,
                                  settings, 2)
        moves = ('nullmove', 'nullmove', 'nullmove', 'nullmove', 'tis')
        for resi, move in zip(results, moves):
            self.assertEqual(resi[0], move)


if __name__ == '__main__':
    unittest.main()
