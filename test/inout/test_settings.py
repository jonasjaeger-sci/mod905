# -*- coding: utf-8 -*-
"""a simple test module for parsing a settings input file.

Here we test that we understand the input file and that fail in
a predictable way.
"""
from __future__ import absolute_import
import os
import logging
import tempfile
import unittest
import numpy as np
from pyretis.inout.settings.common import (create_integrator,
                                           create_orderparameter)
from pyretis.inout.settings.createforcefield import (create_potentials,
                                                     create_force_field)
from pyretis.inout.settings.settings import (parse_settings_file,
                                             _parse_raw_section,
                                             _parse_all_raw_sections,
                                             _parse_sections,
                                             settings_to_text)
from pyretis.inout.settings.createsystem import create_initial_positions
from pyretis.core.units import create_conversion_factors, CONVERT
from pyretis.forcefield.potentials import (PairLennardJonesCut,
                                           PairLennardJonesCutnp,
                                           DoubleWellWCA,
                                           DoubleWell,
                                           RectangularWell)
from pyretis.forcefield import PotentialFunction
logging.disable(logging.CRITICAL)


class KeywordParsing(unittest.TestCase):
    """Test the parsing of input settings."""

    def test_parse_file(self):
        """Test that we can parse an input file."""
        here = os.path.abspath(os.path.dirname(__file__))
        inputfile = os.path.join(here, 'settings.rst')
        settings = parse_settings_file(inputfile)
        correct = {}
        correct['system'] = {'units': 'lj',
                             'temperature': 2.0}
        correct['simulation'] = {'task': 'md-nve',
                                 'steps': 100}
        correct['integrator'] = {'class': 'velocityverlet',
                                 'timestep': 0.002}
        correct['particles'] = {'position': {'file': 'initial.gro'},
                                'velocity': {'generate': 'maxwell',
                                             'set-temperature': 2.0,
                                             'momentum': True,
                                             'seed': 0},
                                'mass': {'Ar': 1.0}}
        correct['force field'] = {'description': 'Lennard Jones test'}
        correct['potential'] = [{'class': 'PairLennardJonesCutnp',
                                 'shift': True}]
        for key in correct:
            self.assertIn(key, settings)
            self.assertEqual(correct[key], settings[key])

    def test_keyword_format(self):
        """Test different forms of some simple keywords."""
        test_data = [(["units = 'lj'"], {'units': 'lj'}),  # normal
                     (["unITS = 'lj'"], {'units': 'lj'}),  # case-sensitive?
                     (["units = 'lj' # comment"], {'units': 'lj'}),  # comments
                     (["units = 'lj' # comment units='a'"], {'units': 'lj'}),
                     (["unITS='lj'"], {'units': 'lj'}),  # spacing
                     (["unITS= 'lj'"], {'units': 'lj'}),  # spacing
                     (['units = "lj"'], {'units': 'lj'}),  # " vs '
                     (['units =          "lj"'], {'units': 'lj'}),  # spacing
                     (['units        = "lj"'], {'units': 'lj'}),  # spacing
                     (['units = lj'], {'units': 'lj'}),  # quotations
                     (['units = "lj'], {'units': '"lj'})]  # quotations

        for data in test_data:
            setting = _parse_raw_section(data[0], 'system')
            self.assertEqual(setting, data[1])

    def test_keyword_dict(self):
        """Test some cases when reading dicts"""
        teststr = []
        correct = []
        # simple test:
        teststr.append(['Integrator settings', '-------------------',
                        'class = velocityverlet', 'timestep = 0.002'])
        correct.append({'timestep': 0.002, 'class': 'velocityverlet'})
        # test with comment
        teststr.append(['Integrator settings', '-------------------',
                        'class = velocityverlet', 'timestep = 0.002 # fs'])
        correct.append({'timestep': 0.002, 'class': 'velocityverlet'})
        # test with spaces etc
        teststr.append(['Integrator settings', '-------------------', 'junk',
                        '    ', 'junk = 10',
                        'class =    velocityverlet', 'timestep=0.002'])
        correct.append({'timestep': 0.002, 'junk': 10,
                        'class': 'velocityverlet'})
        teststr.append(['Integrator settings', '-------------------', 'junk',
                        '    ', 'junk = 10',
                        'class =    velocityverlet', 'timestep=0.002'])
        correct.append({'timestep': 0.002, 'class': 'velocityverlet',
                        'junk': 10})
        teststr.append(['Integrator settings', '-------------------',
                        'class = langevin', 'timestep = 0.002',
                        'gamma = 0.3', 'high_friction = False',
                        'seed = 0'])
        correct.append({'timestep': 0.002, 'class': 'langevin',
                        'gamma': 0.3, 'high_friction': False,
                        'seed': 0})
        for tst, corr in zip(teststr, correct):
            raw, _ = _parse_sections(tst)
            setting = _parse_raw_section(raw['integrator'], 'integrator')
            self.assertEqual(setting, corr)

    def test_write_and_read(self):
        """Test that we can parse some data, write it and read it."""
        data = """
Simulation settings
-------------------
task = md-nve
steps = 100

System settings
---------------
dimensions = 2
temperature = 1.0

Integrator settings
-------------------
class = velocityverlet
timestep = 0.002"""
        raw, _ = _parse_sections(data.split('\n'))
        settings = {}
        for key in raw:
            settings[key] = _parse_raw_section(raw[key], key)
        correct = {'integrator': {'timestep': 0.002,
                                  'class': 'velocityverlet'},
                   'system': {'dimensions': 2, 'temperature': 1.0},
                   'simulation': {'task': 'md-nve', 'steps': 100}}
        for key in correct:
            self.assertIn(key, settings)
            self.assertEqual(correct[key], settings[key])
        with tempfile.NamedTemporaryFile() as temp:
            for key in settings:
                txt = settings_to_text(settings[key], key)
                temp.write(txt.encode('utf-8'))
            temp.flush()
            settings_read = parse_settings_file(temp.name, add_default=False)
        self.assertEqual(settings_read, correct)


