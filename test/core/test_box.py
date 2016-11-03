# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""Test the Box class from pyretis.core"""
import logging
import unittest
from pyretis.core.box import Box
logging.disable(logging.CRITICAL)


class BoxTest(unittest.TestCase):
    """Run the tests for the Box() class."""

    def test_create_empty_box(self):
        """Test the creation of boxes with no arguments."""
        box = Box()
        self.assertEqual(box.size, [[-float('inf'), float('inf')]])
        self.assertEqual(box.length, [float('inf')])
        self.assertEqual(box.periodic, [False])

    def test_create_missing_periodic(self):
        """Test default behavior of creation without periodic arguments."""
        box = Box(size=[10, 10, 10], periodic=None)
        self.assertEqual(box.periodic, [True, True, True])

    def test_box_size(self):
        """Test that giving a size works as expected."""
        test_cases = [([10, 10],  # 2D box with just lengths
                       [10., 10.],
                       [0.0, 0.0],
                       [10., 10.]),
                      ([[0.0, 10.0], [-10, 20.]],  # 2D with low/high
                       [10.0, 30.0],
                       [0.0, -10.],
                       [10.0, 20.]),
                      ([(-1.0, 1.0)],  # 1D with low/high
                       [2.0],
                       [-1.0],
                       [1.0])]
        for case in test_cases:
            size_in, correct_length, correct_low, correct_high = case
            box = Box(size=size_in)
            for length, correct in zip(box.length, correct_length):
                self.assertAlmostEqual(length, correct)
            for low, correct in zip(box.low, correct_low):
                self.assertAlmostEqual(low, correct)
            for high, correct in zip(box.high, correct_high):
                self.assertAlmostEqual(high, correct)

    def test_volume_calculate(self):
        """Test calculation of volume."""
        box = Box(size=[10])
        self.assertAlmostEqual(box.calculate_volume(), 10.)
        box2 = Box(size=[10, 10])
        self.assertAlmostEqual(box2.calculate_volume(), 100.)
        box3 = Box(size=[10, 10, 10])
        self.assertAlmostEqual(box3.calculate_volume(), 1000.)
        box4 = Box(size=[(-10, 10), (0, 5), (11, 19)])
        self.assertAlmostEqual(box4.calculate_volume(), 20.*5.*8.)

    def test_faulty_input(self):
        """Test that the initialization fails as we expect."""
        with self.assertRaises(ValueError):
            Box(size=[10, -10, 10])
        with self.assertRaises(TypeError):
            Box(size=10)
        with self.assertRaises(ValueError):
            Box(size=[10, (-10, 10), (0, -15)])
        with self.assertRaises(ValueError):
            Box(size=[10, (-10, 10), (15, 15)])
        with self.assertRaises(ValueError):
            Box(size=[10, (-10, 10), (15, 15)])
        with self.assertRaises(TypeError):
            Box(size=[10, (15.0, 'crash')])
        with self.assertRaises(ValueError):
            Box(size=['crash', 15])

if __name__ == '__main__':
    unittest.main()
