# -*- coding: utf-8 -*-
"""A simple test module for parsing a settings input file.

Here we test that we understand the input file and that fail in
a predictable way.
"""
import os
import logging
import tempfile
import unittest
from pyretis.inout.settings.common import create_integrator
from pyretis.inout.settings.common import create_orderparameter
from pyretis.inout.settings.settings import parse_settings_file
from pyretis.inout.settings.settings import parse_settings
from pyretis.inout.settings.settings import settings_to_text
logging.disable(logging.CRITICAL)


class KeywordTest(unittest.TestCase):
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
        # test with junk:
        teststr.append("""integrator = {'class': 'velocityverlet',
                                        'timestep': 0.002}and here is some junk
                                        more junk""")
        correct.append({'integrator': {'timestep': 0.002,
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

    def test_load_external_integrator(self):
        """Test that we can load external python modules for integrators."""
        data = """integrator = {'class': 'FooIntegrator',
                                'module': 'foointegrator',
                                'args': [0.5],
                                'kwargs': {'parameter': 100}}"""
        correct = {'integrator': {'class': 'FooIntegrator',
                                  'module': 'foointegrator',
                                  'args': [0.5],
                                  'kwargs': {'parameter': 100}}}
        settings = parse_settings(data.split('\n'), add_default=False)
        self.assertEqual(settings, correct)
        foointegrator = create_integrator(settings)
        self.assertEqual(foointegrator.delta_t,
                         correct['integrator']['args'][0])
        self.assertEqual(foointegrator.parameter,
                         correct['integrator']['kwargs']['parameter'])

    def test_fail_external_integrator(self):
        """Test that external loads fail in a predicable way."""
        data = """integrator = {'class': 'BarIntegrator',
                                'module': 'foointegrator',}"""
        correct = {'integrator': {'class': 'BarIntegrator',
                                  'module': 'foointegrator'}}
        settings = parse_settings(data.split('\n'), add_default=False)
        self.assertEqual(settings, correct)
        args = [settings]
        self.assertRaises(ValueError, create_integrator, *args)
        # test for another integrator that defines a self.integration_step,
        # on __init__
        data = """integrator = {'class': 'BazIntegrator',
                                'module': 'foointegrator',}"""
        correct = {'integrator': {'class': 'BazIntegrator',
                                  'module': 'foointegrator'}}
        settings = parse_settings(data.split('\n'), add_default=False)
        self.assertEqual(settings, correct)
        args = [settings]
        self.assertRaises(ValueError, create_integrator, *args)
        # test for a case where we forgot to input the 'class'
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

    def test_load_orderparameter(self):
        """Test loading of external order parameter."""
        data = """orderparameter = {'class': 'FooOrderParameter',
                                    'module': 'fooorderparameter',
                                    'args': ['Dummy']}"""
        correct = {'orderparameter': {'class': 'FooOrderParameter',
                                      'module': 'fooorderparameter',
                                      'args': ['Dummy']}}
        settings = parse_settings(data.split('\n'), add_default=False)
        self.assertEqual(settings, correct)
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
                                    'module': 'fooorderparameter'}"""
        correct = {'orderparameter': {'class': 'BarOrderParameter',
                                      'module': 'fooorderparameter'}}
        settings = parse_settings(data.split('\n'), add_default=False)
        self.assertEqual(settings, correct)
        args = [settings]
        self.assertRaises(ValueError, create_orderparameter, *args)
        data = """orderparameter = {'class': 'BazOrderParameter',
                                    'module': 'fooorderparameter'}"""
        correct = {'orderparameter': {'class': 'BazOrderParameter',
                                      'module': 'fooorderparameter'}}
        settings = parse_settings(data.split('\n'), add_default=False)
        self.assertEqual(settings, correct)
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


if __name__ == '__main__':
    unittest.main()
