# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""A test module for path ensemble analysis."""
import logging
import os
import unittest
import warnings
from pyretis.core.pathensemble import PathEnsemble
from pyretis.core.system import System
from pyretis.core.path import Path
from pyretis.analysis.path_analysis import (
    analyse_path_ensemble,
    analyse_path_ensemble_object,
    match_probabilities,
    retis_flux,
    retis_rate,
)
from pyretis.inout.formats.pathensemble import PathEnsembleFile
from pyretis.inout.settings import SECTIONS
from .help import turn_on_logging
logging.disable(logging.CRITICAL)


HERE = os.path.abspath(os.path.dirname(__file__))


def add_some_paths(ensemble, raw_data):
    """Add some fake path to the given ensemble."""
    interfaces = ensemble.interfaces
    for _, path in enumerate(raw_data.get_paths()):
        dummy_path = Path(None, maxlen=None, time_origin=0)
        dummy_path.generated = path['generated']
        # Add fake points for the interfaces:
        start, _, end = path['interface']
        order = ([((path['ordermax'][0] + path['ordermin'][0]) * 0.5, 0)] *
                 path['length'])
        for i in (start, end):
            if i == 'L':
                order.append([interfaces[0]-0.1])
            elif start == 'R':
                order.append([interfaces[2]+0.1])
            else:
                order.append([0.5*(interfaces[0] + interfaces[2])])
        order[path['ordermax'][1]] = path['ordermax']
        order[path['ordermin'][1]] = path['ordermin']
        for i in order:
            phasepoint = System()
            phasepoint.order = i
            dummy_path.append(phasepoint)
        ensemble.add_path_data(dummy_path, path['status'])


