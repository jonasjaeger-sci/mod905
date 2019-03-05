# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test functionality for the random generator classes."""
import logging
import unittest
import math
import numpy as np
from numpy.random import RandomState
from pyretis.core.system import System
from pyretis.core.box import create_box
from pyretis.core.particles import Particles
from pyretis.core.particlefunctions import (
    calculate_linear_momentum,
    calculate_kinetic_temperature,
)
from pyretis.core.random_gen import (
    RandomGenerator,
    MockRandomGenerator,
    ReservoirSampler,
    RandomGeneratorBorg,
    MockRandomGeneratorBorg,
    create_random_generator,
)
logging.disable(logging.CRITICAL)


class RandomTest(unittest.TestCase):
    """Run the tests for the random classes."""

    def test_rand(self):
        """Test that we can draw random numbers in [0, 1)."""
        rgen = RandomGenerator(seed=0)
        for i in (0, 1, 10, 100, 1000000):
            numbers = rgen.rand(shape=i)
            left = all([j >= 0 for j in numbers])
            self.assertTrue(left)
            right = all([j < 1 for j in numbers])
            self.assertTrue(right)
            self.assertEqual(i, len(numbers))

        # Without arguments
        number = rgen.rand()
        self.assertEqual(1, len(number))
        # Test that it fails as we expect:
        args = [1, 2]
        self.assertRaises(TypeError, rgen.rand, *args)
        self.assertRaises(TypeError, rgen.rand, (1, 2))

    def test_random_integers(self):
        """Test generation for [low, high]."""
        rgen = RandomGenerator(seed=0)
        for i in (-5, 0, 10, 100):
            for j in (-5, 0, 10, 100):
                if i >= j + 1:
                    args = [i, j]
                    self.assertRaises(ValueError, rgen.random_integers,
                                      *args)
                else:
                    for _ in range(100):  # just repeat a bit
                        number = rgen.random_integers(i, j)
                        self.assertTrue(i <= number <= j)
        # Just draw ones:
        numbers = [rgen.random_integers(1, 1) for _ in range(10)]
        self.assertTrue(all([i == 1 for i in numbers]))
        # Just draw 1 or 2
        numbers = [rgen.random_integers(1, 2) for _ in range(100)]
        self.assertTrue(all([i in (1, 2) for i in numbers]))

    def test_random_normal(self):
        """Test generation of numbers from normal distribution."""
        rgen = RandomGenerator(seed=0)
        loc = 1.2345
        std = 0.2468
        numbers = rgen.normal(loc=loc, scale=std, size=100000)
        self.assertAlmostEqual(loc, np.average(numbers), delta=0.01)
        self.assertAlmostEqual(std, np.std(numbers), delta=0.01)

    def test_random_normal_shape(self):
        """Test drawing of numbers from normal distribution with shape."""
        rgen = RandomGenerator(seed=0)
        shape = (10, 3)
        numbers = rgen.normal(loc=0.0, scale=2.0, size=shape)
        self.assertEqual(shape, numbers.shape)

        # Pretend that we have 6 particles with different "mass"
        sigma = [1.0, 2.0, 4.0, 8.0, 16.0, 32.0]
        tol = 0.1
        for dim in (1, 2, 3):
            # lets draw numbers a couple of times:
            pos = []
            for _ in range(1000):
                numbers = rgen.normal(loc=0.0, scale=np.repeat(sigma, dim))
                numbers.shape = (len(sigma), dim)
                pos.append(numbers)
            pos = np.array(pos)
            # std over all drawn matrices:
            std = np.std(pos, axis=(0,))
            # compare for each dimension:
            for i in range(dim):
                std_diff = np.abs(std[:, i] - sigma) / sigma
                self.assertTrue(all([i < tol for i in std_diff]))

    def test_multivariate_normal(self):
        """Just test that we can draw from the multivariate distribution."""
        rgen = RandomGenerator(seed=0)
        mean = np.array([[1.0, 0.0], [0.0, 1.0]])
        cov = np.array([[1.0, 0.0], [0.0, 1.0]])
        numbers = rgen.multivariate_normal(mean, cov)
        self.assertEqual(numbers.shape, (1, 2, 2))
        numbers = rgen.multivariate_normal(mean, cov, size=2)
        self.assertEqual(numbers.shape, (2, 2, 2))

    def test_draw_maxwellian_velocities(self):
        """Test that we can draw with the system object as input."""
        temperature = 2.0
        mass = np.array([1.0, 2.0, 4.0, 16.0, 256.0, 65536.0])
        sigv = np.sqrt(temperature / mass)
        tol = 0.1
        rgen = RandomGenerator(seed=0)
        for dim in (1, 2, 3):
            system = System(
                temperature=temperature,
                units='reduced',
                box=create_box(periodic=[False]*dim))
            system.particles = Particles(dim=dim)
            for i in mass:
                system.add_particle(np.zeros(dim), mass=i, name='Ar', ptype=0)
            all_vel = []
            for _ in range(1000):
                veli, _ = rgen.draw_maxwellian_velocities(system)
                all_vel.append(veli)
            vel = np.array(all_vel)
            # std over all drawn matrices:
            std = np.std(vel, axis=(0,))
            # compare for each dimension:
            for i in range(dim):
                std_diff = np.abs(std[:, i] - sigv) / sigv
                self.assertTrue(all([i < tol for i in std_diff]))

    def test_generate_maxwellian(self):
        """Test the generate_maxwellian_velocities method."""
        particles = Particles(dim=3)
        dof = [1., 1., 1.]
        heavy = []
        light = []
        for i in range(10):
            if i % 2 == 0:
                mass = 1
                light.append(i)
            else:
                mass = 2
                heavy.append(i)
            particles.add_particle(np.zeros(3), np.zeros(3),
                                   np.zeros(3), mass=mass)
        rgen = RandomGenerator(seed=0)
        for mom in (True, False):
            rgen.generate_maxwellian_velocities(particles, 1.0, 2.0,
                                                dof=dof, momentum=mom)
            _, temp, _ = calculate_kinetic_temperature(particles, 1.0,
                                                       dof=dof)
            self.assertAlmostEqual(temp, 2.0)
            close = np.allclose(np.zeros(3),
                                calculate_linear_momentum(particles))
            if mom:
                self.assertTrue(mom)
            else:
                self.assertFalse(mom)
        rgen.generate_maxwellian_velocities(particles, 1.0, 2.0,
                                            dof=dof, momentum=True,
                                            selection=heavy)
        rgen.generate_maxwellian_velocities(particles, 1.0, 2.0,
                                            dof=None, momentum=False,
                                            selection=light)
        _, temp, _ = calculate_kinetic_temperature(particles, 1.0,
                                                   dof=dof)
        self.assertAlmostEqual(temp, 2.0)
        close = np.allclose(
            np.zeros(3),
            calculate_linear_momentum(particles, selection=heavy)
        )
        self.assertTrue(close)
        close = np.allclose(
            np.zeros(3),
            calculate_linear_momentum(particles, selection=light)
        )
        self.assertFalse(close)

    def test_state(self):
        """Test that we can set and get the state of the generator."""
        rgen = RandomGenerator(seed=123)
        for _ in range(5):
            rgen.random_integers(1, 1000)
        state = rgen.get_state()
        numbers1 = [rgen.random_integers(1, 1000) for _ in range(10)]
        rgen.set_state(state)
        numbers2 = [rgen.random_integers(1, 1000) for _ in range(10)]
        for i, j in zip(numbers1, numbers2):
            self.assertEqual(i, j)

    def test_create(self):
        """Test that we create random generators from settings."""
        settings = {}
        rgen = create_random_generator(settings)
        self.assertEqual(rgen.seed, 0)
        self.assertIsInstance(rgen, RandomGenerator)

        settings = {'seed': 100}
        rgen = create_random_generator(settings)
        self.assertEqual(rgen.seed, 100)
        self.assertIsInstance(rgen, RandomGenerator)

        settings = {'rgen': 'mock', 'seed': 101}
        rgen = create_random_generator(settings)
        self.assertEqual(rgen.seed, 101)
        self.assertIsInstance(rgen, MockRandomGenerator)


