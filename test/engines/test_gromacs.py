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
from pyretis.engines import GromacsEngine
from pyretis.inout.common import make_dirs
from pyretis.inout.writers.gromacsio import read_gromacs_gro_file
from pyretis.orderparameter.orderparameter import (
    OrderParameterPosition,
)
import numpy as np


logging.disable(logging.CRITICAL)
HERE = os.path.abspath(os.path.dirname(__file__))
GMX = os.path.join(HERE, 'mockgmx.py')
MDRUN = os.path.join(HERE, 'mockmdrun.py')
GMX_DIR = os.path.join(HERE, 'gmx_input')


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
        """Test that we can invert time."""
        eng = GromacsEngine('echo', 'echo', GMX_DIR, 0.002, 10,
                            maxwarn=10, gmx_format='gro', write_vel=True,
                            write_force=False)
        eng.exe_dir = GMX_DIR
        with self.assertRaises(ValueError):
            GromacsEngine('echo', 'echo', 'gmx_input', 0.002, 10,
                          gmx_format='not-a-format')
        with self.assertRaises(ValueError):
            GromacsEngine('echo', 'echo', 'missing-files', 0.002, 10,
                          gmx_format='g96')

    def test_single_step(self):
        """Test a single step using the MOCK gromacs engine."""
        eng = GromacsEngine(GMX, MDRUN, GMX_DIR, 0.002, 3,
                            maxwarn=1, gmx_format='gro', write_vel=True,
                            write_force=False)
        rundir = os.path.join(HERE, 'generategmx')
        # Create the directory for running:
        make_dirs(rundir)
        eng.exe_dir = rundir
        # Create the system:
        system = make_test_system((eng.input_files['conf'], 0))
        out = eng.step(system, 'gmx_mock_step')
        self.assertEqual(out, 'gmx_mock_step.gro')
        # Check that output files are present:
        for i in ('conf.gro', 'gmx_mock_step.gro'):
            self.assertTrue(os.path.isfile(os.path.join(rundir, i)))
        # Check that output files contain the expected data:
        _, xyz1, vel1, _ = read_gromacs_gro_file(
            os.path.join(rundir, 'conf.gro')
        )
        _, xyz2, vel2, _ = read_gromacs_gro_file(
            os.path.join(rundir, 'gmx_mock_step.gro')
        )
        self.assertTrue(np.allclose(xyz2 - xyz1,
                                    eng.subcycles * np.ones_like(xyz1)))
        self.assertTrue(np.allclose(
            vel1,
            np.repeat([0.1111, 0.2222, 0.3333], 27).reshape(3, 27).T
        ))
        self.assertTrue(np.allclose(vel2, np.ones_like(vel2)))
        # Check the final state:
        state = system.particles.get_particle_state()
        self.assertAlmostEqual(eng.subcycles * 1.0, state['ekin'])
        self.assertAlmostEqual(eng.subcycles * -1.0, state['vpot'])
        self.assertEqual(
            state['pos'][0],
            os.path.join(rundir, 'gmx_mock_step.gro')
        )
        eng.clean_up()
        remove_dir(rundir)

    def test_modify_velocities(self):
        """Test the modify velocities method."""
        eng = GromacsEngine(GMX, MDRUN, GMX_DIR, 0.002, 10,
                            maxwarn=1, gmx_format='gro', write_vel=False,
                            write_force=False)
        rundir = os.path.join(HERE, 'generategmxvel')
        # Create the directory for running:
        make_dirs(rundir)
        eng.exe_dir = rundir
        # Create the system:
        system = make_test_system((eng.input_files['conf'], 0))
        dek, kin_new = eng.modify_velocities(system, None, sigma_v=None,
                                             aimless=True, momentum=False,
                                             rescale=None)
        self.assertAlmostEqual(kin_new, 1234.5678)
        self.assertTrue(dek == float('inf'))
        # Check that aiming fails:
        with self.assertRaises(NotImplementedError):
            eng.modify_velocities(system, None, sigma_v=None, aimless=False,
                                  momentum=False, rescale=None)
        # Check that rescaling fails:
        with self.assertRaises(NotImplementedError):
            eng.modify_velocities(system, None, sigma_v=None, aimless=False,
                                  momentum=True, rescale=11)
        dek, kin_new = eng.modify_velocities(system, None, sigma_v=None,
                                             aimless=True, momentum=False,
                                             rescale=None)
        self.assertAlmostEqual(kin_new, 1234.5678)
        self.assertAlmostEqual(dek, 0.0)
        eng.clean_up()
        remove_dir(rundir)

    def test_propagate_forward(self):
        """Test the propagate method forward in time."""
        eng = GromacsEngine(GMX, MDRUN, GMX_DIR, 0.002, 7,
                            maxwarn=1, gmx_format='gro',
                            write_vel=True,
                            write_force=False)
        rundir = os.path.join(HERE, 'generategmxf')
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
        initial_x = -0.422
        for i, point in enumerate(path.trajectory()):
            self.assertAlmostEqual(point['ekin'], eng.subcycles * i)
            self.assertAlmostEqual(point['vpot'], -1.0 * eng.subcycles * i)
            self.assertAlmostEqual(point['order'][0],
                                   i * eng.subcycles + initial_x, places=3)
        self.assertTrue(success)
        eng.clean_up()
        remove_dir(rundir)

    def test_propagate_backward(self):
        """Test the propeagate method backward in time."""
        eng = GromacsEngine(GMX, MDRUN, GMX_DIR, 0.002, 3,
                            maxwarn=1, gmx_format='gro',
                            write_vel=True,
                            write_force=False)
        rundir = os.path.join(HERE, 'generategmxb')
        # Create the directory for running:
        make_dirs(rundir)
        eng.exe_dir = rundir
        # Create the system:
        system = make_test_system((eng.input_files['conf'], 0))
        # Propagate:
        orderp = OrderParameterPosition(0, dim='x', periodic=False)
        path = PathExt(None, maxlen=3)
        success, _ = eng.propagate(path, system, orderp, [-0.45, 10.0, 14.0],
                                   reverse=True)
        self.assertFalse(success)
        # Check that velocities were reversed:
        _, _, vel1, _ = read_gromacs_gro_file(
            os.path.join(rundir, 'conf.gro')
        )
        _, _, vel2, _ = read_gromacs_gro_file(
            os.path.join(rundir, 'r_conf.gro')
        )
        self.assertTrue(np.allclose(vel1, -1.0 * vel2))
        eng.clean_up()
        remove_dir(rundir)


if __name__ == '__main__':
    unittest.main(module='test_gromacs')
