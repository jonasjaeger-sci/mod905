# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the ForceField and PotentialFunction classes."""
import logging
import unittest
import numpy as np
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
        return np.sum(pos * pos * self.params['a'])

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

        pot2 = TestPotential()
        potr, paramr = forcefield.remove_potential(pot2)
        self.assertTrue(potr is None)
        self.assertTrue(paramr is None)
        logging.disable(logging.INFO)
        with self.assertLogs('pyretis.forcefield.forcefield',
                             level='WARNING'):
            forcefield.update_potential_parameters(pot2, param2)
        logging.disable(logging.CRITICAL)

    def test_add_potential(self):
        """Test the forcefield add potential method in more detail."""
        forcefield = ForceField('Generic testing force field')
        param1 = {'a': 1.0}
        pot1 = TestPotential()
        ret = forcefield.add_potential(pot1, parameters=param1)
        self.assertTrue(ret)
        ret = forcefield.add_potential(None, parameters=param1)
        self.assertFalse(ret)
        pot2 = TestPotential()
        forcefield = ForceField('Generic testing force field',
                                potential=[pot1, pot2],
                                params=[param1])
        self.assertTrue(pot1 in forcefield.potential)
        self.assertTrue(pot2 in forcefield.potential)
        self.assertEqual(param1, forcefield.params[0])
        self.assertTrue(forcefield.params[1] is None)

    def test_evaluation(self):
        """Test evaluation of the force field."""
        system = System()
        system.particles = Particles(dim=system.get_dim())
        system.add_particle(1.0)
        param1 = {'a': 1.0}
        pot1 = TestPotential()
        param2 = {'a': 2.0}
        pot2 = TestPotential()
        forcefield = ForceField('Generic testing force field',
                                potential=[pot1, pot2],
                                params=[param1, param2])
        vpot = forcefield.evaluate_potential(system)
        self.assertAlmostEqual(vpot, 3.0)
        _, force, virial = forcefield.evaluate_potential_and_force(system)
        self.assertTrue(np.allclose(force, np.array([[3.0]])))
        self.assertTrue(np.allclose(virial, np.array([[4.0]])))
        force, virial = forcefield.evaluate_force(system)
        self.assertTrue(np.allclose(force, np.array([[3.0]])))
        self.assertTrue(np.allclose(virial, np.array([[4.0]])))

    def test_print_potentials(self):
        """Test the printing of force field information."""
        param1 = {'a': 1.0}
        pot1 = TestPotential()
        param2 = {'a': 2.0}
        pot2 = TestPotential()
        forcefield = ForceField('Generic testing force field',
                                potential=[pot1, pot2],
                                params=[param1, param2])
        txt = forcefield.print_potentials()
        correct_txt = ['Force field: Generic testing force field',
                       '1: Test potential', '2: Test potential']
        for i, j in zip(txt.split('\n'), correct_txt):
            self.assertEqual(i.strip(), j.strip())


if __name__ == '__main__':
    unittest.main()
