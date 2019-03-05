# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the system class from pyretis.core.system"""
import copy
import logging
import unittest
import numpy as np
from pyretis.core.box import create_box
from pyretis.core.particles import Particles
from pyretis.core.system import System
from pyretis.core.units import UNIT_SYSTEMS, CONSTANTS
from pyretis.forcefield import ForceField, PotentialFunction


logging.disable(logging.CRITICAL)


class FakePotential(PotentialFunction):
    """A potential which may potentially be used in testing."""

    def __init__(self, desc='Test potential'):
        """Initiate."""
        super().__init__(dim=3, desc=desc)
        self.pstate = 10
        self.fstate = 10

    def potential(self, system):
        """Evaluate the fake potential."""
        self.pstate -= 1 * system.particles.npart
        return self.pstate

    def force(self, system):
        """Evaluate the fake force."""
        pos = system.particles.pos
        self.fstate -= 1
        vir = np.eye(3, 3) * self.fstate
        return self.fstate * np.ones_like(pos), vir

    def potential_and_force(self, system):
        """Evaluate potential and force."""
        pot = self.potential(system)
        force, virial = self.force(system)
        return pot, force, virial


def prepare_test_system():
    """Create system with some particles."""
    box = create_box(cell=[10., 10., 10])
    particles = Particles(dim=3)
    particles.add_particle(np.zeros(3), np.zeros(3), np.zeros(3))
    particles.add_particle(np.zeros(3), np.zeros(3), np.zeros(3))
    particles.add_particle(np.zeros(3), np.zeros(3), np.zeros(3))
    syst = System(box=box, temperature=10)
    syst.particles = particles
    forcefield = ForceField('Testing force field')
    pot = FakePotential()
    forcefield.add_potential(pot)
    syst.forcefield = forcefield
    return syst


