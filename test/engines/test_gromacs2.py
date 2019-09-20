# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the GromacsEngine class."""
import logging
import os
import tempfile
import unittest
from pyretis.core.path import Path
from pyretis.engines.gromacs2 import GromacsEngine2
from pyretis.inout.common import make_dirs
from pyretis.orderparameter.orderparameter import Position
from .test_helpers.test_helpers import make_test_system


logging.disable(logging.CRITICAL)
HERE = os.path.abspath(os.path.dirname(__file__))
GMX_DIR = os.path.join(HERE, 'gmx_input2')
GMX = os.path.join(HERE, 'mockgmx.py')
MDRUN = os.path.join(HERE, 'mockmdrun2.py')


class GromacsEngineTest(unittest.TestCase):
    """Run the tests for the GromacsEngine."""

    def test_init(self):
        """Test the initiation."""
        eng = GromacsEngine2(gmx='echo',
                             mdrun='echo',
                             input_path=GMX_DIR,
                             timestep=0.002,
                             subcycles=10,
                             maxwarn=10,
                             gmx_format='g96',
                             write_vel=True,
                             write_force=False)
        eng.exe_dir = GMX_DIR
        with self.assertRaises(ValueError):
            GromacsEngine2(gmx='echo',
                           mdrun='echo',
                           input_path='gmx_input',
                           timestep=0.002,
                           subcycles=10,
                           gmx_format='not-a-format')
        with self.assertRaises(FileNotFoundError):
            GromacsEngine2(gmx='echo',
                           mdrun='echo',
                           input_path='missing-files',
                           timestep=0.002,
                           subcycles=10)

    def test_propagate_forward(self):
        """Test the propagate method, forward direction.

        Here, the .trr file will be created before starting the
        engine. The engine will then be lagging behind and this
        should trigger the `read_remaining_trr` method.
        """
        with tempfile.TemporaryDirectory() as tempdir:
            eng = GromacsEngine2(GMX, MDRUN, GMX_DIR, 0.002, 7,
                                 maxwarn=1, gmx_format='g96',
                                 write_vel=True,
                                 write_force=False)
            rundir = os.path.join(tempdir, 'generate2gmxf')
            # Create the directory for running:
            make_dirs(rundir)
            eng.exe_dir = rundir
            # Create the system:
            system = make_test_system((eng.input_files['conf'], 0))
            # Propagate:
            orderp = Position(0, dim='x', periodic=False)
            path = Path(None, maxlen=8)
            success, _ = eng.propagate(path, system, orderp,
                                       [-0.45, 10.0, 14.0],
                                       reverse=False)
            self.assertTrue(success)
            self.assertEqual(path.length, 4)
            initial_x = -0.422
            for i, point in enumerate(path.phasepoints):
                self.assertAlmostEqual(point.particles.ekin, eng.subcycles * i)
                self.assertAlmostEqual(point.particles.vpot,
                                       eng.subcycles * -1.0 * i)
                self.assertAlmostEqual(point.order[0],
                                       i * eng.subcycles + initial_x, places=3)
                self.assertFalse(point.particles.get_vel())

            eng.clean_up()

    def test_propagate_backward(self):
        """Test the propagate method, backward direction.

        Here, the .trr file will be created before starting the
        engine. The engine will then be lagging behind and this
        should trigger the `read_remaining_trr` method.
        """
        with tempfile.TemporaryDirectory() as tempdir:
            eng = GromacsEngine2(GMX, MDRUN, GMX_DIR, 0.002, 7,
                                 maxwarn=1, gmx_format='g96',
                                 write_vel=True,
                                 write_force=False)
            rundir = os.path.join(tempdir, 'generate2gmxb')
            # Create the directory for running:
            make_dirs(rundir)
            eng.exe_dir = rundir
            # Create the system:
            system = make_test_system((eng.input_files['conf'], 0))
            # Propagate:
            orderp = Position(0, dim='x', periodic=False)
            path = Path(None, maxlen=8)
            success, _ = eng.propagate(path, system, orderp,
                                       [-20., 10.0, 14.0],
                                       reverse=True)
            self.assertTrue(success)
            self.assertEqual(path.length, 4)
            initial_x = -0.422
            for i, point in enumerate(path.phasepoints):
                self.assertAlmostEqual(point.particles.ekin, eng.subcycles * i)
                self.assertAlmostEqual(point.particles.vpot,
                                       eng.subcycles * -1.0 * i)
                self.assertAlmostEqual(point.order[0],
                                       initial_x - i * eng.subcycles, places=3)
                self.assertTrue(point.particles.get_vel())
            eng.clean_up()

    def test_propagate_crash(self):
        """Test the propagate method when engine crashes."""
        with tempfile.TemporaryDirectory() as tempdir:
            mdrun = '{} -crash'.format(MDRUN)
            eng = GromacsEngine2(GMX, mdrun, GMX_DIR,
                                 timestep=0.002,
                                 subcycles=7,
                                 maxwarn=1, gmx_format='g96',
                                 write_vel=True,
                                 write_force=False)
            rundir = os.path.join(tempdir, 'generate3gmxf')
            # Create the directory for running:
            make_dirs(rundir)
            eng.exe_dir = rundir
            # Create the system:
            system = make_test_system((eng.input_files['conf'], 0))
            # Propagate:
            orderp = Position(0, dim='x', periodic=False)
            path = Path(None, maxlen=8)
            with self.assertRaises(RuntimeError):
                eng.propagate(path, system, orderp, [-0.45, 10.0, 14.0],
                              reverse=False)
            # Check the error - output:
            with open(os.path.join(rundir, 'stderr.txt')) as infile:
                data = infile.readlines()
                self.assertEqual(len(data), 1)
                self.assertEqual(data[0].strip(), 'Crash error for testing.')
            eng.clean_up()

    def test_propagate_sleep(self):
        """Test the propagate method.

        Here, we try to write the trr file a bit slower so that
        the class running the GROMACS simulation will have to wait
        for the data to be written.
        """
        with tempfile.TemporaryDirectory() as tempdir:
            mdrun = '{} -sleep'.format(MDRUN)
            eng = GromacsEngine2(GMX, mdrun, GMX_DIR, 0.002, 7,
                                 maxwarn=1, gmx_format='g96',
                                 write_vel=True,
                                 write_force=False)
            rundir = os.path.join(tempdir, 'generate4gmxf')
            # Create the directory for running:
            make_dirs(rundir)
            eng.exe_dir = rundir
            # Create the system:
            system = make_test_system((eng.input_files['conf'], 0))
            # Propagate:
            orderp = Position(0, dim='x', periodic=False)
            path = Path(None, maxlen=8)
            success, _ = eng.propagate(path, system, orderp,
                                       [-0.45, 10.0, 14.0],
                                       reverse=False)
            self.assertTrue(success)
            self.assertEqual(path.length, 4)
            initial_x = -0.422
            for i, point in enumerate(path.phasepoints):
                self.assertAlmostEqual(point.particles.ekin, eng.subcycles * i)
                self.assertAlmostEqual(point.particles.vpot,
                                       eng.subcycles * -1.0 * i)
                self.assertAlmostEqual(point.order[0],
                                       i * eng.subcycles + initial_x, places=3)
            eng.clean_up()

    def test_integrate(self):
        """Test the integrate method."""
        with tempfile.TemporaryDirectory() as tempdir:
            eng = GromacsEngine2(GMX, MDRUN, GMX_DIR, 0.002, 3,
                                 maxwarn=1, gmx_format='g96',
                                 write_vel=True,
                                 write_force=False)
            rundir = os.path.join(tempdir, 'gmxintegrate2')
            # Create the directory for running:
            make_dirs(rundir)
            eng.exe_dir = rundir
            # Create the system:
            system = make_test_system((eng.input_files['conf'], 0))
            # Propagate:
            order = Position(0, dim='x', periodic=False)
            i = 0
            initial_x = -0.422
            for step in eng.integrate(system, 5, order_function=order):
                j = max(i - 1, 0)
                self.assertAlmostEqual(step['order'][0],
                                       j * eng.subcycles + initial_x, places=3)
                i += 1
            eng.clean_up()


if __name__ == '__main__':
    unittest.main()
