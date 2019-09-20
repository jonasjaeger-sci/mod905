# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test parsing from a settings input file.

Here we test that we parse the input file correctly and also that
we fail in predictable ways.
"""
import logging
import numpy as np
import os
import tempfile
import unittest
from io import StringIO
from pyretis.core.common import big_fat_comparer
from pyretis.core.units import create_conversion_factors, CONVERT
from pyretis.engines import Verlet, VelocityVerlet, Langevin
from pyretis.forcefield import PotentialFunction
from pyretis.forcefield.potentials import (
    DoubleWell,
    DoubleWellWCA,
    PairLennardJonesCut,
    PairLennardJonesCutnp,
    RectangularWell
)
from pyretis.inout.settings import (
    copy_settings,
    parse_settings_file,
    settings_to_text,
    write_settings_file,
    _check_for_bullshitt,
    _clean_settings,
    _parse_raw_section,
    _parse_all_raw_sections,
    _parse_sections,
)
from pyretis.orderparameter import (
    Angle,
    Dihedral,
    Distance,
    Distancevel,
    DistanceVelocity,
    OrderParameter,
    Position,
    PositionVelocity,
    Velocity,
)
from pyretis.inout.setup.common import (
    create_engine,
    create_orderparameter
)
from pyretis.inout.setup.createforcefield import (
    create_potentials,
    create_force_field
)
from pyretis.inout.setup.createsystem import create_initial_positions
from unittest.mock import patch
logging.disable(logging.CRITICAL)


LOCAL_DIR = os.path.abspath(os.path.dirname(__file__))


def _read_raw_settings(filename):
    """Read raw settings from a local file.

    Parameters
    ----------
    filename : string
        The file we are going to read.

    Return
    ------
    out : string
        The data read from the file.
    """
    inputfile = os.path.join(LOCAL_DIR, filename)
    data = None
    with open(inputfile, 'r') as indata:
        data = indata.read()
    return data


def _test_correct_parsing(test, data, correct):
    """Helper method to test that we correctly parse settings.

    Parameters
    ----------
    test : object like unittest.TestCase
        The test that should pass or fail.
    data : string
        Raw data to be parsed.
    correct : dict
        The correct data.

    Returns
    -------
    out : dict
        The parsed settings.
    """
    raw = _parse_sections(data.split('\n'))
    settings = _parse_all_raw_sections(raw)
    for key in settings:
        test.assertEqual(settings[key], correct[key])
    return settings


class KeywordParsing(unittest.TestCase):
    """Test the parsing of input settings."""

    def test_parse_file(self):
        """Test that we can parse an input file."""
        inputfile = os.path.join(LOCAL_DIR, 'settings.rst')
        settings = parse_settings_file(inputfile)
        correct = {
            'heading': {'text': ('Molecular dynamics example settings\n'
                                 '===================================\n'
                                 'this is a simple test system to check '
                                 'the input statements are correct')},
            'system': {'units': 'lj',
                       'dimensions': 3,  # Added by default.
                       'temperature': 2.0},
            'simulation': {'task': 'md-nve',
                           'steps': 100},
            'engine': {'class': 'velocityverlet',
                       'timestep': 0.002},
            'particles': {'position': {'file': 'initial.gro'},
                          'velocity': {'generate': 'maxwell',
                                       'temperature': 2.0,
                                       'momentum': True,
                                       'seed': 0},
                          'mass': {'Ar': 1.0}},
            'forcefield': {'description': 'Lennard Jones test'},
            'potential': [{'class': 'PairLennardJonesCutnp',
                           'shift': True}],
        }
        for key in correct:
            self.assertIn(key, settings)
            self.assertEqual(correct[key], settings[key])

    def test_keyword_format(self):
        """Test different forms of some simple keywords."""
        test_data = [
            (["units = 'lj'"], {'units': 'lj'}),  # Normal input
            (["unITS = 'lj'"], {'units': 'lj'}),  # Test case-sensitive?
            (["units = 'lj' # comment"], {'units': 'lj'}),  # Add a comment.
            (["units = 'lj' # comment units='a'"], {'units': 'lj'}),
            (["unITS='lj'"], {'units': 'lj'}),  # Test spacing.
            (["unITS= 'lj'"], {'units': 'lj'}),  # Test spacing.
            (['units = "lj"'], {'units': 'lj'}),  # Test " vs '.
            (['units =          "lj"'], {'units': 'lj'}),  # Test spacing.
            (['units        = "lj"'], {'units': 'lj'}),  # Test spacing.
            (['units = lj'], {'units': 'lj'}),  # Test quotations.
            (['units = "lj'], {'units': '"lj'})  # Test quotations.
        ]

        for data in test_data:
            setting = _parse_raw_section(data[0], 'system')
            self.assertEqual(setting, data[1])

    def test_keyword_dict(self):
        """Test some cases when reading dicts."""
        teststr = []
        correct = []
        # First, some simple input:
        teststr.append(['Engine settings',
                        '---------------',
                        'class = velocityverlet', 'timestep = 0.002'])
        correct.append({'timestep': 0.002, 'class': 'velocityverlet'})
        # Test input with comment(s):
        teststr.append(['Engine settings',
                        '---------------',
                        'class = velocityverlet', 'timestep = 0.002 # fs'])
        correct.append({'timestep': 0.002, 'class': 'velocityverlet'})
        # Test with white space, etc.:
        teststr.append(['Engine settings',
                        '---------------', 'junk',
                        '    ', 'junk = 10',
                        'class =    velocityverlet', 'timestep=0.002'])
        correct.append({'timestep': 0.002, 'junk': 10,
                        'class': 'velocityverlet'})
        teststr.append(['Engine settings',
                        '---------------', 'junk',
                        '    ', 'junk = 10',
                        'class =    velocityverlet', 'timestep=0.002'])
        correct.append({'timestep': 0.002, 'class': 'velocityverlet',
                        'junk': 10})
        teststr.append(['Engine settings',
                        '---------------',
                        'class = langevin', 'timestep = 0.002',
                        'gamma = 0.3', 'high_friction = False',
                        'seed = 0'])
        correct.append({'timestep': 0.002, 'class': 'langevin',
                        'gamma': 0.3, 'high_friction': False,
                        'seed': 0})

        for tst, corr in zip(teststr, correct):
            raw = _parse_sections(tst)
            setting = _parse_raw_section(raw['engine'], 'engine')
            self.assertEqual(setting, corr)

    def test_write_and_read(self):
        """Test that we can parse some data, write it and read it."""
        data = _read_raw_settings('settings-rw-test.rst')
        correct = {'engine': {'timestep': 0.002,
                              'class': 'velocityverlet'},
                   'system': {'dimensions': 2, 'temperature': 1.0},
                   'simulation': {'task': 'md-nve', 'steps': 100}}
        raw = _parse_sections(data.split('\n'))
        settings = _parse_all_raw_sections(raw)
        settings = _test_correct_parsing(self, data, correct)
        with tempfile.NamedTemporaryFile() as temp:
            txt = settings_to_text(settings)
            temp.write(txt.encode('utf-8'))
            temp.flush()
            settings_read = parse_settings_file(temp.name, add_default=False)
        self.assertEqual(settings_read, correct)

    def test_ignore_section(self):
        """Test that we ignore unknown sections."""
        data = _read_raw_settings('settings-unknown-section.rst')
        correct = {'engine': {'timestep': 0.002,
                              'class': 'velocityverlet'}}
        settings = _test_correct_parsing(self, data, correct)
        self.assertNotIn('junk', settings)


class KeywordEngine(unittest.TestCase):
    """Test the parsing of input settings for engines."""

    def test_load_external_engine(self):
        """Test that we can load external python modules for engines."""
        data = _read_raw_settings('external-engine.rst')
        correct = {'engine': {'class': 'FooEngine',
                              'module': 'fooengine.py',
                              'timestep': 0.5,
                              'extra': 100}}
        settings = _test_correct_parsing(self, data, correct)
        # Here we add the exe-path key to the settings to tell
        # PyRETIS where we are executing from. This is to locate the
        # script we want to run.
        settings['simulation'] = {'exe-path': LOCAL_DIR}
        fooengine = create_engine(settings)
        self.assertEqual(fooengine.timestep,
                         correct['engine']['timestep'])
        self.assertEqual(fooengine.extra,  # pylint: disable=no-member
                         correct['engine']['extra'])

    def test_fail_external_engine(self):
        """Test that external loads fail in a predicable way."""
        # First test: an engine that forgot to define a required method.
        test_data, correct = [], []
        test_data.append('---------------\n'
                         'Engine settings\n'
                         '---------------\n'
                         'class = BarEngine\n'
                         'module = fooengine.py')
        correct.append({'engine': {'class': 'BarEngine',
                                   'module': 'fooengine.py'}})
        test_data.append('Engine settings\n'
                         '---------------\n'
                         'class = BazEngine\n'
                         'module = fooengine.py')
        correct.append({'engine': {'class': 'BazEngine',
                                   'module': 'fooengine.py'}})
        test_data.append('Engine\n'
                         '------\n'
                         'module =  dummy')
        correct.append({'engine': {'module': 'dummy'}})
        test_data.append('Engine\n'
                         '------\n'
                         'module = dummy\n'
                         'class = dummy')
        correct.append({'engine': {'module': 'dummy', 'class': 'dummy'}})

        for data, corr in zip(test_data, correct):
            settings = _test_correct_parsing(self, data, corr)
            settings['simulation'] = {'exe-path': LOCAL_DIR}
            with self.assertRaises(ValueError):
                create_engine(settings)

    def test_internal_engine(self):
        """Test that we can load all internal engines."""
        klass, test_data, correct = [], [], []
        klass.append(Verlet)
        test_data.append('Engine\n'
                         '------\n'
                         'class = Verlet\n'
                         'timestep = 0.5')
        correct.append({'engine': {'class': 'Verlet', 'timestep': 0.5}})
        klass.append(VelocityVerlet)
        test_data.append('Engine\n'
                         '------\n'
                         'class = VelocityVerlet\n'
                         'timestep = 0.314\n'
                         'desc = Test VV engine')
        correct.append({'engine': {'class': 'VelocityVerlet',
                                   'timestep': 0.314,
                                   'desc': 'Test VV engine'}})
        klass.append(Langevin)
        test_data.append('Engine\n'
                         '------\n'
                         'class = Langevin\n'
                         'timestep = 0.1\n'
                         'gamma = 2.718281828\n'
                         'seed = 101\n'
                         'high_friction = True')
        correct.append({'engine': {'class': 'Langevin',
                                   'timestep': 0.1,
                                   'gamma': 2.718281828,
                                   'seed': 101,
                                   'high_friction': True}})
        klass.append(Langevin)
        test_data.append('Engine\n'
                         '------\n'
                         'class = Langevin\n'
                         'timestep = 0.25\n'
                         'gamma = 2.718281828\n'
                         'seed = 11\n'
                         'high_friction = False')
        correct.append({'engine': {'class': 'Langevin',
                                   'timestep': 0.25,
                                   'gamma': 2.718281828,
                                   'seed': 11,
                                   'high_friction': False}})
        for data, corr, cls in zip(test_data, correct, klass):
            settings = _test_correct_parsing(self, data, corr)
            engine = create_engine(settings)
            self.assertIsInstance(engine, cls)
            self.assertAlmostEqual(engine.timestep,
                                   corr['engine']['timestep'])
            for key, val in corr['engine'].items():
                if hasattr(engine, key):
                    self.assertAlmostEqual(getattr(engine, key), val)


class KeywordOrderPrameter(unittest.TestCase):
    """Test creation of order parameters."""

    def test_load_orderparameter(self):
        """Test loading of external order parameter."""
        data = [
            'Orderparameter',
            '--------------',
            'class = FooOrderParameter',
            'module = fooorderparameter.py',
            'name = Dummy'
        ]
        correct = {
            'orderparameter': {
                'class': 'FooOrderParameter',
                'module': 'fooorderparameter.py',
                'name': 'Dummy'
            }
        }
        settings = _test_correct_parsing(self, '\n'.join(data), correct)
        # Here we add the exe-path key to the settings to tell
        # PyRETIS where we are executing from. This is to locate the
        # script we want to run.
        settings['simulation'] = {'exe-path': LOCAL_DIR}
        orderp = create_orderparameter(settings)
        self.assertEqual(
            correct['orderparameter']['class'],
            orderp.__class__.__name__,
        )

    def test_fail_orderparameter(self):
        """Test that loading external order parameters fails."""
        test_data, correct = [], []
        test_data.append('Orderparameter\n'
                         '--------------\n'
                         'class = BarOrderParameter\n'
                         'module = fooorderparameter.py')
        correct.append(
            {'orderparameter': {'class': 'BarOrderParameter',
                                'module': 'fooorderparameter.py'}}
        )
        for data, corr in zip(test_data, correct):
            settings = _test_correct_parsing(self, data, corr)
            settings['simulation'] = {'exe-path': LOCAL_DIR}
            with self.assertRaises(ValueError):
                create_orderparameter(settings)

    def test_create_orderparameter(self):
        """Test that we can create internal order parameters."""
        test_data = _read_raw_settings('internal-order.rst')
        klass = [
            OrderParameter,
            Position,
            Velocity,
            PositionVelocity,
            Distance,
            Distancevel,
            DistanceVelocity,
            Angle,
            Dihedral,
        ]
        correct = {
            'orderparameter': {
                'class': 'OrderParameter',
                'name': 'test'
            },
            'collective-variable':
                [
                    {
                        'class': 'Position',
                        'name': 'Position',
                        'index': 0, 'dim': 'x',
                        'periodic': False
                    },
                    {
                        'class': 'Velocity',
                        'name': 'Velocity',
                        'index': 0, 'dim': 'x',
                    },
                    {
                        'class': 'PositionVelocity',
                        'name': 'PositionVelocity',
                        'index': 0, 'dim': 'x',
                        'periodic': True
                    },
                    {
                        'class': 'Distance',
                        'name': 'My distance',
                        'index': (100, 101), 'periodic': False
                    },
                    {
                        'class': 'Distancevel',
                        'name': 'My distance Velocity',
                        'index': (102, 103), 'periodic': True
                    },
                    {
                        'class': 'DistanceVelocity',
                        'name': 'My distance Position Velocity',
                        'index': (1001, 1002), 'periodic': True
                    },
                    {
                        'class': 'Angle',
                        'name': 'Angle',
                        'index': (1001, 1002, 1003), 'periodic': True
                    },
                    {
                        'class': 'Dihedral',
                        'name': 'Dihedral',
                        'index': (1001, 1002, 1003, 1004), 'periodic': True
                    },
                ],
        }
        raw = _parse_sections(test_data.split('\n'))
        settings = _parse_all_raw_sections(raw)
        # Compare for order parameter:
        for key, val in settings['orderparameter'].items():
            self.assertEqual(val, correct['orderparameter'][key])
        for setting, corr in zip(settings['collective-variable'],
                                 correct['collective-variable']):
            for key, val in setting.items():
                self.assertEqual(val, corr[key])
        order = create_orderparameter(settings)
        for i, j in zip(order.order_parameters, klass):
            self.assertIsInstance(i, j)


class KeywordParticles(unittest.TestCase):
    """Test initialisation of particles."""

    def test_lattice(self):
        """Test initialisation on a lattice."""
        data = _read_raw_settings('settings-lattice.rst')
        correct = {'particles': {'position': {'generate': 'fcc',
                                              'repeat': [6, 6, 6],
                                              'lcon': 1.0}},
                   'system': {'units': 'lj'}}
        settings = _test_correct_parsing(self, data, correct)
        create_conversion_factors(settings['system']['units'])
        particles, size, _ = create_initial_positions(settings)
        correct_size = {'low': np.array([0., 0., 0.]),
                        'high': np.array([6., 6., 6.])}
        for key, val in correct_size.items():
            self.assertTrue(np.allclose(size[key], val))
        self.assertEqual(particles.npart, 4 * 6 * 6 * 6)
        self.assertAlmostEqual(particles.mass[0][0], 1.0)
        self.assertAlmostEqual(particles.imass[0][0], 1.0)
        for i in range(particles.npart):
            self.assertEqual(particles.name[i], 'Ar')

    def test_lattice_type(self):
        """Test initialisation on a lattice with types."""
        data = _read_raw_settings('settings-lattice-type.rst')
        correct = {'particles': {'position': {'generate': 'fcc',
                                              'repeat': [3, 3, 3],
                                              'lcon': 1.0},
                                 'type': [0, 1]},
                   'system': {'units': 'lj'}}
        settings = _test_correct_parsing(self, data, correct)
        particles, _, _ = create_initial_positions(settings)
        for i in range(particles.npart):
            self.assertEqual(particles.name[i], 'Ar')
        for i in range(particles.npart):
            if i == 0:
                self.assertEqual(particles.ptype[i], 0)
            else:
                self.assertEqual(particles.ptype[i], 1)

    def test_lattice_dens(self):
        """Test initialisation on a lattice with density set."""
        data = _read_raw_settings('settings-lattice-dens.rst')
        correct = {'particles': {'position': {'generate': 'fcc',
                                              'repeat': [3, 3, 3],
                                              'density': 0.9}},
                   'system': {'units': 'lj'}}
        settings = _test_correct_parsing(self, data, correct)
        particles, size, _ = create_initial_positions(settings)
        correct_size = []
        lcon = 3.0 * (4.0 / 0.9)**(1.0 / 3.0)
        for _ in settings['particles']['position']['repeat']:
            correct_size.append([0.0, lcon])
        correct_size = np.array(correct_size)
        self.assertTrue(np.allclose(size['low'], correct_size[:, 0]))
        self.assertTrue(np.allclose(size['high'], correct_size[:, 1]))
        for i in range(particles.npart):
            self.assertEqual(particles.name[i], 'Ar')
            self.assertEqual(particles.ptype[i], 0)

    def test_lattice_dens_lcon(self):
        """Test initialisation on a lattice with density and lcon set."""
        data = _read_raw_settings('settings-lattice-dens-lcon.rst')
        correct = {'particles': {'position': {'generate': 'fcc',
                                              'repeat': [3, 3, 3],
                                              'density': 0.9,
                                              'lcon': 1000.}},
                   'system': {'units': 'lj'}}
        settings = _test_correct_parsing(self, data, correct)
        _, size, _ = create_initial_positions(settings)
        correct_size = []
        # `lcon` should be replaced by density:
        lcon = 3.0 * (4.0 / 0.9)**(1.0 / 3.0)
        for _ in settings['particles']['position']['repeat']:
            correct_size.append([0.0, lcon])
        correct_size = np.array(correct_size)
        self.assertTrue(np.allclose(size['low'], correct_size[:, 0]))
        self.assertTrue(np.allclose(size['high'], correct_size[:, 1]))

    def test_lattice_and_mass(self):
        """Test initialisation on a lattice and setting of masses/types."""
        data = _read_raw_settings('settings-lattice-mass.rst')
        correct = {'particles': {'position': {'generate': 'fcc',
                                              'repeat': [3, 3, 3],
                                              'lcon': 1.},
                                 'type': [0, 1],
                                 'name': ['Ar', 'Kr'],
                                 'mass': {'Ar': 1.0}},
                   'system': {'units': 'lj'}}
        settings = _test_correct_parsing(self, data, correct)
        particles, _, _ = create_initial_positions(settings)
        for i in range(particles.npart):
            if i == 0:
                self.assertEqual(particles.ptype[i], 0)
                self.assertEqual(particles.name[i], 'Ar')
                self.assertAlmostEqual(particles.mass[i][0], 1.0)
            else:
                self.assertEqual(particles.ptype[i], 1)
                self.assertEqual(particles.name[i], 'Kr')
                self.assertAlmostEqual(particles.mass[i][0], 2.09767698)

    def test_inconsistent_dimlattice(self):
        """Test initialisation on a lattice with inconsistent dimensions."""
        data = _read_raw_settings('settings-lattice-dims.rst')
        correct = {'particles': {'position': {'generate': 'sq',
                                              'repeat': [6, 6],
                                              'lcon': 1.},
                                 'name': ['Ar'],
                                 'mass': {'Ar': 1.0}},
                   'system': {'units': 'lj', 'dimensions': 3}}
        settings = _test_correct_parsing(self, data, correct)
        args = [settings]
        self.assertRaises(ValueError, create_initial_positions, *args)

    def test_file_xyz(self):
        """Test initialisation from a XYZ file."""
        data = _read_raw_settings('initial-xyz2.rst')
        correct = {'particles': {'position': {'file': 'config.xyz'}},
                   'system': {'units': 'lj'}}
        settings = _test_correct_parsing(self, data, correct)
        units = settings['system']['units']
        create_conversion_factors(units)
        # Add path to the file for this test:
        settings['simulation'] = {'exe-path': LOCAL_DIR}
        particles, size, vel_read = create_initial_positions(settings)
        self.assertFalse(vel_read)
        self.assertIsNone(size)
        pos = particles.pos * CONVERT['length'][units, 'A']
        correct_pos = np.array([[0.0, 0.0, 0.0], [0.5, 0.5, 0.5],
                                [0.5, 0.5, 0.0], [0.5, 0.0, 0.5],
                                [0.0, 0.5, 0.5]])
        self.assertTrue(np.allclose(pos, correct_pos))
        self.assertTrue(all([i == j for i, j in zip(particles.ptype,
                                                    [0, 1, 2, 2, 2])]))
        self.assertTrue(all([i == j for i, j in zip(particles.name,
                                                    ['Ba', 'Hf', 'O',
                                                     'O', 'O'])]))
        masses = []
        for i in particles.mass:
            masses.append(i[0] * CONVERT['mass'][units, 'g/mol'])
        self.assertTrue(np.allclose(masses, [137.327, 178.49, 15.9994,
                                             15.9994, 15.9994]))

    def test_file_gro(self):
        """Test initialisation from a GRO file."""
        data = _read_raw_settings('initial-gro.rst')
        correct = {'particles': {'position': {'file': 'config.gro'}},
                   'system': {'units': 'gromacs'}}
        settings = _test_correct_parsing(self, data, correct)
        # Add path to the file for this test:
        create_conversion_factors(settings['system']['units'])
        settings['simulation'] = {'exe-path': LOCAL_DIR}
        particles, size, vel_read = create_initial_positions(settings)
        self.assertTrue(vel_read)
        self.assertTrue(np.allclose(size['cell'], [2., 2., 2.]))
        correct_pos = np.array([[0., 0., 0.], [0.05, 0.05, 0.05],
                                [0.05, 0.05, 0.], [0.05, 0., 0.05],
                                [0., 0.05, 0.05]])
        self.assertTrue(np.allclose(particles.pos, correct_pos))
        self.assertTrue(all([i == j for i, j in zip(particles.ptype,
                                                    [0, 1, 2, 2, 2])]))
        self.assertTrue(all([i == j for i, j in zip(particles.name,
                                                    ['Ba', 'Hf', 'O',
                                                     'O', 'O'])]))
        self.assertTrue(np.allclose(particles.mass.T,
                                    [137.327, 178.49, 15.9994,
                                     15.9994, 15.9994]))
        correct_vel = np.array([[1.0, 1.0, 1.0], [-1.0, -1.0, -1.0],
                                [2.0, 0.0, -2.0], [-2.0, 1.0, 2.0],
                                [0.0, -1.0, 0.0]])
        self.assertTrue(np.allclose(particles.vel, correct_vel))

    def test_file_xyztab(self):
        """Test initialisation from a XYZ file with mass dict."""
        data = _read_raw_settings('initial-xyz.rst')
        correct = {'particles': {'position': {'file': 'configtag.xyz'},
                                 'type': [0, 0, 0, 1, 1],
                                 'mass': {'Ar': 1., 'Kr': 2.09767698,
                                          'Kr2': 2.09767698}},
                   'system': {'units': 'lj'}}
        settings = _test_correct_parsing(self, data, correct)
        units = settings['system']['units']
        create_conversion_factors(units)
        # Add path to the file for this test:
        settings['simulation'] = {'exe-path': LOCAL_DIR}
        particles, size, vel_read = create_initial_positions(settings)
        self.assertFalse(vel_read)
        self.assertIsNone(size)
        self.assertTrue(all([i == j for i, j in zip(particles.ptype,
                                                    [0, 0, 0, 1, 1])]))
        self.assertTrue(all([i == j for i, j in zip(particles.name,
                                                    ['Ar', 'Ar', 'Ar',
                                                     'Kr', 'Kr2'])]))
        masses = []
        for i in particles.mass:
            masses.append(i[0] * CONVERT['mass'][units, 'g/mol'])
        self.assertTrue(np.allclose(masses, [39.948, 39.948, 39.948,
                                             83.798, 83.798]))


class KeywordForcefield(unittest.TestCase):
    """Test initialisation of force fields."""

    def test_forcefield(self):
        """Test initialisation of a simple force field."""
        data = _read_raw_settings('forcefield-simple.rst')
        correct = {'forcefield': {'description': 'My first force field'},
                   'potential': [{'class': 'PairLennardJonesCutnp',
                                  'shift': True,
                                  'parameter': {0: {'sigma': 1.0,
                                                    'epsilon': 1.0,
                                                    'rcut': 2.5}}}]}
        settings = _test_correct_parsing(self, data, correct)
        forcefield = create_force_field(settings)
        self.assertIsInstance(forcefield.potential[0], PairLennardJonesCutnp)
        self.assertEqual(forcefield.potential[0].shift,
                         correct['potential'][0]['shift'])

    def test_potential_parse(self):
        """Test creation of potentials while parsing input."""
        data = _read_raw_settings('settings-potential1.rst')
        correct = {'potential': [{'class': 'PairLennardJonesCut',
                                  'shift': False, 'mixing': 'geometric',
                                  'parameter': {0: {'sigma': 1.0,
                                                    'epsilon': 1.0,
                                                    'rcut': 2.5},
                                                1: {'sigma': 2.0,
                                                    'epsilon': 2.0,
                                                    'rcut': 2.5}}}]}
        settings = _test_correct_parsing(self, data, correct)
        potentials, pot_par = create_potentials(settings)
        self.assertIsInstance(potentials[0], PairLennardJonesCut)
        self.assertEqual(potentials[0].shift,
                         correct['potential'][0]['shift'])
        # Test that we can assign parameters:
        for pot, params in zip(potentials, pot_par):
            pot.set_parameters(params)
        potparam = potentials[0].params
        self.assertAlmostEqual(potparam[(0, 0)]['epsilon'], 1.0)
        self.assertAlmostEqual(potparam[(0, 0)]['sigma'], 1.0)
        self.assertAlmostEqual(potparam[(0, 0)]['rcut'], 2.5)
        self.assertAlmostEqual(potparam[(1, 1)]['epsilon'], 2.0)
        self.assertAlmostEqual(potparam[(1, 1)]['sigma'], 2.0)
        self.assertAlmostEqual(potparam[(1, 1)]['rcut'], 2.5)
        self.assertAlmostEqual(potparam[(0, 1)]['epsilon'], 1.4142135623730951)
        self.assertAlmostEqual(potparam[(0, 1)]['sigma'], 1.4142135623730951)
        self.assertAlmostEqual(potparam[(0, 1)]['rcut'], 2.5)

    def test_empty_create_potential(self):
        """Test the create potential method."""
        correct = {'potential': [{'class': 'Fake'}]}
        potentials, pot_par = create_potentials(correct)
        for i, j in zip(potentials, pot_par):
            self.assertIsNone(i)
            self.assertIsNone(j)

    def test_potential_inconsitentdim(self):
        """Test creation of potentials with inconsistent dims."""
        data = _read_raw_settings('settings-potential2.rst')
        correct = {'system': {'dimensions': 2},
                   'potential': [{'class': 'PairLennardJonesCut',
                                  'shift': True,
                                  'parameter': {0: {'sigma': 1.0,
                                                    'epsilon': 1.0,
                                                    'rcut': 2.5}}}]}
        settings = _test_correct_parsing(self, data, correct)
        args = [settings]
        self.assertRaises(ValueError, create_potentials, *args)

    def test_potential_create(self):
        """Test that we can create all potentials."""
        data = _read_raw_settings('allpotentials.rst')
        all_potentials = [PairLennardJonesCut,
                          PairLennardJonesCutnp,
                          DoubleWellWCA,
                          DoubleWell,
                          RectangularWell]
        raw = _parse_sections(data.split('\n'))
        settings = _parse_all_raw_sections(raw)
        potentials, _ = create_potentials(settings)
        for pot, pot_input in zip(potentials, all_potentials):
            self.assertIsInstance(pot, pot_input)

    def test_ext_potential(self):
        """Test creation of potentials while parsing input from externals."""
        data = _read_raw_settings('settings-ext-potential.rst')
        correct = {'potential': [{'class': 'FooPotential',
                                  'module': 'foopotential.py',
                                  'parameter': {'a': 2.0}}]}
        settings = _test_correct_parsing(self, data, correct)
        self.assertEqual(settings, correct)
        # Add path for testing:
        settings['simulation'] = {'exe-path': LOCAL_DIR}
        potentials, pot_param = create_potentials(settings)
        self.assertIsInstance(potentials[0], PotentialFunction)
        self.assertAlmostEqual(potentials[0].params['a'], 0.0)
        for pot, pot_param in zip(potentials, pot_param):
            pot.set_parameters(pot_param)
        self.assertAlmostEqual(potentials[0].params['a'], 2.0)

    def test_ext_potentialfail(self):
        """Test failure of external potential creation."""
        data = _read_raw_settings('settings-ext-potential-fail.rst')
        correct = {'potential': [{'class': 'BarPotential',
                                  'module': 'foopotential.py',
                                  'parameter': {'a': 2.0}}]}
        settings = _test_correct_parsing(self, data, correct)
        self.assertEqual(settings, correct)
        settings['simulation'] = {'exe-path': LOCAL_DIR}
        args = [settings]
        self.assertRaises(ValueError, create_potentials, *args)

    def test_complicated_input(self):
        """Test that we can read 'complex' force field input."""
        data = _read_raw_settings('forcefield.rst')
        correct = {'forcefield': {'description': 'My force field mix'},
                   'potential': [{'class': 'PairLennardJonesCutnp',
                                  'shift': True,
                                  'parameter': {0: {'sigma': 1.0,
                                                    'epsilon': 1.0,
                                                    'rcut': 2.5}}},
                                 {'class': 'DoubleWellWCA',
                                  'parameter': {'types': [(0, 0)],
                                                'rzero': 1. * (2.**(1./6.)),
                                                'height': 6.0, 'width': 0.25}},
                                 {'class': 'FooPotential',
                                  'module': 'foopotential.py',
                                  'parameter': {'a': 10.0}}]}
        settings = _test_correct_parsing(self, data, correct)
        self.assertEqual(settings, correct)
        settings['simulation'] = {'exe-path': LOCAL_DIR}
        forcefield = create_force_field(settings)
        self.assertEqual(len(forcefield.potential), 3)
        self.assertIsInstance(forcefield.potential[0], PairLennardJonesCutnp)
        self.assertIsInstance(forcefield.potential[1], DoubleWellWCA)
        self.assertIsInstance(forcefield.potential[2], PotentialFunction)

    def test_check_for_bullshitt(self):
        """Test that _check for bullshitt finds the inconsistent settings."""
        # Insufficient interfaces for TIS/RETIS:
        settings = {'simulation': {'task': 'tis', 'interfaces': [1]}}
        with patch('sys.stdout', new=StringIO()):
            with self.assertRaises(ValueError) as err:
                _check_for_bullshitt(settings)
        self.assertTrue('Insufficient number of interfaces for tis' in
                        str(err.exception))
        # No references:
        settings = {'simulation': {'task': 'tis', 'interfaces': [1, 2, 3]},
                    'ensemble': [{'gino': 'strada'}, {'interface': 1},
                                 {'interface': 3}]}
        with patch('sys.stdout', new=StringIO()):
            with self.assertRaises(ValueError) as err:
                _check_for_bullshitt(settings)
        self.assertTrue('An ensemble has been introduced without references'
                        ' (interface in ensemble settings)' in
                        str(err.exception))

        settings = {'simulation': {'task': 'tis', 'interfaces': [1, 2, 3]},
                    'ensemble': [{'ensemble_number': 0}, {'interface': 2},
                                 {'interface': 3}]}
        _check_for_bullshitt(settings)

        # Not Sorted interfaces:
        settings = {'simulation': {'task': 'tis', 'interfaces': [2, 5, 1]}}
        with patch('sys.stdout', new=StringIO()):
            with self.assertRaises(ValueError) as err:
                _check_for_bullshitt(settings)
        self.assertTrue('Interface lambda positions in the simulation entry '
                        'are NOT sorted (small to large)' in
                        str(err.exception))

        # Wrong interfaces:
        settings = {'simulation': {'task': 'tis', 'interfaces': [1, 2, 3]},
                    'ensemble': [{'interface': 1}, {'interface': 2},
                                 {'interface': 4}]}
        with patch('sys.stdout', new=StringIO()):
            with self.assertRaises(ValueError) as err:
                _check_for_bullshitt(settings)
        self.assertTrue('An ensemble with declared interface is not present '
                        'in the simulation interface list' in
                        str(err.exception))

    def test_too_many(self):
        """Test what happens when we add too many potentials."""
        settings = {
            'forcefield': {'description': 'My force field mix'},
            'potential': [],
        }
        for i in range(66):
            settings['potential'].append(
                {'class': 'DoubleWellWCA',
                 'parameter': {'types': [(i, i)],
                               'rzero': 1. * (2.**(1./6.))}}
            )
        txt = settings_to_text(settings)
        raw = _parse_sections(txt.split('\n'))
        settings2 = _parse_all_raw_sections(raw)
        for i, pot in enumerate(settings2['potential']):
            self.assertEqual(pot['parameter']['types'][0], (i, i))

        # Looking for troubles:
        settings['ensemble'] = []
        for i in range(66):
            settings['ensemble'].append(
                {'potential': [{'class': 'DoubleWellWCA',
                                'parameter': {'types': [(i, i)],
                                              'rzero': 16}}]})

        txt = settings_to_text(settings)
        raw = _parse_sections(txt.split('\n'))
        settings3 = _parse_all_raw_sections(raw)
        hidden = settings3['ensemble'][10]['potential'][0]
        self.assertEqual(hidden['parameter']['rzero'], 16)

    def test_copy_settings(self):
        """Test that the copy method works as intended."""
        inputfile = os.path.join(LOCAL_DIR, 'settings-retis.rst')
        settings = parse_settings_file(inputfile)
        settings2 = copy_settings(settings)
        for key, val in settings.items():
            self.assertTrue(key in settings2)
            self.assertEqual(val, settings2[key])

    def test_settings_to_txt(self):
        """Test the settings to text in more detail."""
        inputfile = os.path.join(LOCAL_DIR, 'settings-retis.rst')
        settings = parse_settings_file(inputfile)
        txt = settings_to_text(settings)
        to_find = ['RETIS EXAMPLE FOR TESTING',
                   'TIS', 'RETIS']
        found = [False for _ in to_find]
        for lines in txt.split('\n'):
            for i, key in enumerate(to_find):
                if found[i]:
                    continue
                if lines.startswith(key):
                    found[i] = True
        self.assertTrue(all(found))

    def test_write_settings(self):
        """Test that we can write settings to a file."""
        inputfile = os.path.join(LOCAL_DIR, 'settings-retis.rst')
        settings = parse_settings_file(inputfile)
        with tempfile.TemporaryDirectory() as tempdir:
            out_file = os.path.join(tempdir, '_pyretis_settings_temp.rst')
            # Check that we can write a file:
            write_settings_file(settings, out_file)
            self.assertTrue(os.path.isfile(out_file))
            # Check that we can write a file and backup:
            write_settings_file(settings, out_file, backup=True)
            out_file2 = '{}_000'.format(out_file)
            with open(out_file, 'r') as fileh:
                raw_sections = _parse_sections(fileh)
            settings2 = _parse_all_raw_sections(raw_sections)
            self.assertTrue(os.path.isfile(out_file2))
        self.assertTrue(big_fat_comparer(settings, settings2, hard=True))

    def test_clean_settings(self):
        """Test that we can clean settings."""
        inputfile = os.path.join(LOCAL_DIR, 'settings-retis.rst')
        settings = parse_settings_file(inputfile)
        settings['junk'] = {'some': 'junk'}
        settings['system']['junk'] = 'this is junk'
        settings['box'] = []
        settings_c = _clean_settings(settings)
        self.assertFalse('junk' in settings_c)
        self.assertFalse('junk' in settings_c['system'])
        self.assertFalse('box' in settings_c)


class KeywordEnsemble(unittest.TestCase):
    """Test ensemble and setting keywords."""

    def test_fill_up_tis_and_retis_settings(self):
        """Test if ensembles are correctly generated."""
        inputfile = os.path.join(LOCAL_DIR, 'settings-retis.rst')
        settings = parse_settings_file(inputfile)

        self.assertEqual(settings['ensemble'][2]
                         ['collective-variable'][3]['something']
                         ['unexpected'], [1, 2, 3])
        self.assertEqual(settings['ensemble'][6]['particles']
                         ['velocity']['fantasy'], 'game')
        self.assertEqual(settings['ensemble'][6]['particles']['velocity']
                         ['generate'], 'Priapo')
        self.assertEqual(settings['ensemble'][5]['retis'], settings['retis'])
        self.assertEqual(settings['ensemble'][2]['box'], settings['box'])
        self.assertTrue(settings['ensemble'][0]['tis']['ensemble_number'] !=
                        settings['ensemble'][1]['tis']['ensemble_number'])
        self.assertEqual(settings['ensemble'][2]
                         ['collective-variable'][5]['name'], 'Bugno')
        self.assertEqual(settings['ensemble'][2]
                         ['collective-variable'][1]
                         ['position']['nonsense'], 'pineapple_on_pizza')
        self.assertEqual(settings['ensemble'][1]['particles']
                         ['velocity']['generate'], 'maxwell')
        self.assertEqual(len(settings['ensemble']), 8)
        self.assertEqual(settings['simulation']['zero_left'], -99)


if __name__ == '__main__':
    unittest.main()
