# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the GromacsEngine class."""
import logging
import unittest
import os
from pyretis.core.system import System
from pyretis.core.path import PathExt
from pyretis.core.particles import ParticlesExt
from pyretis.engines.gromacs2 import GromacsEngine2
from pyretis.inout.common import make_dirs
from pyretis.orderparameter.orderparameter import (
    OrderParameterPosition,
)


logging.disable(logging.CRITICAL)
HERE = os.path.abspath(os.path.dirname(__file__))
GMX_DIR = os.path.join(HERE, 'gmx_input2')
GMX = os.path.join(HERE, 'mockgmx.py')
MDRUN = os.path.join(HERE, 'mockmdrun2.py')


def remove_dir(dirname):
    """Remove a directory silently."""
    try:
        os.removedirs(dirname)
    except OSError:
        pass


def make_test_system(conf):
    """Make a system with particles for testing."""
    system = System()
    system.particles = ParticlesExt(dim=3)
    system.particles.config = conf
    system.particles.set_vel(False)
    return system


class GromacsEngineTest(unittest.TestCase):
    """Run the tests for the GromacsEngine"""

    def test_init(self):
        """Test the initiation."""
        eng = GromacsEngine2('echo', 'echo', GMX_DIR, 0.002, 10,
                             maxwarn=10, gmx_format='g96', write_vel=True,
                             write_force=False)
        eng.exe_dir = GMX_DIR
        with self.assertRaises(ValueError):
            GromacsEngine2('echo', 'echo', 'gmx_input', 0.002, 10,
                           gmx_format='not-a-format')
        with self.assertRaises(ValueError):
            GromacsEngine2('echo', 'echo', 'missing-files', 0.002, 10,
                           gmx_format='gro')

    def test_propagate_forward(self):
        """Test the propagate method, forward direction.

        Here, the .trr file will be created before starting the
        engine. The engine will then be lagging behind and this
        should trigger the `read_remaining_trr` method.
        """
        eng = GromacsEngine2(GMX, MDRUN, GMX_DIR, 0.002, 7,
                             maxwarn=1, gmx_format='g96',
                             write_vel=True,
                             write_force=False)
        rundir = os.path.join(HERE, 'generate2gmxf')
        # Create the directory for running:
        make_dirs(rundir)
        eng.exe_dir = rundir
        # Create the system:
        system = make_test_system((eng.input_files['conf'], 0))
        # Propagate:
        orderp = OrderParameterPosition(0, dim='x', periodic=False)
        path = PathExt(None, maxlen=8)
        success, _ = eng.propagate(path, system, orderp, [-0.45, 10.0, 14.0],
                                   reverse=False)
        self.assertTrue(success)
        self.assertEqual(path.length, 4)
        initial_x = -0.422
        for i, point in enumerate(path.trajectory()):
            self.assertAlmostEqual(point['ekin'], eng.subcycles * i)
            self.assertAlmostEqual(point['vpot'], eng.subcycles * -1.0 * i)
            self.assertAlmostEqual(point['order'][0],
                                   i * eng.subcycles + initial_x, places=3)
            self.assertFalse(point['vel'])

        eng.clean_up()
        remove_dir(rundir)

    def test_propagate_backward(self):
        """Test the propagate method, backward direction.

        Here, the .trr file will be created before starting the
        engine. The engine will then be lagging behind and this
        should trigger the `read_remaining_trr` method.
        """
        eng = GromacsEngine2(GMX, MDRUN, GMX_DIR, 0.002, 7,
                             maxwarn=1, gmx_format='g96',
                             write_vel=True,
                             write_force=False)
        rundir = os.path.join(HERE, 'generate2gmxb')
        # Create the directory for running:
        make_dirs(rundir)
        eng.exe_dir = rundir
        # Create the system:
        system = make_test_system((eng.input_files['conf'], 0))
        # Propagate:
        orderp = OrderParameterPosition(0, dim='x', periodic=False)
        path = PathExt(None, maxlen=8)
        success, _ = eng.propagate(path, system, orderp, [-20., 10.0, 14.0],
                                   reverse=True)
        self.assertTrue(success)
        self.assertEqual(path.length, 4)
        initial_x = -0.422
        for i, point in enumerate(path.trajectory()):
            self.assertAlmostEqual(point['ekin'], eng.subcycles * i)
            self.assertAlmostEqual(point['vpot'], eng.subcycles * -1.0 * i)
            self.assertAlmostEqual(point['order'][0],
                                   initial_x - i * eng.subcycles, places=3)
            self.assertTrue(point['vel'])
        eng.clean_up()
        remove_dir(rundir)

    def test_propagate_crash(self):
        """Test the propagate method when engine crashes."""
        mdrun = '{} -crash'.format(MDRUN)
        eng = GromacsEngine2(GMX, mdrun, GMX_DIR, 0.002, 7,
                             maxwarn=1, gmx_format='g96',
                             write_vel=True,
                             write_force=False)
        rundir = os.path.join(HERE, 'generate3gmxf')
        # Create the directory for running:
        make_dirs(rundir)
        eng.exe_dir = rundir
        # Create the system:
        system = make_test_system((eng.input_files['conf'], 0))
        # Propagate:
        orderp = OrderParameterPosition(0, dim='x', periodic=False)
        path = PathExt(None, maxlen=8)
        with self.assertRaises(RuntimeError):
            eng.propagate(path, system, orderp, [-0.45, 10.0, 14.0],
                          reverse=False)
        # Check the error - output:
        with open(os.path.join(rundir, 'stderr.txt')) as infile:
            data = infile.readlines()
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0].strip(), 'Crash error for testing.')
        eng.clean_up()
        remove_dir(rundir)

    def test_propagate_sleep(self):
        """Test the propagate method.

        Here, we try to write the trr file a bit slower so that
        the class running the GROMACS simulation will have to wait
        for the data to be written.
        """
        mdrun = '{} -sleep'.format(MDRUN)
        eng = GromacsEngine2(GMX, mdrun, GMX_DIR, 0.002, 7,
                             maxwarn=1, gmx_format='g96',
                             write_vel=True,
                             write_force=False)
        rundir = os.path.join(HERE, 'generate4gmxf')
        # Create the directory for running:
        make_dirs(rundir)
        eng.exe_dir = rundir
        # Create the system:
        system = make_test_system((eng.input_files['conf'], 0))
        # Propagate:
        orderp = OrderParameterPosition(0, dim='x', periodic=False)
        path = PathExt(None, maxlen=8)
        success, _ = eng.propagate(path, system, orderp, [-0.45, 10.0, 14.0],
                                   reverse=False)
        self.assertTrue(success)
        self.assertEqual(path.length, 4)
        initial_x = -0.422
        for i, point in enumerate(path.trajectory()):
            self.assertAlmostEqual(point['ekin'], eng.subcycles * i)
            self.assertAlmostEqual(point['vpot'], eng.subcycles * -1.0 * i)
            self.assertAlmostEqual(point['order'][0],
                                   i * eng.subcycles + initial_x, places=3)
        eng.clean_up()
        remove_dir(rundir)


if __name__ == '__main__':
    unittest.main()
