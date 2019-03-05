# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the classes and methods from pyretis.core.box"""
import logging
import unittest
import numpy as np
from pyretis.core.box import (
    create_box,
    RectangularBox,
    TriclinicBox,
    box_matrix_to_list,
    box_vector_angles,
    angles_from_box_matrix,
)
logging.disable(logging.CRITICAL)


class RectBoxTest(unittest.TestCase):
    """Run the tests for the RectangularBox and the generic box."""

    def test_create_empty_box(self):
        """Test the creation of boxes with no arguments."""
        box = create_box()
        self.assertIsInstance(box, RectangularBox)
        self.assertEqual(box.low, [-float('inf')])
        self.assertEqual(box.high, [float('inf')])
        self.assertEqual(box.length, [float('inf')])
        self.assertEqual(box.periodic, [False])

    def test_create_missing_periodic(self):
        """Test default behaviour of creation without periodic arguments."""
        box = create_box(cell=[10, 10, 10], periodic=None)
        self.assertIsInstance(box, RectangularBox)
        self.assertEqual(box.periodic, [True, True, True])
        self.assertTrue(np.allclose(box.low, [0., 0., 0.]))
        self.assertTrue(np.allclose(box.high, [10., 10., 10.]))
        self.assertTrue(np.allclose(box.length, [10., 10., 10.]))

        box = create_box(cell=[10, 10, 10], periodic=[False])
        self.assertEqual(box.periodic, [False, True, True])

    def test_create_box_fail(self):
        """Test some corner cases when we fail to create a box."""
        # Test that we fail for too many periodic values given:
        with self.assertRaises(ValueError):
            create_box(cell=[10, 10, 10], periodic=[False]*4)
        # Test that we fail when low == high:
        with self.assertRaises(ValueError):
            create_box(cell=[10, 10], low=[0, 10], high=[10, 10])
        # Test that we fail for inconsistent lengths:
        with self.assertRaises(ValueError):
            create_box(cell=[10, 10], low=[0, 0], high=[10, 20])

    def test_box_size(self):
        """Test that giving a size works as expected."""
        test_in = (
            {'length': [10, 10]},
            {'low': [0., -10.], 'high': [10., 20.]},
            {'low': [1, 1, 1], 'length': [10, 11, 12]},
            {'high': [1, 1, 1], 'length': [10, 11, 12]},
            {'high': [10, 9, 8]},
            {'low': [-10, 10]},
        )
        correct = (
            {'low': [0., 0.], 'high': [10., 10.], 'length': [10., 10.]},
            {'low': [0., -10.], 'high': [10., 20.], 'length': [10., 30.]},
            {'low': [1, 1, 1], 'high': [11., 12., 13.],
             'length': [10., 11., 12.]},
            {'low': [-9, -10, -11], 'high': [1., 1., 1.],
             'length': [10., 11., 12.]},
            {'low': [0., 0., 0.], 'high': [10, 9, 8], 'length': [10, 9, 8]},
            {'low': [-10, 10], 'high': [float('inf'), float('inf')],
             'length': [float('inf'), float('inf')]},
        )
        for case, corr in zip(test_in, correct):
            box = create_box(low=case.get('low', None),
                             high=case.get('high', None),
                             cell=case.get('length', None),
                             periodic=case.get('periodic', None))
            self.assertIsInstance(box, RectangularBox)
            self.assertTrue(np.allclose(box.length, corr['length']))
            self.assertTrue(np.allclose(box.low, corr['low']))
            self.assertTrue(np.allclose(box.high, corr['high']))

    def test_volume_calculate(self):
        """Test calculation of volume."""
        box = create_box(cell=[10])
        self.assertIsInstance(box, RectangularBox)
        self.assertAlmostEqual(box.calculate_volume(), 10.)
        box2 = create_box(cell=[10, 10])
        self.assertIsInstance(box2, RectangularBox)
        self.assertAlmostEqual(box2.calculate_volume(), 100.)
        box3 = create_box(cell=[10, 10, 10])
        self.assertIsInstance(box3, RectangularBox)
        self.assertAlmostEqual(box3.calculate_volume(), 1000.)
        box4 = create_box(low=[-10, 0, 11], high=[10, 5, 19])
        self.assertIsInstance(box4, RectangularBox)
        self.assertAlmostEqual(box4.calculate_volume(), 20.*5.*8.)

    def test_faulty_input(self):
        """Test that the initialisation fails as we expect."""
        with self.assertRaises(ValueError):
            create_box(cell=[10, -10, 10])
        with self.assertRaises(TypeError):
            create_box(cell=10)
        with self.assertRaises(ValueError):
            create_box(cell=[10, (-10, 10), (0, -15)])
        with self.assertRaises(ValueError):
            create_box(low=[0, 0], high=[10, 10], cell=[11, 11])
        with self.assertRaises(ValueError):
            create_box(cell=['crash', 15])
        with self.assertRaises(ValueError):
            create_box(low=[10, 10], high=[10, 10])

    def test_update_box(self):
        """Test update of box size."""
        box = create_box(cell=[10, 10, 10])
        new_length = [10, 11, 12]
        box.update_size(new_length)
        for i, j in zip(box.length, new_length):
            self.assertAlmostEqual(i, j)
        new_length2 = [13, 12, 11, 10]
        box.update_size(new_length2)  # This should NOT update.
        for i, j in zip(box.length, new_length):
            self.assertAlmostEqual(i, j)
        new_length3 = [3, 3]
        box.update_size(new_length3)  # This should NOT update.
        for i, j in zip(box.length, new_length):
            self.assertAlmostEqual(i, j)
        new_length4 = None
        box.update_size(new_length4)
        for i, j in zip(box.length, new_length):
            self.assertAlmostEqual(i, j)

    def test_bounds(self):
        """Test the bounds method."""
        box = create_box(cell=[10, 11, 12])
        correct = [[0., 10.], [0., 11.], [0., 12.]]
        bounds = box.bounds()
        for bound, corr in zip(bounds, correct):
            for i, j in zip(bound, corr):
                self.assertAlmostEqual(i, j)

    def test_print_length(self):
        """Test that we print out cell parameters correctly."""
        lengths = [
            [1],
            [1, 2],
            [1, 2, 3],
            [1, 2, 3, 4, 5, 6],
            [1, 2, 3, 4, 5, 6, 7, 8, 9],
        ]
        fmt = '{:6.2f}'
        for i in lengths:
            box = create_box(cell=i)
            correct = ' '.join([fmt.format(j) for j in i])
            self.assertEqual(correct, box.print_length(fmt=fmt))

    def test_restart_info(self):
        """Test that we create required restart info for a box."""
        box_settings = [
            {'low': [10, -1, 101], 'high': [12, 5, 102],
             'periodic': [True, True, False], 'cell': [2., 6., 1.]},
            {'low': [9, 8, 7], 'periodic': [False, True, False],
             'cell': [1, 2, 3, 4, 5, 6]},
        ]

        keys = ('cell', 'periodic', 'low', 'high')

        for setting in box_settings:
            box = create_box(**setting)
            restart = box.restart_info()
            self.assertTrue(all(k in restart for k in keys))
            for key, val in restart.items():
                if key not in setting:
                    continue
                if key == 'periodic':
                    self.assertEqual(val, setting[key])
                else:
                    self.assertTrue(np.allclose(val, setting[key]))

    def test_pbc_coordinate_dim(self):
        """Test pbc for a specific dimension."""
        length = [10, 11, 12]
        box = create_box(cell=length, periodic=[False, True, True])
        pos = [11, 10, 14]
        pbc_pos = box.pbc_coordinate_dim(pos[2], 2)
        self.assertAlmostEqual(pbc_pos, 2.0)
        pbc_pos = box.pbc_coordinate_dim(pos[0], 0)
        self.assertAlmostEqual(pbc_pos, pos[0])

    def test_pbc_wrap(self):
        """Test pbc wrap for coordinates."""
        length = [10, 11, 12]
        box = create_box(cell=length, periodic=[False, True, True])
        pos = np.array([[11, 10, 14], ])
        correct = np.array([[11, 10, 2], ])
        pbc_pos = box.pbc_wrap(pos)
        self.assertTrue(np.allclose(correct, pbc_pos))
        self.assertFalse(np.allclose(correct, pos))

    def test_pbc_dist_matrix(self):
        """Test pbc wrap for a distance vector."""
        box = create_box(cell=[10, 10, 10], periodic=[False, True, True])
        dist = np.array([[8., 7., 9.], ])
        pbc_dist = box.pbc_dist_matrix(dist)
        correct = np.array([[8., -3., -1.], ])
        self.assertTrue(np.allclose(correct, pbc_dist))
        self.assertTrue(np.allclose(correct, dist))


