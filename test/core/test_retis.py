# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the RETIS method(s)."""
import copy
import logging
import unittest
import numpy as np
from pyretis.core.system import System
from pyretis.core.particles import Particles
from pyretis.core.random_gen import MockRandomGenerator
from pyretis.inout.setup.createsimulation import create_path_ensembles
from pyretis.forcefield import ForceField
from pyretis.core.retis import (
    retis_swap,
    make_retis_step,
    null_move,
    retis_moves,
    _relative_shoots_select,
)
from .help import (
    make_internal_path,
    MockEngine,
    MockOrder,
    MockPotential
)


logging.disable(logging.CRITICAL)


def compare_path_skip_generated(path1, path2):
    """Compare two paths, but skip the generated attribute."""
    gen1 = copy.deepcopy(path1.generated)
    gen2 = copy.deepcopy(path2.generated)
    del path1.generated
    del path2.generated
    equal = path1 == path2
    path1.generated = gen1
    path2.generated = gen2
    return equal


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
    """The RETIS specific methods, for Internal simulations."""

    def test_swap_internal(self):
        """Test swapping of paths."""
        ensembles = create_ensembles_and_paths()
        # 1) Try [0^+] with [1^+]:
        # This move should be reject, we here check that
        # the currently accepted paths are not modified.
        path1 = ensembles[1].last_path
        path1c = path1.copy()
        path2 = ensembles[2].last_path
        path2c = path2.copy()
        accept, (trial1, trial2), status = retis_swap(
            ensembles, 1, None, None, None, 0
        )
        self.assertFalse(accept)
        self.assertEqual(status, 'NCR')
        # Check that the return trial paths are identical are identical
        # to the accepted paths, with the exception of the move:
        self.assertTrue(compare_path_skip_generated(path1, trial2))
        self.assertFalse(path1.generated is trial2.generated)
        self.assertTrue(compare_path_skip_generated(path2, trial1))
        self.assertFalse(path2.generated is trial1.generated)
        # Check that paths path1 and path2 did not change:
        self.assertEqual(path1, path1c)
        self.assertEqual(path2, path2c)

        # 2) Try [3^+] with [4^+]
        # This move should be accepted:
        path1 = ensembles[3].last_path
        path1c = path1.copy()
        path2 = ensembles[4].last_path
        path2c = path2.copy()
        accept, (trial1, trial2), status = retis_swap(
            ensembles, 3, None, None, None, 0
        )
        self.assertTrue(accept)
        self.assertEqual(status, 'ACC')
        # Here, path1 and trial2 should be identical:
        self.assertTrue(path1 is trial2)
        self.assertTrue(path1 is ensembles[4].last_path)
        # Here, path2 and trial1 should be identical:
        self.assertTrue(path2 is trial1)
        self.assertTrue(path2 is ensembles[3].last_path)
        # Copies should be identical with the exception of the
        # generated attribute.
        self.assertTrue(compare_path_skip_generated(path1, path1c))
        self.assertFalse(path1.generated[0] == path1c.generated[0])
        self.assertTrue(compare_path_skip_generated(path2, path2c))
        self.assertFalse(path2.generated[0] == path2c.generated[0])

    def test_nullmove_internal(self):
        """Test the null move."""
        ensembles = create_ensembles_and_paths()
        for ens in ensembles:
            path0 = ens.last_path
            before = ens.last_path.copy()
            accept, trial, status = null_move(ens, 1)
            self.assertTrue(accept)
            self.assertTrue(path0 is trial)
            self.assertTrue(status == 'ACC')
            self.assertTrue(path0.generated[0] == '00')
            after = ens.last_path
            self.assertTrue(compare_path_skip_generated(before, after))

    def test_swap_zero_internal(self):
        """Test the retis swap zero move."""
        ensembles = create_ensembles_and_paths()
        settings = {'tis': {'maxlength': 1000}}
        order = MockOrder()
        engine = MockEngine(1.0)
        path1 = ensembles[0].last_path
        path1c = path1.copy()
        path2 = ensembles[1].last_path
        path2c = path2.copy()
        accept, (trial1, trial2), status = retis_swap(
            ensembles, 0, order, engine, settings, 0
        )
        # This should be accepted:
        self.assertTrue(accept)
        self.assertEqual(status, 'ACC')
        # Check that paths path1 and path2 did not change:
        self.assertEqual(path1, path1c)
        self.assertEqual(path2, path2c)
        # Last point in trial 1 is second in path 2:
        self.assertEqual(trial1.phasepoints[-1], path2.phasepoints[1])
        # Second last point in trial 1 is first in path 2:
        self.assertEqual(trial1.phasepoints[-2], path2.phasepoints[0])
        # First point in trial 2 is second last in path 1:
        self.assertEqual(trial2.phasepoints[0], path1.phasepoints[-2])
        # Second point in trial 2 is last point in path 1:
        self.assertEqual(trial2.phasepoints[1], path1.phasepoints[-1])

    def test_swap_zero_internal_ftx(self):
        """Test the swap zero when we force a FTX."""
        ensembles = create_ensembles_and_paths()
        settings = {'tis': {'maxlength': 100}}
        order = MockOrder()
        engine = MockEngine(1.0, turn_around=500)
        accept, _, status = retis_swap(
            ensembles, 0, order, engine, settings, 0
        )
        self.assertFalse(accept)
        self.assertEqual(status, 'FTX')

    def test_swap_zero_internal_btx(self):
        """Test the swap zero when we force a BTX."""
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
            ensembles, 0, order, engine, settings, 0
        )
        self.assertFalse(accept)
        self.assertEqual(status, 'BTX')

    def test_swap_zero_internal_bts(self):
        """Test the swap zero when we force a BTS."""
        ensembles = create_ensembles_and_paths()
        settings = {'tis': {'maxlength': 1000}}
        order = MockOrder()
        engine = MockEngine(200.0)
        # We set up for BTS by making a faulty initial path:
        path = make_internal_path((0, -0.9), (100, -1.2), (50, -0.2), None)
        ensembles[1].add_path_data(path, 'ACC')
        accept, _, status = retis_swap(
            ensembles, 0, order, engine, settings, 0
        )
        self.assertFalse(accept)
        self.assertEqual(status, 'BTS')

    def test_swap_zero_internal_fts(self):
        """Test the swap zero when we force a FTS."""
        ensembles = create_ensembles_and_paths()
        settings = {'tis': {'maxlength': 1000}}
        order = MockOrder()
        engine = MockEngine(1.0)
        # We set up for FTS by making a faulty initial path:
        path = make_internal_path((0, -0.9), (100, -1.2), (50, -5), None)
        ensembles[0].add_path_data(path, 'ACC')
        accept, _, status = retis_swap(
            ensembles, 0, order, engine, settings, 0
        )
        self.assertFalse(accept)
        self.assertEqual(status, 'FTS')

    def test_retis_moves(self):
        """Test the retis moves function."""
        ensembles = create_ensembles_and_paths()
        settings = {'tis': {'maxlength': 1000},
                    'retis': {'swapsimul': False,
                              'nullmoves': True}}
        order = MockOrder()
        engine = MockEngine(1.0)
        rgen = MockRandomGenerator(seed=0)
        path1 = ensembles[3].last_path
        path2 = ensembles[4].last_path
        results = retis_moves(
            ensembles, order, engine, rgen, settings, 0
        )
        # We should have done swapping for [2^+] and [3^+] and nullmoves
        # for the rest:
        for resi in results:
            idx = resi['ensemble']
            if idx not in (3, 4):
                self.assertEqual(resi['retis-move'], 'nullmove')
            else:
                self.assertEqual(resi['retis-move'], 'swap')
                if idx == 3:
                    self.assertEqual(resi['swap-with'], 4)
                    self.assertTrue(path2 is resi['trial'])
                elif idx == 4:
                    self.assertEqual(resi['swap-with'], 3)
                    self.assertTrue(path1 is resi['trial'])
            self.assertEqual(resi['status'], 'ACC')
            self.assertTrue(resi['accept'])

    def test_retis_moves_simul(self):
        """Test the retis moves function with swaps."""
        ensembles = create_ensembles_and_paths()
        settings = {'tis': {'maxlength': 1000},
                    'retis': {'swapsimul': True,
                              'nullmoves': True}}
        order = MockOrder()
        engine = MockEngine(1.0)
        rgen = MockRandomGenerator(seed=0)
        results = retis_moves(
            ensembles, order, engine, rgen, settings, 0
        )
        # We expect a nullmove for the first and swapping for the rest:
        moves = ('nullmove', 'swap', 'swap', 'swap', 'swap')
        for resi in results:
            self.assertEqual(resi['retis-move'], moves[resi['ensemble']])
        # Try with an even number of ensembles. This should trigger
        # the ``if len(ensembles) % 2`` for a particular scheme, we
        # enforce this scheme by resetting the seed:
        ensembles = ensembles[:-1]
        ensembles[0].last_path.set_move('ld')
        rgen = MockRandomGenerator(seed=0)
        results = retis_moves(
            ensembles, order, engine, rgen, settings, 0
        )
        moves = ('nullmove', 'swap', 'swap', 'nullmove')
        for resi in results:
            self.assertEqual(resi['retis-move'], moves[resi['ensemble']])
        self.assertEqual(ensembles[0].last_path.get_move(), 'ld')
        # Finally, try with just 2 ensembles:
        ensembles = ensembles[0:2]
        results = retis_moves(
            ensembles, order, engine, rgen, settings, 0
        )
        for resi in results:
            self.assertEqual(resi['retis-move'], 'swap')

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
        settings = {'tis': {'maxlength': 1000, 'freq': 1.0},
                    'retis': {'swapsimul': True,
                              'nullmoves': True}}
        order = MockOrder()
        engine = MockEngine(1.0)
        rgen = MockRandomGenerator(seed=0)

        # Check that we can do RETIS:
        settings['retis']['swapfreq'] = 1.0
        ensembles[1].last_path.set_move('ld')
        results = make_retis_step(ensembles, order, engine, rgen,
                                  settings, 0)
        self.assertTrue(ensembles[1].last_path.get_move() == 'ld')
        moves = ('swap', 'swap', 'swap', 'swap', 'nullmove')
        for resi in results:
            self.assertEqual(resi['retis-move'], moves[resi['ensemble']])
        # Check that we can select TIS moves:
        settings['retis']['swapfreq'] = 0.0
        results = make_retis_step(ensembles, order, engine, rgen,
                                  settings, 1)
        for resi in results:
            self.assertEqual(resi['retis-move'], 'tis')
        # Check that we can do relative shoots:
        settings['retis']['relative_shoots'] = [0.1, 0.1, 0.1, 0.1, 0.6]
        results = make_retis_step(ensembles, order, engine, rgen,
                                  settings, 2)
        moves = ('nullmove', 'nullmove', 'nullmove', 'nullmove', 'tis')
        for resi in results:
            self.assertEqual(resi['retis-move'], moves[resi['ensemble']])


if __name__ == '__main__':
    unittest.main()
