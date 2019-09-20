# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the FileIO class."""
import filecmp
import logging
import os
import tempfile
import unittest
import numpy as np
from numpy.random import randint, rand
from pyretis.core.path import Path
from pyretis.core.pathensemble import PathEnsemble
from pyretis.inout.formats.formatter import OutputFormatter
from pyretis.inout.formats.snapshot import read_txt_snapshots
from pyretis.inout.fileio import FileIO
from pyretis.inout.formats.energy import EnergyFile, EnergyPathFile
from pyretis.inout.formats.cross import CrossFile
from pyretis.inout.formats.order import OrderFile, OrderPathFile
from pyretis.inout.formats.pathensemble import PathEnsembleFile
from pyretis.inout.formats.path import PathExtFile, PathIntFile
from pyretis.inout.formats.snapshot import SnapshotFile
from .help import (
    assert_equal_path_dict,
    create_external_path,
    create_test_paths,
    turn_on_logging,
    remove_file,
    set_up_system,
)

logging.disable(logging.CRITICAL)


HERE = os.path.abspath(os.path.dirname(__file__))


PATH_DATA = [
    {
        'cycle': 0, 'generated': ['ki', 0.0, 0, 0],
        'interface': ('L', 'M', 'L'), 'length': 494,
        'ordermax': (-0.765171027, 255), 'ordermin': (-0.9002987171, 0),
        'status': 'ACC', 'weight': 1.,
    },
    {
        'cycle': 1, 'generated': ['s-', 0.0, 0, 0],
        'interface': ('L', 'M', 'L'), 'length': 400,
        'ordermax': (-0.8643118362, 136),
        'ordermin': (-0.9004062103, 399),
        'status': 'ACC', 'weight': 1.,
    },
    {
        'cycle': 2, 'generated': ['tr', 0.0, 0, 0],
        'interface': ('L', 'M', 'L'), 'length': 400,
        'ordermax': (-0.8643118362, 263), 'ordermin': (-0.9004062103, 0),
        'status': 'ACC', 'weight': 1.,
    },
]