class TriBoxTest(unittest.TestCase):
    """Run the tests specific for the TriclinicBox class."""

    def test_create_box(self):
        """Test creation of TriclinicBox."""
        box1 = create_box(
            cell=[17.5092040633036, 7.58170825120892, 6.95903807579504,
                  4.37730063346742, 0.0, 0.0]
        )
        self.assertIsInstance(box1, TriclinicBox)
        box2 = create_box(cell=[10, 10, 10, 0.0, 0.0, 0.0])
        self.assertIsInstance(box2, TriclinicBox)
        box3 = create_box(cell=[1, 2, 3, 4, 5, 6, 7, 8, 9])
        self.assertIsInstance(box3, TriclinicBox)

    def test_volume_calculate(self):
        """Test calculation of volume."""
        box1 = create_box(cell=[10, 1, 1, 0, 0, 0])
        self.assertAlmostEqual(box1.calculate_volume(), 10.)
        box2 = create_box(cell=[10, 11, 12, 0, 0, 0])
        self.assertAlmostEqual(box2.calculate_volume(), 10.*11.*12.)
        length = [17.5092040633036, 7.58170825120892, 6.95903807579504,
                  4.37730063346742, 0.0, 0.0]
        box3 = create_box(cell=length)
        self.assertAlmostEqual(box3.calculate_volume(), 923.810056228)
        length = [17.5092040633036, 7.58170825120892, 6.95903807579504,
                  4.37730063346742, 0.0, 0.0, 0.0, 0.0, 0.0]
        box4 = create_box(cell=length)
        self.assertAlmostEqual(box4.calculate_volume(), 923.810056228)

    def test_update_box(self):
        """Test update for triclinic box."""
        box = create_box(cell=[1, 2, 3, 0, 0, 0])
        new_size = [1, 2, 3, 4, 5, 6]
        box.update_size(new_size)
        correct_size = np.array([[1., 4., 5.], [0., 2., 6.], [0., 0, 3.]])
        self.assertTrue(np.allclose(box.box_matrix, correct_size))
        new_size = [-1, -1, -1]
        box.update_size(new_size)  # This should NOT update size.
        self.assertTrue(np.allclose(box.box_matrix, correct_size))
        new_size = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        box.update_size(new_size)
        correct_size = np.array([[1., 4., 5.], [6., 2., 7.], [8., 9., 3.]])
        self.assertTrue(np.allclose(box.box_matrix, correct_size))

    def test_box_matrix_to_list(self):
        """Test that we return the box matrix as a list as expected."""
        new_size = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        box = create_box(cell=new_size)
        out = box_matrix_to_list(box.box_matrix)
        for i, j in zip(new_size, out):
            self.assertAlmostEqual(i, j)
        self.assertIsNone(box_matrix_to_list(None))

    def test_box_vector_angles(self):
        """Test conversion from a,b,c, alpha, beta, gamma."""
        test_data = [
            {'length': [3., 3., 3.],
             'alpha': 100., 'beta': 80., 'gamma': 75.,
             'box': np.array([[3.0, 0.77646, 0.52094],
                              [0.0, 2.89778, -0.67891],
                              [0.0, 0.0, 2.87536]])},
            {'length': [3., 5.1, 1.9],
             'alpha': 100., 'beta': 85., 'gamma': 66.,
             'box': np.array([[3.0, 2.07436, 0.16559],
                              [0.0, 4.65908, -0.43488],
                              [0.0, 0.0, 1.84213]])},
        ]
        for i in test_data:
            box_matrix = box_vector_angles(i['length'], i['alpha'],
                                           i['beta'], i['gamma'])
            self.assertTrue(np.allclose(box_matrix, i['box'], atol=1e-4))

    def test_get_angles(self):
        """Test that we can get box angles and lengths from a box matrix."""
        test_data = [
            {'length': [3., 3., 3.],
             'alpha': 100., 'beta': 80., 'gamma': 75.,
             'box': np.array([[3.0, 0.77646, 0.52094],
                              [0.0, 2.89778, -0.67891],
                              [0.0, 0.0, 2.87536]])},
            {'length': [3., 5.1, 1.9],
             'alpha': 100., 'beta': 85., 'gamma': 66.,
             'box': np.array([[3.0, 2.07436, 0.16559],
                              [0.0, 4.65908, -0.43488],
                              [0.0, 0.0, 1.84213]])},
        ]
        for i in test_data:
            length, alpha, beta, gamma = angles_from_box_matrix(i['box'])
            self.assertTrue(np.allclose(length, i['length'], atol=1e-5))
            self.assertAlmostEqual(alpha, i['alpha'], places=3)
            self.assertAlmostEqual(beta, i['beta'], places=3)
            self.assertAlmostEqual(gamma, i['gamma'], places=3)


