# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""A test module for flux analysis."""
import logging
import unittest
import os
import pickle
import numpy as np
from pyretis.analysis.flux_analysis import analyse_flux
from pyretis.inout.writers import prepare_load
from pyretis.inout.settings import SECTIONS
logging.disable(logging.CRITICAL)


HERE = os.path.abspath(os.path.dirname(__file__))


class FluxTest(unittest.TestCase):
    """Test that we can analyse for initial flux."""

    def test_flux_analysis(self):
        """Test the flux analysis."""
        filename = os.path.join(HERE, 'cross.txt')
        data = prepare_load('cross', filename, required=True)
        settings = {
            'simulation': {'endcycle': 250000, 'interfaces': [-0.9]},
            'engine': {'timestep': 0.002},
        }
        settings['analysis'] = SECTIONS['analysis']

        correct_file = os.path.join(HERE, 'flux-results.dat')
        for i in data:
            results = analyse_flux(i['data'], settings)
            break
        correct_data = {}
        with open(correct_file, 'rb') as infile:
            correct_data = pickle.load(infile)
        for key0 in ('eff_cross', 'ncross', 'neffcross',
                     'flux', 'runflux', 'interfaces', 'cross_time',
                     'neffc/nc', 'pMD', '1-p', 'teffMD', 'corrMD'):
            self.assertTrue(key0 in correct_data)
            self.assertTrue(key0 in results)
            for i, j in zip(correct_data[key0], results[key0]):
                self.assertTrue(np.allclose(i, j))
        self.assertAlmostEqual(correct_data['totalcycle'],
                               results['totalcycle'])
        for key, val in correct_data['times'].items():
            self.assertAlmostEqual(val, results['times'][key])
        for data1, data2 in zip(correct_data['errflux'],
                                results['errflux']):
            for i, j in zip(data1, data2):
                self.assertTrue(np.allclose(i, j))


if __name__ == '__main__':
    unittest.main()
