# -*- coding: utf-8 -*-
"""
Example of running a MD NVE simulation.
In this example we re-run a LAMMPS simulation of
a mixture of 3 Lennard-Jones particles.
"""
# pylint: disable=C0103
from __future__ import print_function
from pyretis.core.simulation import Simulation
from pyretis.core import System, Box
from pyretis.core.units import create_conversion_factors
from pyretis.core.integrators import VelocityVerlet
from pyretis.forcefield import ForceField
from pyretis.forcefield.pairpotentials import PairLennardJonesCutnp
from pyretis.core.particlefunctions import calculate_thermo
import numpy as np
import os
# for plotting:
from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator
from matplotlib import gridspec as gridspec
from pyretis.inout.plotting import mpl_set_style

create_conversion_factors('lj')
size = [[0.0, 8.39798] for _ in range(3)]  # hard coded box-size
box = Box(size)
ljsystem = System(box=box, units='lj')

ljpot = PairLennardJonesCutnp(shift=True, mixing='geometric')
lj_parameters = {'A': {'sigma': 1.0, 'epsilon': 1.0, 'rcut': 2.5},
                 'B': {'sigma': 1.2, 'epsilon': 1.1, 'rcut': 2.5},
                 'C': {'sigma': 1.4, 'epsilon': 0.9, 'rcut': 2.5},
                 'mixing': 'geometric'}
forcefield = ForceField(potential=[ljpot], params=[lj_parameters])

ljsystem.forcefield = forcefield

# read initial position and velocity:
dirname = 'input_data'
pos = np.loadtxt(os.path.join(dirname, 'initial_pos_mixture.txt.gz'))
vel = np.loadtxt(os.path.join(dirname, 'initial_vel_mixture.txt.gz'))
idx = np.loadtxt(os.path.join(dirname, 'atom_types_mixture.txt.gz'))
names = {1: 'A', 2: 'B', 3: 'C'}
masses = {1: 1.0, 2: 1.0, 3: 1.5}
natoms = {}
npart = 0.0
for xyzi, veli, idxi in zip(pos, vel, idx):
    itype = int(idxi)
    ljsystem.add_particle(name=names[itype], pos=xyzi, vel=veli,
                          mass=masses[itype], ptype=names[itype])
    if not names[itype] in natoms:
        natoms[names[itype]] = 0
    natoms[names[itype]] += 1
    npart += 1.0
print('Initiated system with {} particles'.format(int(npart)))
for atom in natoms:
    print('{0:>4d} atoms of type {1}'.format(int(natoms[atom]), atom))
ljsystem.potential_and_force()

# run simulation from this starting point:
numberofsteps = 1000
simulationLAMMPS = Simulation(endcycle=numberofsteps)
integrator = VelocityVerlet(0.0025)
task_integrate = {'func': integrator.integration_step,
                  'args': [ljsystem]}

simulationLAMMPS.add_task(task_integrate)

thermo_output = {}
step = []
outfmt = '{0:8d} {1:12.7f} {2:12.7f} {3:12.7f} {4:12.7f} {5:12.7f}'
outfmt2 = '# {0:>6s} {1:>12s} {2:>12s} {3:>12s} {4:>12s} {5:>12s}'
print(outfmt2.format('Step', 'Temp', 'Press', 'Pot', 'Kin', 'Total'))

while not simulationLAMMPS.is_finished():
    # do a step
    simulationLAMMPS.step()
    thermo = calculate_thermo(ljsystem)
    for key in thermo:
        try:
            thermo_output[key].append(thermo[key])
        except KeyError:
            thermo_output[key] = [thermo[key]]
    step.append(simulationLAMMPS.cycle['step'])
    print(outfmt.format(step[-1], thermo['temp'], thermo['press'],
                        thermo['vpot'], thermo['ekin'], thermo['etot']))

for key in thermo_output:
    thermo_output[key] = np.array(thermo_output[key])
# The simulation have now ended, we will plot some results and compare
# with output from LAMMPS:
mpl_set_style()  # load pyretis style

dirname = 'output_data'
d = np.loadtxt(os.path.join(dirname, 'lammps-output_mixture.txt.gz'))
# step, temperature, press, potential, ekin, etot, pxx, pyy, pzz, pxy, pxz, pyz
n = min(len(thermo_output['vpot']), len(d[:, 0]))

