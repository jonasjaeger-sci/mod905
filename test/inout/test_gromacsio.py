# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""A test module for the gromacsio module."""
import logging
import unittest
import tempfile
import os
import numpy as np
from pyretis.core.box import box_matrix_to_list
from pyretis.inout.writers.gromacsio import (
    read_gromacs_lines,
    read_gromacs_file,
    read_gromacs_gro_file,
    write_gromacs_gro_file,
    read_gromos96_file,
    write_gromos96_file,
    read_xvg_file,
    swap_integer,
    swap_endian,
    read_trr_file,
    read_trr_frame,
    reverse_trr,
    trr_frame_to_g96,
)


logging.disable(logging.CRITICAL)
HERE = os.path.abspath(os.path.dirname(__file__))


RAW_FILE_VEL = [
    'Example from: https://en.wikipedia.org/wiki/XYZ_file_format',
    '5',
    '    1DUM     Ba    1   0.000   0.000   0.000   1.000   1.000   1.000',
    '    2DUM     Hf    2   0.050   0.050   0.050  -1.000  -1.000  -1.000',
    '    3DUM      O    3   0.050   0.050   0.000   2.000   0.000  -2.000',
    '    3DUM      O    4   0.050   0.000   0.050  -2.000   1.000   2.000',
    '    3DUM      O    5   0.000   0.050   0.050   0.000  -1.000   0.000',
    '   2.00000   2.00000   2.00000',
]

RAW_FILE = [
    'Example from: https://en.wikipedia.org/wiki/XYZ_file_format',
    '5',
    '    1DUM     Ba    1   0.000   0.000   0.000',
    '    2DUM     Hf    2   0.050   0.050   0.050',
    '    3DUM      O    3   0.050   0.050   0.000',
    '    3DUM      O    4   0.050   0.000   0.050',
    '    3DUM      O    5   0.000   0.050   0.050',
    '   2.00000   2.00000   2.00000',
]

CORRECT_GRO = {
    'x': [0.0, 0.05, 0.05, 0.05, 0.0],
    'y': [0.0, 0.05, 0.05, 0.0, 0.05],
    'z': [0.0, 0.05, 0.0, 0.05, 0.05],
    'vx': [1.0, -1.0, 2.0, -2.0, 0.0],
    'vy': [1.0, -1.0, 0.0, 1.0, -1.0],
    'vz': [1.0, -1.0, -2.0, 2.0, 0.0],
    'residunr': [1, 2, 3, 3, 3],
    'atomnr': [1, 2, 3, 4, 5],
    'header': RAW_FILE[0],
    'residuname': ['DUM', 'DUM', 'DUM', 'DUM', 'DUM'],
    'atomname': ['Ba', 'Hf', 'O', 'O', 'O'],
    'box': [2.0, 2.0, 2.0],
    'xyz': np.transpose(np.array([[0.0, 0.05, 0.05, 0.05, 0.0],
                                  [0.0, 0.05, 0.05, 0.0, 0.05],
                                  [0.0, 0.05, 0.0, 0.05, 0.05]])),
    'vel': np.transpose(np.array([[1.0, -1.0, 2.0, -2.0, 0.0],
                                  [1.0, -1.0, 0.0, 1.0, -1.0],
                                  [1.0, -1.0, -2.0, 2.0, 0.0]])),
}


CORRECT_XVG = {
    'potential': np.array([-937898.125, -965421.6875, -992991.0,
                           -1015228.375, -1037830.125, -1046103.3125]),
    'pressure': np.array([-22567.054688, -22762.349609, -22956.455078,
                          -23085.162109, -23215.666016, -23260.259766]),
    't-rest': np.array([0.0] * 6),
    'step': np.array([i for i in range(6)]),
}


