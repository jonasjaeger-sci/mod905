# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test functionality for the path classes from pyretis.core.path"""
import logging
import unittest
import numpy as np
from pyretis.core.system import System
from pyretis.core.particles import Particles, ParticlesExt
from pyretis.core.path import (
    Path,
    paste_paths,
    check_crossing,
)
from pyretis.core.random_gen import RandomGenerator
from .help import NegativeOrder, SameOrder
logging.disable(logging.CRITICAL)


def set_up_system(order, pos, vel, vpot, ekin, internal=True):
    """Create a system for testing."""
    system = System()
    if internal:
        system.particles = Particles(dim=3)
    else:
        system.particles = ParticlesExt(dim=3)
    system.add_particle(pos, vel=vel)
    system.order = order
    system.particles.vpot = vpot
    system.particles.ekin = ekin
    return system


RGEN0 = RandomGenerator(seed=0)
PATHTEST0 = Path(RGEN0)
for _ in range(4):
    for k in range(16):
        PATHTEST0.append(
            set_up_system([k, k], np.zeros(3), np.zeros(3), 0.0, 0.0)
        )

PATHTEST1 = Path(RGEN0)
for k in [4, 5, 6]:
    PATHTEST1.append(
        set_up_system([k, k], np.zeros(3), np.zeros(3), 0.0, 0.0)
    )

PATHTEST2 = Path(RGEN0)
for _ in range(4):
    for k in [4, 5, 6]:
        PATHTEST2.append(
            set_up_system([k, k], np.zeros(3), np.zeros(3), 0.0, 0.0)
        )


def fill_forward_backward(pathf, pathb, npoints=20):
    """Fill in data for forward and backward paths."""
    for i in range(npoints):
        pathf.append(
            set_up_system([1.0 * i], np.zeros(3) * i, np.zeros(3) * i, i, i)
        )
        pathb.append(
            set_up_system([-1.0 * i], np.zeros(3) * i * -1.0,
                          np.zeros(3) * i * -1.0, -1.0 * i, -1.0 * i)
        )  # Pretty exotic kinetic energy.


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
        for i, phasepoint in enumerate(path.phasepoints):
            if i <= 19:
                self.assertAlmostEqual(phasepoint.order[0], i - 19.)
            else:
                self.assertAlmostEqual(phasepoint.order[0], i - 20.)
        path = paste_paths(pathb, pathf, overlap=True, maxlen=None)
        self.assertEqual(path.length, 39)
        for i, phasepoint in enumerate(path.phasepoints):
            self.assertAlmostEqual(phasepoint.order[0], i - 19.)

    def test_paste_paths2(self):
        """Test that we can paste paths together when we truncate."""
        rgen = RandomGenerator(seed=0)
        pathf = Path(rgen, maxlen=30)
        pathb = Path(rgen, maxlen=30)
        fill_forward_backward(pathf, pathb, npoints=20)
        path = paste_paths(pathb, pathf, overlap=True, maxlen=None)
        self.assertEqual(path.length, 30)
        for i, phasepoint in enumerate(path.phasepoints):
            self.assertAlmostEqual(phasepoint.order[0], i - 19.)
        pathf = Path(rgen, maxlen=32)
        pathb = Path(rgen, maxlen=31)
        fill_forward_backward(pathf, pathb, npoints=20)
        path = paste_paths(pathb, pathf, overlap=True, maxlen=None)
        self.assertEqual(path.length, 32)
        for i, phasepoint in enumerate(path.phasepoints):
            self.assertAlmostEqual(phasepoint.order[0], i - 19.)
        path = paste_paths(pathb, pathf, overlap=True, maxlen=10)
        self.assertEqual(path.length, 10)
        for i, phasepoint in enumerate(path.phasepoints):
            self.assertAlmostEqual(phasepoint.order[0], i - 19.)


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


