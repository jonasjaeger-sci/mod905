# -*- coding: utf-8 -*-
"""A simple test module for parsing a settings input file.

Here we test that we understand the input file and that fail in
a predictable way.
"""
from __future__ import absolute_import
import logging
import unittest
from pyretis.forcefield import ForceField, PotentialFunction
logging.disable(logging.CRITICAL)


class TestPotential(PotentialFunction):
    """A potential function to use in tests."""

    def __init__(self, desc='Test potential'):
        super(TestPotential, self).__init__(dim=1, desc=desc)
        self.params = {'a': 10}

    def potential(self, pos):
        """Evaluate the potentia."""
        return pos * pos * self.params['a']

    def force(self, pos):
        """Evaluate force and virial."""
        return pos * self.params['a'], 2.0 * pos

    def potential_and_force(self, pos):
        """Evaluate potential, force and virial."""
        pot = self.potential(pos)
        force, virial = self.force(pos)
        return pot, force, virial


class TestForceField(unittest.TestCase):
    """Test set-up of force fields."""

    def test_forcefield_class(self):
        """Test functionality of the ForceField class."""
        forcefield = ForceField()
        param1 = {'a': 1.0}
        pot1 = TestPotential()
        forcefield.add_potential(pot1, parameters=param1)
        force, virial = forcefield.evaluate_force(x=1)
        self.assertAlmostEqual(1.0, force)
        self.assertAlmostEqual(2.0, virial)
        vpot = forcefield.evaluate_potential(x=1)
        self.assertAlmostEqual(1.0, vpot)
        vpot, force, virial = forcefield.evaluate_potential_and_force(x=1)
        self.assertAlmostEqual(1.0, force)
        self.assertAlmostEqual(2.0, virial)
        self.assertAlmostEqual(1.0, vpot)
        param2 = {'a': 2.0}
        forcefield.update_potential_parameters(pot1, param2)
        vpot, force, virial = forcefield.evaluate_potential_and_force(x=1)
        self.assertAlmostEqual(2.0, force)
        self.assertAlmostEqual(2.0, virial)
        self.assertAlmostEqual(2.0, vpot)
        potr, paramr = forcefield.remove_potential(pot1)
        self.assertIs(pot1, potr)
        self.assertIs(param2, paramr)


if __name__ == '__main__':
    unittest.main()
