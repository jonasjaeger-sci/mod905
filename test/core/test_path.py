# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test functionality for the path classes."""
import logging
import unittest
import numpy as np
from pyretis.core.path import (
    Path,
    PathExt,
    paste_paths,
    check_crossing,
)
from pyretis.core.reservoirpath import ReservoirPath
from pyretis.core.random_gen import RandomGenerator
logging.disable(logging.CRITICAL)


def fill_forward_backward(pathf, pathb, npoints=20):
    """Fill in data for forward and backward paths."""
    for i in range(npoints):
        phasepoint = {'order': [1.0 * i], 'pos': np.ones(3) * i,
                      'vel': np.ones(3) * i, 'vpot': i, 'ekin': i}
        pathf.append(phasepoint)
        phasepoint = {'order': [-1.0 * i], 'pos': np.ones(3) * i * -1.0,
                      'vel': np.ones(3) * i * -1,
                      'vpot': -1. * i, 'ekin': -1. * i}
        pathb.append(phasepoint)


class TestPaste(unittest.TestCase):
    """Test the paste_paths method."""

    def test_paste_paths1(self):
        """Test that we can paste paths together."""
        rgen = RandomGenerator(seed=0)
        pathf = Path(rgen, maxlen=1000)
        pathb = Path(rgen, maxlen=1000)
        fill_forward_backward(pathf, pathb, npoints=20)
        path = paste_paths(pathb, pathf, overlap=False, maxlen=None)
        self.assertEqual(path.length, 40)
        for i, phasepoint in enumerate(path.trajectory()):
            if i <= 19:
                self.assertAlmostEqual(phasepoint['order'][0], i - 19.)
            else:
                self.assertAlmostEqual(phasepoint['order'][0], i - 20.)
        path = paste_paths(pathb, pathf, overlap=True, maxlen=None)
        self.assertEqual(path.length, 39)
        for i, phasepoint in enumerate(path.trajectory()):
            self.assertAlmostEqual(phasepoint['order'][0], i - 19.)

    def test_paste_paths2(self):
        """Test that we can paste paths together when we truncate."""
        rgen = RandomGenerator(seed=0)
        pathf = Path(rgen, maxlen=30)
        pathb = Path(rgen, maxlen=30)
        fill_forward_backward(pathf, pathb, npoints=20)
        path = paste_paths(pathb, pathf, overlap=True, maxlen=None)
        self.assertEqual(path.length, 30)
        for i, phasepoint in enumerate(path.trajectory()):
            self.assertAlmostEqual(phasepoint['order'][0], i - 19.)
        pathf = Path(rgen, maxlen=32)
        pathb = Path(rgen, maxlen=31)
        fill_forward_backward(pathf, pathb, npoints=20)
        path = paste_paths(pathb, pathf, overlap=True, maxlen=None)
        self.assertEqual(path.length, 32)
        for i, phasepoint in enumerate(path.trajectory()):
            self.assertAlmostEqual(phasepoint['order'][0], i - 19.)
        path = paste_paths(pathb, pathf, overlap=True, maxlen=10)
        self.assertEqual(path.length, 10)
        for i, phasepoint in enumerate(path.trajectory()):
            self.assertAlmostEqual(phasepoint['order'][0], i - 19.)


class TestCheckCrossing(unittest.TestCase):
    """Test the check_crossing method."""

    def test_check_crossing(self):
        """Test the check crossing method."""
        leftof, cross = check_crossing(0, 1.0, [-1.0, 0.0, 1.1], None)
        self.assertEqual(leftof, [False, False, True])
        self.assertTrue(not cross)
        leftof, cross = check_crossing(1, 1.2, [-1.0, 0.0, 1.1], leftof)
        self.assertEqual(leftof, [False, False, False])
        self.assertEqual(cross[0], (1, 2, '+'))
        leftof, cross = check_crossing(10, -2, [-1.0, 0.0, 1.1], leftof)
        self.assertEqual(leftof, [True, True, True])
        self.assertEqual(cross[0], (10, 0, '-'))
        self.assertEqual(cross[1], (10, 1, '-'))
        self.assertEqual(cross[2], (10, 2, '-'))


