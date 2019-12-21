# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the common methods in pyretis.visualization.common."""

import os
import logging
import unittest
from pyretis.visualization.orderparam_density import (PathDensity,
                                                      PathVisualize,
                                                      main)
from unittest import mock
import argparse
logging.disable(logging.CRITICAL)

HERE = os.path.abspath(os.path.dirname(__file__))
INPUTFILE = os.path.join(HERE, 'test_simulation_dir/input.rst')

CORRECT = {
    'path': ['000', '001', '002', '003'],
    'op_labels': ['op1', 'op2', 'cycO'],
    'energy_labels': ['time', 'cycE', 'potE', 'kinE', 'totE'],
    'interfaces': [-0.9, -0.8, -0.7, -0.5, -0.4, -0.3, 1.0],
    'num_op': 2
}

CORRECT_LENGTHS_SLOW = {
    '000 A': [968, 968, 968, 968, 3872, 3872, 3872, 3872],
    '000 R': [0, 0, 0, 0, 1500, 1500, 1500, 1500],
    '001 A': [247, 247, 247, 247, 1235, 1235, 1235, 1235],
    '001 R': [454, 454, 454, 454, 2719, 2719, 2719, 2719],
    '002 A': [247, 247, 247, 247, 2223, 2223, 2223, 2223],
    '002 R': [454, 454, 454, 454, 2719, 2719, 2719, 2719],
    '003 A': [247, 247, 247, 247, 2223, 2223, 2223, 2223],
    '003 R': [454, 454, 454, 454, 2719, 2719, 2719, 2719],
}


def init_PathDensity(ifile=INPUTFILE):
    """Initialize PathDensity with input file"""
    data_dict = PathDensity(ifile)
    return data_dict


def init_PathVisualize(pfile=None):
    """Initialize PathVisualize"""
    data = PathVisualize(pfile=pfile)
    return data


def compare_keys(dict1, correct):
    """Test if given dictionary contains the correct set of keys"""
    for key in correct:
        check = (True if key in dict1 else False)
    return check


