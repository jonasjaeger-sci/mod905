# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""A test module for path ensemble analysis."""
import logging
import unittest
import os
from pyretis.core.pathensemble import PathEnsemble
from pyretis.core.path import Path
from pyretis.analysis.path_analysis import (
    analyse_path_ensemble,
    analyse_path_ensemble_object,
    match_probabilities,
    retis_flux,
    retis_rate,
)
from pyretis.inout.writers import PathEnsembleFile
from pyretis.inout.settings import SECTIONS
logging.disable(logging.CRITICAL)


HERE = os.path.abspath(os.path.dirname(__file__))


class AnalysePathEnsembleTest(unittest.TestCase):
    """Test that we run the analysis for PathEnsemble results."""

    def test_path_analysis(self):
        """Test the path ensemble analysis."""
        ensembles = [
            {
                'name': 0,
                'interfaces': [-float('inf'), -0.9, -0.9],
                'detect': -0.9,
                'file': 'pathensemble000.txt',
                'test': {'fluxlength': (0, 1545.5524475524476)},
            },
            {
                'name': 1,
                'interfaces': [-0.9, -0.9, 1],
                'detect': -0.8,
                'file': 'pathensemble001.txt',
                'test': {'prun': (-1, 0.22377622)},
            },
            {
                'name': 2,
                'interfaces': [-0.9, -0.8, 1],
                'detect': -0.7,
                'file': 'pathensemble002.txt',
                'test': {'prun': (-1, 0.14485514)},
            },
            {
                'name': 3,
                'interfaces': [-0.9, -0.7, 1],
                'detect': -0.6,
                'file': 'pathensemble003.txt',
                'test': {'prun': (-1, 0.12487512)},
            },
        ]
        settings = {'analysis': SECTIONS['analysis']}
        results = []
        detect = []
        for ens in ensembles:
            filename = os.path.join(HERE, ens['file'])
            raw_data = PathEnsembleFile(filename, ens['name'],
                                        ens['interfaces'],
                                        detect=ens['detect'])
            res = analyse_path_ensemble(raw_data, settings)
            for key, val in ens['test'].items():
                self.assertAlmostEqual(val[-1], res[key][val[0]])
            results.append(analyse_path_ensemble(raw_data, settings))
            detect.append(ens['detect'])
        match = match_probabilities(results[1:], detect[1:])
        self.assertAlmostEqual(match['prob'], 0.00404784431946)
        flux = retis_flux(results[0], results[1], 0.002)
        self.assertAlmostEqual(flux[0], 0.26513774978836657)
        self.assertAlmostEqual(flux[1], 0.023855082020650387)
        rate = retis_rate(match['prob'], match['relerror'], flux[0], flux[1])
        self.assertAlmostEqual(rate[0], 0.0010732363343554615)
        self.assertAlmostEqual(rate[1], 0.43377192333568948)

    def test_path_analysisobject(self):
        """Test analyse_path_ensemble_object"""
        filename = os.path.join(HERE, 'pathensemble001.txt')
        settings = {'analysis': SECTIONS['analysis']}
        interfaces = [-0.9, -0.9, 1.0]
        raw_data = PathEnsembleFile(
            filename,
            1,
            interfaces,
            detect=-0.8,
        )
        ensemble = PathEnsemble(1, interfaces, detect=-0.8)
        for path in raw_data.get_paths():
            dummy_path = Path(None, maxlen=None, time_origin=0)
            dummy_path.generated = path['generated']
            dummy_path.length = path['length']
            dummy_path.ordermax = path['ordermax']
            dummy_path.ordermin = path['ordermin']
            # Add fake points for the interfaces:
            start, _, end = path['interface']
            order = []
            for i in (start, end):
                if i == 'L':
                    order.append([interfaces[0]-0.1])
                elif start == 'R':
                    order.append([interfaces[2]+0.1])
                else:
                    order.append([0.5*(interfaces[0] + interfaces[2])])
            dummy_path.order = order
            ensemble.add_path_data(dummy_path, path['status'])
        results = analyse_path_ensemble_object(ensemble, settings)
        self.assertAlmostEqual(results['prun'][-1], 0.22377622)


if __name__ == '__main__':
    unittest.main()