class TestPath(unittest.TestCase):
    """Run the tests for the Path class."""

    def test_path_reverse(self):
        """Test if we reverse correctly for class Path."""
        rgen = RandomGenerator(seed=0)
        path = Path(rgen)
        for _ in range(50):
            phasepoint = {'order': [rgen.rand()[0]], 'pos': np.zeros(3),
                          'vel': np.zeros(3), 'vpot': 0.0, 'ekin': 0.0}
            path.append(phasepoint)
        path_rev = path.reverse()
        for original, rev in zip(path.trajectory(reverse=True),
                                 path_rev.trajectory()):
            self.assertAlmostEqual(original['order'][0],
                                   rev['order'][0])

    def test_path_exceed_maxlen(self):
        """Test that we stop adding points if we exceed the path max-length."""
        rgen = RandomGenerator(seed=0)
        path = Path(rgen, maxlen=10)
        for _ in range(path.maxlen):
            phasepoint = {'order': [rgen.rand()[0]], 'pos': np.zeros(3),
                          'vel': np.zeros(3), 'vpot': 0.0, 'ekin': 0.0}
            add = path.append(phasepoint)
            self.assertTrue(add)
        for _ in range(path.maxlen):
            phasepoint = {'order': [rgen.rand()[0]], 'pos': np.zeros(3),
                          'vel': np.zeros(3), 'vpot': 0.0, 'ekin': 0.0}
            add = path.append(phasepoint)
            self.assertFalse(add)

    def test_empty_path_creation(self):
        """Test that empty paths are created with correct type/settings."""
        rgen = RandomGenerator(seed=0)
        maxlen = 10
        path = Path(rgen, maxlen=maxlen)
        for _ in range(maxlen + 5):
            phasepoint = {'order': [rgen.rand()[0]], 'pos': np.zeros(3),
                          'vel': np.zeros(3), 'vpot': 0.0, 'ekin': 0.0}
            path.append(phasepoint)

        path2 = path.empty_path(maxlen=maxlen)

        self.assertIsInstance(path2, Path)
        self.assertEqual(path.maxlen, path2.maxlen)
        self.assertEqual(path.rgen, path2.rgen)

    def test_get_min_max(self):
        """Test the getting of min/max order parameter."""
        rgen = RandomGenerator(seed=0)
        path = Path(rgen, maxlen=100)
        all_order = []
        for i in range(20):
            order = -1.0 * i
            if i == 10:
                order = 100.
            elif i == 15:
                order = -100.
            phasepoint = {'order': [order], 'pos': np.zeros(3),
                          'vel': np.zeros(3), 'vpot': 0.0, 'ekin': 0.0}
            all_order.append(order)
            path.append(phasepoint)
        ordermin, ordermax = path.get_min_max_orderp()
        self.assertAlmostEqual(min(all_order), ordermin[0])
        self.assertAlmostEqual(max(all_order), ordermax[0])
        self.assertAlmostEqual(15, ordermin[1])
        self.assertAlmostEqual(10, ordermax[1])

    def test_check_interfaces(self):
        """Test the check interfaces method."""
        path = Path(None, maxlen=100)
        ret = path.check_interfaces([1.0, 4.0, 5.0])
        self.assertTrue(all((i is None for i in ret)))
        for i in range(5):
            phasepoint = {'order': [i], 'pos': np.zeros(3),
                          'vel': np.zeros(3), 'vpot': 0.0, 'ekin': 0.0}
            path.append(phasepoint)
        ret = path.check_interfaces([1.0, 3.0, 5.0])
        self.assertEqual(ret[0], 'L')
        self.assertTrue(ret[1] is None)
        self.assertEqual(ret[2], 'M')
        self.assertEqual(ret[3], [True, True, False])

    def test_start_end(self):
        """Test the get start/end points method."""
        path = Path(None, maxlen=100)
        for i in range(5):
            phasepoint = {'order': [-1.0 * i], 'pos': np.zeros(3),
                          'vel': np.zeros(3), 'vpot': 0.0, 'ekin': 0.0}
            path.append(phasepoint)
        end = path.get_end_point(0, 1)
        self.assertEqual(end, 'L')
        end = path.get_end_point(-10, -6)
        self.assertEqual(end, 'R')
        end = path.get_end_point(-100, -1)
        self.assertTrue(end is None)
        start = path.get_start_point(0, 1)
        self.assertEqual(start, 'L')
        start = path.get_start_point(-2, -3)
        self.assertEqual(start, 'R')
        start = path.get_start_point(-2, 1)
        self.assertTrue(start is None)

    def test_get_path_data(self):
        """Test the get_path_data and set_move methods."""
        path = Path(None, maxlen=100)
        path.set_move('fake')
        for i in range(5):
            phasepoint = {'order': [i], 'pos': np.zeros(3),
                          'vel': np.zeros(3), 'vpot': 0.0, 'ekin': 0.0}
            path.append(phasepoint)
        path_info = path.get_path_data('ACC', [1.0, 2.0, 3.0])
        correct = {'length': 5, 'ordermax': (4, 4), 'ordermin': (0, 0),
                   'generated': ('fake', 0, 0, 0),
                   'status': 'ACC',
                   'interface': ('L', 'M', 'R')}
        for key, val in correct.items():
            self.assertEqual(val, path_info[key])

    def test_success(self):
        """Test the success method."""
        path = Path(None, maxlen=100)
        for i in range(5):
            phasepoint = {'order': [i], 'pos': np.zeros(3),
                          'vel': np.zeros(3), 'vpot': 0.0, 'ekin': 0.0}
            path.append(phasepoint)
        self.assertTrue(path.success(3.0))
        self.assertFalse(path.success(4.0))

    def test_add(self):
        """Test the __iadd__ method."""
        path = Path(None, maxlen=10)
        path2 = Path(None, maxlen=10)
        for i in range(5):
            phasepoint = {'order': [i], 'pos': np.zeros(3),
                          'vel': np.zeros(3), 'vpot': 0.0, 'ekin': 0.0}
            path.append(phasepoint)
            phasepoint = {'order': [i*10], 'pos': np.zeros(3),
                          'vel': np.zeros(3), 'vpot': 0.0, 'ekin': 0.0}
            path2.append(phasepoint)
        path += path2
        self.assertEqual(path.length, 10)
        for i, phasepoint in enumerate(path.trajectory()):
            if i <= 4:
                self.assertEqual(phasepoint['order'][0], i)
            else:
                self.assertEqual(phasepoint['order'][0], (i - 5) * 10)
        # try to add more
        path += path2
        self.assertEqual(path.length, 10)


