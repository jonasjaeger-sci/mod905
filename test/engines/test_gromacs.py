# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the GROMACS Engine class."""
import logging
import numpy as np
import os
import shutil
import tempfile
import unittest
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
GMX_DIR2 = os.path.join(HERE, 'gmx_input2')
GMX_DIR3 = os.path.join(HERE, 'gmx_input3')
GMX_LOAD = os.path.join(HERE, '../initiation/gromacs/gmx_input')


class GromacsEngineTest(unittest.TestCase):
    """Run the tests for the GROMACS Engine."""

    def test_init(self):
        """Test that we can initiate the engine."""
        eng = GromacsEngine(gmx='echo',
                            mdrun='echo',
                            input_path=GMX_DIR,
                            timestep=0.002,
                            subcycles=10,
                            maxwarn=10,
                            gmx_format='gro',
                            write_vel=True,
                            write_force=False)
        eng.exe_dir = GMX_DIR
        with self.assertRaises(ValueError):
            GromacsEngine(gmx='echo',
                          mdrun='echo',
                          input_path='gmx_input',
                          timestep=0.002,
                          subcycles=10,
                          gmx_format='not-a-format')
        with self.assertRaises(FileNotFoundError):
            GromacsEngine('echo', 'echo', 'missing-files', 0.002, 10,
                          gmx_format='g96')
        # Test with an index.ndx file:
        eng2 = GromacsEngine(gmx='echo',
                             mdrun='echo',
                             input_path=GMX_DIR3,
                             timestep=0.002,
                             subcycles=10,
                             maxwarn=10,
                             gmx_format='gro',
                             write_vel=True,
                             write_force=False)
        eng2.exe_dir = GMX_DIR3

    def test_single_step(self):
        """Test a single step using the MOCK GROMACS engine."""
        with tempfile.TemporaryDirectory() as tempdir:
            eng = GromacsEngine(gmx=GMX,
                                mdrun=MDRUN,
                                input_path=GMX_DIR,
                                timestep=0.002,
                                subcycles=3,
                                maxwarn=1,
                                gmx_format='gro',
                                write_vel=True,
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
            eng = GromacsEngine(gmx=GMX,
                                mdrun=MDRUN,
                                input_path=GMX_DIR,
                                timestep=0.002,
                                subcycles=10,
                                maxwarn=1,
                                gmx_format='gro',
                                write_vel=False,
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
            eng = GromacsEngine(gmx=GMX,
                                mdrun=MDRUN,
                                input_path=GMX_DIR,
                                timestep=0.002,
                                subcycles=7,
                                maxwarn=1,
                                gmx_format='gro',
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
            eng = GromacsEngine(gmx=GMX,
                                mdrun=MDRUN,
                                input_path=GMX_DIR,
                                timestep=0.002,
                                subcycles=3,
                                maxwarn=1,
                                gmx_format='gro',
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
            eng = GromacsEngine(gmx=GMX,
                                mdrun=MDRUN,
                                input_path=GMX_DIR,
                                timestep=0.002,
                                subcycles=3,
                                maxwarn=1,
                                gmx_format='gro',
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
            # Clean
            eng.clean_up()

    def test_select_energy_term(self):
        """Test the select_energy_term method."""
        eng = GromacsEngine(gmx=GMX,
                            mdrun=MDRUN,
                            input_path=GMX_DIR,
                            timestep=0.002,
                            subcycles=3,
                            gmx_format='gro')
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
        eng = GromacsEngine(gmx=GMX,
                            mdrun=MDRUN,
                            input_path=GMX_DIR,
                            timestep=0.002,
                            subcycles=1,
                            gmx_format='gro')
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
                for _ in eng.integrate(system, 1,
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

            # Add a non existing .ndx file and get an error
            eng.input_files['index'] = 'ufo.ndx'
            with self.assertRaises(Exception) as context:
                eng._execute_grompp('should_be_a_grompp.mdp',
                                    'configuration.gro', 'a_label')
            self.assertTrue("(GROMACS engine) fail" in str(context.exception))

            eng.clean_up()

    def test_trjconv(self):
        """Test behavior when extracting frames."""
        # We only test the trajectory conversion here as the
        # other parts are tested elsewhere.
        eng = GromacsEngine(gmx=GMX,
                            mdrun=MDRUN,
                            input_path=GMX_DIR,
                            timestep=0.002,
                            subcycles=1,
                            gmx_format='gro')
        with tempfile.TemporaryDirectory() as tempdir:
            eng.exe_dir = tempdir
            # Use an already done TRR file:
            any_trr = os.path.join(HERE, '..', 'tools', '2water.trr')
            any_gro = os.path.join(HERE, '..', 'tools', '2water.gro')
            eng.input_files['conf'] = any_gro
            out_gro = os.path.join(tempdir, 'output.gro')
            eng._extract_frame(any_trr, 4, out_gro)
            # Check the created output file:
            self.assertTrue(os.path.isfile(out_gro))
            with open(out_gro, 'r') as infile:
                data = [i.strip().split() for i in infile]
            # Note: this is a fake output from a fake engine
            self.assertEqual(data[0][1], 'froggy')

            # This tests only the creation of the conf.g96
            shutil.copytree(GMX_LOAD, tempdir+'2')
            any_trr = os.path.join(GMX_LOAD, '../load/023/accepted/trajB.trr')
            eng = GromacsEngine(gmx=GMX,
                                mdrun=MDRUN,
                                input_path=tempdir+'2',
                                timestep=666,
                                subcycles=1,
                                gmx_format='g96')
            out_gro = os.path.join(tempdir+'2', 'my_uncle_jonny.g96')
            # Note, we use a fake engine and it will just copy the file
            eng._extract_frame(any_trr, 0, out_gro)
            self.assertTrue(os.path.isfile(out_gro))

            shutil.rmtree(os.path.join(tempdir+'2'), 'conf.gro')
            # A partial test to avoid the need to install GROMACS to run
            with self.assertRaises(RuntimeError) as err:
                GromacsEngine(gmx=GMX,
                              mdrun=MDRUN,
                              input_path=tempdir+'2',
                              timestep=0.002,
                              subcycles=1,
                              gmx_format='g96')
            self.assertTrue('GROMACS' in str(err.exception))


if __name__ == '__main__':
    unittest.main(module='test_gromacs')
