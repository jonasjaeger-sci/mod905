# -*- coding: utf-8 -*-
"""
Example of running a MD NVE simulation.
This system considered is a simple Lennard-Jones fluid.
"""
# pylint: disable=C0103
from __future__ import print_function
from retis.core import Simulation, System, Box, RandomGenerator
from retis.core.particlefunctions import (calculate_kinetic_energy_tensor,
                                          calculate_kinetic_temperature,
                                          calculate_scalar_pressure,
                                          calculate_linear_momentum)
from retis.core.integrators import VelocityVerlet
from retis.forcefield import ForceField, PairLennardJonesCutnp
from retis.io import WriteGromacs
from retis.tools import latticefcc
import numpy as np

# set up potential function(s) and force field:
potential = PairLennardJonesCutnp(shift=True)
forcefield = ForceField(potential=[potential],
                        params=[{'Ar': {'sigma': 1.0,
                                        'epsilon': 1.0,
                                        'rcut': 2.5}}])
lattice, size = latticefcc(density=0.9, nrx=3, nry=3, nrz=3)
box = Box(size)

ljsystem = System(temperature=2.0, units='lj', box=box)
for pos in lattice:
    ljsystem.add_particle(name='Ar', pos=pos, mass=1.0, ptype='Ar')
npart = ljsystem.particles.npart
print('Created fcc grid with {} atoms.'.format(npart))

ljsystem.adjust_dof([1, 1, 1])  # adjust DOF since we are in "NVEMG"
# generate velocities:
rgen = RandomGenerator(seed=0)
ljsystem.generate_velocities(rgen, momentum=True)
avgtemp = ljsystem.calculate_temperature()
print('Generated temperatures with average: {}'.format(avgtemp))
# Attach force field:
ljsystem.forcefield = forcefield
ljsystem.potential_and_force()
# initial trajectory writer
write_gro = WriteGromacs('test.gro', box, frame=0, units=ljsystem.units)

# set up a simple NVE simulation
numberofsteps = 2000
simulationNVE = Simulation(endcycle=numberofsteps)
integrator = VelocityVerlet(0.002)

task_integrate = {'func': integrator.integration_step,
                  'args': [ljsystem]}

simulationNVE.add_task(task_integrate)


def common_calculations(system):
    """
    This function defines some common calculations for the system.
    It used functions from the particle functions module to obtain
    energies, pressure, etc.
    """
    particles = system.particles
    dof = system.temperature['dof']
    dim = system.get_dim()
    volume = system.box.calculate_volume()
    kin_tens = calculate_kinetic_energy_tensor(particles)
    _, tempi, _ = calculate_kinetic_temperature(particles, dof=dof,
                                                kin_tensor=kin_tens)
    ekini = kin_tens.trace()
    pressi = calculate_scalar_pressure(particles, volume, dim,
                                       kin_tensor=kin_tens)
    vpoti = system.v_pot
    etoti = ekini + vpoti
    momi = calculate_linear_momentum(particles)
    return vpoti, ekini, etoti, tempi, pressi, momi

temps = []
kinetic_e = []
potential_e = []
total_e = []
pressure = []
step = []
momentum = []
outfmt = '{0:8d} {1:12.7f} {2:12.7f} {3:12.7f} {4:12.7f} {5:12.7f}'
outfmt2 = '# {0:>6s} {1:>12s} {2:>12s} {3:>12s} {4:>12s} {5:>12s}'
print(outfmt2.format('Step', 'Temp', 'Pot', 'Kin', 'Total', 'Press'))
while not simulationNVE.is_finished():
    step.append(simulationNVE.cycle['step'])
    vpot, ekin, etot, avgtemp, press, mom = common_calculations(ljsystem)
    temps.append(avgtemp)
    kinetic_e.append(ekin / npart)
    potential_e.append(vpot / npart)
    total_e.append(etot / npart)
    pressure.append(press)
    momentum.append(mom)
    print(outfmt.format(step[-1], temps[-1], potential_e[-1], kinetic_e[-1],
                        total_e[-1], pressure[-1]))
    write_gro.write_frame(ljsystem.particles.pos)
    simulationNVE.step()

# make some plots of results from the simulation:
from matplotlib import pyplot as plt
import matplotlib.gridspec as gridspec

gs = gridspec.GridSpec(2, 2)
fig = plt.figure(figsize=(12, 6))
ax1 = fig.add_subplot(gs[:, 0])
ax1.set_ylabel('Energy per particle')
ax1.plot(step, potential_e, lw=4, ls='-',
         color='b', alpha=0.5, label='Potential')
ax1.plot(step, kinetic_e, lw=4, ls='-',
         color='g', alpha=0.5, label='Kinetic')
ax1.plot(step, total_e, lw=4, ls='-',
         color='k', alpha=0.5, label='Total')
ax1.legend()
ax1.set_xlabel('Step')
ax2 = fig.add_subplot(gs[0, 1])
ax2.set_ylabel('Pressure')
ax2.plot(step, pressure, lw=4, ls='-',
         color='b', alpha=0.5, label='Pressure')
ax2.legend()
momentum = np.array(momentum)
ax3 = fig.add_subplot(gs[1, 1])
ax3.plot(step, momentum[:, 0], lw=4, ls='-',
         color='b', alpha=0.5, label='x-direction')
ax3.plot(step, momentum[:, 1], lw=4, ls='-',
         color='g', alpha=0.5, label='y-direction')
ax3.plot(step, momentum[:, 2], lw=4, ls='-',
         color='k', alpha=0.5, label='z-direction')
ax3.set_xlabel('Step')
ax3.set_ylabel('Linear momentum')
fig.subplots_adjust(bottom=0.1, right=0.95, top=0.9, left=0.12, wspace=0.3)
plt.show()