class TestFileIO(unittest.TestCase):
    """Test the FileIO class."""

    def test_initiation(self):
        """Test initiation and opening of files."""
        with turn_on_logging():
            with self.assertLogs('pyretis.inout.fileio', level='INFO'):
                FileIO('some-name', 'r', None, backup='not-an-option!')

        # Test for completely new file:
        filename = os.path.join(HERE, 'a_new_file')
        remove_file(filename)
        fileio = FileIO(filename, 'w', None, backup=False)
        self.assertIsNone(fileio.fileh)
        fileio.open()
        self.assertIsNotNone(fileio.fileh)
        fileio.write('test')
        fileio.close()
        remove_file(filename)

        # Test when a file exists:
        filename = os.path.join(HERE, 'already_exists2')
        remove_file(filename)
        remove_file('{}_000'.format(filename))
        with open(filename, 'w') as fileh:
            fileh.write('test')
        fileio = FileIO(filename, 'w', None, backup=True)
        fileio.open()
        fileio.write('text')
        self.assertIsNotNone(fileio.fileh)
        self.assertTrue(os.path.isfile(filename))
        self.assertTrue(os.path.isfile('{}_000'.format(filename)))
        del fileio
        remove_file(filename)
        remove_file('{}_000'.format(filename))
        # Test for invalid filename + context manager:
        with turn_on_logging():
            with self.assertLogs('pyretis.inout.fileio',
                                 level='CRITICAL'):
                with FileIO('/#"½%&?<><|*', 'r', None) as some_file:
                    self.assertEqual(some_file.file_mode, 'r')
                    lines = [i for i in some_file]
                    self.assertFalse(lines)
        # Test for weird mode:
        fileio = FileIO('some-file', 'q', None)
        with self.assertRaises(ValueError):
            fileio.open()
        fileio = FileIO('some-file', 'r', None)
        fileio.file_mode = 'q'
        with self.assertRaises(ValueError):
            fileio.open_file_read()
        fileio = FileIO('some-file', 'w', None)
        fileio.file_mode = 'q'
        with self.assertRaises(ValueError):
            fileio.open_file_write()

    def test_write_modes(self):
        """Test the write modes and backup settings."""
        with tempfile.NamedTemporaryFile() as tmp:
            with FileIO(tmp.name, 'w', None, backup=True) as fileio:
                self.assertIsNotNone(fileio.fileh)
                self.assertFalse(fileio.fileh.closed)
                fileio.write('some text')
            with FileIO(tmp.name, 'a', None, backup=True) as fileio:
                self.assertIsNotNone(fileio.fileh)
                self.assertFalse(fileio.fileh.closed)
                status = fileio.write('some text')
                self.assertTrue(status)
                status = fileio.write('some text', end=None)
                self.assertTrue(status)
                status = fileio.write(None)
                self.assertFalse(status)
            fileio = FileIO(tmp.name, 'w', None, backup=True)
            fileio.open()
            fileio.close()
            with turn_on_logging():
                with self.assertLogs('pyretis.inout.fileio',
                                     level='WARNING'):
                    fileio.write('text')
            fileio = FileIO(tmp.name, 'a', None, backup='True')
            with turn_on_logging():
                with self.assertLogs('pyretis.inout.fileio',
                                     level='WARNING'):
                    fileio.write('text')

    def test_reading(self):
        """Test generic reading."""
        filename = os.path.join(HERE, 'energy.txt')
        correct = []
        with open(filename, 'r') as infile:
            correct = [line for line in infile]
        lines = []
        with FileIO(filename, 'r', OutputFormatter('test')) as fileio:
            for line in fileio:
                lines.append(line)
        self.assertListEqual(lines, correct)
        with FileIO(filename, 'r', OutputFormatter('test')) as fileio:
            fileio.close()
            lines = [line for line in fileio]
            self.assertFalse(lines)

    def test_load(self):
        """Test generic load."""
        filename = os.path.join(HERE, 'energy.txt')
        with FileIO(filename, 'r', OutputFormatter('test')) as fileio:
            for block in fileio.load():
                self.assertEqual(
                    block['comment'],
                    [('#     Time      Potential        Kinetic'
                      '          Total    Temperature')],
                )

    def test_output(self):
        """Test generic output."""
        data = [1, 2.0, 3.123456]
        with tempfile.NamedTemporaryFile() as tmp:
            with FileIO(tmp.name, 'w', OutputFormatter('test'),
                        backup=False) as fileio:
                fileio.output(1, data)
                fileio.output(2, data)
            tmp.flush()
            with FileIO(tmp.name, 'r', OutputFormatter('test')) as fileio:
                for block in fileio.load():
                    for i, line in enumerate(block['data']):
                        raw = [i + 1] + data
                        self.assertListEqual(line, raw)
        with tempfile.NamedTemporaryFile() as tmp:
            fileio = FileIO(tmp.name, 'w', OutputFormatter(''), backup=False)
            fileio.open()
            fileio.output(1, data)
            fileio.flush()
            fileio.close()
            fileio.flush()

    def test_formatter_info(self):
        """Test the formatter info method."""
        fileio = FileIO('My-name-is-nobody', 'r', None)
        info = fileio.formatter_info()
        self.assertIsNone(info)
        formatter = OutputFormatter('Yippee ki-yay')
        fileio = FileIO('My-name-is-nobody', 'r', formatter)
        info = fileio.formatter_info()
        self.assertEqual(info, OutputFormatter)


class TestEnergyFile(unittest.TestCase):
    """Test the energy file i/o."""

    def test_energy_fileio(self):
        """Test reading and writing for energy files."""
        fields = ['vpot', 'ekin', 'etot', 'temp']
        with tempfile.NamedTemporaryFile() as tmp:
            raw_data = []
            with EnergyFile(tmp.name, 'w') as efile:
                for i in range(50):
                    rnd = rand(len(fields))
                    raw_data.append([i] + [j for j in rnd])
                    data = {key: j for (key, j) in zip(fields, rnd)}
                    efile.output(i, data)
            tmp.flush()
            raw_data = np.array(raw_data)
            with EnergyFile(tmp.name, 'r') as efile:
                for block in efile.load():
                    data = block['data']
                    for i, key in enumerate(['time'] + fields):
                        for num1, num2 in zip(raw_data[:, i], data[key]):
                            self.assertAlmostEqual(num1, num2, 6)

    def test_energy_file_read(self):
        """Test reading existing energy data."""
        filename = os.path.join(HERE, 'energy.txt')
        correct = {
            'time': [0, 1000, 2000],
            'vpot': [-0.165063, -0.806879, -0.760215],
            'ekin': [0.035000, 0.328694, 0.041118],
            'etot': [-0.130063, -0.478185, -0.719097],
            'temp': [0.070000, 0.657387, 0.082236],
        }
        with EnergyFile(filename, 'r') as efile:
            for block in efile.load():
                for key, val in correct.items():
                    self.assertTrue(np.allclose(val, block['data'][key]))
        # Reading a file with errors, this should give a warning:
        filename = os.path.join(HERE, 'energy-error.txt')
        with turn_on_logging():
            with self.assertLogs('pyretis.inout.fileio',
                                 level='WARNING'):
                with EnergyFile(filename, 'r') as efile:
                    for _ in efile.load():
                        pass