print('Plotting energies')
# make figure of energies: potential, kinetic and total:
fig = plt.figure()
ax1 = fig.add_subplot(311)
ax1.set_ylabel('Potential')
ax1.set_title('Energies per particle')
ax1.plot(d[:n, 0], d[:n, 3], lw=4, ls='-',
         color='b', alpha=0.5, label='lammps')
ax1.plot(step[:n], thermo_output['vpot'][:n], lw=4, ls='--',
         color='k', alpha=0.5, label='pyretis')

ax2 = fig.add_subplot(312)
ax2.set_ylabel('Kinetic')
ax2.plot(d[:n, 0], d[:n, 4], lw=4, ls='-',
         color='b', alpha=0.5, label='lammps')
ax2.plot(step[:n], thermo_output['ekin'][:n], lw=4, ls='--',
         color='k', alpha=0.5, label='pyretis')

ax3 = fig.add_subplot(313)
ax3.set_ylabel('Total')
ax3.plot(d[:n, 0], d[:n, 5], lw=4, ls='-',
         color='b', alpha=0.5, label='lammps')
ax3.plot(step[:n], thermo_output['etot'][:n], lw=4, ls='--',
         color='k', alpha=0.5, label='pyretis')

ax1.set_xticklabels(())
ax2.set_xticklabels(())
ax3.set_xlabel('step no.')
ax1.yaxis.set_major_locator(MaxNLocator(nbins=3 + 1,  # + 1 due to prune lower
                                        prune='lower'))
ax2.yaxis.set_major_locator(MaxNLocator(nbins=3 + 2,  # + 2 due to prune both
                                        prune='both'))
ax3.yaxis.set_major_locator(MaxNLocator(nbins=4))
ax1.legend(loc='upper right', prop={'size': 'small'})
fig.tight_layout()
plt.subplots_adjust(hspace=0.0)

print('Plotting pressure and temperature')
# make figure of pressure and temperature:
fig2 = plt.figure()
ax1 = fig2.add_subplot(211)
ax1.set_ylabel('Temperature')
ax1.plot(d[:n, 0], d[:n, 1], lw=4, ls='-',
         color='b', alpha=0.5, label='lammps')
ax1.plot(step[:n], thermo_output['temp'][:n], lw=4, ls='--',
         color='k', alpha=0.5, label='pyretis')
ax1.legend(loc='lower right', prop={'size': 'small'})
ax1.set_xticklabels(())

ax2 = fig2.add_subplot(212)
ax2.set_ylabel('Pressure')
ax2.plot(d[:n, 0], d[:n, 2], lw=4, ls='-',
         color='b', alpha=0.5, label='lammps')
ax2.plot(step[:n], thermo_output['press'][:n], lw=4, ls='--',
         color='k', alpha=0.5, label='pyretis')
plt.subplots_adjust(hspace=0.0)
ax2.set_xlabel('step no.')

ax1.yaxis.set_major_locator(MaxNLocator(nbins=len(ax1.get_yticklabels()),
                                        prune='lower'))
ax2.yaxis.set_major_locator(MaxNLocator(nbins=len(ax2.get_yticklabels()),
                                        prune='upper'))

print('Plotting pressure tensor')
# make detailed plot of pressure tensor:
fig3 = plt.figure()
grid = gridspec.GridSpec(3, 2)
presslab = ['pxx', 'pyy', 'pzz', 'pxy', 'pxz', 'pyz']
pressindex = [(0, 0), (1, 1), (2, 2), (0, 1), (0, 2), (1, 2)]
for i, (pi, idx) in enumerate(zip(presslab, pressindex)):
    ax = fig3.add_subplot(grid[i % 3, int(i / 3)])
    ax.set_ylabel(pi)
    ax.plot(d[:n, 0], d[:n, i + 6], lw=4, ls='-',
            color='b', alpha=0.5, label='lammps')
    ax.plot(step[:n], thermo_output['press-tens'][:n, idx[0], idx[1]],
            lw=4, ls='--', color='k', alpha=0.5, label='pyretis')
    if i == 0:
        ax.legend(loc='upper left', prop={'size': 'small'}, ncol=1)
    if i == 2 or i == 5:
        ax.yaxis.set_major_locator(MaxNLocator(nbins=3 + 1,
                                               prune='lower'))
        ax.set_xlabel('step no.')
    else:
        ax.set_xticklabels(())
        ax.yaxis.set_major_locator(MaxNLocator(nbins=3 + 2,
                                               prune='both'))
fig3.tight_layout()
plt.subplots_adjust(hspace=0.0)
plt.show()
