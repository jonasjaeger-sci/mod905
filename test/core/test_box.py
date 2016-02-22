# -*- coding: utf-8 -*-
import logging
import unittest
from pyretis.core.box import Box
logging.disable(logging.CRITICAL)


class BoxTest(unittest.TestCase):

    def test_create_empty_box(self):
        """Test the creation of boxes with no arguments."""
        box = Box()
        self.assertEqual(box.size, [[-float('inf'), float('inf')]])
        self.assertEqual(box.length, [float('inf')])
        self.assertEqual(box.periodic, [False])

    def test_create_without_periodic_settings(self):
        """Test default behavior of creation without periodic arguments."""
        box = Box(size=[10, 10, 10], periodic=None)
        self.assertEqual(box.periodic, [True, True, True])

    def test_volume_calculate(self):
        """Test calculation of volume."""
        box = Box(size=[10])
        self.assertAlmostEqual(box.calculate_volume(), 10.)
        box2 = Box(size=[10, 10])
        self.assertAlmostEqual(box2.calculate_volume(), 100.)
        box3 = Box(size=[10, 10, 10])
        self.assertAlmostEqual(box3.calculate_volume(), 1000.)


if __name__ == '__main__':
    unittest.main()