class TestCrossFile(unittest.TestCase):
    """Test the cross file i/o."""

    def test_cross_fileio(self):
        """Test reading and writing for cross files."""
        with tempfile.NamedTemporaryFile() as tmp:
            raw_data = []
            with CrossFile(tmp.name, 'w') as cfile:
                prev = 0
                for i in range(50):
                    interf = randint(1, 10)
                    step = prev + randint(1, 1000)
                    prev = step
                    direction = 1 if randint(0, 2) == 1 else -1
                    raw_data.append((step, interf + 1, direction))
                    data = [(step, interf, ('-', '+', '+')[direction + 1])]
                    cfile.output(i, data)
            tmp.flush()
            with CrossFile(tmp.name, 'r') as cfile:
                for block in cfile.load():
                    data = block['data']
                    for i, j in zip(data, raw_data):
                        self.assertEqual(i, j)

    def test_cross_fileread(self):
        """Test reading from existing files."""
        filename1 = os.path.join(HERE, 'cross-error.txt')
        filename2 = os.path.join(HERE, 'cross.txt')
        data1 = None
        with turn_on_logging():
            with self.assertLogs('pyretis.inout.fileio',
                                 level='WARNING'):
                with CrossFile(filename1, 'r') as cfile:
                    for block in cfile.load():
                        data1 = block['data']
        data2 = None
        with CrossFile(filename2, 'r') as cfile:
            for block in cfile.load():
                data2 = block['data']
        for i, line in enumerate(data2):
            if i < 10:
                self.assertEqual(line, data1[i])
            elif i == 10:
                pass
            else:
                self.assertEqual(line, data1[i-1])


class TestOrderFile(unittest.TestCase):
    """Test the order parameter file i/o."""

    def test_order_parameter_fileio(self):
        """Test writing and reading of order parameter files."""
        extra = 3
        with tempfile.NamedTemporaryFile() as tmp:
            raw_data = []
            with OrderFile(tmp.name, 'w') as ofile:
                for i in range(50):
                    rnd = rand(1 + extra)
                    raw_data.append([i] + [j for j in rnd])
                    ofile.output(i, rnd)
            tmp.flush()
            with OrderFile(tmp.name, 'r') as ofile:
                for block in ofile.load():
                    data = block['data']
                    for i, j in zip(data, raw_data):
                        for num1, num2 in zip(i, j):
                            self.assertAlmostEqual(num1, num2, 6)

    def test_order_parameter_read(self):
        """Test reading of order parameter data from a file."""
        filename = os.path.join(HERE, 'order-data.txt')
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
        with OrderFile(filename, 'r') as ofile:
            for i, data in enumerate(ofile.load()):
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


class TestPathFiles(unittest.TestCase):
    """Test file i/o for path files."""

    def test_energy_path_file(self):
        """Test i/o for energy path data."""
        paths, correct_data = create_test_paths(npath=5)
        with tempfile.NamedTemporaryFile() as tmp:
            for i, path in enumerate(paths):
                with EnergyPathFile(tmp.name, 'a') as efile:
                    efile.output(i, [path, 'ACC'])
            tmp.flush()
            with EnergyPathFile(tmp.name, 'r') as efile:
                for i, block in enumerate(efile.load()):
                    for key in ('ekin', 'vpot'):
                        self.assertTrue(np.allclose(block['data'][key],
                                                    correct_data[i][key]))

    def test_order_path_file(self):
        """Test i/o for order path data."""
        paths, correct_data = create_test_paths(npath=5)
        with tempfile.NamedTemporaryFile() as tmp:
            for i, path in enumerate(paths):
                with OrderPathFile(tmp.name, 'a') as ofile:
                    ofile.output(i, [path, 'ACC'])
            tmp.flush()
            with OrderPathFile(tmp.name, 'r') as ofile:
                for i, block in enumerate(ofile.load()):
                    corr = np.array(correct_data[i]['order'])
                    data = block['data']
                    self.assertTrue(np.allclose(data[:, 1], corr[:, 0]))
                    self.assertTrue(np.allclose(data[:, 2], corr[:, 1]))
                    self.assertTrue(np.allclose(data[:, 3], corr[:, 2]))

    def test_path_int_file(self):
        """Test the internal path writer."""
        paths, _ = create_test_paths(npath=3)
        with tempfile.NamedTemporaryFile() as tmp:
            for i, path in enumerate(paths):
                with PathIntFile(tmp.name, 'a') as pfile:
                    pfile.output(i, [path, 'ACC'])
            tmp.flush()
            with PathIntFile(tmp.name, 'r') as pfile:
                for i, block in enumerate(pfile.load()):
                    self.assertEqual('# Cycle: {}, status: ACC'.format(i),
                                     block['comment'][0])

    def test_path_ext_file(self):
        """Test the external path writer."""
        with tempfile.NamedTemporaryFile() as tmp:
            for i in range(3):
                path, _ = create_external_path(random_length=True)
                with PathExtFile(tmp.name, 'a') as pfile:
                    pfile.output(i, [path, 'ACC'])
            tmp.flush()
            with PathExtFile(tmp.name, 'r') as pfile:
                for i, block in enumerate(pfile.load()):
                    self.assertEqual('# Cycle: {}, status: ACC'.format(i),
                                     block['comment'][0])


