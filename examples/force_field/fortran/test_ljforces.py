# -*- coding: utf-8 -*-
"""Test the Fortran implementation of the Lennard Jones potential.

This test is comparing the three versions of the Lennard Jones
potential:

1) The pure python implementation

2) The numpy python implementation

3) The Fortran implementation.
"""
# pylint: disable=C0103
from __future__ import print_function
import unittest
import numpy as np
from pyretis.core import System, Box
from pyretis.core.units import create_conversion_factors
from pyretis.forcefield import ForceField
from pyretis.forcefield.potentials import PairLennardJonesCut
from pyretis.forcefield.potentials import PairLennardJonesCutnp
from pyretis.tools import generate_lattice
from ljpotentialf import PairLennardJonesCutF


def set_up_initial_state():
    """Create particles for the test."""
    create_conversion_factors('lj')
    lattice, size = generate_lattice('fcc', [5, 5, 5], density=0.9)
    npart = len(lattice)
    lattice += np.random.randn(npart, 3) * 0.05
    box = Box(size, periodic=[True, True, True])
    system = System(temperature=1.0, units='lj', box=box)
    for pos in lattice:
        system.add_particle(name='Ar', pos=pos, mass=1.0, ptype=0)
    msg = 'Created lattice with {} atoms.'
    print(msg.format(system.particles.npart))
    return system


def run_calculations(system, parameters):
    """Evaluate the LJ potential."""
    # Calculate with Fortran:
    potentialF = PairLennardJonesCutF(dim=3, shift=True)
    system.forcefield = ForceField(potential=[potentialF],
                                   params=[parameters])
    vpotF, forcesF, virialF = system.potential_and_force()
    # Calculate with pure python implementation:
    potential = PairLennardJonesCut(dim=3, shift=True)
    system.forcefield = ForceField(potential=[potential],
                                   params=[parameters])
    vpot, forces, virial = system.potential_and_force()
    # Calculate with numpy python implementation:
    potentialnp = PairLennardJonesCutnp(dim=3, shift=True)
    system.forcefield = ForceField(potential=[potentialnp],
                                   params=[parameters])
    vpotnp, forcesnp, virialnp = system.potential_and_force()
    return ((vpot, forces, virial),
            (vpotnp, forcesnp, virialnp),
            (vpotF, forcesF, virialF))


class LennardJonesTest(unittest.TestCase):
    """Run the tests for the Fortran potential class."""

    def test_ljfortran(self):
        """Test one-component system."""
        print('Testing for one-component system')
        system = set_up_initial_state()
        param1 = {0: {'sigma': 1.0, 'epsilon': 1.0, 'rcut': 2.5}}
        result = run_calculations(system, param1)
        keys = ['python', 'python-numpy', 'fortran']
        for i, keyi in enumerate(keys[:-1]):
            for j, key2 in enumerate(keys[i+1:]):
                print('\nCompare {} and {}'.format(keyi, key2))
                force = np.allclose(result[i][1], result[i+j+1][1])
                print(' -> Forces close: {}'.format(force))
                self.assertTrue(force)
                virial = np.allclose(result[i][2], result[i+j+1][2])
                print(' -> Virial close: {}'.format(virial))
                self.assertTrue(virial)
                self.assertAlmostEqual(result[i][0], result[i+j+1][0], 7)
                vdiff = np.abs(result[i][0] - result[i+j+1][0])
                print(' -> Difference in pot. energy: {:.15e}'.format(vdiff))

    def test_ljfortran_mix(self):
        """Test for mixture."""
        print('Testing for two-component mixture')
        system = set_up_initial_state()
        param1 = {0: {'sigma': 1.0, 'epsilon': 1.0, 'rcut': 2.5},
                  1: {'sigma': 2.0, 'epsilon': 1.2, 'rcut': 3.5}}
        idx = [i for i in range(system.particles.npart)]
        idx2 = np.random.choice(idx, size=int(system.particles.npart*0.25),
                                replace=False)
        print('Mutating {} particles'.format(len(idx2)))
        for i in idx2:
            system.particles.ptype[i] = 1
        result = run_calculations(system, param1)
        keys = ['python', 'python-numpy', 'fortran']
        for i, keyi in enumerate(keys[:-1]):
            for j, key2 in enumerate(keys[i+1:]):
                print('\nCompare {} and {}'.format(keyi, key2))
                force = np.allclose(result[i][1], result[i+j+1][1])
                print(' -> Forces close: {}'.format(force))
                self.assertTrue(force)
                virial = np.allclose(result[i][2], result[i+j+1][2])
                print(' -> Virial close: {}'.format(virial))
                self.assertTrue(virial)
                self.assertAlmostEqual(result[i][0], result[i+j+1][0], 7)
                vdiff = np.abs(result[i][0] - result[i+j+1][0])
                print(' -> Difference in pot. energy: {:.15e}'.format(vdiff))
if __name__ == '__main__':
    unittest.main()
