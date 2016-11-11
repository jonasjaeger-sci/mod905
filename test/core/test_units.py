# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""Test the functionality of units from pyretis.core.

We also do some test to check the correctness of values.
"""
import logging
import os
import unittest
from pyretis.core.units import (create_conversion_factors,
                                generate_system_conversions,
                                read_conversions,
                                CONVERT, UNITS)
logging.disable(logging.CRITICAL)


class UnitsTest(unittest.TestCase):
    """Run the tests of methods from pyretis.core.units."""

    def test_create_lennard_jones_units(self):
        """Test that we create correct Lennard-Jones units."""
        create_conversion_factors('lj', length=(3.405, 'A'),
                                  energy=(119.8, 'kB'),
                                  mass=(39.948, 'g/mol'),
                                  charge='e')
        self.assertAlmostEqual(CONVERT['length']['bohr', 'nm'],
                               0.052917721067000, 12)
        self.assertAlmostEqual(CONVERT['length']['lj', 'nm'],
                               0.34050, 4)
        self.assertAlmostEqual(CONVERT['length']['bohr', 'lj'],
                               0.155411809301, 12)
        self.assertAlmostEqual(CONVERT['time']['lj', 'ps'],
                               2.156349772323142, 12)
        self.assertAlmostEqual(CONVERT['mass']['lj', 'kg'],
                               6.633521358698435e-26, 12)
        self.assertAlmostEqual(CONVERT['force']['lj', 'N'],
                               4.857612120293684e-12, 12)
        self.assertAlmostEqual(CONVERT['energy']['lj', 'J'],
                               1.654016926960000e-21, 12)
        self.assertAlmostEqual(CONVERT['velocity']['lj', 'nm/ps'],
                               1.579057369867981e-01, 12)
        self.assertAlmostEqual(CONVERT['pressure']['lj', 'bar'],
                               4.189754740302599e+02, 12)
        self.assertAlmostEqual(CONVERT['temperature']['lj', 'K'],
                               1.198000000000000e+02, 12)
        self.assertAlmostEqual(CONVERT['charge']['lj', 'e'],
                               4.940801883873017e-02, 12)

    def test_create_cgs_units(self):
        """Test that we create correct cgs units."""
        create_conversion_factors('cgs', length=(0.01, 'm'),
                                  energy=(1.0e-7, 'J'),
                                  mass=(1.0, 'g'), charge='e')
        self.assertAlmostEqual(CONVERT['force']['cgs', 'dyn'],
                               1.0, 12)
        self.assertAlmostEqual(CONVERT['force']['cgs', 'N'],
                               1.0e-5, 12)
        self.assertAlmostEqual(CONVERT['time']['cgs', 's'],
                               1.0, 12)
        self.assertAlmostEqual(CONVERT['length']['cgs', 'm'],
                               1.0e-2, 12)
        self.assertAlmostEqual(CONVERT['mass']['cgs', 'kg'],
                               1.0e-3, 12)
        self.assertAlmostEqual(CONVERT['velocity']['cgs', 'm/s'],
                               1.0e-2, 12)
        self.assertAlmostEqual(CONVERT['energy']['cgs', 'J'],
                               1.0e-7, 12)
        self.assertAlmostEqual(CONVERT['pressure']['cgs', 'Pa'],
                               1.0e-1, 12)
        self.assertAlmostEqual(CONVERT['temperature']['cgs', 'K'],
                               1.0, 12)
        self.assertAlmostEqual(CONVERT['charge']['cgs', 'C'],
                               3.335640951981520e-10, 12)

    def test_have_common_unit_systems(self):
        """Test that we can generate all conversions."""
        systems = ('lj', 'real', 'metal', 'au',
                   'electron', 'si', 'gromacs')
        for sys in systems:
            create_conversion_factors(sys)
        all_pairs = []
        for sys1 in systems:
            for sys2 in systems:
                if sys1 != sys2:
                    generate_system_conversions(sys1, sys2)
                    all_pairs.append((sys1, sys2))
        for key in CONVERT:
            msg = ['Could not find conversion "{}" -> "{}"',
                   'for dimension "{}"'.format(key)]
            for pair in all_pairs:
                msg[0] = msg[0].format(*pair)
                msgtxt = ' '.join(msg)
                self.assertIn(pair, CONVERT[key], msg=msgtxt)

    def test_creation_of_units(self):
        """Test that creation of units works and fails as expected."""
        self.assertRaises(ValueError, create_conversion_factors, ['test'],
                          dict(length=None, energy=None, mass=None,
                               charge=None))
        self.assertRaises(ValueError, create_conversion_factors, ['test'],
                          dict(length=(1.0, 'm'), energy=(1.0, 'J'),
                               mass=(1.0, 'kg'), charge=None))
        self.assertRaises(ValueError, create_conversion_factors, ['test'],
                          dict(length=(1.0, 'm'), energy=(1.0, 'J'),
                               mass=(1.0, 'kg'),
                               charge='a non-existing unit'))
        # the next one should be successful
        create_conversion_factors('test', length=(1.0, 'm'),
                                  energy=(1.0, 'J'), mass=(1.0, 'kg'),
                                  charge='e')
        # check if we indeed created all conversions
        for key in CONVERT:
            dimtxt = 'for dimension "{}"'.format(key)
            for unit in UNITS[key]:
                pair = ('test', unit)
                msg = 'Could not find conversion "{}" -> "{}"'.format(*pair)
                msgtxt = ' '.join([msg, dimtxt])
                self.assertIn(pair, CONVERT[key], msgtxt)
                pair = (unit, 'test')
                msg = 'Could not find conversion "{}" -> "{}"'.format(*pair)
                msgtxt = ' '.join([msg, dimtxt])
                self.assertIn(pair, CONVERT[key], msgtxt)

        self.assertRaises(ValueError, create_conversion_factors, ['test'],
                          dict(length=(1.0, 'm'), energy=(1.0, 'J'),
                               mass=(1.0, 'kg'), charge=(100, 'e')))

    def test_read_from_file(self):
        """Test that we can read units from a input file."""
        dirname = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.join(dirname, 'units_input.txt')
        conv = read_conversions(filename=filename,
                                select_units='test_system')
        self.assertAlmostEqual(conv['charge']['C', 'test_system'],
                               1.23450, 12)
        self.assertAlmostEqual(conv['energy']['J', 'test_system'],
                               6.7890, 12)
        self.assertAlmostEqual(conv['force']['N', 'test_system'],
                               4.2424242e1, 12)
        self.assertAlmostEqual(conv['length']['m', 'test_system'],
                               1.111112e1, 12)
        self.assertAlmostEqual(conv['mass']['kg', 'test_system'],
                               1.234e-4, 12)
        self.assertAlmostEqual(conv['pressure']['Pa', 'test_system'],
                               1e-1, 12)
        self.assertAlmostEqual(conv['temperature']['K', 'test_system'],
                               1.0, 12)
        self.assertAlmostEqual(conv['time']['s', 'test_system'],
                               0.5, 12)
        self.assertAlmostEqual(conv['velocity']['m/s', 'test_system'],
                               2.0, 12)


if __name__ == '__main__':
    unittest.main()
