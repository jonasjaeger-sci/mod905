# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Test functionality for the path classes."""
import logging
import unittest
import numpy as np
from pyretis.core.path import Path
from pyretis.core.reservoirpath import ReservoirPath
from pyretis.core.random_gen import RandomGenerator
logging.disable(logging.CRITICAL)


class PathTest(unittest.TestCase):
    """Run the tests for the path classes."""

    def test_path_reverse(self):
        """Test if we reverse correctly for class Path."""
        rgen = RandomGenerator(seed=0)
        path = Path(rgen)
        for _ in range(50):
            phasepoint = {'order': [rgen.rand()], 'pos': np.zeros(3),
                          'vel': np.zeros(3), 'vpot': 0.0, 'ekin': 0.0}
            path.append(phasepoint)
        path_rev = path.reverse()
        for original, rev in zip(path.trajectory(reverse=True),
                                 path_rev.trajectory()):
            self.assertAlmostEqual(original['order'][0],
                                   rev['order'][0])

    def test_reservoir_path_reverse(self):
        """Test if we reverse correctly for class ReservoirPath."""
        rgen = RandomGenerator(seed=0)
        path = ReservoirPath(rgen, res_length=3)
        for _ in range(100):
            phasepoint = {'order': [rgen.rand()], 'pos': np.zeros(3),
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

    def test_path_exceed_maxlen(self):
        """Test that we stop adding points if we exceed the path max-length."""
        rgen = RandomGenerator(seed=0)
        path = Path(rgen, maxlen=10)
        for _ in range(path.maxlen):
            phasepoint = {'order': [rgen.rand()], 'pos': np.zeros(3),
                          'vel': np.zeros(3), 'vpot': 0.0, 'ekin': 0.0}
            add = path.append(phasepoint)
            self.assertTrue(add)
        for _ in range(path.maxlen):
            phasepoint = {'order': [rgen.rand()], 'pos': np.zeros(3),
                          'vel': np.zeros(3), 'vpot': 0.0, 'ekin': 0.0}
            add = path.append(phasepoint)
            self.assertFalse(add)

    def test_empty_path_creation(self):
        """Test that empty paths are created with correct type/settings."""
        rgen = RandomGenerator(seed=0)
        maxlen = 10
        path = Path(rgen, maxlen=maxlen)
        path_rev = ReservoirPath(rgen, maxlen=maxlen, res_length=2)
        for _ in range(maxlen + 5):
            phasepoint = {'order': [rgen.rand()], 'pos': np.zeros(3),
                          'vel': np.zeros(3), 'vpot': 0.0, 'ekin': 0.0}
            path.append(phasepoint)
            path_rev.append(phasepoint)

        path2 = path.empty_path(maxlen=maxlen)
        path_rev2 = path_rev.empty_path(maxlen=maxlen)

        self.assertIsInstance(path2, Path)
        self.assertEqual(path.maxlen, path2.maxlen)
        self.assertEqual(path.rgen, path2.rgen)

        self.assertIsInstance(path_rev2, ReservoirPath)
        self.assertEqual(path_rev.maxlen, path_rev2.maxlen)
        self.assertEqual(path_rev.res_length, path_rev2.res_length)
        self.assertEqual(path_rev.rgen, path_rev2.rgen)
        self.assertNotEqual(len(path_rev.reservoir),
                            len(path_rev2.reservoir))


if __name__ == '__main__':
    unittest.main()
