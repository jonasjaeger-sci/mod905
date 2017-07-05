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
from pyretis.inout.writers.writers import (EnergyWriter, OrderWriter,
                                           CrossWriter)
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
                rand = np.random.rand(len(fields))
                all_data.append([i])
                all_data[-1].extend(rand)
                data = {key: randi for (key, randi) in zip(fields, rand)}
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
                rand = np.random.rand(2 * (1 + extra))
                all_data.append([i])
                all_data[-1].extend(rand)
                for lines in order_writer.generate_output(i, rand):
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
                interf = np.random.randint(1, 10)
                step = prev + np.random.randint(1, 1000)
                prev = step
                direction = [-1, 1][np.random.randint(0, 2)]
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


if __name__ == '__main__':
    unittest.main()
