# -*- coding: utf-8 -*-
import logging
import unittest
import numpy as np
from pyretis.core.path import Path, ReservoirPath
from pyretis.core.random_gen import RandomGenerator
logging.disable(logging.CRITICAL)


class PathTest(unittest.TestCase):

    def test_path_reverse(self):
        """Test if we reverse correctly for class Path."""
        rgen = RandomGenerator(seed=0)
        path = Path(rgen)
        for i in range(50):
            path.append([rgen.rand()], np.zeros(3), np.zeros(3), 0.0)
        path_rev = path.reverse()
        for original, rev in zip(path.trajectory(reverse=True),
                                 path_rev.trajectory()):
            self.assertAlmostEqual(original[0][0], rev[0][0])

    def test_reservoir_path_reverse(self):
        """Test if we reverse correctly for class ReservoirPath."""
        rgen = RandomGenerator(seed=0)
        path = ReservoirPath(rgen, res_length=3)
        for i in range(100):
            path.append([rgen.rand()], np.zeros(3), np.zeros(3), 0.0)
        path_rev = path.reverse()
        for original, rev in zip(path.trajectory(reverse=True),
                                 path_rev.trajectory()):
            self.assertAlmostEqual(original[0][0], rev[0][0])
        # check if reservoir point are equal
        for point, point_rev in zip(path.reservoir, path_rev.reservoir):
            ppoint = path.phasepoint(point[0])
            ppoint_rev = path_rev.phasepoint(point_rev[0])
            self.assertAlmostEqual(ppoint[0], ppoint_rev[0], 12)
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
            add = path.append([rgen.rand()], np.zeros(3), np.zeros(3), 0.0)
            self.assertTrue(add)
        for _ in range(path.maxlen):
            add = path.append([rgen.rand()], np.zeros(3), np.zeros(3), 0.0)
            self.assertFalse(add)

    def test_empty_path_creation(self):
        """Test that empty paths are created with correct type/settings."""
        rgen = RandomGenerator(seed=0)
        MAXLEN = 10
        path = Path(rgen, maxlen=MAXLEN)
        path_rev = ReservoirPath(rgen, maxlen=MAXLEN, res_length=2)
        for _ in range(MAXLEN + 5):
            path.append([rgen.rand()], np.zeros(3), np.zeros(3), 0.0)
            path_rev.append([rgen.rand()], np.zeros(3), np.zeros(3), 0.0)

        path2 = path.empty_path()
        path_rev2 = path_rev.empty_path()

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
