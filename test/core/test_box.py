# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Test the box classes from pyretis.core"""
import logging
import unittest
import numpy as np
from pyretis.core.box import create_box, RectangularBox, TriclinicBox
logging.disable(logging.CRITICAL)


class RectBoxTest(unittest.TestCase):
    """Run the tests for the RectangularBox class."""

    def test_create_empty_box(self):
        """Test the creation of boxes with no arguments."""
        box = create_box()
        self.assertIsInstance(box, RectangularBox)
        self.assertEqual(box.low, [-float('inf')])
        self.assertEqual(box.high, [float('inf')])
        self.assertEqual(box.length, [float('inf')])
        self.assertEqual(box.periodic, [False])

    def test_create_missing_periodic(self):
        """Test default behavior of creation without periodic arguments."""
        box = create_box(length=[10, 10, 10], periodic=None)
        self.assertIsInstance(box, RectangularBox)
        self.assertEqual(box.periodic, [True, True, True])
        self.assertTrue(np.allclose(box.low, [0., 0., 0.]))
        self.assertTrue(np.allclose(box.high, [10., 10., 10.]))
        self.assertTrue(np.allclose(box.length, [10., 10., 10.]))

    def test_box_size(self):
        """Test that giving a size works as expected."""
        test_in = (
            {'length': [10, 10]},
            {'low': [0., -10.], 'high': [10., 20.]},
            {'low': [1, 1, 1], 'length': [10, 11, 12]},
            {'high': [1, 1, 1], 'length': [10, 11, 12]},
        )
        correct = (
            {'low': [0., 0.], 'high': [10., 10.], 'length': [10., 10.]},
            {'low': [0., -10.], 'high': [10., 20.], 'length': [10., 30.]},
            {'low': [1, 1, 1], 'high': [11., 12., 13.],
             'length': [10., 11., 12.]},
            {'low': [-9, -10, -11], 'high': [1., 1., 1.],
             'length': [10., 11., 12.]},
        )
        for case, corr in zip(test_in, correct):
            box = create_box(low=case.get('low', None),
                             high=case.get('high', None),
                             length=case.get('length', None),
                             periodic=case.get('periodic', None))
            self.assertIsInstance(box, RectangularBox)
            self.assertTrue(np.allclose(box.length, corr['length']))
            self.assertTrue(np.allclose(box.low, corr['low']))
            self.assertTrue(np.allclose(box.high, corr['high']))

    def test_volume_calculate(self):
        """Test calculation of volume."""
        box = create_box(length=[10])
        self.assertIsInstance(box, RectangularBox)
        self.assertAlmostEqual(box.calculate_volume(), 10.)
        box2 = create_box(length=[10, 10])
        self.assertIsInstance(box2, RectangularBox)
        self.assertAlmostEqual(box2.calculate_volume(), 100.)
        box3 = create_box(length=[10, 10, 10])
        self.assertIsInstance(box3, RectangularBox)
        self.assertAlmostEqual(box3.calculate_volume(), 1000.)
        box4 = create_box(low=[-10, 0, 11], high=[10, 5, 19])
        self.assertIsInstance(box4, RectangularBox)
        self.assertAlmostEqual(box4.calculate_volume(), 20.*5.*8.)

    def test_faulty_input(self):
        """Test that the initialization fails as we expect."""
        with self.assertRaises(ValueError):
            create_box(length=[10, -10, 10])
        with self.assertRaises(TypeError):
            create_box(length=10)
        with self.assertRaises(TypeError):
            create_box(length=[10, (-10, 10), (0, -15)])
        with self.assertRaises(ValueError):
            create_box(low=[0, 0], high=[10, 10], length=[11, 11])
        with self.assertRaises(ValueError):
            create_box(length=['crash', 15])

    def test_update_box(self):
        """Test update of box size."""
        box = create_box(length=[10, 10, 10])
        new_length = [10, 11, 12]
        box.update_size(new_length)
        for i, j in zip(box.length, new_length):
            self.assertAlmostEqual(i, j)
        new_length2 = [13, 12, 11, 10]
        box.update_size(new_length2)  # this should NOT update
        for i, j in zip(box.length, new_length):
            self.assertAlmostEqual(i, j)
        new_length3 = [3, 3]
        box.update_size(new_length3)  # this should NOT update
        for i, j in zip(box.length, new_length):
            self.assertAlmostEqual(i, j)


class TriBoxTest(unittest.TestCase):
    """Run the tests for the TriclinicBox class."""

    def test_create_box(self):
        """Test creation of TriclinicBox"""
        box1 = create_box(
            length=[17.5092040633036, 7.58170825120892, 6.95903807579504,
                    4.37730063346742, 0.0, 0.0]
        )
        self.assertIsInstance(box1, TriclinicBox)
        box2 = create_box(length=[10, 10, 10, 0.0, 0.0, 0.0])
        self.assertIsInstance(box2, TriclinicBox)
        box3 = create_box(length=[1, 2, 3, 4, 5, 6, 7, 8, 9])
        self.assertIsInstance(box3, TriclinicBox)

    def test_volume_calculate(self):
        """Test calculation of volume."""
        box1 = create_box(length=[10, 1, 1, 0, 0, 0])
        self.assertAlmostEqual(box1.calculate_volume(), 10.)
        box2 = create_box(length=[10, 11, 12, 0, 0, 0])
        self.assertAlmostEqual(box2.calculate_volume(), 10.*11.*12.)
        length = [17.5092040633036, 7.58170825120892, 6.95903807579504,
                  4.37730063346742, 0.0, 0.0]
        box3 = create_box(length=length)
        self.assertAlmostEqual(box3.calculate_volume(), 923.810056228)
        length = [17.5092040633036, 7.58170825120892, 6.95903807579504,
                  4.37730063346742, 0.0, 0.0, 0.0, 0.0, 0.0]
        box4 = create_box(length=length)
        self.assertAlmostEqual(box4.calculate_volume(), 923.810056228)

    def test_update_box(self):
        """Test update for triclinic box."""
        box = create_box(length=[1, 2, 3, 0, 0, 0])
        new_size = [1, 2, 3, 4, 5, 6]
        box.update_size(new_size)
        correct_size = np.array([[1., 4., 5.], [0., 2., 6.], [0., 0, 3.]])
        self.assertTrue(np.allclose(box.box_matrix, correct_size))
        new_size = [-1, -1, -1]
        box.update_size(new_size)  # This should NOT update size.
        self.assertTrue(np.allclose(box.box_matrix, correct_size))
        new_size = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        box.update_size(new_size)
        correct_size = np.array([[1., 6., 8.], [4., 2., 9.], [5., 7., 3.]])
        self.assertTrue(np.allclose(box.box_matrix, correct_size))


if __name__ == '__main__':
    unittest.main()
