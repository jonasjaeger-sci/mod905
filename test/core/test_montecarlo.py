# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test Monte Carlo Methods"""
import logging
import unittest
import numpy as np
from pyretis.core.system import System
from pyretis.core.particles import Particles
from pyretis.forcefield.potentials import DoubleWell
from pyretis.forcefield import ForceField
from pyretis.core.montecarlo import (
    metropolis_accept_reject,
    accept_reject_momenta,
    max_displace_step,
)
from pyretis.core.random_gen import MockRandomGenerator
logging.disable(logging.CRITICAL)


class MonteCarloTest(unittest.TestCase):
    """Run test for the Monte Carlo module"""

    def test_metropolis(self):
        """Test that we can draw random numbers in [0, 1)"""
        rgen = MockRandomGenerator(seed=0)
        system = System(units='reduced', temperature=1)
        self.assertTrue(metropolis_accept_reject(rgen, system, -1.0))
        acc = metropolis_accept_reject(rgen, system, 1.0)
        self.assertFalse(acc)

    def test_momenta(self):
        """Test the accept/reject for momenta."""
        rgen = MockRandomGenerator(seed=0)
        system = System(units='reduced', temperature=1)
        acc = accept_reject_momenta(rgen, system, 10.0, aimless=True)
        self.assertTrue(acc)
        acc = accept_reject_momenta(rgen, system, 10.0, aimless=False)
        self.assertFalse(acc)

    def test_max_displace(self):
        """Test the max-displace."""
        rgen = MockRandomGenerator(seed=0)
        system = System(units='reduced', temperature=1)
        particles = Particles(dim=1)
        particles.add_particle(np.zeros(1), np.zeros(1), np.zeros(1))
        particles.add_particle(np.zeros(1), np.zeros(1), np.zeros(1))
        system.particles = particles
        potential_dw = DoubleWell(a=1, b=1, c=0.02)
        system.forcefield = ForceField(
            'Test',
            potential=[potential_dw],
            params=[{'a': 1.0, 'b': 1.0, 'c': 0.02}]
        )
        system.potential_and_force()
        acc = max_displace_step(rgen, system, maxdx=10., idx=None)
        self.assertFalse(acc[-1])
        acc = max_displace_step(rgen, system, maxdx=1.25, idx=0)
        acc = max_displace_step(rgen, system, maxdx=1.25, idx=0)
        self.assertTrue(acc[-1])


if __name__ == '__main__':
    unittest.main()