class TestReservoirSampler(unittest.TestCase):
    """Run the tests for the ReservoirSampler classe."""

    def test_init(self):
        """Test the initialisation."""
        rgen = ReservoirSampler()
        self.assertIsInstance(rgen.rgen, RandomState)
        rgen = ReservoirSampler(length=10, rgen=RandomGenerator(seed=1))
        self.assertIsInstance(rgen.rgen, RandomGenerator)

    def test_add_get(self):
        """Test that we can add to the reservoir."""
        rgen = ReservoirSampler(length=10, rgen=MockRandomGenerator(seed=1))
        correct = [21, 0, 0, 0, 2, 2, 18, 29, 1, 0]
        for i in range(30):
            rgen.append(i)
            self.assertEqual(len(rgen.reservoir), 10)
        for i, j in zip(correct, rgen.reservoir):
            self.assertEqual(i, j)
        for i in range(10):
            j = rgen.get_item()
            self.assertEqual(correct[i], j)
        logging.disable(logging.INFO)
        with self.assertLogs('pyretis.core.random_gen', level='CRITICAL'):
            j = rgen.get_item()
        self.assertEqual(correct[0], j)
        logging.disable(logging.CRITICAL)


class TestMockRandomGenerator(unittest.TestCase):
    """Run some tests for the MockRandomGenerator."""

    def test_state(self):
        """Test that we can get and set the state of the generator."""
        rgen = MockRandomGenerator(seed=987)
        for _ in range(5):
            rgen.random_integers(1, 100)
        state = rgen.get_state()
        numbers1 = [rgen.random_integers(1, 100) for _ in range(10)]
        rgen.set_state(state)
        numbers2 = [rgen.random_integers(1, 100) for _ in range(10)]
        for i, j in zip(numbers1, numbers2):
            self.assertEqual(i, j)

    def test_rand(self):
        """Test that we can draw fake random numbers in [0, 1)."""
        rgen = MockRandomGenerator(seed=0)
        numbers = rgen.rand(shape=5)
        self.assertTrue(np.allclose(numbers, rgen.rgen[0:5]))

    def test_random_integers(self):
        """Test that we can draw fake random integers."""
        rgen = MockRandomGenerator(seed=0)
        correct = [14, 10, 14, 15, 13]
        for i in correct:
            j = rgen.random_integers(10, 15)
            self.assertEqual(i, j)
        rgen = MockRandomGenerator(seed=0)
        for _ in range(len(rgen.rgen)):
            j = rgen.random_integers(4, 9)
            self.assertTrue(4 <= j <= 9)

    def test_normal(self):
        """Test that we can draw fake normal numbers."""
        rgen = MockRandomGenerator(seed=0)
        numbers = rgen.normal()
        self.assertAlmostEqual(numbers[0], rgen.rgen[0])
        numbers = rgen.normal(loc=1.0, scale=10, size=5)
        for i, j in zip(numbers, rgen.rgen[1:6]):
            self.assertAlmostEqual(i, j)

    def test_multivariate_normal(self):
        """Test that we can draw fake normal numbers."""
        rgen = MockRandomGenerator(seed=0)
        correct = np.array([[0.0178008, 0.01044599]])
        numbers = rgen.multivariate_normal(1.0, None)
        self.assertTrue(np.allclose(correct, numbers))
        numbers = rgen.multivariate_normal([1.0, 1.0], None, size=3)
        correct = np.array([[0.01765968, 0.01976767],
                            [0.01537996, 0.01986571],
                            [0.01363436, 0.01553565]])
        self.assertTrue(np.allclose(correct, numbers))


