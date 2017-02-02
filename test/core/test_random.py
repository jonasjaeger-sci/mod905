# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Test functionality for the random generator classes."""
import logging
import unittest
import numpy as np
from pyretis.core.random_gen import RandomGenerator
logging.disable(logging.CRITICAL)


class RandomTest(unittest.TestCase):
    """Run the tests for the random classes."""

    def test_rand(self):
        """Test that we can draw random numbers in [0, 1)"""
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
        """Test generation for [low, high]"""
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
        self.assertTrue(all([i == 1 or i == 2 for i in numbers]))

    def test_random_normal(self):
        """Test generation of numbers from normal distribution"""
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


if __name__ == '__main__':
    unittest.main()