class TestPathEnsembleFile(unittest.TestCase):
    """Test the i/o for the PathEnsembleFile."""

    @staticmethod
    def test_path_ensemble_read():
        """Test reading of path ensemble files."""
        filename = os.path.join(HERE, 'pathensemble001.txt')
        with PathEnsembleFile(filename, 'r') as pfile:
            for i, path in enumerate(pfile.get_paths()):
                assert_equal_path_dict(path, PATH_DATA[i])

    @staticmethod
    def _fake_path_from_dict(path_dict):
        """Return a path object from a path dict."""
        path = Path(None)
        path.generated = path_dict['generated']
        avg = 0.5 * (path_dict['ordermax'][0] + path_dict['ordermin'][0])
        for i in range(path_dict['length']):
            path.append(
                set_up_system([avg, i], [0], [0], vpot=0, ekin=0)
            )
        if path_dict['interface'][0] == 'L':
            path.phasepoints[0].order[0] = path_dict['ordermin'][0] + 0.0001
        if path_dict['interface'][0] == 'R':
            path.phasepoints[0].order[0] = path_dict['ordermax'][0]
        if path_dict['interface'][-1] == 'L':
            path.phasepoints[-1].order[0] = path_dict['ordermin'][0] + 0.0001
        if path_dict['interface'][-1] == 'R':
            path.phasepoints[-1].order[0] = path_dict['ordermax'][0]
        for key in ('ordermax', 'ordermin'):
            idx = path_dict[key][1]
            path.phasepoints[idx].order[0] = path_dict[key][0]
        return path

    def test_path_ensemble_write(self):
        """Test writing of path ensemble data."""
        filename = os.path.join(HERE, 'pathensemble001.txt')
        settings = {
            'ensemble_number': 1,
            'interfaces': [-0.9, -0.9, 1],
            'detect': -0.8
        }
        ens = PathEnsemble(settings['ensemble_number'],
                           settings['interfaces'],
                           detect=settings['detect'])
        with tempfile.NamedTemporaryFile() as tmp:
            with PathEnsembleFile(tmp.name, 'w',
                                  ensemble_settings=settings) as pfile:
                for pathi in PATH_DATA:
                    path = self._fake_path_from_dict(pathi)
                    ens.add_path_data(path, pathi['status'],
                                      cycle=pathi['cycle'])
                    pfile.output(pathi['cycle'], ens)
            tmp.flush()
            self.assertTrue(filecmp.cmp(tmp.name, filename))
        # Test warning when ensemble settings are not given:
        with turn_on_logging():
            with self.assertLogs('pyretis.inout.formats.pathensemble',
                                 level='WARNING'):
                with PathEnsembleFile(filename, 'r') as pfile:
                    pass
        # Test open missing file:
        with PathEnsembleFile('path_mack_path/file__', 'r',
                              ensemble_settings=settings) as pfile:
            with turn_on_logging():
                with self.assertLogs('pyretis.inout.formats.pathensemble',
                                     level='CRITICAL'):
                    for _ in pfile.load():
                        pass


class TestSnapshot(unittest.TestCase):
    """Test methods related to the snapshot files."""

    def test_initiate_settings(self):
        """Test initiation of the snapshot file with settings."""
        settings = {'write_vel': False, 'extra-to-ignore': False}
        with tempfile.NamedTemporaryFile() as tmp:
            with SnapshotFile(tmp.name, 'r',
                              format_settings=settings) as sfile:
                self.assertFalse(sfile.formatter.write_vel)

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
        filename = os.path.join(HERE, 'config_with_error.txt')
        read3 = read_txt_snapshots(filename)
        context = None
        with self.assertRaises(Exception) as context:
            for i in read3:
                print(i)
        self.assertTrue('Oops_not_an_integer' in str(context.exception))
        self.assertTrue('invalid literal for int()' in str(context.exception))
        # Also test the file writer:
        filename = os.path.join(HERE, 'config.txt')
        with SnapshotFile(filename, 'r') as traj:
            for i, data in enumerate(traj.load()):
                for j in ('x', 'y', 'z', 'box'):
                    self.assertTrue(np.allclose(data[j], correct[j][i]))


if __name__ == '__main__':
    unittest.main()