class KeywordIntegrator(unittest.TestCase):
    """Test the parsing of input settings for integrators."""
    def test_load_external_integrator(self):
        """Test that we can load external python modules for integrators."""
        data = """
Integrator settings
-------------------
class = FooIntegrator
module = foointegrator.py
timestep = 0.5
extra = 100
"""
        correct = {'class': 'FooIntegrator',
                   'module': 'foointegrator.py',
                   'timestep': 0.5,
                   'extra': 100}
        raw, _ = _parse_sections(data.split('\n'))
        settings = {}
        settings['integrator'] = _parse_raw_section(raw['integrator'],
                                                    'integrator')
        self.assertEqual(settings['integrator'], correct)
        # Here we add the exe-path key to the settings to tell
        # pyretis where we are executing from. This is to locate the
        # script we want to run.
        here = os.path.abspath(os.path.dirname(__file__))
        settings['exe-path'] = here
        foointegrator = create_integrator(settings)
        self.assertEqual(foointegrator.delta_t,
                         correct['timestep'])
        self.assertEqual(foointegrator.extra,  # pylint: disable=no-member
                         correct['extra'])

    def test_fail_external_integrator(self):
        """Test that external loads fail in a predicable way."""
        # First test: an integrator that forgot to define a required method.
        test_data, correct = [], []
        test_data.append('Integrator settings\n'
                         '-------------------\n'
                         'class = BarIntegrator\n'
                         'module = foointegrator.py')
        correct.append({'class': 'BarIntegrator',
                        'module': 'foointegrator.py'})

        test_data.append('Integrator settings\n'
                         '-------------------\n'
                         'class = BazIntegrator\n'
                         'module = foointegrator.py')
        correct.append({'class': 'BazIntegrator',
                        'module': 'foointegrator.py'})

        test_data.append('Integrator\n'
                         '----------\n'
                         'module =  dummy')
        correct.append({'module': 'dummy'})

        test_data.append('Integrator\n'
                         '----------\n'
                         'module = dummy\n'
                         'class = dummy')
        correct.append({'module': 'dummy', 'class': 'dummy'})

        here = os.path.abspath(os.path.dirname(__file__))
        for data, corr in zip(test_data, correct):
            raw, _ = _parse_sections(data.split('\n'))
            settings = {}
            settings['integrator'] = _parse_raw_section(raw['integrator'],
                                                        'integrator')
            self.assertEqual(settings['integrator'], corr)
            settings['exe-path'] = here
            args = [settings]
            self.assertRaises(ValueError, create_integrator, *args)