class SystemTest(unittest.TestCase):
    """Run the tests for the System class."""

    def test_adjust_dof(self):
        """Test if we can change the dofs."""
        system = System()
        system.adjust_dof([1, 1, 1])
        self.assertTrue(np.allclose(system.temperature['dof'],
                                    [1, 1, 1]))
        system.adjust_dof([0, 0, 9])
        self.assertTrue(np.allclose(system.temperature['dof'],
                                    [1, 1, 10]))

    def test_get_boltzmann(self):
        """Test that kB is set correctly."""
        for key in UNIT_SYSTEMS:
            syst = System(units=key)
            self.assertAlmostEqual(syst.get_boltzmann(),
                                   CONSTANTS['kB'][key])

    def test_restart_info(self):
        """Test that we can create restart info."""
        box = create_box(cell=[1, 2, 3])
        syst = System(units='lj', box=box, temperature=10.)
        restart = syst.restart_info()
        correct = {
            'temperature': {'set': 10.0, 'dof': np.array([1, 1, 1]),
                            'beta': 0.1},
            'box': {'high': np.array([1., 2., 3.]),
                    'periodic': [True, True, True],
                    'low': np.array([0., 0., 0.]),
                    'length': np.array([1., 2., 3.])},
            'units': 'lj'}
        for key in correct:
            self.assertTrue(key in restart)
        self.assertEqual(correct['units'], restart['units'])
        for key1 in ('temperature', 'box'):
            for key in correct[key1]:
                self.assertTrue(np.allclose(correct[key1][key],
                                            restart[key1][key]))

        syst = System(units='real', box=None, temperature=100.)
        restart = syst.restart_info()
        self.assertEqual('real', restart['units'])
        self.assertTrue(restart['temperature']['dof'] is None)
        self.assertAlmostEqual(restart['temperature']['beta'],
                               1./(100 * CONSTANTS['kB']['real']))
        self.assertAlmostEqual(restart['temperature']['set'], 100.)

    def test_evaluate_fp(self):
        """Test that we can evaluate forces and potential."""
        syst = prepare_test_system()
        pos = syst.particles.pos
        self.assertEqual(syst.potential(), 7)
        self.assertEqual(syst.evaluate_potential(), 4)
        pot, force, virial = syst.evaluate_potential_and_force()
        self.assertEqual(pot, 1)
        self.assertTrue(np.allclose(force, 9 * np.ones_like(pos)))
        self.assertTrue(np.allclose(virial, 9 * np.eye(3, 3)))
        force, virial = syst.force()
        self.assertTrue(np.allclose(force, 8 * np.ones_like(pos)))
        self.assertTrue(np.allclose(virial, 8 * np.eye(3, 3)))
        force, virial = syst.evaluate_force()
        self.assertTrue(np.allclose(force, 7 * np.ones_like(pos)))
        self.assertTrue(np.allclose(virial, 7 * np.eye(3, 3)))

    def test_generate_vel(self):
        """Test that we can generate velocities."""
        syst = prepare_test_system()
        vel = syst.particles.vel
        syst.generate_velocities(rgen='mock', seed=0, momentum=True,
                                 temperature=None, distribution='maxwell')
        correct_vel = np.array([[0.61114808, -2.78504494, 1.42713429],
                                [2.25062036, 1.32763469, 3.26596079],
                                [-2.86176844, 1.45741024, -4.69309508]])
        self.assertTrue(np.allclose(vel, correct_vel))
        logging.disable(logging.INFO)
        with self.assertLogs('pyretis.core.system', level='ERROR'):
            syst.generate_velocities(rgen='mock', distribution='fake news')
        logging.disable(logging.CRITICAL)

    def test_calculate_temp(self):
        """Test that we can calculate temperatures."""
        syst = prepare_test_system()
        syst.generate_velocities(rgen='mock', seed=0, momentum=True,
                                 temperature=None, distribution='maxwell')
        temp = syst.calculate_temperature()
        self.assertAlmostEqual(temp, 10.)

    def test_rescale_velocities(self):
        """Test that we can rescale velocities."""
        syst = prepare_test_system()
        syst.generate_velocities(rgen='mock', seed=0, momentum=True,
                                 temperature=None, distribution='maxwell')
        syst.rescale_velocities(13)
        temp = syst.calculate_temperature()
        self.assertAlmostEqual(temp, 2.)
        logging.disable(logging.INFO)
        with self.assertLogs('pyretis.core.system', level='WARNING'):
            syst.rescale_velocities(1)
        logging.disable(logging.CRITICAL)

    def test_extra_setup(self):
        """Test that we can do extra set-up."""
        syst = prepare_test_system()
        syst.generate_velocities(rgen='mock', seed=0, momentum=True,
                                 temperature=None, distribution='maxwell')
        temp = syst.calculate_temperature()
        self.assertAlmostEqual(temp, 10.)
        syst.extra_setup()

        syst.post_setup.append(('rescale_velocities', [11]))
        syst.extra_setup()
        temp = syst.calculate_temperature()
        self.assertAlmostEqual(temp, 1.333333333)

    def test_update_box(self):
        """Test that we can update the system box."""
        syst = System()
        length = [1, 2, 3, 4, 5, 6]
        syst.update_box(length)
        for i, j in zip(syst.box.cell, length):
            self.assertEqual(i, j)
        length2 = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        syst.update_box(length2)
        for i, j in zip(syst.box.cell, length):
            self.assertEqual(i, j)

    def test_system_copy(self):
        """Test that we can copy a system."""
        system = prepare_test_system()
        system.order = 1234
        system_copy = system.copy()
        self.assertIsNot(system, system_copy)
        self.assertEqual(system, system_copy)
        # Check that order parameter was also copied:
        self.assertEqual(system_copy.order, system.order)
        # Test that a change in one of the systems does not alter the other:
        self.assertEqual(system.temperature['set'],
                         system_copy.temperature['set'])
        system.temperature['set'] = 11
        self.assertNotEqual(system.temperature['set'],
                            system_copy.temperature['set'])
        self.assertNotEqual(system, system_copy)
        system.temperature['dof'] = np.array([2, 2, 2])
        # By construction, this should fail:
        system_copy = system.copy()
        system.forcefield = copy.deepcopy(system_copy.forcefield)
        self.assertNotEqual(system, system_copy)
        # Test what happens is some attribute is missing:
        del system.temperature
        system_copy = system.copy()
        # Systems should not be equal in this case since one is
        # missing an essential attribute:
        self.assertNotEqual(system, system_copy)
        # Test if particles/box are None:
        system = System()
        system_copy = system.copy()
        self.assertEqual(system, system_copy)
        # Test if articles/box are missing:
        del system.box
        del system.particles
        with self.assertRaises(AttributeError):
            system_copy = system.copy()


if __name__ == '__main__':
    unittest.main()
