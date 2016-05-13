# -*- coding: utf-8 -*-
"""Test the Fortran implementation of the velocity verlet integrator.

This test is comparing:

1) The python (numpy) implementation

2) The Fortran implementation.
"""
# pylint: disable=C0103
from __future__ import print_function
import unittest
import numpy as np
from pyretis.core import System, Box
from pyretis.core.simulation import Simulation
from pyretis.core.units import create_conversion_factors
from pyretis.forcefield import ForceField
from pyretis.forcefield.potentials import PairLennardJonesCutnp
from pyretis.tools import generate_lattice
from pyretis.core.integrators import VelocityVerlet
from vvintegratorc import VelocityVerletC


def set_up_initial_state():
    """Create particles for the test."""
    create_conversion_factors('lj')
    lattice, size = generate_lattice('fcc', [3, 3, 3], density=0.9)
    npart = len(lattice)
    lattice += np.random.randn(npart, 3) * 0.05
    box = Box(size, periodic=[True, True, True])
    system = System(temperature=1.0, units='lj', box=box)
    for pos in lattice:
        system.add_particle(name='Ar', pos=pos, mass=1.0, ptype=0)
    msg = 'Created lattice with {} atoms.'
    print(msg.format(system.particles.npart))
    parameters = {0: {'sigma': 1.0, 'epsilon': 1.0, 'rcut': 2.5}}
    potentialnp = PairLennardJonesCutnp(dim=3, shift=True)
    forcefieldnp = ForceField(potential=[potentialnp],
                              params=[parameters],
                              desc='Python (Numpy)')
    system.forcefield = forcefieldnp
    return system


class VVIntegratorTest(unittest.TestCase):
    """Run the tests for the Fortran integrator."""

    def test_integrator(self):
        """Test by integrating the equations of motion."""
        system = set_up_initial_state()
        initial = system.particles.get_phase_point()
        numberofsteps = 20
        simulation = Simulation(endcycle=numberofsteps)
        integrator = VelocityVerlet(0.0025)
        task_integrate = {'func': integrator.integration_step,
                          'args': [system]}
        simulation.add_task(task_integrate)
        traj = []
        for _ in simulation.run():
            traj.append(system.particles.get_phase_point())
        # repeat with external integrator:
        system.particles.set_phase_point(initial)
        simulation = Simulation(endcycle=numberofsteps)
        integrator = VelocityVerletC(0.0025)
        task_integrate = {'func': integrator.integration_step,
                          'args': [system]}
        simulation.add_task(task_integrate)
        traj2 = []
        for _ in simulation.run():
            traj2.append(system.particles.get_phase_point())
        for trj1, trj2 in zip(traj, traj2):
            posok = np.allclose(trj1['pos'], trj2['pos'])
            self.assertTrue(posok)
            velok = np.allclose(trj1['vel'], trj2['vel'])
            self.assertTrue(velok)
            forceok = np.allclose(trj1['force'], trj2['force'])
            self.assertTrue(forceok)


if __name__ == '__main__':
    unittest.main()
