# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the particle functions from pyretis.core.particlefunctions"""
import logging
import unittest
import numpy as np
from pyretis.core.box import create_box
from pyretis.core.system import System
from pyretis.core.particles import Particles
from pyretis.core.particlefunctions import (
    _get_vel_mass,
    atomic_kinetic_energy_tensor,
    calculate_kinetic_energy,
    calculate_kinetic_energy_tensor,
    calculate_kinetic_temperature,
    kinetic_temperature,
    calculate_linear_momentum,
    calculate_pressure_from_temp,
    calculate_pressure_tensor,
    calculate_scalar_pressure,
    calculate_thermo,
    calculate_thermo_path,
    reset_momentum,
)
logging.disable(logging.CRITICAL)


def empty_particles(masses):
    """Set up a particle object for testing."""
    particles = Particles(dim=3)
    for i in masses:
        particles.add_particle(np.zeros(3), np.zeros(3), np.zeros(3), mass=i)
    particles.virial = np.zeros((3, 3))
    return particles


class ParticleTest(unittest.TestCase):
    """Run the tests for the Particle() class."""

    def test_get_selection(self):
        """Test the creation a particle list."""
        particles = empty_particles([1, 2, 1, 2])
        _, mass = _get_vel_mass(particles, selection=[0, 1])
        for i, j in zip(mass, (1, 2)):
            self.assertAlmostEqual(i[0], j)
        _, mass = _get_vel_mass(particles, selection=[0, 2])
        for i in mass:
            self.assertAlmostEqual(i[0], 1.0)
        _, mass = _get_vel_mass(particles, selection=[1, 3])
        for i in mass:
            self.assertAlmostEqual(i[0], 2.0)

    def test_get_atomic_ek(self):
        """Test the atomic ek tensor calculation."""
        particles = empty_particles([1, 2, 1, 2])
        particles.vel = np.array([[1., 1., 1.], [2., 2., 2.],
                                  [3., 3., 3.], [4., 4., 4.]])
        kin = atomic_kinetic_energy_tensor(particles)
        kin1 = atomic_kinetic_energy_tensor(particles, selection=[0, 2])
        kin2 = atomic_kinetic_energy_tensor(particles, selection=[1, 3])
        self.assertTrue(np.allclose(kin[0], kin1[0]))
        self.assertTrue(np.allclose(kin[2], kin1[1]))
        self.assertTrue(np.allclose(kin[1], kin2[0]))
        self.assertTrue(np.allclose(kin[3], kin2[1]))
        kin3 = atomic_kinetic_energy_tensor(particles, selection=[3])
        self.assertTrue(np.allclose(kin[3], kin3[0]))

    def test_calculate_ek(self):
        """Test calculation of kinetic energy."""
        particles = empty_particles([1, 2, 1, 2])
        particles.vel = np.array([[1., 1., 1.], [2.1, 2.1, 2.1],
                                  [3.1, 3.1, 3.1], [4.1, 4.1, 4.1]])
        ekin, tensor = calculate_kinetic_energy(particles)
        tensor2 = calculate_kinetic_energy_tensor(particles)
        self.assertTrue(np.allclose(tensor, tensor2))
        self.assertAlmostEqual(ekin, 79.575)

    def test_calculate_temp(self):
        """Test calculation of temperature."""
        particles = empty_particles([1, 2, 1, 0.01])
        particles.vel = np.ones_like(particles.pos)
        temp1, temp2, _ = calculate_kinetic_temperature(particles, 1.0)
        self.assertAlmostEqual(temp2, 1.0025)
        for i in temp1:
            self.assertAlmostEqual(i, 1.0025)

    def test_kinetic_temp(self):
        """Test calculation of kinetic temperature."""
        particles = empty_particles([1, 2, 1, 0.01])
        particles.vel = np.ones_like(particles.pos)
        vel = particles.vel
        mass = particles.mass
        temp1, temp2, _ = kinetic_temperature(vel, mass, 1.0)
        self.assertAlmostEqual(temp2, 1.0025)
        for i in temp1:
            self.assertAlmostEqual(i, 1.0025)
        temp1, temp2, _ = kinetic_temperature(vel, mass, 1.0,
                                              dof=[1.0, 0.0, 0.0])
        self.assertAlmostEqual(temp2, 1.11388888889)
        for i, j in zip(temp1, (1.33666667, 1.0025, 1.0025)):
            self.assertAlmostEqual(i, j)

    def test_linear_momentum(self):
        """Test calculation of linear momentum."""
        particles = empty_particles([1, 0.5, 2, 1])
        particles.vel = np.array([[1., 1., 1.], [2., 2., 2.],
                                  [0.5, 0.5, 0.5], [1., 1., 1.]])
        mom = calculate_linear_momentum(particles)
        for i in mom:
            self.assertAlmostEqual(i, 4.)

    def test_pressure_from_temp(self):
        """Test calculation of pressure."""
        particles = empty_particles([1, 0.5, 2, 1])
        particles.vel = np.array([[1., 1., 1.], [2., 2., 2.],
                                  [0.5, 0.5, 0.5], [1., 1., 1.]])
        pvol, press = calculate_pressure_from_temp(particles, 3, 1.0, 1.0)
        self.assertAlmostEqual(pvol, 4.5)
        self.assertAlmostEqual(press, 4.5)
        pvol, press = calculate_pressure_from_temp(particles, 3, 1.0, 1.0,
                                                   dof=[1., 0., 0.])
        self.assertAlmostEqual(pvol, 4.583333333)
        self.assertAlmostEqual(press, 4.583333333)

    def test_pressure_tensors(self):
        """Test calculation of the pressure tensor and scalar."""
        particles = empty_particles([1, 2, 3, 4])
        particles.vel = np.array([[1., 1., 1.], [2., 2., 2.],
                                  [0.5, 0.5, 0.5], [1., 1., 1.]])
        press = calculate_pressure_tensor(particles, 1.0)
        for i in press.ravel():
            self.assertAlmostEqual(i, 13.75)
        presss = calculate_scalar_pressure(particles, 1.0, 3.0)
        self.assertAlmostEqual(presss, 13.75)

    def test_calculate_thermo(self):
        """Test the calculate_thermo method."""
        system = System(units='reduced', box=create_box(cell=[1., 1., 1.]))
        particles = empty_particles([1, 2, 3, 4])
        particles.vel = np.array([[1., 1., 1.], [2., 2., 2.],
                                  [0.5, 0.5, 0.5], [1., 1., 1.]])
        particles.vpot = 123.456
        system.particles = particles
        res = calculate_thermo(system)
        correct = {
            'etot': 36.020250000000004,
            'vpot': 30.864,
            'press': 13.75,
            'mom': np.array([10.5, 10.5, 10.5]),
            'temp': 4.583333333333333,
            'ekin': 5.15625,
            'press-tens': 13.75 * np.ones((3, 3)),
        }
        for key in ('etot', 'vpot', 'press', 'temp', 'ekin'):
            self.assertAlmostEqual(correct[key], res[key])
        for key in ('mom', 'press-tens'):
            self.assertTrue(np.allclose(correct[key], res[key]))

    def test_thermo_path(self):
        """Test thermo calculation for path-style output."""
        system = System(units='reduced', box=create_box(cell=[1., 1.5, 1.]))
        particles = empty_particles([1, 2])
        particles.vel = np.array([[1., 1., 1.], [2., 2., 2.]])
        particles.vpot = 314.21
        system.particles = particles
        res = calculate_thermo_path(system)
        correct = {
            'temp': 9.0,
            'vpot': 314.21,
            'ekin': 13.5,
            'etot': 327.70999999999998
        }
        for key, val in correct.items():
            self.assertAlmostEqual(val, res[key])

    def test_reset_mom(self):
        """Test that we can reset momentum."""
        particles = empty_particles([1, 0.5, 2, 1])
        particles.vel = np.array([[1., 1., 1.], [2., 2., 2.],
                                  [0.5, 0.5, 0.5], [1., 1., 1.]])
        vel = np.copy(particles.vel)
        reset_momentum(particles)
        mom = calculate_linear_momentum(particles)
        self.assertTrue(np.allclose(mom, np.zeros(3)))
        particles.vel = vel
        reset_momentum(particles, dim=[False, True, False])
        mom = calculate_linear_momentum(particles)
        correct = [4., 0.0, 4.0]
        for i, j in zip(mom, correct):
            self.assertAlmostEqual(i, j)


if __name__ == '__main__':
    unittest.main()