class BoxTest(unittest.TestCase):
    """Run the test for the base class."""

    def test_box_equality(self):
        """Test that we can compare boxes."""
        box1 = create_box(cell=[1, 2, 3, 4, 5, 6, 7, 8, 9])
        box2 = create_box(cell=[1, 2, 3, 4, 5, 6, 7, 8, 9])
        self.assertEqual(box1, box2)
        # Test failure for different periodic settings:
        box1.periodic = [False, True, True]
        self.assertNotEqual(box1, box2)
        box1.periodic = [False]
        self.assertNotEqual(box1, box2)
        box1.periodic = [True, True, True]
        self.assertEqual(box1, box2)
        box1.length = None
        self.assertNotEqual(box1, box2)
        box2.length = None
        self.assertEqual(box1, box2)
        del box2.length
        self.assertNotEqual(box1, box2)
        box2.length2 = 100
        self.assertNotEqual(box1, box2)
        box3 = create_box(cell=[1, 2])
        self.assertNotEqual(box1, box3)
        box4 = create_box(cell=[1, 2])
        self.assertEqual(box3, box4)
        box3.dim = 100
        self.assertNotEqual(box3, box4)

    def test_box_copy(self):
        """Test that we can copy a box."""
        box1 = create_box(cell=[1, 2, 3, 4, 5, 6, 7, 8, 9])
        box2 = box1.copy()
        self.assertIsNot(box1, box2)
        self.assertEqual(box1, box2)
        box1 = create_box(cell=[1, 2, 3])
        box2 = box1.copy()
        self.assertIsNot(box1, box2)
        self.assertEqual(box1, box2)


if __name__ == '__main__':
    unittest.main()
