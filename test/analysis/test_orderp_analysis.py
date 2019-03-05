# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""A test module for the order parameter analysis."""
import logging
import unittest
import os
import pickle
import numpy as np
from pyretis.analysis.order_analysis import analyse_orderp
from pyretis.inout.settings import SECTIONS
from pyretis.inout.formats.order import OrderFile

logging.disable(logging.CRITICAL)
HERE = os.path.abspath(os.path.dirname(__file__))


class TestOrderAnalysis(unittest.TestCase):
    """Test that we can analyse order parameters."""

    def test_energy_analysis(self):
        """Test the energy analysis."""
        filename = os.path.join(HERE, 'order.txt')
        data = None
        with OrderFile(filename, 'r') as orderfile:
            data = orderfile.load()
        settings = {}
        settings['analysis'] = SECTIONS['analysis']
        for i in data:
            results = analyse_orderp(i['data'], settings)
            break
        correct_file = os.path.join(HERE, 'order-results.dat')
        with open(correct_file, 'rb') as infile:
            correct_data = pickle.load(infile)
            for i, j in zip(correct_data, results):
                for itemi, itemj in zip(i['blockerror'], j['blockerror']):
                    self.assertTrue(np.allclose(itemi, itemj))
                self.assertTrue(np.allclose(i['running'], j['running']))
                if 'msd' in i:
                    self.assertTrue(np.allclose(i['msd'], j['msd']))
                for itemi, itemj in zip(i['distribution'], j['distribution']):
                    self.assertTrue(np.allclose(itemi, itemj))
                    self.assertTrue(np.allclose(itemi, itemj))


if __name__ == '__main__':
    unittest.main()