class KeywordOrderPrameter(unittest.TestCase):
    """Test creation of order parameters."""

    def test_load_orderparameter(self):
        """Test loading of external order parameter."""
        data = """
Order parameter
---------------
class = FooOrderParameter
module = fooorderparameter.py
name = Dummy"""
        correct = {'order parameter': {'class': 'FooOrderParameter',
                                       'module': 'fooorderparameter.py',
                                       'name': 'Dummy'}}
        settings = {}
        raw, _ = _parse_sections(data.split('\n'))
        for key in raw:
            settings[key] = _parse_raw_section(raw[key], key)
            self.assertEqual(settings[key], correct[key])
        # Here we add the exe-path key to the settings to tell
        # pyretis where we are executing from. This is to locate the
        # script we want to run.
        here = os.path.abspath(os.path.dirname(__file__))
        settings['exe-path'] = here
        orderp = create_orderparameter(settings)
        self.assertEqual(orderp.name,
                         correct['order parameter']['name'])

        def extra_function(args):
            """Dummy function for testing."""
            return args
        added = orderp.add_orderparameter(extra_function)
        self.assertTrue(added)
        self.assertIs(orderp.extra[0], extra_function)
        # check that we can't add something that's not callable
        added = orderp.add_orderparameter('dummy')
        self.assertFalse(added)

    def test_fail_orderparameter(self):
        """Test that loading external order parameters fails."""
        test_data, correct = [], []
        test_data.append('Order parameter\n'
                         '---------------\n'
                         'class = BarOrderParameter\n'
                         'module = fooorderparameter.py')
        test_data.append('Order parameter\n'
                         '---------------\n'
                         'class = BazOrderParameter\n'
                         'module =  fooorderparameter.py')
        correct.append({'class': 'BarOrderParameter',
                        'module': 'fooorderparameter.py'})
        correct.append({'class': 'BazOrderParameter',
                        'module': 'fooorderparameter.py'})
        here = os.path.abspath(os.path.dirname(__file__))
        sec = 'order parameter'
        for data, corr in zip(test_data, correct):
            raw, _ = _parse_sections(data.split('\n'))
            settings = {}
            settings[sec] = _parse_raw_section(raw[sec], sec)
            self.assertEqual(settings[sec], corr)
            settings['exe-path'] = here
            args = [settings]
            self.assertRaises(ValueError, create_orderparameter, *args)

    def test_create_orderparameter(self):
        """Test that we can create internal order parameters."""
        data = """
Order parameter
---------------
class = OrderParameter
name =  test"""
        correct = {'class': 'OrderParameter', 'name': 'test'}
        settings = {}
        raw, _ = _parse_sections(data.split('\n'))
        sec = 'order parameter'
        settings[sec] = _parse_raw_section(raw[sec], sec)
        self.assertEqual(settings[sec], correct)
        orderp = create_orderparameter(settings)
        self.assertEqual(orderp.name, correct['name'])

        data = """
Order parameter
---------------
class = OrderParameterPosition
name = Position
index = 0
dim = x
periodic = False"""
        correct = {'class': 'OrderParameterPosition',
                   'name': 'Position', 'index': 0,
                   'dim': 'x', 'periodic': False}
        settings = {}
        raw, _ = _parse_sections(data.split('\n'))
        settings[sec] = _parse_raw_section(raw[sec], sec)
        self.assertEqual(settings[sec], correct)
        orderp = create_orderparameter(settings)
        self.assertEqual(orderp.name, correct['name'])
        self.assertEqual(orderp.index, correct['index'])
        self.assertEqual(orderp.dim, 0)
        self.assertEqual(orderp.periodic, correct['periodic'])