class TestGromacsIO(unittest.TestCase):
    """Test Gromacs input output."""

    def test_read_gromacs_lines(self):
        """Test that we can read GROMACS lines."""
        for snapshot in (RAW_FILE_VEL, RAW_FILE):
            snap = next(read_gromacs_lines(snapshot))
            for key, val in snap.items():
                for i, j in zip(val, CORRECT_GRO[key]):
                    self.assertEqual(i, j)
        multi = [i for i in RAW_FILE_VEL] * 2
        for snap in read_gromacs_lines(multi):
            for key, val in snap.items():
                for i, j in zip(val, CORRECT_GRO[key]):
                    self.assertEqual(i, j)

    def test_read_gromacs_file(self):
        """Test that we can read a GROMACS file."""
        filename = os.path.join(HERE, 'config.gro')
        for snap in read_gromacs_file(filename):
            for key, val in snap.items():
                for i, j in zip(val, CORRECT_GRO[key]):
                    self.assertEqual(i, j)

    def test_read_gromacs_file2(self):
        """Test that we can read a single config GROMACS file."""
        for name in ('config.gro', 'config-novel.gro'):
            filename = os.path.join(HERE, name)
            frame, xyz, vel, box = read_gromacs_gro_file(filename)
            self.assertTrue(np.allclose(box, np.array(CORRECT_GRO['box'])))
            self.assertTrue(np.allclose(xyz, CORRECT_GRO['xyz']))
            if 'vx' in frame:
                self.assertTrue(np.allclose(vel, CORRECT_GRO['vel']))
            else:
                self.assertTrue(np.allclose(vel, np.zeros_like(vel)))

    def test_write_gromacs_gro(self):
        """Test that we can write GROMACS GRO files."""
        filename = os.path.join(HERE, 'config.gro')
        frame, xyz, vel, box = read_gromacs_gro_file(filename)
        with tempfile.NamedTemporaryFile() as tmp:
            write_gromacs_gro_file(tmp.name, frame, xyz, vel)
            tmp.flush()
            frame2, xyz2, vel2, box2 = read_gromacs_gro_file(tmp.name)
            self.assertTrue(np.allclose(xyz, xyz2))
            self.assertTrue(np.allclose(vel, vel2))
            self.assertTrue(np.allclose(box, box2))
            for key, val in frame.items():
                self.assertEqual(val, frame2[key])

    def test_read_gromosg96(self):
        """Test that we can read GROMACS g96 files."""
        for name in ('config.g96', 'config-novel.g96'):
            filename = os.path.join(HERE, name)
            frame, xyz, vel, box = read_gromos96_file(filename)
            self.assertTrue(np.allclose(box, np.array(CORRECT_GRO['box'])))
            self.assertTrue(np.allclose(xyz, CORRECT_GRO['xyz']))
            if frame['VELOCITY']:
                self.assertTrue(np.allclose(vel, CORRECT_GRO['vel']))
            else:
                self.assertTrue(np.allclose(vel, np.zeros_like(vel)))

    def test_write_gromos96(self):
        """Test that we can write GROMACS g96 files."""
        filename = os.path.join(HERE, 'config.g96')
        frame, xyz, vel, box = read_gromos96_file(filename)
        with tempfile.NamedTemporaryFile() as tmp:
            write_gromos96_file(tmp.name, frame, xyz, vel)
            tmp.flush()
            frame2, xyz2, vel2, box2 = read_gromos96_file(tmp.name)
            self.assertTrue(np.allclose(xyz, xyz2))
            self.assertTrue(np.allclose(vel, vel2))
            self.assertTrue(np.allclose(box, box2))
            for key, val in frame.items():
                self.assertEqual(val, frame2[key])

    def test_read_xvg_file(self):
        """Test that we can read GROMACS xvg files."""
        filename = os.path.join(HERE, 'energy.xvg')
        data = read_xvg_file(filename)
        for key, val in data.items():
            self.assertTrue(np.allclose(val, CORRECT_XVG[key]))


