# -*- coding: utf-8 -*-
"""Test the Fortran implementation of the Lennard Jones potential.

This test is actually running a simulation and then comparing the results
with output from a similar simulation performed in LAMMPS.
"""
# pylint: disable=C0103
from __future__ import print_function
import os
import unittest
import numpy as np
from pyretis.core.simulation import Simulation
from pyretis.core import System, Box
from pyretis.core.units import create_conversion_factors
from pyretis.core.integrators import VelocityVerlet
from pyretis.forcefield import ForceField
from pyretis.core.particlefunctions import calculate_thermo
from ljpotentialf import PairLennardJonesCutF


def set_up_simulation():
    """Create the simulation object."""
    create_conversion_factors('lj')
    size = [[0.0, 8.39798] for _ in range(3)]  # hard coded box-size
    box = Box(size)
    ljsystem = System(box=box, units='lj')

    ljpot = PairLennardJonesCutF(shift=True)
    lj_parameters = {0: {'sigma': 1.0, 'epsilon': 1.0, 'rcut': 2.5},
                     1: {'sigma': 1.2, 'epsilon': 1.1, 'rcut': 2.5},
                     2: {'sigma': 1.4, 'epsilon': 0.9, 'rcut': 2.5},
                     'mixing': 'geometric'}
    forcefield = ForceField(potential=[ljpot], params=[lj_parameters])
    ljsystem.forcefield = forcefield
    # read initial position and velocity:
    dirname = 'molecular_dynamics/initial_lammps/input_data'
    dirname = os.path.join(os.pardir, dirname)
    dirname = os.path.join(os.pardir, dirname)
    pos = np.loadtxt(os.path.join(dirname, 'initial_pos_mixture.txt.gz'))
    vel = np.loadtxt(os.path.join(dirname, 'initial_vel_mixture.txt.gz'))
    idx = np.loadtxt(os.path.join(dirname, 'atom_types_mixture.txt.gz'))
    names = {0: 'A', 1: 'B', 2: 'C'}
    masses = {0: 1.0, 1: 1.0, 2: 1.5}
    natoms = {}
    npart = 0.0
    for xyzi, veli, idxi in zip(pos, vel, idx):
        itype = int(idxi) - 1
        ljsystem.add_particle(name=names[itype], pos=xyzi, vel=veli,
                              mass=masses[itype], ptype=itype)
        if not names[itype] in natoms:
            natoms[names[itype]] = 0
        natoms[names[itype]] += 1
        npart += 1.0
    print('Initiated system with {} particles'.format(int(npart)))
    for atom in natoms:
        print('{0:>4d} atoms of type {1}'.format(int(natoms[atom]), atom))
    ljsystem.potential_and_force()
    numberofsteps = 100
    simulationLAMMPS = Simulation(endcycle=numberofsteps)
    integrator = VelocityVerlet(0.0025)
    task_integrate = {'func': integrator.integration_step,
                      'args': [ljsystem]}
    simulationLAMMPS.add_task(task_integrate)
    return simulationLAMMPS, ljsystem


def run_simulation(simulationLAMMPS, ljsystem):
    """Run the simulation."""
    thermo_output = {}
    step = []
    outfmt = '{0:8d} {1:12.7f} {2:12.7f} {3:12.7f} {4:12.7f} {5:12.7f}'
    outfmt2 = '# {0:>6s} {1:>12s} {2:>12s} {3:>12s} {4:>12s} {5:>12s}'
    print('Running simulation...')
    print(outfmt2.format('Step', 'Temp', 'Press', 'Pot', 'Kin', 'Total'))
    while not simulationLAMMPS.is_finished():
        simulationLAMMPS.step()
        thermo = calculate_thermo(ljsystem)
        for key in thermo:
            try:
                thermo_output[key].append(thermo[key])
            except KeyError:
                thermo_output[key] = [thermo[key]]
        step.append(simulationLAMMPS.cycle['step'])
        if step[-1] % 10 == 0:
            print(outfmt.format(step[-1], thermo['temp'], thermo['press'],
                                thermo['vpot'], thermo['ekin'],
                                thermo['etot']))
    for key in thermo_output:
        thermo_output[key] = np.array(thermo_output[key])
    return thermo_output


class LennardJonesTest(unittest.TestCase):
    """Run the tests for the Fortran potential class."""

    def setUp(self):
        """Run the simulation and get the outputs."""
        simulationLAMMPS, ljsystem = set_up_simulation()
        thermo_output = run_simulation(simulationLAMMPS, ljsystem)
        dirname = 'molecular_dynamics/initial_lammps/output_data'
        dirname = os.path.join(os.pardir, dirname)
        dirname = os.path.join(os.pardir, dirname)
        lmp_out = os.path.join(dirname, 'lammps-output_mixture.txt.gz')
        lmp_data = np.loadtxt(lmp_out)
        self.thermo_output = thermo_output
        self.lmp_data = lmp_data

    def test_ljfortran(self):
        """Test the creation of boxes with no arguments."""
        n = min(len(self.thermo_output['vpot']), len(self.lmp_data[:, 0]))
        print('Comparing with LAMMPS')
        lammps_idx = [1, 2, 3, 4, 5]
        pyretis_key = ['temp', 'press', 'vpot', 'ekin', 'etot']
        TOL = 1.0e-4
        for i, key in zip(lammps_idx, pyretis_key):
            lammps = self.lmp_data[:n, i]
            pyretis = self.thermo_output[key][:n]
            rmse = np.linalg.norm(pyretis - lammps) / np.sqrt(len(lammps))
            print('\nComparing: {}'.format(key.title()))
            close = np.allclose(lammps, pyretis, atol=TOL)
            print(' -> Values equal with tol. {}: {}'.format(TOL, close))
            print(' -> Root mean squared error: {}'.format(rmse))
            self.assertTrue(close)
            self.assertGreater(TOL, rmse)

        presslab = ['pxx', 'pyy', 'pzz', 'pxy', 'pxz', 'pyz']
        pressindex = [(0, 0), (1, 1), (2, 2), (0, 1), (0, 2), (1, 2)]
        for i, (pi, idx) in enumerate(zip(presslab, pressindex)):
            lammps = self.lmp_data[:n, i+6]
            pyretis = self.thermo_output['press-tens'][:n, idx[0], idx[1]]
            rmse = np.linalg.norm(pyretis - lammps) / np.sqrt(len(lammps))
            print('\nComparing: {}'.format(pi.title()))
            close = np.allclose(lammps, pyretis, atol=TOL)
            print(' -> Values equal with tol. {}: {}'.format(TOL, close))
            print(' -> Root mean squared error: {}'.format(rmse))
            self.assertTrue(close)
            self.assertGreater(TOL, rmse)

if __name__ == '__main__':
    unittest.main()
