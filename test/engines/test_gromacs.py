# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the GromacsEngine class."""
import logging
import os
import tempfile
import unittest
import numpy as np
from pyretis.core.path import Path
from pyretis.engines import GromacsEngine
from pyretis.inout.common import make_dirs
from pyretis.inout.formats.gromacs import read_gromacs_gro_file
from pyretis.orderparameter.orderparameter import Position
from .test_helpers.test_helpers import make_test_system


logging.disable(logging.CRITICAL)
HERE = os.path.abspath(os.path.dirname(__file__))
GMX = os.path.join(HERE, 'mockgmx.py')
MDRUN = os.path.join(HERE, 'mockmdrun.py')
GMX_DIR = os.path.join(HERE, 'gmx_input')
GMX_DIR3 = os.path.join(HERE, 'gmx_input3')


class GromacsEngineTest(unittest.TestCase):
    """Run the tests for the GromacsEngine."""

    def test_init(self):
        """Test that we can initiate the engine."""
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
        # Test with an index.ndx file:
        eng2 = GromacsEngine('echo', 'echo', GMX_DIR3, 0.002, 10,
                             maxwarn=10, gmx_format='gro', write_vel=True,
                             write_force=False)
        eng2.exe_dir = GMX_DIR3

    def test_single_step(self):
        """Test a single step using the MOCK gromacs engine."""
        with tempfile.TemporaryDirectory() as tempdir:
            eng = GromacsEngine(GMX, MDRUN, GMX_DIR, 0.002, 3,
                                maxwarn=1, gmx_format='gro', write_vel=True,
                                write_force=False)
            rundir = os.path.join(tempdir, 'generategmx')
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
            self.assertAlmostEqual(eng.subcycles * 1.0, system.particles.ekin)
            self.assertAlmostEqual(eng.subcycles * -1.0, system.particles.vpot)
            self.assertEqual(
                system.particles.get_pos()[0],
                os.path.join(rundir, 'gmx_mock_step.gro')
            )
            eng.clean_up()

    def test_modify_velocities(self):
        """Test the modify velocities method."""
        with tempfile.TemporaryDirectory() as tempdir:
            eng = GromacsEngine(GMX, MDRUN, GMX_DIR, 0.002, 10,
                                maxwarn=1, gmx_format='gro', write_vel=False,
                                write_force=False)
            rundir = os.path.join(tempdir, 'generategmxvel')
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
                eng.modify_velocities(system, None, sigma_v=None,
                                      aimless=False, momentum=False,
                                      rescale=None)
            # Check that rescaling fails:
            with self.assertRaises(NotImplementedError):
                eng.modify_velocities(system, None, sigma_v=None,
                                      aimless=False, momentum=True,
                                      rescale=11)
            dek, kin_new = eng.modify_velocities(system, None, sigma_v=None,
                                                 aimless=True, momentum=False,
                                                 rescale=None)
            self.assertAlmostEqual(kin_new, 1234.5678)
            self.assertAlmostEqual(dek, 0.0)
            eng.clean_up()

    def test_propagate_forward(self):
        """Test the propagate method forward in time."""
        with tempfile.TemporaryDirectory() as tempdir:
            eng = GromacsEngine(GMX, MDRUN, GMX_DIR, 0.002, 7,
                                maxwarn=1, gmx_format='gro',
                                write_vel=True,
                                write_force=False)
            rundir = os.path.join(tempdir, 'generategmxf')
            # Create the directory for running:
            make_dirs(rundir)
            eng.exe_dir = rundir
            # Create the system:
            system = make_test_system((eng.input_files['conf'], 0))
            # Propagate:
            orderp = Position(0, dim='x', periodic=False)
            path = Path(None, maxlen=8)
            success, _ = eng.propagate(path, system, orderp,
                                       [-0.45, 10.0, 14.0], reverse=False)
            initial_x = -0.422
            for i, point in enumerate(path.phasepoints):
                self.assertAlmostEqual(point.particles.ekin, eng.subcycles * i)
                self.assertAlmostEqual(point.particles.vpot,
                                       -1.0 * eng.subcycles * i)
                self.assertAlmostEqual(point.order[0],
                                       i * eng.subcycles + initial_x, places=3)
            self.assertTrue(success)
            eng.clean_up()

    def test_propagate_backward(self):
        """Test the propagate method backward in time."""
        with tempfile.TemporaryDirectory() as tempdir:
            eng = GromacsEngine(GMX, MDRUN, GMX_DIR, 0.002, 3,
                                maxwarn=1, gmx_format='gro',
                                write_vel=True,
                                write_force=False)
            rundir = os.path.join(tempdir, 'generategmxb')
            # Create the directory for running:
            make_dirs(rundir)
            eng.exe_dir = rundir
            # Create the system:
            system = make_test_system((eng.input_files['conf'], 0))
            # Propagate:
            orderp = Position(0, dim='x', periodic=False)
            path = Path(None, maxlen=3)
            success, _ = eng.propagate(path, system, orderp,
                                       [-0.45, 10.0, 14.0],
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

    def test_integrate(self):
        """Test the integrate method."""
        with tempfile.TemporaryDirectory() as tempdir:
            eng = GromacsEngine(GMX, MDRUN, GMX_DIR, 0.002, 3,
                                maxwarn=1, gmx_format='gro',
                                write_vel=True,
                                write_force=False)
            rundir = os.path.join(tempdir, 'gmxintegrate')
            # Create the directory for running:
            make_dirs(rundir)
            eng.exe_dir = rundir
            # Create the system:
            system = make_test_system((eng.input_files['conf'], 0))
            # Propagate:
            order = Position(0, dim='x', periodic=False)
            i = 0
            initial_x = -0.422
            for step in eng.integrate(system, 3, order_function=order):
                self.assertAlmostEqual(step['order'][0],
                                       i * eng.subcycles + initial_x, places=3)
                i += 1
            eng.clean_up()

    def test_select_energy_term(self):
        """Test the select_energy_term method."""
        eng = GromacsEngine(GMX, MDRUN, GMX_DIR, 0.002, 3, gmx_format='gro')
        terms = 'full'
        self.assertEqual(
            str(eng.select_energy_terms(terms)),
            r"b'Potential\nKinetic-En.\nTotal-Energy\nTemperature\nPressure'"
        )
        terms = 'path'
        self.assertEqual(
            str(eng.select_energy_terms(terms)),
            r"b'Potential\nKinetic-En.'"
        )
        terms = 'non_allowed_term'  # Will be equal to terms = 'path'.
        self.assertEqual(
            str(eng.select_energy_terms(terms)),
            r"b'Potential\nKinetic-En.'"
        )

    def test_check_fails(self):
        """Test behavior if orderfunction not given."""
        eng = GromacsEngine(GMX, MDRUN, GMX_DIR, 0.002, 1, gmx_format='gro')
        with tempfile.TemporaryDirectory() as tempdir:
            rundir = os.path.join(tempdir, 'gmxintegrate')
            # Create the directory for running:
            make_dirs(rundir)
            eng.exe_dir = rundir
            # Create the system:
            system = make_test_system((eng.input_files['conf'], 0))
            # Propagate:
            for step in eng.integrate(system, 1):
                self.assertTrue("thermo" in step)
                self.assertFalse("order" in step)
            order_function = Position(0, dim='x', periodic=False)
            eng.ext = "notexistingextension"
            # Propagate:
            with self.assertRaises(Exception) as context:
                for step in eng.integrate(system, 1,
                                          order_function=order_function):
                    pass
            self.assertTrue("GROMACS engine does not support reading" in
                            str(context.exception))
            path = Path(None, maxlen=3)
            with self.assertRaises(Exception) as context:
                eng.propagate(path, system, order_function, [-1., 0.0, 1.0],
                              reverse=True)
            self.assertTrue("GROMACS engine does not support writing" in
                            str(context.exception))
            eng.clean_up()

    def test_trjconv(self):
        """Test behavior when extracting frames."""
        # We only test the trajectory conversion here as the
        # other parts are tested elsewhere.
        eng = GromacsEngine(GMX, MDRUN, GMX_DIR, 0.002, 1, gmx_format='gro')
        with tempfile.TemporaryDirectory() as tempdir:
            eng.exe_dir = tempdir
            # Create a fake TRR file:
            fake_trr = os.path.join(tempdir, 'fake.trr')
            out_gro = os.path.join(tempdir, 'output.gro')
            with open(fake_trr, 'w') as output:
                output.write('This is a fake TRR file')
            eng._extract_frame(fake_trr, 10, out_gro)
            # Check the created output file:
            self.assertTrue(os.path.isfile(out_gro))
            data = []
            with open(out_gro, 'r') as infile:
                data = [i.strip().split() for i in infile]
            self.assertEqual(data[1][2], 'trjconv')
            self.assertAlmostEqual(float(data[1][10]), 9 * 0.002)
            self.assertAlmostEqual(float(data[1][12]), 10 * 0.002)


if __name__ == '__main__':
    unittest.main(module='test_gromacs')