class TestPathProperties(unittest.TestCase):
    """Run the tests for the properties of the Path class."""

    def test_length(self):
        """Test for calculate the length of a path."""
        self.assertTrue(PATHTEST0.length == 64)
        self.assertTrue(PATHTEST2.length == 12)

    def test_minvalue(self):
        """Test for calculate the min value of a path."""
        self.assertTrue(PATHTEST0.ordermin[0] == 0)
        self.assertTrue(PATHTEST2.ordermin[0] == 4)

    def test_maxvalue(self):
        """Test for calculate the max value of a path."""
        self.assertTrue(PATHTEST0.ordermax[0] == 15)
        self.assertTrue(PATHTEST2.ordermax[0] == 6)

    def test___eq__(self):
        """Test for equal properties for paths."""
        self.assertNotEqual(PATHTEST0, PATHTEST2)
        # Compare a path with something that is not a path:
        self.assertNotEqual(PATHTEST0, 'This_is_not_a_path')
        # Compare where one path has "lost" one attribute:
        path2 = PATHTEST0.copy()
        self.assertEqual(PATHTEST0, path2)
        del path2.status
        self.assertNotEqual(PATHTEST0, path2)
        # Test when a phase point is different:
        path2 = PATHTEST0.copy()
        path2.phasepoints[-1].particles.pos = np.ones(3)
        self.assertNotEqual(PATHTEST0, path2)
        # Test with different time origin as an example of differing
        # attributes:
        path2 = PATHTEST0.copy()
        path2.time_origin = -1
        self.assertNotEqual(PATHTEST0, path2)

    def test___ne__(self):
        """Test for non equal properties for paths."""
        self.assertTrue(PATHTEST0 != PATHTEST2)