class TestMethods(unittest.TestCase):
    """Testing class of pyretis.visualization.orderparam_density."""

    def test_PathDensity_blank(self):
        """Testing initiate PathDensity without a compatible inputfile"""
        _ = init_PathDensity(ifile='blank')

    def test_PathDensity(self):
        """Testing the PathDensity class creation from file."""
        d = init_PathDensity()
        self.assertEqual(d.iofile, INPUTFILE)
        self.assertEqual(True, compare_keys(d.infos,
                                            CORRECT.keys()))
        self.assertEqual(True, compare_keys(d.infos['path'],
                                            CORRECT['path']))
        self.assertEqual(True, compare_keys(d.infos['op_labels'],
                                            CORRECT['op_labels']))
        self.assertEqual(True, compare_keys(d.infos['energy_labels'],
                                            CORRECT['energy_labels']))
        self.assertEqual(True, compare_keys(d.infos['interfaces'],
                                            CORRECT['interfaces']))
        self.assertEqual(d.infos['num_op'], CORRECT['num_op'])

    def test_walk_Dirs(self):
        """Testing the walk_Dirs function of PathDensity"""
        d = init_PathDensity()
        d.walk_dirs()

    def test_write_lengths(self):
        d = init_PathDensity()
        d.walk_dirs()
        d.write_lengths()
        self.assertTrue(os.path.isfile('pathdens.txt'))
        f = open('pathdens.txt', 'r')
        lines = f.readlines()
        f.close()
        os.remove('pathdens.txt')

        for line in lines[8:12]:
            data = line.replace('\t', '').split('|')
            key = data[0].rstrip()
            eops = [int(i) for i in data[1].split()]
            ops = [int(i) for i in data[2].split()]
            self.assertEqual(
                CORRECT_LENGTHS_SLOW[key],
                eops+ops
                )

    def test_pickle(self):
        """Testing the pickling to a file"""
        d = init_PathDensity()
        d.walk_dirs()
        d.pickle_data()
        self.assertTrue(os.path.isfile('pathdens.pickle'))
        os.remove('pathdens.pickle')

    def test_pickling_and_loading(self):
        """Test for pickling data to file and load with PathVisualize"""
        d = init_PathDensity()
        d.walk_dirs()
        d.pickle_data()
        self.assertTrue(os.path.isfile('pathdens.pickle'))
        _ = init_PathVisualize('pathdens.pickle')
        os.rename('pathdens.pickle', 'mypickle.pickle')
        _ = init_PathVisualize('mypickle.pickle')
        os.remove('mypickle.pickle')

    def test_get_Odata(self):
        """Test for loading pickle and getting data from compiled dictionary"""
        d = init_PathDensity()
        d.walk_dirs()
        d.pickle_data()
        w = init_PathVisualize('pathdens.pickle')
        os.remove('pathdens.pickle')

        for fol in d.infos['path']:
            accw, _ = w.get_Odata(fol, ['cycO', 'timo', 'ACC'])
            accb, _ = w.get_Odata(fol, ['cycO', 'timo', 'ACC'], weight=False)
            rejw, _ = w.get_Odata(fol, ['cycO', 'timo', 'REJ'])
            rejb, _ = w.get_Odata(fol, ['cycO', 'timo', 'REJ'], weight=False)
            self.assertEqual(rejw, rejb)
            bothw, _ = w.get_Odata(fol, ['cycO', 'timo', 'BOTH'])
            bothb, _ = w.get_Odata(fol, ['cycO', 'timo', 'BOTH'], weight=False)
            self.assertEqual(accb+rejb, bothb)
            self.assertEqual(accw+rejw, bothw)

        cyca, _ = w.get_Odata(fol, ['cycO', 'timo', 'ACC'], min_max=[2, 7])
        cycr, _ = w.get_Odata(fol, ['cycO', 'timo', 'REJ'], min_max=[2, 7])
        cycb, _ = w.get_Odata(fol, ['cycO', 'timo', 'BOTH'], min_max=[2, 7])
        self.assertEqual(cyca+cycr, cycb)

    def test_get_Edata(self):
        """Test for loading pickle and getting data from compiled dictionary"""
        d = init_PathDensity()
        d.walk_dirs()
        d.pickle_data()
        w = init_PathVisualize('pathdens.pickle')
        for fol in d.infos['path']:
            xa, _, _ = w.get_Edata(fol, ['cycO', 'timo', 'potE'], 'ACC')
            xr, _, _ = w.get_Edata(fol, ['cycO', 'timo', 'potE'], 'REJ')
            xb, _, _ = w.get_Edata(fol, ['cycO', 'timo', 'potE'], 'BOTH')
            self.assertEqual(xa + xr, xb)

        _, _, empty = w.get_Edata('000', ['cycO', 'timo', 'None'], 'BOTH')
        self.assertEqual(empty[0], 1)
        _, _, emtpy = w.get_Edata('000', ['cycO', 'timo', 'None'], 'ACC')
        self.assertEqual(empty[0], 1)

    def test_get_EOP_file_starts(self):
        d = init_PathDensity()
        fol = os.path.join(HERE, 'test_simulation_dir/test_path')
        # Set empty lists, because vis code can't handle new dirs)
        d.eops['acycE', fol] = []
        d.eops['atime', fol] = []
        d.eops['apotE', fol] = []
        d.eops['akinE', fol] = []
        d.eops['atotE', fol] = []
        d.eops['rcycE', fol] = []
        d.eops['rtime', fol] = []
        d.eops['rpotE', fol] = []
        d.eops['rkinE', fol] = []
        d.eops['rtotE', fol] = []
        d.eops['acycO', fol] = []
        d.eops['atimo', fol] = []
        d.eops['aop1', fol] = []
        d.eops['aop2', fol] = []
        d.eops['rtimo', fol] = []
        d.eops['rcycO', fol] = []
        d.eops['rop1', fol] = []
        d.eops['rop2', fol] = []

        d.get_EOP(fol=fol,
                  files=[os.path.join(fol, 'order.txt'),
                         os.path.join(fol, 'energy.txt')],
                  file_starts=(1, 2))

    def test_get_OP_file_starts(self):
        d = init_PathDensity()
        fol = os.path.join(HERE, 'test_simulation_dir/test_path')
        # Set empty lists, because vis code can't handle new dirs)
        d.ops['acycO', fol] = []
        d.ops['atimo', fol] = []
        d.ops['aop1', fol] = []
        d.ops['aop2', fol] = []
        d.ops['rtimo', fol] = []
        d.ops['rcycO', fol] = []
        d.ops['rop1', fol] = []
        d.ops['rop2', fol] = []
        d.ops['astatw', fol] = []
        d.get_OP(fol=fol,
                 ofile=os.path.join(fol, 'order.txt'),
                 ostart=1)

    def test_compare_and_cut(self):
        d = init_PathDensity()
        fol = os.path.join(HERE, 'test_simulation_dir/005')
        # More energies than orderps
        d.eops['atime', fol] = [1, 2, 3]
        d.eops['atimo', fol] = [1, 2]
        d.eops['acycE', fol] = [0, 0, 0]
        d.eops['acycO', fol] = [0, 0]
        d.eops['aop1', fol] = [1, 2]
        d.eops['aop2', fol] = [1, 2]
        d.eops['apotE', fol] = [0, 0, 0]
        d.eops['akinE', fol] = [0, 0, 0]
        d.eops['atotE', fol] = [0, 0, 0]
        d.compare_and_cut(fol, 'a', (3, 2))

        # More OPs than energies
        d.eops['atimo', fol] = [1, 2, 3]
        d.eops['atime', fol] = [1, 2]
        d.eops['acycO', fol] = [0, 0, 0]
        d.eops['acycE', fol] = [0, 0]
        d.eops['aop1', fol] = [1, 2, 3]
        d.eops['aop2', fol] = [1, 2, 3]
        d.eops['apotE', fol] = [0, 0]
        d.eops['akinE', fol] = [0, 0]
        d.eops['atotE', fol] = [0, 0]
        d.compare_and_cut(fol, 'a', (2, 3))

        # Missing center energies
        d.eops['atimo', fol] = [1, 2, 3]
        d.eops['atime', fol] = [1, 3]
        d.eops['acycO', fol] = [0, 0, 0]
        d.eops['acycE', fol] = [0, 0]
        d.eops['aop1', fol] = [1, 2, 3]
        d.eops['aop2', fol] = [1, 2, 3]
        d.eops['apotE', fol] = [0, 0]
        d.eops['akinE', fol] = [0, 0]
        d.eops['atotE', fol] = [0, 0]
        d.compare_and_cut(fol, 'a', (2, 3))

        # Missin center orderps , match on time
        d.eops['atime', fol] = [1, 2, 3]
        d.eops['atimo', fol] = [1, 3]
        d.eops['acycE', fol] = [0, 0, 0]
        d.eops['acycO', fol] = [0, 0]
        d.eops['aop1', fol] = [1, 2]
        d.eops['aop2', fol] = [1, 2]
        d.eops['apotE', fol] = [0, 0, 0]
        d.eops['akinE', fol] = [0, 0, 0]
        d.eops['atotE', fol] = [0, 0, 0]
        d.compare_and_cut(fol, 'a', (3, 2), target='time')

    def test_get_Odata_uneven(self):
        d = init_PathDensity()
        d.walk_dirs()
        d.pickle_data()
        v = init_PathVisualize('pathdens.pickle')
        fol = os.path.join(HERE, "/test_simulation_dir/000")
        v.ops['acycO', fol] = [0, 0, 0, 0]
        v.ops['rcycO', fol] = []
        v.ops['atime', fol] = [1, 2, 3]
        v.ops['atimo', fol] = [None, None, None]
        v.get_Odata(fol, ['time', 'timo', 'ACC'], weight=False,
                    min_max=(0, 4))

    def test_get_Edata_uneven(self):
        d = init_PathDensity()
        d.walk_dirs()
        d.pickle_data()
        v = init_PathVisualize('pathdens.pickle')
        fol = os.path.join(HERE, "/test_simulation_dir/000")
        v.eops['acycE', fol] = [0, 0, 0, 0]
        v.eops['rcycE', fol] = []
        v.eops['atime', fol] = [1, 2, 3]
        v.eops['atimo', fol] = [None, None, None]
        v.get_Edata(fol, ['time', 'timo'], ACC='ACC',
                    min_max=(0, 4))

    @mock.patch('argparse.ArgumentParser.parse_args',
                return_value=argparse.Namespace(input=INPUTFILE,
                                                only_orderp=True))
    def test_main(self, mock_args):
        main()


if __name__ == '__main__':
    unittest.main()