class AnalysePathEnsembleTest(unittest.TestCase):
    """Test that we run the analysis for PathEnsemble results."""

    def test_path_analysis(self):
        """Test the path ensemble analysis."""
        ensembles = [
            {
                'ensemble_number': 0,
                'interfaces': [-float('inf'), -0.9, -0.9],
                'detect': -0.9,
                'file': 'pathensemble000.txt',
                'test': {'fluxlength': (0, 1545.5524475524476)},
            },
            {
                'ensemble_number': 1,
                'interfaces': [-0.9, -0.9, 1],
                'detect': -0.8,
                'file': 'pathensemble001.txt',
                'test': {'prun': (-1, 0.22377622)},
            },
            {
                'ensemble_number': 2,
                'interfaces': [-0.9, -0.8, 1],
                'detect': -0.7,
                'file': 'pathensemble002.txt',
                'test': {'prun': (-1, 0.14485514)},
            },
            {
                'ensemble_number': 3,
                'interfaces': [-0.9, -0.7, 1],
                'detect': -0.6,
                'file': 'pathensemble003.txt',
                'test': {'prun': (-1, 0.12487512)},
            },
            {
                'ensemble_number': 4,
                'interfaces': [-0.9, -0.71, 1],
                'detect': -0.6,
                'file': 'pathensemble004.txt',
                'test': {'prun': (-1, 0.129132231)},
            },
        ]
        settings = {'analysis': SECTIONS['analysis']}
        results = []
        detect = []
        for ens in ensembles:
            filename = os.path.join(HERE, ens['file'])
            raw_data = PathEnsembleFile(filename, 'r', ensemble_settings=ens)
            res = analyse_path_ensemble(raw_data, settings)
            for key, val in ens['test'].items():
                self.assertAlmostEqual(val[-1], res[key][val[0]])
            results.append(analyse_path_ensemble(raw_data, settings))
            detect.append(ens['detect'])
        match = match_probabilities(results[1:], detect[1:], settings)
        self.assertAlmostEqual(match['prob'], 0.0005227071693518608)
        flux = retis_flux(results[0], results[1], 0.002)
        self.assertAlmostEqual(flux[0], 0.26513774978836657)
        self.assertAlmostEqual(flux[1], 0.023855082020650387)
        rate = retis_rate(match['prob'], match['relerror'], flux[0], flux[1])
        self.assertAlmostEqual(rate[0], 0.00013858940268019902)
        self.assertAlmostEqual(rate[1], 0.4684306995194783)

        # Re-check the last one:
        settings['analysis']['maxblock'] = 0
        res = analyse_path_ensemble(raw_data, settings)
        self.assertAlmostEqual(val[-1], res[key][val[0]])

    def test_path_analysisobject(self):
        """Test analyse_path_ensemble_object."""
        filename = os.path.join(HERE, 'pathensemble001.txt')
        settings = {'analysis': SECTIONS['analysis']}
        interfaces = [-0.9, -0.9, 1.0]
        ens_settings = {
            'ensemble_number': 1,
            'interfaces': interfaces,
            'detect': -0.8
        }
        raw_data = PathEnsembleFile(
            filename,
            'r',
            ensemble_settings=ens_settings,
        )
        ensemble = PathEnsemble(1, interfaces, detect=-0.8)
        add_some_paths(ensemble, raw_data)
        results = analyse_path_ensemble_object(ensemble, settings)
        self.assertAlmostEqual(results['prun'][-1], 0.22377622)
        self.assertAlmostEqual(results['pcross'][1][0], 1.)
        self.assertAlmostEqual(results['pcross'][1][-1], 0.000999000999001)
        # Check warning if path is too low ordermax:
        ordermax = ensemble.paths[0]['ordermax']
        ensemble.paths[0]['ordermax'] = (-9999, 1)
        results = {}
        with turn_on_logging():
            with self.assertLogs('pyretis.analysis.path_analysis',
                                 level=logging.WARNING):
                results = analyse_path_ensemble_object(ensemble, settings)
            self.assertTrue(results['pcross'][1][0] < 1.)
        ensemble.paths[0]['ordermax'] = ordermax

        # Check that this modification did not alter last crossing
        # probability:
        self.assertAlmostEqual(results['pcross'][1][-1], 0.000999000999001)

        # Check warning for a path generated by an unknown move:
        ensemble.paths[0]['generated'] = 'unknown move'
        results = {}
        with turn_on_logging():
            with self.assertLogs('pyretis.analysis.path_analysis',
                                 level=logging.WARNING):
                results = analyse_path_ensemble_object(ensemble, settings)
        ensemble.paths[0]['generated'] = 'ki'
        # Check that this modification did not alter last crossing
        # probability:
        self.assertTrue(results['pcross'][1][0] <= 1.)
        self.assertAlmostEqual(results['pcross'][1][-1], 0.000999000999001)

        # Test some shooting statistics:
        self.assertAlmostEqual(results['shoots'][1]['ALL'], 1.0)
        self.assertAlmostEqual(results['shoots'][1]['ACC'], 0.821428571)
        self.assertAlmostEqual(results['shoots'][1]['REJ'], 0.178571428)
        self.assertAlmostEqual(results['shoots'][1]['FTL'], 0.123015873)
        self.assertAlmostEqual(results['shoots'][1]['BTL'], 0.0555555555)
        self.assertEqual(len(ensemble.paths), ensemble.nstats['npath'])

        # Check warning when deleting a path without updating the
        # statistics in the path ensemble:
        del ensemble.paths[0]
        results = {}
        with turn_on_logging():
            with self.assertLogs('pyretis.analysis.path_analysis',
                                 level=logging.WARNING):
                results = analyse_path_ensemble_object(ensemble, settings)

        # Check warning when we delete some information from a path:
        del ensemble.paths[0]['cycle']
        results = {}
        with turn_on_logging():
            with self.assertLogs('pyretis.analysis.path_analysis',
                                 level=logging.WARNING):
                results = analyse_path_ensemble_object(ensemble, settings)

        # Check divide-by-zero warning which can happen if we do not obtain
        # some of the statuses:
        for path in ensemble.paths:
            path['status'] = 'ACC'
        with warnings.catch_warnings(record=True) as warn:
            results = analyse_path_ensemble_object(ensemble, settings)
            self.assertEqual(
                str(warn[-1].message),
                'invalid value encountered in true_divide'
            )


if __name__ == '__main__':
    unittest.main()
