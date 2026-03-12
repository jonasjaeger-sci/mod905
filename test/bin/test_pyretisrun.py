# -*- coding: utf-8 -*-
# Copyright (c) 2026, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the bin."""
import logging
import os
import unittest
import shutil
import subprocess
import types
import tempfile
import tqdm  # For a progress bar
from io import StringIO
from unittest.mock import patch
from collections.abc import Iterable
from pyretis.bin.pyretisrun import (hello_world,
                                    use_tqdm,
                                    bye_bye_world,
                                    set_up_simulation,
                                    run_generic_simulation,
                                    main,
                                    _RUNNERS)
from pyretis.setup import create_simulation
from pyretis.inout.settings import parse_settings_file

logging.disable(logging.CRITICAL)
HERE = os.path.abspath(os.path.dirname(__file__))


class test_pyretis_main_runner(unittest.TestCase):
    """Test Main."""

    def test_pyretisrun(self):
        """Test pyretisrun."""
        with patch('sys.stdout', new=StringIO()) as stdout:
            with subprocess.Popen(['pyretisrun', '-V'],
                                  stdout=subprocess.PIPE) as ex:
                asd = ex.stdout.read().split()
            self.assertTrue(b'PyRETIS' in asd)

            with subprocess.Popen(['pyretisrun'],
                                  stderr=subprocess.PIPE) as ex:
                asd = ex.stderr.read().split()
            self.assertTrue(b'pyretisrun' in asd)

    def test_pyretisrun2(self):
        """Test pyretisrun by actually running a retis sim with 0 steps."""
        input_file = 'dummy_input.rst'
        with patch('sys.stdout', new=StringIO()):
            with tempfile.TemporaryDirectory() as tempdir:
                shutil.copyfile(os.path.join(HERE, input_file),
                                os.path.join(tempdir, input_file))
                with subprocess.Popen(['pyretisrun', '-i', input_file, '-p',
                                       '-l', 'DEBUG'],
                                      cwd=tempdir,
                                      stderr=subprocess.DEVNULL,
                                      stdout=subprocess.PIPE) as ex:
                    asd = ex.stdout.read().split()
        self.assertTrue(b'Riccardi' in asd)
        self.assertTrue(b'"kick"' in asd)

    def test_exit(self):
        """Test pyretisrun exit by creating an EXIT file."""
        infile = 'dummy_input.rst'
        with tempfile.TemporaryDirectory() as tempdir:
            input_file = os.path.join(tempdir, infile)
            shutil.copyfile(os.path.join(HERE, infile), input_file)
            with patch('sys.stdout', new=StringIO()) as stdout:
                open(tempdir + '/EXIT', 'w').close()
                main(input_file, tempdir, tempdir,
                     progress=False, log_level=20)
                asd = stdout.getvalue().strip()
        self.assertIn('EXIT file found', asd)

    def test_main(self):
        """Test the main() function for a tis task."""
        infile = 'dummy_input.rst'
        with tempfile.TemporaryDirectory() as tempdir:
            input_file = os.path.join(tempdir, infile)
            shutil.copyfile(os.path.join(HERE, infile), input_file)
            with patch('sys.stdout', new=StringIO()) as stdout:
                main(input_file, tempdir, tempdir, progress=False, log_level=9)
                asd = stdout.getvalue().strip()
            self.assertIn('Execution ended', asd)
            with patch('sys.stdout', new=StringIO()) as stdout:
                input_file = os.path.join(tempdir, 'does_not_exist.rst')
                self.assertRaises(ValueError, main, input_file, tempdir,
                                  tempdir, progress=False,
                                  log_level=9)
                asd = stdout.getvalue().strip()
            self.assertIn('ERROR - execution stopped.', asd)

    def test_run_simulation(self):
        """Test all simulations functions."""
        infile = 'dummy_input.rst'
        runners = _RUNNERS
        runners['umbrellawindow'] = run_generic_simulation
        for key, runner in runners.items():
            with patch('sys.stdout', new=StringIO()):
                with tempfile.TemporaryDirectory() as tempdir:
                    if key in ['repptis', 'retis']:
                        continue
                    input_file = os.path.join(tempdir, infile)
                    shutil.copyfile(os.path.join(HERE, infile), input_file)
                    sim_settings = parse_settings_file(input_file)
                    sim_settings['simulation']['exe_path'] = tempdir
                    sim_settings['engine']['exe_path'] = tempdir
                    for ens in sim_settings['ensemble']:
                        ens['simulation']['exe_path'] = tempdir
                        ens['engine']['exe_path'] = tempdir
                    sim_settings['simulation']['task'] = key
                    sim = create_simulation(sim_settings)
                    self.assertTrue(runner(sim, sim_settings))

    def test_simulation_exit(self):
        """Test exit feature of explore_simulation and run_path_simulation."""
        infile = 'dummy_input.rst'
        runners = _RUNNERS
        for key, runner in runners.items():
            with patch('sys.stdout', new=StringIO()):
                with tempfile.TemporaryDirectory() as tempdir:
                    if key not in ('tis', 'explore'):
                        continue
                    input_file = os.path.join(tempdir, infile)
                    shutil.copyfile(os.path.join(HERE, infile), input_file)
                    sim_settings = parse_settings_file(input_file)
                    sim_settings['simulation']['exe_path'] = tempdir
                    sim_settings['engine']['exe_path'] = tempdir
                    for ens in sim_settings['ensemble']:
                        ens['simulation']['exe_path'] = tempdir
                        ens['engine']['exe_path'] = tempdir
                    sim_settings['simulation']['task'] = key
                    sim = create_simulation(sim_settings)
                    open(tempdir + '/EXIT', 'w').close()
                    self.assertFalse(runner(sim, sim_settings))

    def test_use_tqdm(self):
        """Test tqdm."""
        bar = use_tqdm(progress=True)
        self.assertEqual(type(bar), type(tqdm.tqdm))
        self.assertTrue(bar is tqdm.tqdm)
        self.assertFalse(isinstance(bar, Iterable))

        bar = use_tqdm(progress=False)
        self.assertTrue(bar is not tqdm.tqdm)
        self.assertTrue(isinstance(bar, types.FunctionType))
        value = bar(iterable='something1', dummy='something2')
        self.assertEqual(value, 'something1')

    def test_hello_world(self):
        """Test that we are polite."""
        with patch('sys.stdout', new=StringIO()) as stdout:
            hello_world(infile='I_can_read_your_mind.rst',
                        rundir=HERE,
                        logfile='nothing_to_declare')
        self.assertIn('Start', stdout.getvalue().strip())

    def test_bye_world(self):
        """Test that we can die."""
        with patch('sys.stdout', new=StringIO()) as stdout:
            bye_bye_world()
        self.assertIn('reference', stdout.getvalue().strip())

    def test_set_up_simulation(self):
        """Test that we know how to set up a simulation."""
        inputfile = 'a_non_existent_input.rst'
        with self.assertRaises(ValueError) as err:
            set_up_simulation(inputfile, HERE)
        self.assertEqual('Input file "{}" NOT found!'.format(inputfile),
                         str(err.exception))

        inputfile = os.path.join(HERE, 'dummy_input.rst')
        with patch('sys.stdout', new=StringIO()) as stdout:
            set_up_simulation(inputfile, HERE)
        self.assertIn('Reading', stdout.getvalue().strip())


if __name__ == '__main__':
    unittest.main()
