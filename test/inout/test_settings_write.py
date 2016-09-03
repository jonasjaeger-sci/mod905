# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""Test parsing from a settings input file.

Here we test that we parse the input file correctly and also that
we fail in predictable ways.
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
                                             write_settings_file)
logging.disable(logging.CRITICAL)

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
    raw, _ = _parse_sections(data.split('\n'))
    settings = _parse_all_raw_sections(raw)
    for key in settings:
        test.assertEqual(settings[key], correct[key])
    return settings
 

class KeywordParsing(unittest.TestCase):
    """Test the parsing of input settings."""

    def test_parse_file(self):
        """Test that we can parse an input file."""
        here = os.path.abspath(os.path.dirname(__file__))
        inputfile = os.path.join(here, 'settings.rst')
        settings = parse_settings_file(inputfile)
        correct = {}
        correct['system'] = {'units': 'lj',
                             'dimensions': 3,
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
        correct['forcefield'] = {'description': 'Lennard Jones test'}
        correct['potential'] = [{'class': 'PairLennardJonesCutnp',
                                 'shift': True}]
        for key in correct:
            self.assertIn(key, settings)
            self.assertEqual(correct[key], settings[key])
        write_settings_file(settings, 'tmp.rst', backup=False)

    def test_complicated_input(self):
        """Test that we can read 'complex' force field input."""
        data = """
Forcefield
----------
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
        settings['exe-path'] = os.path.abspath(os.path.dirname(__file__))
        forcefield = create_force_field(settings)
        self.assertEqual(len(forcefield.potential), 3)
        write_settings_file(settings, 'tmp2.rst', backup=False)

if __name__ == '__main__':
    unittest.main()