class TestGromacsTRR(unittest.TestCase):
    """Test Gromacs TRR input output."""

    def test_swap_integer(self):
        """Test the gromacsio swap_integer method."""
        test = [(1, 16777216), (2, 33554432), (4, 67108864),
                (8, 134217728), (16, 268435456)]
        for i, j in test:
            self.assertEqual(i, swap_integer(j))
            self.assertEqual(j, swap_integer(i))

    def test_swap_endian(self):
        """Test the gromacsio swap_endian method."""
        test = [('>', '<'), ('<', '>')]
        for i, j in test:
            self.assertEqual(j, swap_endian(i))
        with self.assertRaises(ValueError):
            swap_endian(1)
        with self.assertRaises(ValueError):
            swap_endian('^')

    def test_read_trr(self):
        """Test the gromacsio reading for TRR files."""
        filename = os.path.join(HERE, 'traj.trr')
        all_data = []
        for i, (header, data) in enumerate(read_trr_file(filename)):
            self.assertEqual(i * 10, header['step'])
            self.assertEqual(16, header['natoms'])
            all_data.append(data)
        all_data2 = []
        for i in range(11):
            _, data = read_trr_frame(filename, i)
            all_data2.append(data)
        self.assertEqual(len(all_data), len(all_data2))
        for data1, data2 in zip(all_data, all_data2):
            for key, val in data1.items():
                self.assertTrue(np.allclose(val, data2[key]))
        header, data = read_trr_frame(filename, 100)
        self.assertTrue(header is None)
        self.assertTrue(data is None)
        header, data = read_trr_frame(filename, -1)
        for i, (header, data) in enumerate(read_trr_file(filename,
                                                         read_data=False)):
            self.assertTrue(data is None)
            self.assertEqual(i * 10, header['step'])

        filename = os.path.join(HERE, 'error.trr')
        logging.disable(logging.INFO)
        with self.assertLogs('pyretis.inout.writers.gromacsio',
                             level='WARNING'):
            for i in read_trr_file(filename):
                pass
        logging.disable(logging.CRITICAL)

    def test_reverse_trr(self):
        """Test that we can reverse a trr file."""
        filename = os.path.join(HERE, 'traj.trr')
        with tempfile.NamedTemporaryFile() as tmp:
            reverse_trr(filename, tmp.name, print_progress=False)
            tmp.flush()
            rev_header = []
            rev_data = []
            for header, data in read_trr_file(tmp.name):
                rev_header.append(header)
                rev_data.append(data)
            all_header = []
            all_data = []
            for header, data in read_trr_file(filename):
                all_header.append(header)
                all_data.append(data)
            for i, j in zip(all_header, reversed(rev_header)):
                for key, val in i.items():
                    self.assertEqual(val, j[key])
            for i, j in zip(all_data, reversed(rev_data)):
                for key, val in i.items():
                    self.assertTrue(np.allclose(val, j[key]))

    def test_trr_to_g96(self):
        """Test that we can extract a GROMOS g96 frame from a TRR."""
        filename = os.path.join(HERE, 'traj.trr')
        with tempfile.NamedTemporaryFile() as tmp:
            trr_frame_to_g96(filename, 2, tmp.name)
            tmp.flush()
            _, xyz, vel, box = read_gromos96_file(tmp.name)
            _, data = read_trr_frame(filename, 2)
            self.assertTrue(np.allclose(xyz, data['x']))
            self.assertTrue(np.allclose(vel, data['v']))
            self.assertTrue(
                np.allclose(box[:3], box_matrix_to_list(data['box']))
            )

    def test_read_double_trr(self):
        """Test that we can read double precision TRR as well."""
        filename1 = os.path.join(HERE, 'traj-double.trr')
        filename2 = os.path.join(HERE, 'traj-single.trr')
        for double, single in zip(read_trr_file(filename1),
                                  read_trr_file(filename2)):
            self.assertAlmostEqual(double[0]['time'], single[0]['time'],
                                   places=5)
            self.assertTrue(double[0]['double'])
            self.assertFalse(single[0]['double'])


if __name__ == '__main__':
    unittest.main()