class TestPath(unittest.TestCase):
    """Run the tests for the Path class."""

    def test_path_reverse(self):
        """Test if we reverse correctly for class Path."""
        rgen = RandomGenerator(seed=0)
        path = Path(rgen)
        for _ in range(50):
            path.append(
                set_up_system([rgen.rand()[0]], np.ones(3),
                              np.ones(1), 0.0, 0.0)
            )
        path_rev = path.reverse(SameOrder())
        for original, rev in zip(reversed(path.phasepoints),
                                 path_rev.phasepoints):
            self.assertAlmostEqual(
                original.order[0],
                rev.order[0]
            )
            self.assertTrue(
                np.allclose(original.particles.get_vel(),
                            rev.particles.get_vel() * -1)
            )
            self.assertTrue(
                np.allclose(original.particles.get_pos(),
                            rev.particles.get_pos())
            )
        # Test that we do nothing if the order parameter is None:
        self.assertEqual(path.reverse(None), path_rev)
        # Test for cases when the order parameter depends on the
        # velocity:
        path_rev = path.reverse(NegativeOrder())
        for original, rev in zip(reversed(path.phasepoints),
                                 path_rev.phasepoints):
            self.assertAlmostEqual(
                original.order[0],
                rev.order[0] * -1
            )
            self.assertTrue(
                np.allclose(original.particles.get_vel(),
                            rev.particles.get_vel() * -1)
            )
            self.assertTrue(
                np.allclose(original.particles.get_pos(),
                            rev.particles.get_pos())
            )

    def test_path_exceed_maxlen(self):
        """Test that we stop adding points if we exceed the path max-length."""
        rgen = RandomGenerator(seed=0)
        path = Path(rgen, maxlen=10)
        for _ in range(path.maxlen):
            add = path.append(
                set_up_system([rgen.rand()[0]], np.zeros(3),
                              np.zeros(3), 0.0, 0.0)
            )
            self.assertTrue(add)
        for _ in range(path.maxlen):
            add = path.append(
                set_up_system([rgen.rand()[0]], np.zeros(3),
                              np.zeros(3), 0.0, 0.0)
            )
            self.assertFalse(add)

    def test_empty_path_creation(self):
        """Test that empty paths are created with correct type/settings."""
        rgen = RandomGenerator(seed=0)
        maxlen = 10
        path = Path(rgen, maxlen=maxlen)
        for _ in range(maxlen + 5):
            path.append(
                set_up_system([rgen.rand()[0]], np.zeros(3),
                              np.zeros(3), 0.0, 0.0)
            )

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
            all_order.append(order)
            path.append(
                set_up_system([order], np.zeros(3), np.zeros(3), 0.0, 0.0)
            )
        ordermin, ordermax = path.ordermin, path.ordermax
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
            path.append(
                set_up_system([i], np.zeros(3), np.zeros(3), 0.0, 0.0)
            )
        ret = path.check_interfaces([1.0, 3.0, 5.0])
        self.assertEqual(ret[0], 'L')
        self.assertTrue(ret[1] is None)
        self.assertEqual(ret[2], 'M')
        self.assertEqual(ret[3], [True, True, False])

    def test_start_end(self):
        """Test the get start/end points method."""
        path = Path(None, maxlen=100)
        for i in range(5):
            path.append(
                set_up_system([i * -1.0], np.zeros(3), np.zeros(3), 0.0, 0.0)
            )
        end = path.get_end_point(1)
        self.assertEqual(end, 'L')
        end = path.get_end_point(0, 1)
        self.assertEqual(end, 'L')
        end = path.get_end_point(-10, -6)
        self.assertEqual(end, 'R')
        end = path.get_end_point(-100, -1)
        self.assertTrue(end is None)
        start = path.get_start_point(0)
        self.assertEqual(start, 'L')
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
            path.append(
                set_up_system([i], np.zeros(3), np.zeros(3), 0.0, 0.0)
            )
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
            path.append(
                set_up_system([i], np.zeros(3), np.zeros(3), 0.0, 0.0)
            )
        self.assertTrue(path.success(3.0))
        self.assertFalse(path.success(4.0))

    def test_update_energies(self):
        """Test the update energies method."""
        path = Path(None, maxlen=100)
        for i in range(5):
            path.append(
                set_up_system([i], np.zeros(3), np.zeros(3), 1.0, 2.0)
            )
        # Test if ekin and vpot have correct length:
        ekin = [10] * path.length
        vpot = [10] * path.length
        path.update_energies(ekin, vpot)
        ekin2 = [i.particles.ekin for i in path.phasepoints]
        vpot2 = [i.particles.vpot for i in path.phasepoints]
        self.assertEqual(ekin, ekin2)
        self.assertEqual(vpot, vpot2)
        # Test for one is longer than the other:
        vpot = [11] * path.length + [12]
        path.update_energies(ekin, vpot)
        vpot2 = [i.particles.vpot for i in path.phasepoints]
        self.assertEqual(ekin, ekin2)
        self.assertEqual(vpot[:path.length], vpot2)
        # Test when energies are too short:
        ekin = [10] * (path.length - 2)
        vpot = [10] * (path.length - 1)
        path.update_energies(ekin, vpot)
        ekin2 = [i.particles.ekin for i in path.phasepoints]
        vpot2 = [i.particles.vpot for i in path.phasepoints]
        self.assertEqual(ekin + [None, None], ekin2)
        self.assertEqual(vpot + [None], vpot2)

    def test_add(self):
        """Test the __iadd__ method."""
        path = Path(None, maxlen=10)
        path2 = Path(None, maxlen=10)
        for i in range(5):
            path.append(
                set_up_system([i], np.zeros(3), np.zeros(3), 0.0, 0.0)
            )
            path2.append(
                set_up_system([i * 10], np.zeros(3), np.zeros(3), 0.0, 0.0)
            )
        path += path2
        self.assertEqual(path.length, 10)
        for i, phasepoint in enumerate(path.phasepoints):
            if i <= 4:
                self.assertEqual(phasepoint.order[0], i)
            else:
                self.assertEqual(phasepoint.order[0], (i - 5) * 10)
        # Try to add some more points (we are now > maxlen):
        path += path2
        self.assertEqual(path.length, 10)

    def test_delete(self):
        """Test the delete method."""
        path = Path(None, maxlen=10)
        for i in range(5):
            path.append(
                set_up_system([i], np.zeros(3), np.zeros(3), 0.0, 0.0)
            )
        self.assertEqual(path.length, 5)
        for i in range(path.length):
            path.delete(0)
        # Check that all points were deleted:
        self.assertEqual(path.length, 0)

    def test_sorting(self):
        """Test the sorting method."""
        data = [
            ([1, 300, 1, 2, -123], ('a', 'b'), ('a', 'b'), 1, 1),
            ([3, -4], ('e', 'f'), ('e', 'f'), 5, 4),
            ([2, 0, 0], ('c', 'd'), ('c', 'd'), 3, 2),
            ([5], ('i', 'j'), ('i', 'j'), 8, 7),
            ([4, 700000], ('g', 'h'), ('g', 'h'), 8, 7),
        ]
        path = Path(None, maxlen=10)
        for datai in data:
            path.append(
                set_up_system(datai[0], datai[1], datai[2],
                              datai[3], datai[4], internal=False)
            )
        correct_order = [1, 2, 3, 4, 5]
        correct_ekin = [1, 2, 4, 7, 7]
        correct_vpot = [1, 3, 5, 8, 8]
        # Sort path by order:
        path.sorting('order', reverse=False)
        sort = [i.order[0] for i in path.phasepoints]
        self.assertEqual(sort, correct_order)
        # Sort path by order, reversed:
        path.sorting('order', reverse=True)
        sort = [i.order[0] for i in path.phasepoints]
        self.assertEqual(sort[::-1], correct_order)
        # Sort path by kinetic energy:
        path.sorting('ekin', reverse=False)
        sort = [i.particles.ekin for i in path.phasepoints]
        self.assertEqual(sort, correct_ekin)
        # Sort path by kinetic energy, reversed:
        path.sorting('ekin', reverse=True)
        sort = [i.particles.ekin for i in path.phasepoints]
        self.assertEqual(sort[::-1], correct_ekin)
        # Sort path by potential energy:
        path.sorting('vpot', reverse=False)
        sort = [i.particles.vpot for i in path.phasepoints]
        self.assertEqual(sort, correct_vpot)
        # Sort path by potential energy, reversed:
        path.sorting('vpot', reverse=True)
        sort = [i.particles.vpot for i in path.phasepoints]
        self.assertEqual(sort[::-1], correct_vpot)
        for key in ('gigio', 'vel'):
            with self.assertRaises(AttributeError):
                for _ in path.sorting(key):
                    pass


class TestExternalPaths(unittest.TestCase):
    """Test paths when we have an external particle class."""

    def test_reverse(self):
        """Test that we can reverse external paths."""
        path = Path(None)
        path.append(
            set_up_system([0.0, None], ('initial.g96', None),
                          False, None, None, internal=False)
        )
        for i in range(5):
            path.append(
                set_up_system([(i + 1) * 10, None], ('trajB.trr', i),
                              True, None, None, internal=False)
            )
        for i in range(5):
            path.append(
                set_up_system([(i + 1) * 20, None], ('trajF.trr', i),
                              False, None, None, internal=False)
            )
        rev = path.reverse(SameOrder())
        for point1, point2 in zip(rev.phasepoints,
                                  reversed(path.phasepoints)):
            self.assertNotEqual(
                point1.particles.vel_rev,
                point2.particles.vel_rev
            )
            self.assertEqual(
                point1.particles.get_pos(),
                point2.particles.get_pos()
            )
            self.assertEqual(point1.order[0], point2.order[0])


if __name__ == '__main__':
    unittest.main()
