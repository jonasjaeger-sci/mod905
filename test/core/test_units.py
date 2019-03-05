# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the functionality of units from pyretis.core.

We also do some test to check the correctness of values.
"""
from copy import deepcopy
import logging
import os
import tempfile
import unittest
from pyretis.core.units import (
    create_conversion_factors,
    generate_system_conversions,
    generate_conversion_factors,
    read_conversions,
    CONVERT,
    UNITS,
    write_conversions,
    units_from_settings,
    convert_bases,
    bfs_convert,
)
from .help import turn_on_logging
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
        with self.assertRaises(ValueError):
            create_conversion_factors('test', length=None, energy=None,
                                      mass=None, charge=None)
        with self.assertRaises(ValueError):
            create_conversion_factors('test', length=(1.0, 'm'),
                                      energy=(1.0, 'J'), mass=(1.0, 'kg'),
                                      charge=None)
        with self.assertRaises(ValueError):
            create_conversion_factors('test', length=(1.0, 'm'),
                                      energy=(1.0, 'J'), mass=(1.0, 'kg'),
                                      charge='a non-existing unit')
        with self.assertRaises(LookupError):
            create_conversion_factors('test', length=(1.0, 'strange_unit'),
                                      energy=(1.0, 'J'), mass=(1.0, 'kg'),
                                      charge='e')
        with self.assertRaises(TypeError):
            create_conversion_factors('test', length=1.0,
                                      energy=(1.0, 'J'), mass=(1.0, 'kg'),
                                      charge='e')
        # the next one should be successful
        create_conversion_factors('test', length=(1.0, 'm'),
                                  energy=(1.0, 'J'), mass=(1.0, 'kg'),
                                  charge='e')
        generate_system_conversions('test', 'real')
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

        with self.assertRaises(ValueError):
            create_conversion_factors('test', length=(1.0, 'm'),
                                      energy=(1.0, 'J'),
                                      mass=(1.0, 'kg'), charge=(100, 'e'))

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

    def test_write_conversions(self):
        """Test that we can write out the conversions."""
        with tempfile.NamedTemporaryFile() as temp:
            write_conversions(filename=temp.name)
            temp.flush()
            conv = read_conversions(filename=temp.name)
            for key, val in conv.items():
                self.assertTrue(key in CONVERT)
                self.assertAlmostEqual(val, CONVERT[key])

    def test_convert_bases(self):
        """Test convert_bases function"""
        copy_convert = deepcopy(CONVERT)
        CONVERT['mass'] = {('kg', 'kg'): 1.0, ('g', 'kg'): 0.001,
                           ('g', 'g'): 1.0}
        with turn_on_logging():
            with self.assertLogs('pyretis.core.units', level='WARNING'):
                convert_bases('mass')
        self.assertAlmostEqual(CONVERT['mass'][('kg', 'g')], 1000.0)
        CONVERT.clear()
        CONVERT.update(copy_convert)

    def test_bfs_convert(self):
        """Test bfs_convert function"""
        convertdim = {('g', 'g'): 1.0, ('kg', 'g'): 1000.0, ('kg', 'kg'): 1.0}
        self.assertEqual(bfs_convert(convertdim, 'g', 'kg'),
                         (('g', 'kg'), None, None))
        self.assertEqual(bfs_convert(convertdim, 'kg', 'kg'),
                         (('kg', 'kg'), 1.0, None))
        self.assertEqual(bfs_convert(convertdim, 'kg', 'g'),
                         (('kg', 'g'), 1000.0, None))

    def test_generate_conversion(self):
        """Test the generator of conversion factors."""
        generate_conversion_factors('myunit', (1.0, 'm'), (1.0, 'J'),
                                    (1.0, 'kg'), charge='e')
        self.assertAlmostEqual(CONVERT['mass']['myunit', 'g'], 1000.)
        generate_conversion_factors('myunit2', (1.0, 'm'), (1.0, 'J'),
                                    (1.0, 'kg'), charge='C')
        # Test with missing kB
        with self.assertRaises(ValueError):
            generate_conversion_factors('myunit3', (1.0, 'm'), (1.0, 'JJ'),
                                        (1.0, 'kg'), charge='e')
        # Test with non-unit "1.0" values
        generate_conversion_factors('myunit4', (2.0, 'm'), (0.5, 'J'),
                                    (3.0, 'g'))
        self.assertAlmostEqual(CONVERT['length']['myunit4', 'm'], 2.0)
        self.assertAlmostEqual(CONVERT['length']['m', 'myunit4'], 0.5)
        self.assertAlmostEqual(CONVERT['energy']['myunit4', 'J'], 0.5)
        self.assertAlmostEqual(CONVERT['energy']['J', 'myunit4'], 2.0)
        self.assertAlmostEqual(CONVERT['mass']['myunit4', 'g'], 3.0)
        self.assertAlmostEqual(CONVERT['mass']['g', 'myunit4'], 0.33333333)
        self.assertAlmostEqual(CONVERT['mass']['myunit4', 'kg'], 0.003)
        # Test with 'unit' label part of  UNITS[dim]. To check coverage.
        copy_convert = deepcopy(CONVERT)
        self.assertEqual(CONVERT, copy_convert)
        generate_conversion_factors('bohr', (1., 'm'), (1., 'J'), (1., 'g'))
        self.assertNotEqual(CONVERT, copy_convert)
        self.assertAlmostEqual(CONVERT['length']['bohr', 'bohr'], 1.)
        # Test some expected but wrong assignment
        self.assertAlmostEqual(CONVERT['length']['bohr', 'm'], 1.)
        self.assertAlmostEqual(CONVERT['mass']['bohr', 'g'], 1.)
        # Restore CONVERT
        CONVERT.clear()
        CONVERT.update(copy_convert)
        self.assertEqual(CONVERT, copy_convert)
        with self.assertRaises(Exception) as context:
            generate_conversion_factors('au', (1., 'm'), (1., 'J'), (1., 'xx'))
        self.assertTrue("Missing" in str(context.exception))

    def test_units_from_settings(self):
        """Test that we can create units from settings."""
        # Using a predefined unit system
        settings = {'system': {'units': 'real'}}
        msg = units_from_settings(settings)
        self.assertEqual(msg, 'Created units: "real".')
        # Using a custom system:
        settings = {'system': {'units': 'my_new_system1'}}
        settings['unit-system'] = {
            'name': 'my_new_system1',
            'length': (1.0, 'bohr'),
            'mass': (1.0, 'g'),
            'energy': (1.0, 'J'),
            'charge': 'e'
        }
        msg = units_from_settings(settings)
        self.assertEqual(msg, 'Created unit system: "my_new_system1".')
        # Test for errors:
        with self.assertRaises(ValueError):
            settings = {'system': {'units': 'my_new_system2'}}
            settings['unit-system'] = {
                'length': (1.0, 'bohr'),
                'mass': (1.0, 'g'),
                'energy': (1.0, 'J'),
                'charge': 'e'
            }
            units_from_settings(settings)
        # Inconsistent name:
        with self.assertRaises(ValueError):
            settings = {'system': {'units': 'my_new_system2'}}
            settings['unit-system'] = {
                'name': 'my_new_system3',
                'length': (1.0, 'bohr'),
                'mass': (1.0, 'g'),
                'energy': (1.0, 'J'),
                'charge': 'e'
            }
            units_from_settings(settings)
        # Missing one of length, mass, energy, charge
        for i in ('length', 'mass', 'energy', 'charge'):
            settings = {'system': {'units': 'my_new_system2'}}
            settings['unit-system'] = {
                'name': 'my_new_system2',
                'length': (1.0, 'bohr'),
                'mass': (1.0, 'g'),
                'energy': (1.0, 'J'),
                'charge': 'e'
            }
            del settings['unit-system'][i]
            with self.assertRaises(ValueError):
                units_from_settings(settings)


if __name__ == '__main__':
    unittest.main()