class KeywordParticles(unittest.TestCase):
    """Test initialization of particles."""

    def test_lattice(self):
        """Test initialization on a lattice."""
        data = """
Particles
---------
position = {'generate': 'fcc',
            'repeat': [6, 6, 6],
            'lcon': 1.0}

System
------
units = lj"""
        correct = {'particles': {'position': {'generate': 'fcc',
                                              'repeat': [6, 6, 6],
                                              'lcon': 1.0}},
                   'system': {'units': 'lj'}}
        settings = {}
        raw, _ = _parse_sections(data.split('\n'))
        for key in raw:
            settings[key] = _parse_raw_section(raw[key], key)
            self.assertEqual(settings[key], correct[key])
        create_conversion_factors(settings['system']['units'])
        particles, size, _ = create_initial_positions(settings)
        self.assertEqual(size, [[0.0, 6.0], [0.0, 6.0], [0.0, 6.0]])
        self.assertEqual(particles.npart, 4 * 6 * 6 * 6)
        self.assertAlmostEqual(particles.mass[0][0], 1.0)
        self.assertAlmostEqual(particles.imass[0][0], 1.0)
        for i in range(particles.npart):
            self.assertEqual(particles.name[i], 'Ar')

    def test_lattice_type(self):
        """Test initialization on a lattice with types."""
        data = """
Particles
---------
position = {'generate': 'fcc',
            'repeat': [3, 3, 3],
            'lcon': 1.0}
type = [0, 1]

System
------
units = lj"""
        correct = {'particles': {'position': {'generate': 'fcc',
                                              'repeat': [3, 3, 3],
                                              'lcon': 1.0},
                                 'type': [0, 1]},
                   'system': {'units': 'lj'}}
        settings = {}
        raw, _ = _parse_sections(data.split('\n'))
        for key in raw:
            settings[key] = _parse_raw_section(raw[key], key)
            self.assertEqual(settings[key], correct[key])
        particles, _, _ = create_initial_positions(settings)
        for i in range(particles.npart):
            self.assertEqual(particles.name[i], 'Ar')
        for i in range(particles.npart):
            if i == 0:
                self.assertEqual(particles.ptype[i], 0)
            else:
                self.assertEqual(particles.ptype[i], 1)

    def test_lattice_dens(self):
        """Test initialization on a lattice with density set."""
        data = """
Particles
---------
position = {'generate': 'fcc',
            'repeat': [3, 3, 3],
            'density': 0.9}
System
------
units = lj"""
        correct = {'particles': {'position': {'generate': 'fcc',
                                              'repeat': [3, 3, 3],
                                              'density': 0.9}},
                   'system': {'units': 'lj'}}
        settings = {}
        raw, _ = _parse_sections(data.split('\n'))
        for key in raw:
            settings[key] = _parse_raw_section(raw[key], key)
            self.assertEqual(settings[key], correct[key])
        particles, size, _ = create_initial_positions(settings)
        correct_size = []
        lcon = 3.0 * (4.0 / 0.9)**(1.0 / 3.0)
        for _ in settings['particles']['position']['repeat']:
            correct_size.append([0.0, lcon])
        self.assertTrue(np.allclose(size, correct_size))
        for i in range(particles.npart):
            self.assertEqual(particles.name[i], 'Ar')
            self.assertEqual(particles.ptype[i], 0)

    def test_lattice_dens_lcon(self):
        """Test initialization on a lattice with density and lcon set."""
        data = """
Particles
---------
position = {'generate': 'fcc',
            'repeat': [3, 3, 3],
            'density': 0.9,
            'lcon': 1000.}


System
------
units = lj"""
        correct = {'particles': {'position': {'generate': 'fcc',
                                              'repeat': [3, 3, 3],
                                              'density': 0.9,
                                              'lcon': 1000.}},
                   'system': {'units': 'lj'}}
        settings = {}
        raw, _ = _parse_sections(data.split('\n'))
        for key in raw:
            settings[key] = _parse_raw_section(raw[key], key)
            self.assertEqual(settings[key], correct[key])
        _, size, _ = create_initial_positions(settings)
        correct_size = []
        # `lcon` should be replaced by density:
        lcon = 3.0 * (4.0 / 0.9)**(1.0 / 3.0)
        for _ in settings['particles']['position']['repeat']:
            correct_size.append([0.0, lcon])
        self.assertTrue(np.allclose(size, correct_size))

    def test_lattice_and_mass(self):
        """Test initialization on a lattice and setting of masses/types."""
        data = """
Particles
---------
position = {'generate': 'fcc',
            'repeat': [3, 3, 3],
            'lcon': 1.0}
type = [0, 1]
name = ['Ar', 'Kr']
mass = {'Ar': 1.0}

System
------
units = lj"""
        correct = {'particles': {'position': {'generate': 'fcc',
                                              'repeat': [3, 3, 3],
                                              'lcon': 1.},
                                 'type': [0, 1],
                                 'name': ['Ar', 'Kr'],
                                 'mass': {'Ar': 1.0}},
                   'system': {'units': 'lj'}}
        settings = {}
        raw, _ = _parse_sections(data.split('\n'))
        for key in raw:
            settings[key] = _parse_raw_section(raw[key], key)
            self.assertEqual(settings[key], correct[key])
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
        """Test initialization on a lattice with inconsistent dims."""
        data = """
Particles
---------
position = {'generate': 'sq',
            'repeat': [6, 6],
            'lcon': 1.0}
name = ['Ar']
mass = {'Ar': 1.0}

System
------
dimensions = 3
units = lj"""
        correct = {'particles': {'position': {'generate': 'sq',
                                              'repeat': [6, 6],
                                              'lcon': 1.},
                                 'name': ['Ar'],
                                 'mass': {'Ar': 1.0}},
                   'system': {'units': 'lj', 'dimensions': 3}}
        settings = {}
        raw, _ = _parse_sections(data.split('\n'))
        for key in raw:
            settings[key] = _parse_raw_section(raw[key], key)
            self.assertEqual(settings[key], correct[key])
        args = [settings]
        self.assertRaises(ValueError, create_initial_positions, *args)

    def test_file_xyz(self):
        """Test initialization from a XYZ file."""
        data = """
Particles
---------
position = {'file': 'config.xyz'}
System
------
units = lj"""
        correct = {'particles': {'position': {'file': 'config.xyz'}},
                   'system': {'units': 'lj'}}
        settings = {}
        raw, _ = _parse_sections(data.split('\n'))
        for key in raw:
            settings[key] = _parse_raw_section(raw[key], key)
            self.assertEqual(settings[key], correct[key])
        units = settings['system']['units']
        create_conversion_factors(units)
        # Add path to the file for this test:
        settings['exe-path'] = os.path.abspath(os.path.dirname(__file__))
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
        """Test initialization from a GRO file."""
        data = """
Particles
---------
position = {'file': 'config.gro'}
System
------
units = real"""
        correct = {'particles': {'position': {'file': 'config.gro'}},
                   'system': {'units': 'real'}}
        settings = {}
        raw, _ = _parse_sections(data.split('\n'))
        for key in raw:
            settings[key] = _parse_raw_section(raw[key], key)
            self.assertEqual(settings[key], correct[key])
        units = settings['system']['units']
        create_conversion_factors(units)
        # Add path to the file for this test:
        settings['exe-path'] = os.path.abspath(os.path.dirname(__file__))
        particles, size, vel_read = create_initial_positions(settings)
        self.assertTrue(vel_read)
        self.assertTrue(np.allclose(size, [20., 20., 20.]))
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
        vel = []
        for i in particles.vel:
            vel.append(i * CONVERT['velocity'][units, 'nm/ps'])
        vel = np.array(vel)
        correct_vel = np.array([[1.0, 1.0, 1.0], [-1.0, -1.0, -1.0],
                                [2.0, 0.0, -2.0], [-2.0, 1.0, 2.0],
                                [0.0, -1.0, 0.0]])
        self.assertTrue(np.allclose(vel, correct_vel))

    def test_file_xyztab(self):
        """Test initialization from a XYZ file with mass dict."""
        data = """
Particles
---------
position = {'file': 'configtag.xyz'}
type = [0, 0, 0, 1, 1]
mass = {'Ar': 1.,
        'Kr': 2.09767698,
        'Kr2': 2.09767698}

System
------
units = lj
"""
        correct = {'particles': {'position': {'file': 'configtag.xyz'},
                                 'type': [0, 0, 0, 1, 1],
                                 'mass': {'Ar': 1., 'Kr': 2.09767698,
                                          'Kr2': 2.09767698}},
                   'system': {'units': 'lj'}}
        settings = {}
        raw, _ = _parse_sections(data.split('\n'))
        for key in raw:
            settings[key] = _parse_raw_section(raw[key], key)
            self.assertEqual(settings[key], correct[key])
        units = settings['system']['units']
        create_conversion_factors(units)
        # Add path to the file for this test:
        settings['exe-path'] = os.path.abspath(os.path.dirname(__file__))
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


