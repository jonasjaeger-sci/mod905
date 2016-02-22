# -*- coding: utf-8 -*-
import unittest
from pyretis.core.box import Box


class BoxTest(unittest.TestCase):

    def test_create_empty_box(self):
        box = Box()
        self.assertEqual(box.size, [[-float('inf'), float('inf')]])
        self.assertEqual(box.length, [float('inf')])
        self.assertEqual(box.periodic, [False])

    def test_create_without_periodic_settings(self):
        box = Box(size=[10, 10, 10], periodic=None)
        self.assertEqual(box.periodic, [True, True, True])

    def test_volume_calculate(self):
        box = Box(size=[10])
        self.assertEqual(int(box.calculate_volume()), 10)
        box2 = Box(size=[10, 10])
        self.assertEqual(int(box2.calculate_volume()), 100)
        box3 = Box(size=[10, 10, 10])
        self.assertEqual(int(box3.calculate_volume()), 1000)


if __name__ == '__main__':
    unittest.main()
