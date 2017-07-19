# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""A test module for the writers.

Here we test that we can write and read different output formats.
"""
import logging
import unittest
import tempfile
import itertools
import os
import numpy as np
from numpy.random import randint, rand
from pyretis.core.path import Path
from pyretis.core.random_gen import MockRandomGenerator
from pyretis.inout.writers.writers import (
    Writer,
    EnergyWriter,
    OrderWriter,
    CrossWriter,
    EnergyPathWriter,
    OrderPathWriter,
    read_some_lines,
    adjust_coordinate,
    read_txt_snapshots,
)
from pyretis.inout.writers.tablewriter import ThermoTable
from pyretis.inout.writers import get_writer, prepare_load


logging.disable(logging.CRITICAL)
HERE = os.path.abspath(os.path.dirname(__file__))


class WriterTest(unittest.TestCase):
    """Test that writers work as intended."""

    def test_get_writer(self):
        """Test that the get_writer method works."""
        wri = get_writer('cross')
        self.assertIsInstance(wri, CrossWriter)
        logging.disable(logging.INFO)
        with self.assertLogs('pyretis.inout.writers', level='ERROR'):
            wri = get_writer('Does not exist')
        logging.disable(logging.CRITICAL)
        self.assertTrue(wri is None)

    def test_prepare_load(self):
        """Test the prepare load method."""
        with self.assertRaises(FileNotFoundError):
            prepare_load('cross', 'no such filename', required=True)
        load = prepare_load('cross', 'no such filename', required=False)
        self.assertTrue(load is None)
        filename = os.path.join(HERE, 'cross.txt')
        prepare_load('cross', filename, required=False)
        with self.assertRaises(ValueError):
            prepare_load('cross-which-is-not', filename, required=False)

    def test_read_some_lines(self):
        """Test the generic reading of files."""
        filename = os.path.join(HERE, 'order-data.txt')
        blocks = read_some_lines(filename)
        correct_data = [
            [[0, 0.1, -0.1], [1, 0.2, -0.2], [2, 0.3, -0.3],
             [3, 0.4, -0.4], [4, 0.5, -0.5]],
            [[0, 1.1, -1.1], [1, 1.2, -1.2], [2, 1.3, -1.3],
             [3, 1.4, -1.4], [4, 1.5, -1.5]],
            [[0, 2.1, -2.1], [1, 2.2, -2.2], [2, 2.3, -2.3],
             [3, 2.4, -2.4], [4, 2.5, -2.5], [5, 2.6, -2.6],
             [6, 2.7, -2.7], [7, 2.8, -2.8]],
            [[0, 3.1, -3.1], [1, 3.2, -3.2], [2, 3.3, -3.3]],
            [[0, 4.1, -4.1], [2, 4.3, -4.3], [3, 4.4, -4.4]],
        ]
        for i, data in enumerate(blocks):
            self.assertEqual(
                data['comment'][0],
                '# Cycle: {}, status: ACC'.format(i)
            )
            self.assertEqual(
                data['comment'][1],
                '#     Time       Orderp',
            )
            for j, k in zip(correct_data[i], data['data']):
                self.assertTrue(np.allclose(j, k))

    def test_writer_header(self):
        """Test that the header work as intended."""
        writer = Writer('test-file', header=None)
        self.assertTrue(writer.header is None)

        with self.assertRaises(AttributeError):
            Writer('test-file', header='Just a text header')

        txt = 'This is the header, it is very long indeed'
        writer = Writer('test-file', header={'text': txt})
        self.assertEqual(writer.header, txt)

        writer = Writer('test-file', header={'text': txt, 'width': 10})
        self.assertEqual(writer.header, txt)

        writer = Writer(
            'test-file',
            header={'width': (10, 10),
                    'labels': ('Label1', 'Label2')},
        )
        self.assertEqual(writer.header, '#   Label1     Label2')
        writer.header = txt
        self.assertEqual(writer.header, txt)

    def test_read_txt_snapshot(self):
        """Test the read_txt_snapshot method."""
        filename = os.path.join(HERE, 'config.txt')
        read1 = read_txt_snapshots(filename)
        read2 = read_txt_snapshots(filename,
                                   data_keys=('name', 'x', 'y', 'z'))
        correct = {
            'atomname': [['X', 'Y'], ['A', 'B']],
            'box': [np.array([1., 2., 3., 4., 5., 6.]),
                    np.array([7., 8., 9.])],
            'x': [[1.0, 7.0], [1.1, 7.1]],
            'y': [[2.0, 8.0], [2.1, 8.1]],
            'z': [[3.0, 9.0], [3.1, 9.1]],
            'vx': [[4.0, 1.0], [4.1, 1.1]],
            'vy': [[5.0, 2.0], [5.1, 2.1]],
            'vz': [[6.0, 3.0], [6.1, 3.1]],
        }
        for i, (snap1, snap2) in enumerate(zip(read1, read2)):
            self.assertTrue(snap1['atomname'] == correct['atomname'][i])
            self.assertTrue(snap2['name'] == correct['atomname'][i])
            for j in ('x', 'y', 'z', 'box'):
                self.assertTrue(np.allclose(snap1[j], correct[j][i]))
                self.assertTrue(np.allclose(snap2[j], correct[j][i]))
            for j in ('vx', 'vy', 'vz'):
                self.assertTrue(np.allclose(snap1[j], correct[j][i]))
                self.assertFalse(j in snap2)


class TableWritersTest(unittest.TestCase):
    """Test that table writers work as intended."""

    def test_thermo_table(self):
        """Test the thermo table."""
        table = ThermoTable()
        data = dict(step=100, temp=1.2345, vpot=5.4321e3, ekin=2.222,
                    etot=3.456, press=1.011e9)
        line = ('       100        1.2345        5432.1         '
                '2.222         3.456     1.011e+09')
        for lines in table.generate_output(100, data):
            self.assertMultiLineEqual(lines, line)
            break
        data = dict(step=100, temp=1.2345, vpot=5.4321e3, ekin=2.222,
                    etot=3.456, press=101.11111111)
        line = ('       100        1.2345        5432.1         '
                '2.222         3.456       101.111')
        for lines in table.generate_output(100, data):
            self.assertMultiLineEqual(lines, line)
            break


class TestCrossWriter(unittest.TestCase):
    """Test the CrossWriter."""

    def test_cross_writer(self):
        """Test that we write and read cross files."""
        cross_writer = CrossWriter()
        cross_reader = CrossWriter()
        all_data = []
        with tempfile.NamedTemporaryFile() as temp:
            string = '{}\n'.format(cross_writer.header)
            temp.write(string.encode('utf-8'))
            prev = 0
            for i in range(50):
                interf = randint(1, 10)
                step = prev + randint(1, 1000)
                prev = step
                direction = 1 if randint(0, 2) == 1 else -1
                all_data.append((step, interf, direction))
                data = (step, interf, ['-', '+', '+'][direction + 1])
                for lines in cross_writer.generate_output(i, [data]):
                    string = '{}\n'.format(lines)
                    temp.write(string.encode('utf-8'))
            del cross_writer
            temp.flush()
            for block in cross_reader.load(temp.name):
                for data1, data2 in zip(block['data'], all_data):
                    self.assertEqual(data1[0], data2[0])
                    self.assertEqual(data1[1], data2[1] + 1)
                    self.assertEqual(data1[2], data2[2])

    def test_cross_writer_error(self):
        """Test reading when file contains errors."""
        filename1 = os.path.join(HERE, 'cross-error.txt')
        cross = prepare_load('cross', filename1, required=False)
        filename2 = os.path.join(HERE, 'cross.txt')
        cross_correct = prepare_load('cross', filename2, required=False)
        correct = next(cross_correct)
        missing = next(cross)
        for i, data in enumerate(correct['data']):
            if i < 10:
                self.assertEqual(data, missing['data'][i])
            elif i == 10:
                pass
            else:
                self.assertEqual(data, missing['data'][i-1])


class TestEnergyWriter(unittest.TestCase):
    """Test the EnergyWriter."""

    def test_energy_file_writer(self):
        """Test that we write and read energy files."""
        energy_writer = EnergyWriter()
        energy_reader = EnergyWriter()
        fields = ['vpot', 'ekin', 'etot', 'temp']
        all_data = []
        with tempfile.NamedTemporaryFile() as temp:
            string = '{}\n'.format(energy_writer.header)
            temp.write(string.encode('utf-8'))
            for i in range(50):
                rnd = rand(len(fields))
                all_data.append([i])
                all_data[-1].extend(rnd)
                data = {key: rndi for (key, rndi) in zip(fields, rnd)}
                for lines in energy_writer.generate_output(i, data):
                    string = '{}\n'.format(lines)
                    temp.write(string.encode('utf-8'))
            del energy_writer
            temp.flush()
            all_data = np.array(all_data)
            for block in energy_reader.load(temp.name):
                data = block['data']
                for i, key in enumerate(itertools.chain(['time'], fields)):
                    for num1, num2 in zip(data[key], all_data[:, i]):
                        self.assertAlmostEqual(num1, num2, 6)

    def test_energy_writer_error(self):
        """Test reading of file with errors."""
        filename1 = os.path.join(HERE, 'energy.txt')
        energy1 = prepare_load('energy', filename1, required=False)
        correct = next(energy1)
        filename2 = os.path.join(HERE, 'energy-error.txt')
        energy2 = prepare_load('energy', filename2, required=False)
        missing = next(energy2)
        for key, val in correct['data'].items():
            for i, vali in enumerate(val):
                if i < 1:
                    self.assertEqual(vali, missing['data'][key][i])
                elif i == 1:
                    pass
                else:
                    self.assertEqual(vali, missing['data'][key][i-1])

    def test_energy_missing_data(self):
        """Test the energy formatting when some data is missing."""
        energy_writer = EnergyWriter()
        data = {'vpot': 1.0, 'ekin': 2.0, 'etot': 3.0}
        txt = energy_writer.format_data(0, data)
        self.assertEqual(txt.strip().split()[-1], 'nan')


class TestOrderWriter(unittest.TestCase):
    """Test the OrderWriter class."""

    def test_order_parameter_writer(self):
        """Test that we write and read order parameter files."""
        order_writer = OrderWriter()
        order_reader = OrderWriter()
        all_data = []
        extra = 3  # number of extra order parameters to simulate here.
        with tempfile.NamedTemporaryFile() as temp:
            string = '{}\n'.format(order_writer.header)
            temp.write(string.encode('utf-8'))
            for i in range(50):
                rnd = rand(2 * (1 + extra))
                all_data.append([i])
                all_data[-1].extend(rnd)
                for lines in order_writer.generate_output(i, rnd):
                    string = '{}\n'.format(lines)
                    temp.write(string.encode('utf-8'))
            del order_writer
            temp.flush()
            all_data = np.array(all_data)
            for block in order_reader.load(temp.name):
                data = block['data']
                for row1, row2 in zip(all_data, data):
                    for num1, num2 in zip(row1, row2):
                        self.assertAlmostEqual(num1, num2, 6)


def _create_test_paths(npath=5):
    """Create some paths we can use.

    Parameters
    ----------
    npath : integer
        The number of paths to create.
    """
    paths = []
    correct_data = []
    for i in range(npath):
        length = randint(10, 100)
        path = Path(rgen=MockRandomGenerator(seed=0))
        data_copy = {}
        for j in range(length):
            phasepoint = {'order': [i, j],
                          'vpot': i + j,
                          'ekin': i + j + 1,
                          'pos': np.ones((9, 3)) * i * j,
                          'vel': np.ones((9, 3)) * i * j * -1}
            path.append(phasepoint)
            for key in phasepoint:
                if key not in data_copy:
                    data_copy[key] = []
                data_copy[key].append(phasepoint[key])
        paths.append(path)
        correct_data.append(data_copy)
    return paths, correct_data


class TestPathWriter(unittest.TestCase):
    """Test that the PathWriter classes work as intended."""

    def test_write_energy_path(self):
        """Test that we can read & write energy info for paths."""
        energy_writer = EnergyPathWriter()
        with tempfile.NamedTemporaryFile() as temp:
            paths, correct_data = _create_test_paths(npath=5)
            for i, path in enumerate(paths):
                for lines in energy_writer.generate_output(i, path, 'ACC'):
                    string = '{}\n'.format(lines)
                    temp.write(string.encode('utf-8'))
            temp.flush()
            energy_reader = EnergyPathWriter()
            for i, block in enumerate(energy_reader.load(temp.name)):
                for key in ('ekin', 'vpot'):
                    self.assertTrue(np.allclose(block['data'][key],
                                                correct_data[i][key]))

    def test_write_order_path(self):
        """Test that we can read & write order info for paths."""
        order_writer = OrderPathWriter()
        with tempfile.NamedTemporaryFile() as temp:
            paths, correct_data = _create_test_paths(npath=5)
            for i, path in enumerate(paths):
                for lines in order_writer.generate_output(i, path, 'ACC'):
                    string = '{}\n'.format(lines)
                    temp.write(string.encode('utf-8'))
            temp.flush()
            order_reader = OrderPathWriter()
            for i, block in enumerate(order_reader.load(temp.name)):
                corr = np.array(correct_data[i]['order'])
                self.assertTrue(np.allclose(block['data'][:, 0], corr[:, 1]))
                self.assertTrue(np.allclose(block['data'][:, 1], corr[:, 0]))
                self.assertTrue(np.allclose(block['data'][:, 2], corr[:, 1]))


if __name__ == '__main__':
    unittest.main()