class Keywordforcefield(unittest.TestCase):
    """Test initialization of force fields."""

    def test_forcefield(self):
        """Test initialization of a simple force field."""
        data = """
Force field
-----------
description = My first force field

potential
---------
class = PairLennardJonesCutnp
shift = True
parameter 0 = {'sigma': 1.0, 'epsilon': 1.0, 'rcut': 2.5}"""
        correct = {'force field': {'description': 'My first force field'},
                   'potential': [{'class': 'PairLennardJonesCutnp',
                                  'shift': True,
                                  'parameter': {0: {'sigma': 1.0,
                                                    'epsilon': 1.0,
                                                    'rcut': 2.5}}}]}
        raw, _ = _parse_sections(data.split('\n'))
        settings = _parse_all_raw_sections(raw)
        for key in settings:
            self.assertEqual(settings[key], correct[key])
        forcefield = create_force_field(settings)
        self.assertIsInstance(forcefield.potential[0], PairLennardJonesCutnp)
        self.assertEqual(forcefield.potential[0].shift,
                         correct['potential'][0]['shift'])

    def test_potential_parse(self):
        """Test creation of potentials while parsing input."""
        data = """
Potential
---------
class = PairLennardJonesCut
shift = False
mixing = geometric
parameter 0 = {'sigma': 1.0, 'epsilon': 1.0, 'rcut': 2.5}
parameter 1 = {'sigma': 2.0, 'epsilon': 2.0, 'rcut': 2.5}"""
        correct = {'potential': [{'class': 'PairLennardJonesCut',
                                  'shift': False, 'mixing': 'geometric',
                                  'parameter': {0: {'sigma': 1.0,
                                                    'epsilon': 1.0,
                                                    'rcut': 2.5},
                                                1: {'sigma': 2.0,
                                                    'epsilon': 2.0,
                                                    'rcut': 2.5}}}]}
        raw, _ = _parse_sections(data.split('\n'))
        settings = _parse_all_raw_sections(raw)
        for key in settings:
            self.assertEqual(settings[key], correct[key])
        potentials, pot_par = create_potentials(settings)
        self.assertIsInstance(potentials[0], PairLennardJonesCut)
        self.assertEqual(potentials[0].shift,
                         correct['potential'][0]['shift'])
        # test that we can assign parameters
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
        self.assertAlmostEqual(potparam[(0, 1)]['sigma'],  1.4142135623730951)
        self.assertAlmostEqual(potparam[(0, 1)]['rcut'], 2.5)

    def test_potential_inconsitentdim(self):
        """Test creation of potentials with inconsistent dims."""
        data = """
Potential
---------
class = PairLennardJonesCut
shift = True
parameter 0 = {'sigma': 1.0, 'epsilon': 1.0, 'rcut': 2.5}
#dim = 2

System
------
dimensions = 2"""
        correct = {'system': {'dimensions': 2},
                   'potential': [{'class': 'PairLennardJonesCut',
                                  'shift': True,
                                  'parameter': {0: {'sigma': 1.0,
                                                    'epsilon': 1.0,
                                                    'rcut': 2.5}}}]}
        raw, _ = _parse_sections(data.split('\n'))
        settings = _parse_all_raw_sections(raw)
        for key in settings:
            self.assertEqual(settings[key], correct[key])
        self.assertEqual(settings, correct)
        args = [settings]
        self.assertRaises(ValueError, create_potentials, *args)

    def test_potential_create(self):
        """Test that we can create all potentials."""
        data = """
Potential
---------
class = PairLennardJonesCut

Potential
---------
class = PairLennardJonesCutnp

Potential
---------
class = DoubleWellWCA

Potential
---------
class = DoubleWell

Potential
---------
class = RectangularWell
"""
        all_potentials = [PairLennardJonesCut,
                          PairLennardJonesCutnp,
                          DoubleWellWCA,
                          DoubleWell,
                          RectangularWell]
        raw, _ = _parse_sections(data.split('\n'))
        settings = _parse_all_raw_sections(raw)
        potentials, _ = create_potentials(settings)
        for pot, pot_input in zip(potentials, all_potentials):
            self.assertIsInstance(pot, pot_input)

    def test_ext_potential(self):
        """Test creation of potentials while parsing input from externals."""
        data = """
Potential
---------
class = FooPotential
module = foopotential.py
parameter a = 2.0"""
        correct = {'potential': [{'class': 'FooPotential',
                                  'module': 'foopotential.py',
                                  'parameter': {'a': 2.0}}]}
        raw, _ = _parse_sections(data.split('\n'))
        settings = _parse_all_raw_sections(raw)
        for key in settings:
            self.assertEqual(settings[key], correct[key])
        self.assertEqual(settings, correct)
        # add path for testing:
        settings['exe-path'] = os.path.abspath(os.path.dirname(__file__))
        potentials, pot_param = create_potentials(settings)
        self.assertIsInstance(potentials[0], PotentialFunction)
        self.assertAlmostEqual(potentials[0].params['a'], 0.0)
        for pot, pot_param in zip(potentials, pot_param):
            pot.set_parameters(pot_param)
        self.assertAlmostEqual(potentials[0].params['a'], 2.0)

    def test_ext_potentialfail(self):
        """Test failure of external potential creation."""
        data = """
Potential
---------
class = BarPotential
module = foopotential.py
parameter a = 2.0"""
        correct = {'potential': [{'class': 'BarPotential',
                                  'module': 'foopotential.py',
                                  'parameter': {'a': 2.0}}]}
        raw, _ = _parse_sections(data.split('\n'))
        settings = _parse_all_raw_sections(raw)
        for key in settings:
            self.assertEqual(settings[key], correct[key])
        self.assertEqual(settings, correct)
        settings['exe-path'] = os.path.abspath(os.path.dirname(__file__))
        args = [settings]
        self.assertRaises(ValueError, create_potentials, *args)

    def test_complicated_input(self):
        """Test that we can read 'complex' force field input."""
        data = """
Force field
-----------
description = My force field mix

Potential
---------
class = PairLennardJonesCutnp
shift = True
parameter 0 = {'sigma': 1.0, 'epsilon': 1.0, 'rcut': 2.5}

Potential
---------
class = DoubleWellWCA
parameter types = [(0, 0)]
parameter rzero = 1.122462048309373
parameter height = 6.0
parameter width = 0.25

Potential
---------
class = FooPotential
module = foopotential.py
parameter a = 10.0"""
        correct = {'force field': {'description': 'My force field mix'},
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
        raw, _ = _parse_sections(data.split('\n'))
        settings = _parse_all_raw_sections(raw)
        for key in settings:
            self.assertEqual(settings[key], correct[key])
        self.assertEqual(settings, correct)
        settings['exe-path'] = os.path.abspath(os.path.dirname(__file__))
        forcefield = create_force_field(settings)
        self.assertEqual(len(forcefield.potential), 3)
        self.assertIsInstance(forcefield.potential[0], PairLennardJonesCutnp)
        self.assertIsInstance(forcefield.potential[1], DoubleWellWCA)
        self.assertIsInstance(forcefield.potential[2], PotentialFunction)


if __name__ == '__main__':
    unittest.main()
