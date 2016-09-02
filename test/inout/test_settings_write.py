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
                                             settings_to_text,
                                             write_settings_file)
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
        write_settings_file(settings, 'tmp.rst')
if __name__ == '__main__':
    unittest.main()