class TestReservoirPath(unittest.TestCase):
    """Test the ReservoirPath class."""

    def test_reservoir_path_reverse(self):
        """Test if we reverse correctly for class ReservoirPath."""
        rgen = RandomGenerator(seed=0)
        path = ReservoirPath(rgen, res_length=3)
        for _ in range(100):
            phasepoint = {'order': [rgen.rand()[0]], 'pos': np.zeros(3),
                          'vel': np.zeros(3), 'vpot': 0.0, 'ekin': 0.0}
            path.append(phasepoint)
        path_rev = path.reverse()
        for original, rev in zip(path.trajectory(reverse=True),
                                 path_rev.trajectory()):
            self.assertAlmostEqual(original['order'][0], rev['order'][0])
        # check if reservoir point are equal
        for point, point_rev in zip(path.reservoir, path_rev.reservoir):
            ppoint = path.phasepoint(point[0])
            ppoint_rev = path_rev.phasepoint(point_rev[0])
            self.assertAlmostEqual(ppoint['order'], ppoint_rev['order'], 12)
        # check if we can exhaust the reservoir:
        for _ in range(path.res_length):
            shoot = path.get_shooting_point()
            self.assertIsNot(shoot, None)
        shoot = path.get_shooting_point()
        self.assertIs(shoot, None)

    def test_empty_path_creation(self):
        """Test that empty paths are created with correct type/settings."""
        rgen = RandomGenerator(seed=0)
        maxlen = 10
        path_rev = ReservoirPath(rgen, maxlen=maxlen, res_length=2)
        for _ in range(maxlen + 5):
            phasepoint = {'order': [rgen.rand()[0]], 'pos': np.zeros(3),
                          'vel': np.zeros(3), 'vpot': 0.0, 'ekin': 0.0}
            path_rev.append(phasepoint)

        path_rev2 = path_rev.empty_path(maxlen=maxlen)

        self.assertIsInstance(path_rev2, ReservoirPath)
        self.assertEqual(path_rev.maxlen, path_rev2.maxlen)
        self.assertEqual(path_rev.res_length, path_rev2.res_length)
        self.assertEqual(path_rev.rgen, path_rev2.rgen)
        self.assertNotEqual(len(path_rev.reservoir),
                            len(path_rev2.reservoir))


class TestPathExt(unittest.TestCase):
    """Test for the PathExt class."""

    def test_reverse(self):
        """Test that we can reverse the PathExt paths."""
        path = PathExt(None)
        phasepoint = {'pos': ('initial.g96', None), 'vel': False,
                      'order': [0.0, None], 'vpot': None,
                      'ekin': None}
        path.append(phasepoint)
        for i in range(5):
            phasepoint = {'pos': ('trajB.trr', i), 'vel': True,
                          'order': [(i + 1) * 10, None], 'vpot': None,
                          'ekin': None}
            path.append(phasepoint)
        for i in range(5):
            phasepoint = {'pos': ('trajF.trr', i), 'vel': False,
                          'order': [(i + 1) * 20, None], 'vpot': None,
                          'ekin': None}
            path.append(phasepoint)
        rev = path.reverse()
        for point1, point2 in zip(rev.trajectory(),
                                  path.trajectory(reverse=True)):
            self.assertEqual(point1['vel'], not point2['vel'])
            self.assertEqual(point1['pos'], point2['pos'])
            self.assertEqual(point1['order'][0], point2['order'][0])


if __name__ == '__main__':
    unittest.main()
