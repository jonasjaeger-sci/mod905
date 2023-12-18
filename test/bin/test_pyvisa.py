# -*- coding: utf-8 -*-
# Copyright (c) 2023, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the bin."""
import os
import unittest
import subprocess
import tempfile
import shutil
from io import StringIO
from unittest.mock import patch
from pyretis.bin.pyvisa import (main,
                                hello_pyvisa,
                                bye_pyvisa,
                                pyvisa_visual)

HERE = os.path.abspath(os.path.dirname(__file__))


class TestVarious(unittest.TestCase):
    """Test Main."""

    def test_pyvisarun(self):
        """Test pyvisa run."""
        with tempfile.TemporaryDirectory() as tempdir:
            with subprocess.Popen(['pyvisa', '-cmp'], cwd=tempdir,
                                  stdout=subprocess.PIPE) as ex:
                asd = ex.stdout.read().split()
            self.assertIn(b'PyVisA', asd)

        with tempfile.TemporaryDirectory() as tempdir:
            with subprocess.Popen(['pyvisa', '-recalculate'], cwd=tempdir,
                                  stdout=subprocess.PIPE) as ex:
                asd = ex.stdout.read().split()
            self.assertIn(b'PyVisA', asd)

        with tempfile.TemporaryDirectory() as tempdir:
            input_file = 'dummy_input.rst'
            with subprocess.Popen(['pyvisa', '-i', input_file, '-cmp'],
                                  cwd=tempdir, stdout=subprocess.PIPE) as ex:
                asd = ex.stdout.read().split()
            self.assertIn(b'PyVisA', asd)

    def test_hello_world(self):
        """Test that we are polite."""
        with patch('sys.stdout', new=StringIO()) as stdout:
            hello_pyvisa(run_dir='.', infile='This_is_enough.lol')
        self.assertIn('Start', stdout.getvalue().strip())

    def test_bye_pyvisa(self):
        """Test that we can die."""
        with patch('sys.stdout', new=StringIO()) as stdout:
            bye_pyvisa()
        self.assertIn('references', stdout.getvalue().strip())

    def test_pyvisa_visual(self):
        """Test that we know how to set up a simulation."""
        inputfile = 'a_non_existent_input.kus'
        with self.assertRaises(ImportError) as err:
            pyvisa_visual('.', inputfile, pyvisa_dict={})
        self.assertIn('no', str(err.exception))

    def test_pyvisa_main(self):
        """Test main."""
        infile = 'dummy_input.rst'
        with tempfile.TemporaryDirectory() as tempdir:
            input_file = os.path.join(tempdir, infile)
            shutil.copyfile(os.path.join(HERE, infile), input_file)
            with patch('sys.stdout', new=StringIO()) as stdout:
                main(basepath=tempdir, input_file=input_file,
                     pyvisa_dict={'pyvisa_recalculate': True})
            self.assertIn('Execution failed!',
                          stdout.getvalue().strip())

        with tempfile.TemporaryDirectory() as tempdir:
            input_file = os.path.join(tempdir, infile)
            shutil.copyfile(os.path.join(HERE, infile), input_file)
            with patch('sys.stdout', new=StringIO()) as stdout:
                main(basepath=tempdir, input_file=input_file,
                     pyvisa_dict={'pyvisa_compressor': True})
            self.assertIn('No files to an', stdout.getvalue().strip())

        with tempfile.TemporaryDirectory() as tempdir:
            input_file = os.path.join(tempdir, infile)
            shutil.copyfile(os.path.join(HERE, infile), input_file)
            with patch('sys.stdout', new=StringIO()) as stdout:
                main(basepath=tempdir, input_file=input_file,
                     pyvisa_dict={})
            self.assertIn('traceback', stdout.getvalue().strip())

        with tempfile.TemporaryDirectory() as tempdir:
            with patch('sys.stdout', new=StringIO()) as stdout:
                main(basepath=tempdir, input_file='no_thank_you',
                     pyvisa_dict={})
            self.assertIn('NOT', stdout.getvalue().strip())


if __name__ == '__main__':
    unittest.main()
