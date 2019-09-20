# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""A test module for the GROMACS in/out module."""
import logging
import unittest
import tempfile
import os
import struct
import numpy as np
from pyretis.core.box import box_matrix_to_list
from pyretis.inout.formats.gromacs import (
    _GROMACS_MAGIC,
    _TRR_VERSION_B,
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
    write_trr_frame,
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

CORRECT_GRO_VEL = {
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
    'box': np.array([2.0, 2.0, 2.0]),
    'xyz': np.transpose(np.array([[0.0, 0.05, 0.05, 0.05, 0.0],
                                  [0.0, 0.05, 0.05, 0.0, 0.05],
                                  [0.0, 0.05, 0.0, 0.05, 0.05]])),
    'vel': np.transpose(np.array([[1.0, -1.0, 2.0, -2.0, 0.0],
                                  [1.0, -1.0, 0.0, 1.0, -1.0],
                                  [1.0, -1.0, -2.0, 2.0, 0.0]])),
}


CORRECT_GRO_NOVEL = {
    'x': [0.0, 0.05, 0.05, 0.05, 0.0],
    'y': [0.0, 0.05, 0.05, 0.0, 0.05],
    'z': [0.0, 0.05, 0.0, 0.05, 0.05],
    'residunr': [1, 2, 3, 3, 3],
    'atomnr': [1, 2, 3, 4, 5],
    'header': RAW_FILE[0],
    'residuname': ['DUM', 'DUM', 'DUM', 'DUM', 'DUM'],
    'atomname': ['Ba', 'Hf', 'O', 'O', 'O'],
    'box': np.array([2.0, 2.0, 2.0]),
    'xyz': np.transpose(np.array([[0.0, 0.05, 0.05, 0.05, 0.0],
                                  [0.0, 0.05, 0.05, 0.0, 0.05],
                                  [0.0, 0.05, 0.0, 0.05, 0.05]])),
    'vel': np.zeros((5, 3)),
}


CORRECT_GRO_NOVEL1D = {
    'x': [0.0, 0.05, 0.05, 0.05, 0.0],
    'residunr': [1, 2, 3, 3, 3],
    'atomnr': [1, 2, 3, 4, 5],
    'header': RAW_FILE[0],
    'residuname': ['DUM', 'DUM', 'DUM', 'DUM', 'DUM'],
    'atomname': ['Ba', 'Hf', 'O', 'O', 'O'],
    'box': np.array([2.0, 2.0, 2.0]),
    'xyz': np.transpose(np.array([[0.0, 0.05, 0.05, 0.05, 0.0],
                                  [0.0, 0.0, 0.0, 0.0, 0.0],
                                  [0.0, 0.0, 0.0, 0.0, 0.0]])),
    'vel': np.zeros((5, 3)),
}


CORRECT_GRO_NOVEL2D = {
    'x': [0.0, 0.05, 0.05, 0.05, 0.0],
    'y': [0.0, 0.05, 0.05, 0.0, 0.05],
    'residunr': [1, 2, 3, 3, 3],
    'atomnr': [1, 2, 3, 4, 5],
    'header': RAW_FILE[0],
    'residuname': ['DUM', 'DUM', 'DUM', 'DUM', 'DUM'],
    'atomname': ['Ba', 'Hf', 'O', 'O', 'O'],
    'box': np.array([2.0, 2.0, 2.0]),
    'xyz': np.transpose(np.array([[0.0, 0.05, 0.05, 0.05, 0.0],
                                  [0.0, 0.05, 0.05, 0.0, 0.05],
                                  [0.0, 0.0, 0.0, 0.0, 0.0]])),
    'vel': np.zeros((5, 3)),
}


CORRECT_XVG = {
    'potential': np.array([-937898.125, -965421.6875, -992991.0,
                           -1015228.375, -1037830.125, -1046103.3125]),
    'pressure': np.array([-22567.054688, -22762.349609, -22956.455078,
                          -23085.162109, -23215.666016, -23260.259766]),
    't-rest': np.array([0.0] * 6),
    'step': np.array([i for i in range(6)]),
}


def generate_trr_data(output, steps, natoms, double=False, endian=None):
    """Generate some random TRR data."""
    all_data = []
    for i in range(steps):
        data = {
            'natoms': natoms,
            'step': i,
            'time': 0.002*i,
            'lambda': 0.0,
            'box': np.random.ranf(size=(3, 3)),
            'x': np.random.ranf(size=(natoms, 3)),
            'v': np.random.ranf(size=(natoms, 3)),
        }
        header = write_trr_frame(output, data, double=double, append=True,
                                 endian=endian)
        all_data.append((header, data))
    return all_data


class TestGromacsIO(unittest.TestCase):
    """Test Gromacs input output."""

    @staticmethod
    def assert_equal_snapshot(snapi, snapj):
        """Compare two snapshots."""
        for key, _ in snapi.items():
            if key not in snapj:
                msg = ('Snapshots have different keys'
                       ' {} is in first but not in second').format(key)
                raise AssertionError(msg)

        for key, _ in snapj.items():
            if key not in snapi:
                msg = ('Snapshots have different keys'
                       ' {} is in second but not in first').format(key)
                raise AssertionError(msg)

        for key, val in snapi.items():
            if key in ('xyz', 'vel'):
                if not np.allclose(val, snapj[key]):
                    raise AssertionError(
                        'Snapshots not equal. "{}" differ'.format(key)
                    )
            else:
                for i, j in zip(val, snapj[key]):
                    if not i == j:
                        raise AssertionError(
                            'Snapshots not equal. "{}" differ'.format(key)
                        )

    def test_read_gromacs_lines(self):
        """Test that we can read GROMACS lines."""
        for snapshot, correct in ((RAW_FILE_VEL, CORRECT_GRO_VEL),
                                  (RAW_FILE, CORRECT_GRO_NOVEL)):
            snap = next(read_gromacs_lines(snapshot))
            self.assert_equal_snapshot(snap, correct)
        multi = [i for i in RAW_FILE_VEL] * 2
        for snap in read_gromacs_lines(multi):
            self.assert_equal_snapshot(snap, CORRECT_GRO_VEL)

    def test_read_gromacs_file(self):
        """Test that we can read a GROMACS file."""
        filename = os.path.join(HERE, 'config.gro')
        for snap in read_gromacs_file(filename):
            self.assert_equal_snapshot(snap, CORRECT_GRO_VEL)

    def test_read_gromacs_file2(self):
        """Test that we can read a single config GROMACS file."""
        for name, correct in (('config.gro', CORRECT_GRO_VEL),
                              ('config-novel.gro', CORRECT_GRO_NOVEL)):
            filename = os.path.join(HERE, name)
            frame, xyz, vel, box = read_gromacs_gro_file(filename)
            self.assertIsNotNone(xyz)
            self.assertIsNotNone(vel)
            self.assertIsNotNone(box)
            self.assert_equal_snapshot(frame, correct)
        # Test what we get if we read 1D and 2D files:
        for dim, correct in ((1, CORRECT_GRO_NOVEL1D),
                             (2, CORRECT_GRO_NOVEL2D)):
            filename = os.path.join(HERE, 'config-{}D.gro'.format(dim))
            frame, xyz, vel, box = read_gromacs_gro_file(filename)
            self.assertIsNotNone(xyz)
            self.assertIsNotNone(vel)
            self.assertIsNotNone(box)
            self.assert_equal_snapshot(frame, correct)

    def test_write_gromacs_gro(self):
        """Test that we can write GROMACS GRO files."""
        filename = os.path.join(HERE, 'config.gro')
        frame, xyz, vel, _ = read_gromacs_gro_file(filename)
        with tempfile.NamedTemporaryFile() as tmp:
            write_gromacs_gro_file(tmp.name, frame, xyz, vel)
            tmp.flush()
            frame2, _, _, _ = read_gromacs_gro_file(tmp.name)
            self.assert_equal_snapshot(frame, frame2)
            write_gromacs_gro_file(tmp.name, frame, xyz)
            tmp.flush()
            _, xyz1, _, _ = read_gromacs_gro_file(tmp.name)
            self.assertTrue(np.allclose(xyz, xyz1))

    def test_read_gromosg96(self):
        """Test that we can read GROMACS g96 files."""
        for name in ('config.g96', 'config-novel.g96', 'config-red.g96'):
            filename = os.path.join(HERE, name)
            frame, xyz, vel, box = read_gromos96_file(filename)
            self.assertTrue(np.allclose(box, np.array(CORRECT_GRO_VEL['box'])))
            self.assertTrue(np.allclose(xyz, CORRECT_GRO_VEL['xyz']))
            if frame['VELOCITY']:
                self.assertTrue(np.allclose(vel, CORRECT_GRO_VEL['vel']))
            else:
                self.assertTrue(np.allclose(vel, np.zeros_like(vel)))

    def test_write_gromos96(self):
        """Test that we can write GROMACS g96 files."""
        filename = os.path.join(HERE, 'config.g96')
        frame, xyz, vel, box = read_gromos96_file(filename)
        with tempfile.NamedTemporaryFile() as tmp:
            write_gromos96_file(tmp.name, frame, xyz, vel, box)
            tmp.flush()
            frame2, xyz2, vel2, box2 = read_gromos96_file(tmp.name)
            self.assertTrue(np.allclose(xyz, xyz2))
            self.assertTrue(np.allclose(vel, vel2))
            self.assertTrue(np.allclose(box, box2))
            for key, val in frame.items():
                self.assertEqual(val, frame2[key])
            box = [0]*9
            write_gromos96_file(tmp.name, frame, xyz, vel, box)
            tmp.flush()
            _, _, _, box2 = read_gromos96_file(tmp.name)
            self.assertTrue(np.allclose(box, box2))

        # Test that we can write without some fields:
        del frame['VELOCITY']
        del frame['TITLE']
        del frame['BOX']
        with tempfile.NamedTemporaryFile() as tmp:
            write_gromos96_file(tmp.name, frame, xyz, vel)
            tmp.flush()
            frame2, xyz2, vel2, box2 = read_gromos96_file(tmp.name)
            self.assertEqual(None, box2)
            self.assertTrue(np.allclose(vel2, np.zeros_like(xyz2)))
            self.assertEqual(len(frame2['TITLE']), 0)
            self.assertTrue(np.allclose(xyz, xyz2))

    def test_read_xvg_file(self):
        """Test that we can read GROMACS xvg files."""
        filename = os.path.join(HERE, 'energy.xvg')
        data = read_xvg_file(filename)
        for key, val in data.items():
            self.assertTrue(np.allclose(val, CORRECT_XVG[key]))


class TestGromacsTRR(unittest.TestCase):
    """Test GROMACS TRR input output."""

    def test_swap_integer(self):
        """Test the swap_integer method."""
        test = [(1, 16777216), (2, 33554432), (4, 67108864),
                (8, 134217728), (16, 268435456)]
        for i, j in test:
            self.assertEqual(i, swap_integer(j))
            self.assertEqual(j, swap_integer(i))

    def test_swap_endian(self):
        """Test the swap_endian method."""
        test = [('>', '<'), ('<', '>')]
        for i, j in test:
            self.assertEqual(j, swap_endian(i))
        with self.assertRaises(ValueError):
            swap_endian(1)
        with self.assertRaises(ValueError):
            swap_endian('^')

    def test_read_trr(self):
        """Test the reading of TRR files."""
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

        with self.assertLogs('pyretis.inout.formats.gromacs',
                             level='WARNING'):
            for i in read_trr_file(filename):
                pass

        with self.assertLogs('pyretis.inout.formats.gromacs',
                             level='CRITICAL'):
            for i in read_trr_file(filename):
                pass
        logging.disable(logging.CRITICAL)

    def test_reverse_trr(self):
        """Test that we can reverse a TRR file."""
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
        for fname in ('traj.trr', 'traj-tric.trr'):
            filename = os.path.join(HERE, fname)
            with tempfile.NamedTemporaryFile() as tmp:
                trr_frame_to_g96(filename, 2, tmp.name)
                tmp.flush()
                _, xyz, vel, box = read_gromos96_file(tmp.name)
                _, data = read_trr_frame(filename, 2)
                self.assertTrue(np.allclose(xyz, data['x']))
                self.assertTrue(np.allclose(vel, data['v']))
                self.assertTrue(
                    np.allclose(box,
                                box_matrix_to_list(data['box'], full=True))
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

    def test_write_trr(self):
        """Test that we can write simple TRR files."""
        compare_direct = {'natoms', 'vir_size', 'ir_size', 'sym_size',
                          'top_size', 'v_size', 'f_size', 'box_size',
                          'x_size', 'step', 'pres_size', 'nre', 'e_size',
                          'double'}
        cases = (
            {'double': False},
            {'double': True},
            {'double': False, 'endian': '<'},
            {'double': False, 'endian': '>'},
        )
        for case in cases:
            with tempfile.NamedTemporaryFile() as tmp:
                all_data = generate_trr_data(tmp.name, 10, 11,
                                             double=case.get('double', False),
                                             endian=case.get('endian', None))
                tmp.flush()
                for frame, correct in zip(read_trr_file(tmp.name), all_data):
                    header, data = frame
                    header2, data2 = correct
                    for key in compare_direct:
                        self.assertEqual(header[key], header2[key])
                    for key in ('time', 'lambda'):
                        self.assertAlmostEqual(header[key], header2[key])
                    for key, val in data.items():
                        self.assertTrue(np.allclose(val, data2[key]))
                    if header2['endian']:
                        self.assertEqual(header['endian'], header2['endian'])

    def test_read_wrong_header(self):
        """Test that we get an error when reading wrong version of TRR."""
        slen = (13, 12)
        fmt = ['1i', '2i', '{}s'.format(slen[0] - 1), '13i']
        with tempfile.NamedTemporaryFile() as tmp:
            with open(tmp.name, 'wb') as outfile:
                outfile.write(struct.pack(fmt[0], _GROMACS_MAGIC))
                outfile.write(struct.pack(fmt[1], *slen))
                outfile.write(struct.pack(fmt[2], b'NOT_GMX_FILE'))
                head = [0, 0, 26, 0, 0, 0, 0, 1000, 0, 0, 10, 0, 0]
                outfile.write(struct.pack(fmt[3], *head))
                outfile.write(struct.pack('1f', 0.0))
                outfile.write(struct.pack('1f', 0.0))
            with self.assertRaises(ValueError):
                for _ in read_trr_file(tmp.name):
                    pass

    def test_read_size(self):
        """Test that we can get double/float when box is missing."""
        slen = (13, 12)
        fmt = ['1i', '2i', '{}s'.format(slen[0] - 1), '13i']
        with tempfile.NamedTemporaryFile() as tmp:
            with open(tmp.name, 'wb') as outfile:
                outfile.write(struct.pack(fmt[0], _GROMACS_MAGIC))
                outfile.write(struct.pack(fmt[1], *slen))
                outfile.write(struct.pack(fmt[2], _TRR_VERSION_B))
                x_size = 3 * 10 * struct.calcsize('f')
                head = [0, 0, 0, 0, 0, 0, 0, x_size, 0, 0, 10, 0, 0]
                outfile.write(struct.pack(fmt[3], *head))
                outfile.write(struct.pack('1f', 0.0))
                outfile.write(struct.pack('1f', 0.0))
            for frame, _ in read_trr_file(tmp.name, read_data=False):
                self.assertFalse(frame['double'])

    def test_read_size_fail(self):
        """Test that we fail when we can't find precision."""
        slen = (13, 12)
        fmt = ['1i', '2i', '{}s'.format(slen[0] - 1), '13i']
        with tempfile.NamedTemporaryFile() as tmp:
            with open(tmp.name, 'wb') as outfile:
                outfile.write(struct.pack(fmt[0], _GROMACS_MAGIC))
                outfile.write(struct.pack(fmt[1], *slen))
                outfile.write(struct.pack(fmt[2], _TRR_VERSION_B))
                x_size = 3 * 10 * (struct.calcsize('d') + 1)
                head = [0, 0, 0, 0, 0, 0, 0, x_size, 0, 0, 10, 0, 0]
                outfile.write(struct.pack(fmt[3], *head))
                outfile.write(struct.pack('1f', 0.0))
                outfile.write(struct.pack('1f', 0.0))
            with self.assertRaises(ValueError):
                for _ in read_trr_file(tmp.name, read_data=False):
                    pass

    def test_overwrite_trr(self):
        """Test that we indeed can turn off the append to TRR."""
        with tempfile.NamedTemporaryFile() as tmp:
            all_data = []
            for i in range(5):
                data = {
                    'natoms': 4,
                    'step': i,
                    'time': 0.002*i,
                    'lambda': 0.0,
                    'box': np.random.ranf(size=(3, 3)),
                    'x': np.random.ranf(size=(4, 3)),
                }
                header = write_trr_frame(tmp.name, data, double=False,
                                         append=False)
                all_data.append((header, data))
            for frame in read_trr_file(tmp.name):
                self.assertTrue(np.allclose(frame[1]['x'],
                                            all_data[-1][1]['x']))


if __name__ == '__main__':
    unittest.main()