class TestBorgRandomGenerators(unittest.TestCase):
    """Test the state sharing random generators."""

    def test_borg_mock(self):
        """Test that we share the Mock state."""
        rgens = [
            MockRandomGeneratorBorg(
                seed=i,
                norm_shift=(i == 0),
            ) for i in range(5)
        ]
        state0 = rgens[0].get_state()
        # Are all states the same?
        self.assertTrue(all([i.get_state() is state0 for i in rgens]))
        # Did the norm_shift get set to the first value?
        self.assertTrue(all([i.norm_shift for i in rgens]))
        # Change the state of one member by requesting a number:
        _ = rgens[0].rand()
        state1 = rgens[0].get_state()
        # Check that the state did change:
        self.assertNotEqual(state0, state1)
        # Are all states still the same?
        self.assertTrue(all([i.get_state() == state1 for i in rgens]))
        # Set state manually
        rgens[-1].set_state(3)
        self.assertTrue(all([i.get_state() == 3 for i in rgens]))
        MockRandomGeneratorBorg.reset_state()

    @staticmethod
    def assert_equal_npstates(state1, state2):
        """Compare two random states coming from numpy.random.get_state()."""
        if not len(state1) == len(state2):
            raise AssertionError('Length of state data differ.')
        if not state1[0] == 'MT19937':
            raise AssertionError('Unexpected state string.')
        if not state1[0] == state2[0]:
            raise AssertionError('States differ for state string.')
        if not np.allclose(state1[1], state2[1]):
            raise AssertionError('States differ for state integers.')
        if not state1[2] == state2[2]:
            raise AssertionError('States differ for "pos" integer.')
        if not state1[3] == state2[3]:
            raise AssertionError('States differ for "has_gauss" integer.')
        if not math.isclose(state1[4], state2[4]):
            raise AssertionError('States differ for "cached_gaussian" float.')

    def test_borg_randomgen(self):
        """Test that we share the Mock state."""
        rgens = [
            RandomGeneratorBorg(seed=i) for i in range(5)
        ]
        # Check that rgen objects are identical:
        obj = rgens[0].rgen
        for i in rgens:
            self.assertIs(obj, i.rgen)
        # Check that the states are the same:
        state0 = rgens[0].get_state()
        for i in rgens:
            self.assert_equal_npstates(state0, i.get_state())
        RandomGeneratorBorg.reset_state()

    def test_new_swarm(self):
        """Test that we make a new swarm without altering the old one."""
        rgenA = RandomGeneratorBorg(seed=0)
        rgb2 = RandomGeneratorBorg.make_new_swarm()
        rgenB = rgb2(seed=0)
        rgenC = RandomGeneratorBorg(seed=0)
        rgenD = rgb2(seed=0)

        assert rgenA.rgen is not rgenB.rgen  # Test new swarm
        assert rgenA.rgen is rgenC.rgen  # Test that the old swarm still works
        assert rgenB.rgen is rgenD.rgen  # Test that the new swarm works


if __name__ == '__main__':
    unittest.main()
