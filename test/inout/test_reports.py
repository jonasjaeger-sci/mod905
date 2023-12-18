# -*- coding: utf-8 -*-
# Copyright (c) 2023, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the FileIO class."""
import logging
import numpy as np
import os
import unittest
from pyretis.analysis import match_all_histograms
from pyretis.inout.plotting import create_plotter
from pyretis.inout.report.report import generate_report, get_template
from .help import turn_on_logging

logging.disable(logging.CRITICAL)


HERE = os.path.abspath(os.path.dirname(__file__))


class Reporting(unittest.TestCase):
    """Test the generate_report."""
    def test_generate_report(self):
        """Test analysisio function"""
        with self.assertRaises(ValueError) as ext:
            generate_report(report_type='fake', analysis_results=None,
                            output='ext')
        self.assertIn('nkown report type fake', str(ext.exception))
        with turn_on_logging():
            with self.assertLogs('pyretis.inout.report.report',
                                 level='WARNING'):
                with self.assertRaises(ValueError) as ext:
                    generate_report(report_type='retis0',
                                    analysis_results=None,
                                    output='ext')
                self.assertIn('Could not locate template', str(ext.exception))

    def test_create_plotter(self):
        """Test create_plotter."""
        with self.assertRaises(ValueError) as ext:
            create_plotter({'plotter': 'Fake'})
        self.assertIn('Unknown plotter: Fake', str(ext.exception))

        with self.assertRaises(ValueError) as ext:
            create_plotter({'plotter': 'mpl', 'output': 'kik'})
        self.assertIn('Output format "kik" is not support', str(ext.exception))

    def test_get_template(self):
        """Test get_template."""
        # Any file would do
        ifile = os.path.join(HERE, 'initial-gro.rst')
        nav, path = get_template(output=None, report_type=None, template=ifile)

        self.assertEqual((path, nav), (HERE, 'initial-gro.rst'))

    def test_match_all_histograms(self):
        """Test match histograms for umbrella sampling."""
        histograms = [[np.array([1, 5, 1, 0, 1, 1]),
                       np.array([+0.76, -0.74, -0.72, -0.71, +0.68, -0.66]),
                       np.array([-0.26, -0.34, +0.42, -0.52, -0.18, -0.16])],
                      [np.array([1, 3, 1, 0, 3, 1]),
                       np.array([-0.76, -0.74, +0.72, -0.71, -0.68, -0.66]),
                       np.array([-0.26, +0.34, -0.42, +0.32, +0.18, -0.16])],
                      [np.array([1, 2, 1, 0, 7, 1]),
                       np.array([-0.76, -0.74, +0.72, -0.71, -0.68, +0.66]),
                       np.array([-0.26, +0.34, -0.42, -0.22, -0.18, -0.16])]]
        windows = [[-1.0, -0.4], [-0.5, -0.2], [-0.3, 0.0]]

        histograms_s, mix, hist_avg = match_all_histograms(histograms, windows)
        self.assertTrue(all(histograms_s[0] == [1, 5, 1, 0, 1, 1]))
        self.assertTrue(all(histograms_s[1] == [1., 3., 1., 0., 3., 1.]))
        self.assertTrue(all(histograms_s[2] == [1., 2., 1., 0., 7., 1.]))
        self.assertTrue(all(np.array(mix) == [1.0, 1.0, 1.0]))
        self.assertTrue(all(hist_avg == np.array([1., 3., 0., 0., 7., 1.])))


if __name__ == '__main__':
    unittest.main()
