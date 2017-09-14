# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the CP2KEngine class."""
import logging
import os
import unittest
import numpy as np
from pyretis.core.system import System
from pyretis.core.path import PathExt
from pyretis.core.particles import ParticlesExt
from pyretis.engines import CP2KEngine
from pyretis.inout.common import make_dirs
from pyretis.inout.writers.xyzio import (
    read_xyz_file,
    convert_snapshot,
)
from pyretis.orderparameter.orderparameter import (
    OrderParameterPosition,
)
logging.disable(logging.DEBUG)

HERE = os.path.abspath(os.path.dirname(__file__))


def remove_dir(dirname):
    """Remove a directory silently."""
    try:
        os.removedirs(dirname)
    except OSError:
        pass


def make_test_system(conf):
    """Just make a test system with particles."""
    system = System()
    system.particles = ParticlesExt(dim=3)
    system.particles.config = conf
    return system


class CP2KEngineTest(unittest.TestCase):
    """Run the tests for the CP2KEngine"""

    def test_init(self):
        """Test that we can invert time."""
        dir_name = os.path.join(HERE, 'cp2k_input')
        extra_files = ['extra_file']
        engine = CP2KEngine('cp2k', dir_name, 0.002, 10, extra_files)
        self.assertEqual(len(engine.extra_files), 1)
        # Check that we get an error if we are missing files:
        with self.assertRaises(ValueError):
            CP2KEngine('cp2k', '', 0.002, 10, extra_files)
        # Check that non-existing extra files are not added:
        extra_files.append('a-non-existing-file-please')
        engine = CP2KEngine('cp2k', dir_name, 0.002, 10, extra_files)
        self.assertEqual(len(engine.extra_files), 1)

    def test_single_step(self):
        """Test that the single step method work as we intend."""
        cmd = os.path.join(HERE, 'mockcp2k.py')
        dir_name = os.path.join(HERE, 'cp2k_input')
        extra_files = ['extra_file']
        engine = CP2KEngine(cmd, dir_name, 0.002, 10, extra_files)
        rundir = os.path.join(HERE, 'generate')
        # Create the directory for running:
        make_dirs(rundir)
        engine.exe_dir = rundir
        # Create the system:
        system = make_test_system((engine.input_files['conf'], 0))
        # Run a single step:
        out = engine.step(system, 'cp2k_step')
        # Check that we have the expected files after the step:
        for i in ('extra_file', 'step.inp', 'conf.xyz', 'cp2k_step.xyz'):
            self.assertTrue(os.path.isfile(os.path.join(rundir, i)))
        state = system.particles.get_particle_state()
        self.assertAlmostEqual(state['ekin'], 0.9)
        self.assertAlmostEqual(state['vpot'], -0.9)
        # Get snapshot:
        box, xyz, vel, names = convert_snapshot(next(read_xyz_file(out)))
        for i, j in zip(names, ['H', 'H']):
            self.assertEqual(i, j)
        self.assertTrue(
            np.allclose(box,
                        np.array([1., 2., 3.]))
        )
        self.assertTrue(
            np.allclose(xyz,
                        np.array([[0.9, 1.8, 2.7], [1.9, 2.8, 3.7]]))
        )
        self.assertTrue(
            np.allclose(vel,
                        np.array([[9.9, 10.8, 11.7], [10.9, 11.8, 12.7]]))
        )
        engine.clean_up()
        remove_dir(rundir)

    def test_modify_velocities(self):
        """Test the modify velocities method."""
        cmd = os.path.join(HERE, 'mockcp2k.py')
        dir_name = os.path.join(HERE, 'cp2k_input')
        extra_files = ['extra_file']
        engine = CP2KEngine(cmd, dir_name, 0.002, 10, extra_files)
        rundir = os.path.join(HERE, 'generatevel')
        # Create the directory for running:
        make_dirs(rundir)
        engine.exe_dir = rundir
        # Create the system:
        system = make_test_system((engine.input_files['conf'], 0))
        # Modify velocities
        dek, kin_new = engine.modify_velocities(system, None, sigma_v=None,
                                                aimless=True,
                                                momentum=False, rescale=None)
        self.assertAlmostEqual(kin_new, 0.9)
        self.assertTrue(dek == float('inf'))
        # Check that aiming fails:
        with self.assertRaises(NotImplementedError):
            engine.modify_velocities(system, None, sigma_v=None, aimless=False,
                                     momentum=False, rescale=None)
        # Check that rescaling fails:
        with self.assertRaises(NotImplementedError):
            engine.modify_velocities(system, None, sigma_v=None, aimless=False,
                                     momentum=False, rescale=10)
        dek, kin_new = engine.modify_velocities(system, None, sigma_v=None,
                                                aimless=True,
                                                momentum=False, rescale=None)
        self.assertAlmostEqual(kin_new, 0.9)
        self.assertAlmostEqual(dek, 0.0)
        engine.clean_up()
        remove_dir(rundir)

    def test_propagate_forward(self):
        """Test the propagate method forward in time."""
        cmd = os.path.join(HERE, 'mockcp2k.py')
        dir_name = os.path.join(HERE, 'cp2k_input')
        extra_files = ['extra_file']
        engine = CP2KEngine(cmd, dir_name, 0.002, 10, extra_files)
        rundir = os.path.join(HERE, 'generatef')
        # Create the directory for running:
        make_dirs(rundir)
        engine.exe_dir = rundir
        # Create the system:
        system = make_test_system((engine.input_files['conf'], 0))
        # Propagate:
        orderp = OrderParameterPosition(0, dim='x', periodic=False)
        path = PathExt(None, maxlen=4)
        success, _ = engine.propagate(path, system, orderp,
                                      [0.2, 8.0, 9.0], reverse=False)
        self.assertFalse(success)
        engine.clean_up()
        remove_dir(rundir)

    def test_propagate_backward(self):
        """Test the propagate method forward in time."""
        cmd = os.path.join(HERE, 'mockcp2k.py')
        dir_name = os.path.join(HERE, 'cp2k_input')
        extra_files = ['extra_file']
        engine = CP2KEngine(cmd, dir_name, 0.002, 10, extra_files)
        rundir = os.path.join(HERE, 'generateb')
        # Create the directory for running:
        make_dirs(rundir)
        engine.exe_dir = rundir
        # Create the system:
        system = make_test_system((engine.input_files['conf'], 0))
        # Propagate:
        orderp = OrderParameterPosition(0, dim='x', periodic=False)
        path = PathExt(None, maxlen=4)
        success, _ = engine.propagate(path, system, orderp,
                                      [0.2, 0.5, 0.8], reverse=True)
        self.assertTrue(success)
        # Check that initial velocities were reversed
        infile = os.path.join(rundir, 'conf.xyz')
        _, _, vel, _ = convert_snapshot(next(read_xyz_file(infile)))
        outfile = os.path.join(rundir, 'r_conf.xyz')
        _, _, rvel, _ = convert_snapshot(next(read_xyz_file(outfile)))
        self.assertTrue(np.allclose(vel, -1.0 * rvel))
        engine.clean_up()
        remove_dir(rundir)


if __name__ == '__main__':
    unittest.main()
