# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""A simple test module for parsing a settings input file.

Here we test that we understand the input file and that fail in
a predictable way.
"""
from __future__ import absolute_import
import logging
import unittest
from pyretis.core.system import System
from pyretis.core.particles import Particles
from pyretis.forcefield import ForceField, PotentialFunction
logging.disable(logging.CRITICAL)


class TestPotential(PotentialFunction):
    """A potential function to use in tests."""

    def __init__(self, desc='Test potential'):
        super().__init__(dim=1, desc=desc)
        self.params = {'a': 10}

    def potential(self, system):
        """Evaluate the potential."""
        pos = system.particles.pos
        return pos * pos * self.params['a']

    def force(self, system):
        """Evaluate force and virial."""
        pos = system.particles.pos
        return pos * self.params['a'], 2.0 * pos

    def potential_and_force(self, system):
        """Evaluate potential, force and virial."""
        pot = self.potential(system)
        force, virial = self.force(system)
        return pot, force, virial


class TestForceField(unittest.TestCase):
    """Test set-up of force fields."""

    def test_forcefield_class(self):
        """Test functionality of the ForceField class."""
        system = System()
        system.particles = Particles(dim=system.get_dim())
        system.add_particle(1.0)
        forcefield = ForceField('Generic testing force field')
        param1 = {'a': 1.0}
        pot1 = TestPotential()
        forcefield.add_potential(pot1, parameters=param1)

        force, virial = forcefield.evaluate_force(system)
        self.assertAlmostEqual(1.0, force)
        self.assertAlmostEqual(2.0, virial)

        vpot = forcefield.evaluate_potential(system)
        self.assertAlmostEqual(1.0, vpot)

        vpot, force, virial = forcefield.evaluate_potential_and_force(system)
        self.assertAlmostEqual(1.0, force)
        self.assertAlmostEqual(2.0, virial)
        self.assertAlmostEqual(1.0, vpot)

        param2 = {'a': 2.0}
        forcefield.update_potential_parameters(pot1, param2)

        vpot, force, virial = forcefield.evaluate_potential_and_force(system)
        self.assertAlmostEqual(2.0, force)
        self.assertAlmostEqual(2.0, virial)
        self.assertAlmostEqual(2.0, vpot)

        potr, paramr = forcefield.remove_potential(pot1)
        self.assertIs(pot1, potr)
        self.assertIs(param2, paramr)


if __name__ == '__main__':
    unittest.main()
