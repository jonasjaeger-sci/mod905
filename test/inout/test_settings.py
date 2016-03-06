# -*- coding: utf-8 -*-
"""A simple test module for parsing a settings input file.

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
                                             parse_settings,
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
        inputfile = os.path.join(here, 'settings.txt')
        settings = parse_settings_file(inputfile)
        correct_settings = {'units': 'lj',
                            'task': 'md-nve',
                            'integrator': {'class': 'velocityverlet',
                                           'timestep': 0.002},
                            'endcycle': 100,
                            'temperature': 2.0,
                            'particles-position': {'file': 'initial.gro'},
                            'particles-velocity': {'generate': 'maxwell',
                                                   'set-temperature': 2.0,
                                                   'momentum': True,
                                                   'seed': 0},
                            'particles-mass': {'Ar': 1.0},
                            'forcefield': {'desc': 'Lennard Jones test'},
                            'potentials': {'class': 'PairLennardJonesCutnp',
                                           'shift': True}}
        for key in correct_settings:
            self.assertIn(key, settings)
            self.assertEqual(correct_settings[key], settings[key])

    def test_keyword_format(self):
        """Test different forms of some simple keywords."""
        test_data = [(["units = 'lj'"], {'units': 'lj'}),  # normal
                     (["unITS = 'lj'"], {'units': 'lj'}),  # case-sensitive?
                     (["units = 'lj' # comment"], {'units': 'lj'}),  # comments
                     (["units = 'lj' # comment units='a'"], {'units': 'lj'}),
                     (["# comment units='a'"], {}),  # comments
                     (["unITS='lj'"], {'units': 'lj'}),  # spacing
                     (["unITS= 'lj'"], {'units': 'lj'}),  # spacing
                     (['units = "lj"'], {'units': 'lj'}),  # " vs '
                     (['units =          "lj"'], {'units': 'lj'}),  # spacing
                     (['units        = "lj"'], {'units': 'lj'}),  # spacing
                     (['units = lj'], {'units': 'lj'}),  # quotations
                     (['units = "lj'], {'units': '"lj'})]  # quotations

        for data in test_data:
            setting = parse_settings(data[0], add_default=False)
            self.assertEqual(setting, data[1])

    def test_keyword_dict(self):
        """Test some cases when reading dicts"""
        teststr = []
        correct = []
        # simple test:
        teststr.append("""integrator = {'class': 'velocityverlet',
                                        'timestep': 0.002}""")
        correct.append({'integrator': {'timestep': 0.002,
                                       'class': 'velocityverlet'}})
        # test with comment
        teststr.append("""integrator = {'class': 'velocityverlet', # comment
                                        'timestep': 0.002}""")
        correct.append({'integrator': {'timestep': 0.002,
                                       'class': 'velocityverlet'}})
        # test with quotes
        teststr.append("""integrator = {'class': 'velocityverlet', # comment
                                        'timestep': "0.002"}""")
        correct.append({'integrator': {'timestep': '0.002',
                                       'class': 'velocityverlet'}})
        # test format
        teststr.append("""integrator = {
                                        'class': 'velocityverlet',
                                        'timestep': "0.002"}
                                        """)
        correct.append({'integrator': {'timestep': '0.002',
                                       'class': 'velocityverlet'}})
        # test format
        teststr.append("""integrator =
                           {
                                        'class': 'velocityverlet',
                                        'timestep': "0.002"}""")
        correct.append({'integrator': {'timestep': '0.002',
                                       'class': 'velocityverlet'}})

        for tst, corr in zip(teststr, correct):
            setting = parse_settings(tst.split('\n'), add_default=False)
            self.assertEqual(setting, corr)

    def test_write_and_read(self):
        """Test that we can parse some data, write it and read it."""
        data = """task = 'md-nve'
                  integrator = {'class': 'velocityverlet', 'timestep': 0.002}
                  endcycle = 100
                  temperature = 2.0"""
        settings = parse_settings(data.split('\n'), add_default=False)
        correct = {'integrator': {'timestep': 0.002,
                                  'class': 'velocityverlet'},
                   'temperature': 2.0, 'task': 'md-nve', 'endcycle': 100}
        with tempfile.NamedTemporaryFile() as temp:
            for dump in settings_to_text(settings):
                temp.write(dump.encode('utf-8'))
            temp.flush()
            settings_read = parse_settings_file(temp.name, add_default=False)
        self.assertEqual(settings_read, correct)


class KeywordIntegrator(unittest.TestCase):
    """Test the parsing of input settings for integrators."""
    def test_load_external_integrator(self):
        """Test that we can load external python modules for integrators."""
        data = """integrator = {'class': 'FooIntegrator',
                                'module': 'foointegrator.py',
                                'args': [0.5],
                                'kwargs': {'parameter': 100}}"""
        correct = {'integrator': {'class': 'FooIntegrator',
                                  'module': 'foointegrator.py',
                                  'args': [0.5],
                                  'kwargs': {'parameter': 100}}}
        settings = parse_settings(data.split('\n'), add_default=False)
        self.assertEqual(settings, correct)
        # Here we add the exe-path key to the settings to tell
        # pyretis where we are executing from. This is to locate the
        # script we want to run.
        here = os.path.abspath(os.path.dirname(__file__))
        settings['exe-path'] = here
        foointegrator = create_integrator(settings)
        self.assertEqual(foointegrator.delta_t,
                         correct['integrator']['args'][0])
        self.assertEqual(foointegrator.parameter,  # pylint: disable=no-member
                         correct['integrator']['kwargs']['parameter'])

    def test_fail_external_integrator(self):
        """Test that external loads fail in a predicable way."""
        data = """integrator = {'class': 'BarIntegrator',
                                'module': 'foointegrator.py',}"""
        correct = {'integrator': {'class': 'BarIntegrator',
                                  'module': 'foointegrator.py'}}
        settings = parse_settings(data.split('\n'), add_default=False)
        self.assertEqual(settings, correct)
        # Here we add the exe-path key to the settings to tell
        # pyretis where we are executing from. This is to locate the
        # script we want to run.
        here = os.path.abspath(os.path.dirname(__file__))
        settings['exe-path'] = here
        args = [settings]
        self.assertRaises(ValueError, create_integrator, *args)
        # Test for another integrator that defines a self.integration_step,
        # on __init__
        data = """integrator = {'class': 'BazIntegrator',
                                'module': 'foointegrator.py',}"""
        correct = {'integrator': {'class': 'BazIntegrator',
                                  'module': 'foointegrator.py'}}
        settings = parse_settings(data.split('\n'), add_default=False)
        self.assertEqual(settings, correct)
        settings['exe-path'] = here
        args = [settings]
        self.assertRaises(ValueError, create_integrator, *args)
        # Test for a case where we forgot to input the 'class'
        data = "integrator = {'module': 'dummy'}"
        correct = {'integrator': {'module': 'dummy'}}
        settings = parse_settings(data.split('\n'), add_default=False)
        self.assertEqual(settings, correct)
        args = [settings]
        self.assertRaises(ValueError, create_integrator, *args)
        # test for a case where we can't find the module:
        data = "integrator = {'module': 'dummy', 'class': 'dummy'}"
        correct = {'integrator': {'module': 'dummy', 'class': 'dummy'}}
        settings = parse_settings(data.split('\n'), add_default=False)
        self.assertEqual(settings, correct)
        args = [settings]
        self.assertRaises(ValueError, create_integrator, *args)


class KeywordOrderPrameter(unittest.TestCase):
    """Test creation of order parameters."""

    def test_load_orderparameter(self):
        """Test loading of external order parameter."""
        data = """orderparameter = {'class': 'FooOrderParameter',
                                    'module': 'fooorderparameter.py',
                                    'args': ['Dummy']}"""
        correct = {'orderparameter': {'class': 'FooOrderParameter',
                                      'module': 'fooorderparameter.py',
                                      'args': ['Dummy']}}
        settings = parse_settings(data.split('\n'), add_default=False)
        self.assertEqual(settings, correct)
        # Here we add the exe-path key to the settings to tell
        # pyretis where we are executing from. This is to locate the
        # script we want to run.
        here = os.path.abspath(os.path.dirname(__file__))
        settings['exe-path'] = here
        orderp = create_orderparameter(settings)
        self.assertEqual(orderp.name,
                         correct['orderparameter']['args'][0])

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
        data = """orderparameter = {'class': 'BarOrderParameter',
                                    'module': 'fooorderparameter.py'}"""
        correct = {'orderparameter': {'class': 'BarOrderParameter',
                                      'module': 'fooorderparameter.py'}}
        settings = parse_settings(data.split('\n'), add_default=False)
        self.assertEqual(settings, correct)
        # Here we add the exe-path key to the settings to tell
        # pyretis where we are executing from. This is to locate the
        # script we want to run.
        here = os.path.abspath(os.path.dirname(__file__))
        settings['exe-path'] = here
        args = [settings]
        self.assertRaises(ValueError, create_orderparameter, *args)
        data = """orderparameter = {'class': 'BazOrderParameter',
                                    'module': 'fooorderparameter.py'}"""
        correct = {'orderparameter': {'class': 'BazOrderParameter',
                                      'module': 'fooorderparameter.py'}}
        settings = parse_settings(data.split('\n'), add_default=False)
        self.assertEqual(settings, correct)
        settings['exe-path'] = here
        args = [settings]
        self.assertRaises(ValueError, create_orderparameter, *args)

    def test_create_orderparameter(self):
        """Test that we can create internal order parameters."""
        data = """orderparameter = {'class': 'OrderParameter',
                                    'name': 'test'}"""
        correct = {'orderparameter': {'class': 'OrderParameter',
                                      'name': 'test'}}
        settings = parse_settings(data.split('\n'), add_default=False)
        self.assertEqual(settings, correct)
        orderp = create_orderparameter(settings)
        self.assertEqual(orderp.name, correct['orderparameter']['name'])

        data = """orderparameter = {'class': 'OrderParameterPosition',
                                    'name': 'Position', 'index': 0,
                                    'dim': 'x', 'periodic': False}"""
        correct = {'orderparameter': {'class': 'OrderParameterPosition',
                                      'name': 'Position', 'index': 0,
                                      'dim': 'x', 'periodic': False}}
        settings = parse_settings(data.split('\n'), add_default=False)
        self.assertEqual(settings, correct)
        orderp = create_orderparameter(settings)
        self.assertEqual(orderp.name, correct['orderparameter']['name'])
        self.assertEqual(orderp.index, correct['orderparameter']['index'])
        self.assertEqual(orderp.dim, 0)
        self.assertEqual(orderp.periodic,
                         correct['orderparameter']['periodic'])

        data = """orderparameter = {'class': 'OrderParameterParse',
                                    'name': 'Position', 'orderp': 'sin(x[0])',
                                    'ordervel': 'cos(x[0])'}"""
        correct = {'orderparameter': {'class': 'OrderParameterParse',
                                      'name': 'Position',
                                      'orderp': 'sin(x[0])',
                                      'ordervel': 'cos(x[0])'}}
        settings = parse_settings(data.split('\n'), add_default=False)
        self.assertEqual(settings, correct)
        orderp = create_orderparameter(settings)

        data = """orderparameter = {'class': 'OrderParameterParse',
                                    'name': 'Position',
                                    'orderp': 'sin(pbc_x(x[0]))',
                                    'ordervel': 'cos(x[0])'}"""
        correct = {'orderparameter': {'class': 'OrderParameterParse',
                                      'name': 'Position',
                                      'orderp': 'sin(pbc_x(x[0]))',
                                      'ordervel': 'cos(x[0])'}}
        settings = parse_settings(data.split('\n'), add_default=False)
        self.assertEqual(settings, correct)
        orderp = create_orderparameter(settings)


class KeywordParticles(unittest.TestCase):
    """Test initialization of particles."""

    def test_lattice(self):
        """Test initialization on a lattice."""
        data = """particles-position = {'generate': 'fcc',
                                        'repeat': [6, 6, 6],
                                        'lcon': 1.0}
                  units = lj"""
        correct = {'particles-position': {'generate': 'fcc',
                                          'repeat': [6, 6, 6],
                                          'lcon': 1.0},
                   'units': 'lj'}
        settings = parse_settings(data.split('\n'), add_default=False)
        self.assertEqual(settings, correct)
        create_conversion_factors(settings['units'])
        particles, size, _ = create_initial_positions(settings)
        self.assertEqual(size, [[0.0, 6.0], [0.0, 6.0], [0.0, 6.0]])
        self.assertEqual(particles.npart, 4 * 6 * 6 * 6)
        self.assertAlmostEqual(particles.mass[0][0], 1.0)
        self.assertAlmostEqual(particles.imass[0][0], 1.0)
        for i in range(particles.npart):
            self.assertEqual(particles.name[i], 'Ar')

    def test_lattice_type(self):
        """Test initialization on a lattice with types."""
        data = """particles-position = {'generate': 'fcc',
                                        'repeat': [3, 3, 3],
                                        'lcon': 1.0}
                  particles-type = [0, 1]
                  units = lj"""
        correct = {'particles-position': {'generate': 'fcc',
                                          'repeat': [3, 3, 3],
                                          'lcon': 1.0},
                   'particles-type': [0, 1],
                   'units': 'lj'}
        settings = parse_settings(data.split('\n'), add_default=False)
        self.assertEqual(settings, correct)
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
        data = """particles-position = {'generate': 'fcc',
                                        'repeat': [3, 3, 3],
                                        'density': 0.9}
                  units = lj"""
        correct = {'particles-position': {'generate': 'fcc',
                                          'repeat': [3, 3, 3],
                                          'density': 0.9},
                   'units': 'lj'}
        settings = parse_settings(data.split('\n'), add_default=False)
        self.assertEqual(settings, correct)
        particles, size, _ = create_initial_positions(settings)
        correct_size = []
        lcon = 3.0 * (4.0 / 0.9)**(1.0 / 3.0)
        for _ in settings['particles-position']['repeat']:
            correct_size.append([0.0, lcon])
        self.assertTrue(np.allclose(size, correct_size))
        for i in range(particles.npart):
            self.assertEqual(particles.name[i], 'Ar')
            self.assertEqual(particles.ptype[i], 0)

    def test_lattice_dens_lcon(self):
        """Test initialization on a lattice with density and lcon set."""
        data = """particles-position = {'generate': 'fcc',
                                        'repeat': [3, 3, 3],
                                        'density': 0.9,
                                        'lcon': 1000.}
                  units = lj"""
        correct = {'particles-position': {'generate': 'fcc',
                                          'repeat': [3, 3, 3],
                                          'density': 0.9,
                                          'lcon': 1000.},
                   'units': 'lj'}
        settings = parse_settings(data.split('\n'), add_default=False)
        self.assertEqual(settings, correct)
        _, size, _ = create_initial_positions(settings)
        correct_size = []
        # `lcon` should be replaced by density:
        lcon = 3.0 * (4.0 / 0.9)**(1.0 / 3.0)
        for _ in settings['particles-position']['repeat']:
            correct_size.append([0.0, lcon])
        self.assertTrue(np.allclose(size, correct_size))

    def test_lattice_and_mass(self):
        """Test initialization on a lattice and setting of masses/types."""
        data = """particles-position = {'generate': 'fcc',
                                        'repeat': [3, 3, 3],
                                        'lcon': 1.0}
                  particles-type = [0, 1]
                  particles-name = ['Ar', 'Kr']
                  particles-mass = {'Ar': 1.0}
                  units = lj"""
        correct = {'particles-position': {'generate': 'fcc',
                                          'repeat': [3, 3, 3],
                                          'lcon': 1.0},
                   'particles-type': [0, 1],
                   'particles-name': ['Ar', 'Kr'],
                   'particles-mass': {'Ar': 1.0},
                   'units': 'lj'}
        settings = parse_settings(data.split('\n'), add_default=False)
        self.assertEqual(settings, correct)
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
        data = """particles-position = {'generate': 'sq',
                                        'repeat': [6, 6],
                                        'lcon': 1.0}
                  dimensions = 3
                  units = lj"""
        correct = {'particles-position': {'generate': 'sq',
                                          'repeat': [6, 6],
                                          'lcon': 1.0},
                   'dimensions': 3,
                   'units': 'lj'}
        settings = parse_settings(data.split('\n'), add_default=False)
        self.assertEqual(settings, correct)
        args = [settings]
        self.assertRaises(ValueError, create_initial_positions, *args)

    def test_file_xyz(self):
        """Test initialization from a XYZ file."""
        data = """particles-position = {'file': 'config.xyz'}
                  units = lj"""
        correct = {'particles-position': {'file': 'config.xyz'},
                   'units': 'lj'}
        settings = parse_settings(data.split('\n'), add_default=False)
        self.assertEqual(settings, correct)
        create_conversion_factors(settings['units'])
        # Add path to the file for this test:
        settings['exe-path'] = os.path.abspath(os.path.dirname(__file__))
        particles, size, vel_read = create_initial_positions(settings)
        self.assertFalse(vel_read)
        self.assertIsNone(size)
        pos = particles.pos * CONVERT['length'][settings['units'], 'A']
        correct_pos = np.array([[0.0, 0.0, 0.0], [0.5, 0.5, 0.5],
                                [0.5, 0.5, 0.0], [0.5, 0.0, 0.5],
                                [0.0, 0.5, 0.5]])
        self.assertTrue(np.allclose(pos, correct_pos))
        pequal = all([i == j for i, j in zip(particles.ptype,
                                             [0, 1, 2, 2, 2])])
        self.assertTrue(pequal)
        nequal = all([i == j for i, j in zip(particles.name,
                                             ['Ba', 'Hf', 'O', 'O', 'O'])])
        self.assertTrue(nequal)
        masses = []
        for i in particles.mass:
            masses.append(i[0] * CONVERT['mass'][settings['units'], 'g/mol'])
        self.assertTrue(np.allclose(masses, [137.327, 178.49, 15.9994,
                                             15.9994, 15.9994]))

    def test_file_gro(self):
        """Test initialization from a GRO file."""
        data = """particles-position = {'file': 'config.gro'}
                  units = real"""
        correct = {'particles-position': {'file': 'config.gro'},
                   'units': 'real'}
        settings = parse_settings(data.split('\n'), add_default=False)
        self.assertEqual(settings, correct)
        create_conversion_factors(settings['units'])
        # Add path to the file for this test:
        settings['exe-path'] = os.path.abspath(os.path.dirname(__file__))
        particles, size, vel_read = create_initial_positions(settings)
        self.assertTrue(vel_read)
        self.assertTrue(np.allclose(size, [20., 20., 20.]))
        #self.assertIsNone(size)
        pos = particles.pos * CONVERT['length'][settings['units'], 'A']
        correct_pos = np.array([[0.0, 0.0, 0.0], [0.5, 0.5, 0.5],
                                [0.5, 0.5, 0.0], [0.5, 0.0, 0.5],
                                [0.0, 0.5, 0.5]])
        self.assertTrue(np.allclose(pos, correct_pos))

        testeq = all([i == j for i, j in zip(particles.ptype,
                                             [0, 1, 2, 2, 2])])
        self.assertTrue(testeq)

        testeq = all([i == j for i, j in zip(particles.name,
                                             ['Ba', 'Hf', 'O', 'O', 'O'])])
        self.assertTrue(testeq)
        masses = []
        for i in particles.mass:
            masses.append(i[0] * CONVERT['mass'][settings['units'], 'g/mol'])
        self.assertTrue(np.allclose(masses, [137.327, 178.49, 15.9994,
                                             15.9994, 15.9994]))
        vel = []
        for i in particles.vel:
            vel.append(i * CONVERT['velocity'][settings['units'], 'nm/ps'])
        vel = np.array(vel)
        correct_vel = np.array([[1.0, 1.0, 1.0], [-1.0, -1.0, -1.0],
                                [2.0, 0.0, -2.0], [-2.0, 1.0, 2.0],
                                [0.0, -1.0, 0.0]])
        self.assertTrue(np.allclose(vel, correct_vel))

    def test_file_xyztab(self):
        """Test initialization from a XYZ file with mass dict."""
        data = """particles-position = {'file': 'configtag.xyz'}
                  particles-type = [0, 0, 0, 1, 1]
                  particles-mass = {'Ar': 1., 'Kr': 2.09767698,
                                    'Kr2': 2.09767698}
                  units = lj"""
        correct = {'particles-position': {'file': 'configtag.xyz'},
                   'particles-type': [0, 0, 0, 1, 1],
                   'particles-mass': {'Ar': 1., 'Kr': 2.09767698,
                                      'Kr2': 2.09767698},
                   'units': 'lj'}
        settings = parse_settings(data.split('\n'), add_default=False)
        self.assertEqual(settings, correct)
        create_conversion_factors(settings['units'])
        # Add path to the file for this test:
        settings['exe-path'] = os.path.abspath(os.path.dirname(__file__))
        particles, size, vel_read = create_initial_positions(settings)
        self.assertFalse(vel_read)
        self.assertIsNone(size)
        pequal = all([i == j for i, j in zip(particles.ptype,
                                             [0, 0, 0, 1, 1])])
        self.assertTrue(pequal)
        nequal = all([i == j for i, j in zip(particles.name,
                                             ['Ar', 'Ar', 'Ar',
                                              'Kr', 'Kr2'])])
        self.assertTrue(nequal)
        masses = []
        for i in particles.mass:
            masses.append(i[0] * CONVERT['mass'][settings['units'], 'g/mol'])
        self.assertTrue(np.allclose(masses, [39.948, 39.948, 39.948,
                                             83.798, 83.798]))


class Keywordforcefield(unittest.TestCase):
    """Test initialization of force fields."""

    def test_forcefield(self):
        """Test initialization of a simple force field."""
        data = """forcefield = {'desc': 'My first force field'}
                   potentials = [{'class': 'PairLennardJonesCutnp',
                                  'shift': True}]
                   potential-parameters = [{0: {'sigma': 1.0, 'epsilon': 1.0,
                                                'rcut': 2.5}}]"""
        correct = {'forcefield': {'desc': 'My first force field'},
                   'potentials': [{'class': 'PairLennardJonesCutnp',
                                   'shift': True}],
                   'potential-parameters': [{0: {'sigma': 1.0, 'epsilon': 1.0,
                                                 'rcut': 2.5}}]}
        settings = parse_settings(data.split('\n'), add_default=False)
        self.assertEqual(settings, correct)
        forcefield = create_force_field(settings)
        self.assertIsInstance(forcefield.potential[0], PairLennardJonesCutnp)

    def test_potential_parse(self):
        """Test creation of potentials while parsing input."""
        data = """potentials = [{'class': 'PairLennardJonesCut',
                                 'shift': True}]
                  potential-parameters = [{0: {'sigma': 1.0, 'epsilon': 1.0,
                                               'rcut': 2.5}}]"""
        correct = {'potentials': [{'class': 'PairLennardJonesCut',
                                   'shift': True}],
                   'potential-parameters': [{0: {'sigma': 1.0, 'epsilon': 1.0,
                                                 'rcut': 2.5}}]}
        settings = parse_settings(data.split('\n'), add_default=False)
        self.assertEqual(settings, correct)
        potentials = create_potentials(settings)
        self.assertIsInstance(potentials[0], PairLennardJonesCut)
        # test that we can assign parameters
        for pot, params in zip(potentials, settings['potential-parameters']):
            pot.set_parameters(params)
        self.assertAlmostEqual(potentials[0].params[(0, 0)]['epsilon'], 1.0)
        self.assertAlmostEqual(potentials[0].params[(0, 0)]['sigma'], 1.0)
        self.assertAlmostEqual(potentials[0].params[(0, 0)]['rcut'], 2.5)

    def test_potential_create(self):
        """Test that we can create all potentials."""
        all_potentials = [('PairLennardJonesCut', PairLennardJonesCut),
                          ('PairLennardJonesCutnp', PairLennardJonesCutnp),
                          ('DoubleWellWCA', DoubleWellWCA),
                          ('DoubleWell', DoubleWell),
                          ('RectangularWell', RectangularWell)]
        settings = {'potentials': []}
        for pot in all_potentials:
            settings['potentials'].append({'class': pot[0]})
        potentials = create_potentials(settings)
        for pot, pot_input in zip(potentials, all_potentials):
            self.assertIsInstance(pot, pot_input[1])

    def test_ext_potential(self):
        """Test creation of potentials while parsing input from externals."""
        data = """potentials = [{'class': 'FooPotential',
                                 'module': 'foopotential.py'}]
                  potential-parameters = [{'a': 2.0}]"""
        correct = {'potentials': [{'class': 'FooPotential',
                                   'module': 'foopotential.py'}],
                   'potential-parameters': [{'a': 2.0}]}
        settings = parse_settings(data.split('\n'), add_default=False)
        self.assertEqual(settings, correct)
        # add path for testing:
        settings['exe-path'] = os.path.abspath(os.path.dirname(__file__))
        potentials = create_potentials(settings)
        self.assertIsInstance(potentials[0], PotentialFunction)
        self.assertAlmostEqual(potentials[0].params['a'], 0.0)
        for pot, pot_param in zip(potentials,
                                  settings['potential-parameters']):
            pot.set_parameters(pot_param)
        self.assertAlmostEqual(potentials[0].params['a'], 2.0)

    def test_ext_potentialfail(self):
        """Test failure of external potential creation."""
        data = """potentials = [{'class': 'BarPotential',
                                 'module': 'foopotential.py'}]
                  potential-parameters = [{'a': 2.0}]"""
        correct = {'potentials': [{'class': 'BarPotential',
                                   'module': 'foopotential.py'}],
                   'potential-parameters': [{'a': 2.0}]}
        settings = parse_settings(data.split('\n'), add_default=False)
        self.assertEqual(settings, correct)
        settings['exe-path'] = os.path.abspath(os.path.dirname(__file__))
        args = [settings]
        self.assertRaises(ValueError, create_potentials, *args)

    def test_complicated_input(self):
        """Test that we can read 'complex' force field input."""
        data = """forcefield = {'desc': 'My force field mix'}
                  potentials = [{'class': 'PairLennardJonesCutnp',
                                 'shift': True},
                                {'class': 'DoubleWellWCA'},
                                {'class': 'FooPotential',
                                 'module': 'foopotential.py'}]
                  potential-parameters = [{0: {'sigma': 1.0, 'epsilon': 1.0,
                                               'rcut': 2.5}},
                                          {'types': [(0, 0)],
                                           'rzero': 1.122462048309373,
                                           'height': 6.0, 'width': 0.25},
                                          {'a': 10.0}]"""
        correct = {'forcefield': {'desc': 'My force field mix'},
                   'potentials': [{'class': 'PairLennardJonesCutnp',
                                   'shift': True},
                                  {'class': 'DoubleWellWCA'},
                                  {'class': 'FooPotential',
                                   'module': 'foopotential.py'}],
                   'potential-parameters': [{0: {'sigma': 1.0, 'epsilon': 1.0,
                                                 'rcut': 2.5}},
                                            {'types': [(0, 0)],
                                             'rzero': 1.0 * (2.0**(1.0/6.0)),
                                             'height': 6.0, 'width': 0.25},
                                            {'a': 10.0}]}
        settings = parse_settings(data.split('\n'), add_default=False)
        self.assertEqual(settings, correct)
        settings['exe-path'] = os.path.abspath(os.path.dirname(__file__))
        forcefield = create_force_field(settings)
        self.assertEqual(len(forcefield.potential), 3)
        self.assertIsInstance(forcefield.potential[0], PairLennardJonesCutnp)
        self.assertIsInstance(forcefield.potential[1], DoubleWellWCA)
        self.assertIsInstance(forcefield.potential[2], PotentialFunction)


if __name__ == '__main__':
    unittest.main()
