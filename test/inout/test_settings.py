# -*- coding: utf-8 -*-
"""A simple test module for parsing a settings input file.

Here we test that we understand the input file and that fail in
a predictable way.
"""
import os
import logging
import tempfile
import unittest
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
                            'integrator': {'name': 'velocityverlet',
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
        teststr.append("""integrator = {'name': 'velocityverlet',
                                        'timestep': 0.002}""")
        correct.append({'integrator': {'timestep': 0.002,
                                       'name': 'velocityverlet'}})
        # test with comment
        teststr.append("""integrator = {'name': 'velocityverlet', # comment
                                        'timestep': 0.002}""")
        correct.append({'integrator': {'timestep': 0.002,
                                       'name': 'velocityverlet'}})
        # test with quotes
        teststr.append("""integrator = {'name': 'velocityverlet', # comment
                                        'timestep': "0.002"}""")
        correct.append({'integrator': {'timestep': '0.002',
                                       'name': 'velocityverlet'}})
        # test format
        teststr.append("""integrator = {
                                        'name': 'velocityverlet',
                                        'timestep': "0.002"}
                                        """)
        correct.append({'integrator': {'timestep': '0.002',
                                       'name': 'velocityverlet'}})
        # test format
        teststr.append("""integrator =
                           {
                                        'name': 'velocityverlet',
                                        'timestep': "0.002"}""")
        correct.append({'integrator': {'timestep': '0.002',
                                       'name': 'velocityverlet'}})
        # test with junk:
        teststr.append("""integrator = {'name': 'velocityverlet',
                                        'timestep': 0.002}and here is some junk
                                        more junk""")
        correct.append({'integrator': {'timestep': 0.002,
                                       'name': 'velocityverlet'}})

        for tst, corr in zip(teststr, correct):
            setting = parse_settings(tst.split('\n'), add_default=False)
            self.assertEqual(setting, corr)

    def test_write_and_read(self):
        """Test that we can parse some data, write it and read it."""
        data = """task = 'md-nve'
                  integrator = {'name': 'velocityverlet', 'timestep': 0.002}
                  endcycle = 100
                  temperature = 2.0"""
        settings = parse_settings(data.split('\n'), add_default=False)
        correct = {'integrator': {'timestep': 0.002, 'name': 'velocityverlet'},
                   'temperature': 2.0, 'task': 'md-nve', 'endcycle': 100}
        with tempfile.NamedTemporaryFile() as temp:
            for dump in settings_to_text(settings):
                temp.write(dump.encode('utf-8'))
            temp.flush()
            settings_read = parse_settings_file(temp.name, add_default=False)
        self.assertEqual(settings_read, correct)


if __name__ == '__main__':
    unittest.main()
