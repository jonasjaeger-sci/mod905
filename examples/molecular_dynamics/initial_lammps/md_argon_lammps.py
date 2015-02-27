# -*- coding: utf-8 -*-
"""
Example of running a MD NVE simulation.
In this example we re-run a LAMMPS simulation using
pyretis.
"""
# pylint: disable=C0103
from __future__ import print_function
from retis.core import Simulation, System, Box
from retis.core.integrators import VelocityVerlet
from retis.forcefield import ForceField, PairLennardJonesCutnp
from retis.core.particlefunctions import (calculate_kinetic_energy_tensor,
                                          calculate_pressure_tensor,
                                          calculate_kinetic_temperature,
                                          calculate_scalar_pressure)
import numpy as np
import os

size = [[0.0, 8.39798] for _ in range(3)]  # hard coded box-size
box = Box(size)
ljsystem = System(box=box, units='lj')

ljpot = PairLennardJonesCutnp(shift=False, mixing='geometric')
forcefield = ForceField(potential=[ljpot],
                        params=[{'Ar': {'sigma': 1.0,
                                        'epsilon': 1.0,
                                        'rcut': 2.5}}])
ljsystem.forcefield = forcefield

# read initial position and velocity:
dirname = 'input_data'
pos = np.loadtxt(os.path.join(dirname, 'initial_pos.txt.gz'))
vel = np.loadtxt(os.path.join(dirname, 'initial_vel.txt.gz'))
for xyzi, veli in zip(pos, vel):
    ljsystem.add_particle(name='Ar', pos=xyzi, vel=veli, mass=1.0, ptype='Ar')
npart = float(ljsystem.particles.npart)
print('Initiated system with {} particles'.format(int(npart)))
ljsystem.potential_and_force()
# run simulation from this starting point:
numberofsteps = 1000
simulationLAMMPS = Simulation(endcycle=numberofsteps)
integrator = VelocityVerlet(0.0025)
task_integrate = {'func': integrator.integration_step,
                  'args': [ljsystem]}

simulationLAMMPS.add_task(task_integrate)
ljsystem.adjust_dof([1, 1, 1])


def common_calculations(system):
    """
    This function defines some common calculations that we
    typically want to do. Here we obtain temperature, pressure,
    kinetic, potential and total energy
    """
    kin_tensi = calculate_kinetic_energy_tensor(system)
    press_tensi = calculate_pressure_tensor(system,
                                            kin_tensor=kin_tensi)
    _, tempi, _ = calculate_kinetic_temperature(system,
                                                kin_tensor=kin_tensi)
    ekini = kin_tensi.trace()
    pressi = calculate_scalar_pressure(system, press_tensor=press_tensi,
                                       kin_tensor=kin_tensi)
    vpoti = system.v_pot
    etoti = ekini + vpoti
    return vpoti, ekini, etoti, tempi, pressi, press_tensi


v_pot, e_kin, e_tot = [], [], []
temp = []
pressure, pressure_tensor = [], []
step = []
outfmt = '{0:8d} {1:12.7f} {2:12.7f} {3:12.7f} {4:12.7f} {5:12.7f}'
while not simulationLAMMPS.is_finished():
    vpot, ekin, etot, avgtemp, press, presstens = common_calculations(ljsystem)
    v_pot.append(vpot / npart)
    e_kin.append(ekin / npart)
    e_tot.append(etot / npart)
    pressure.append(press)
    pressure_tensor.append(presstens)
    temp.append(avgtemp)
    step.append(simulationLAMMPS.cycle['step'])
    print(outfmt.format(step[-1], temp[-1], pressure[-1],
                        v_pot[-1], e_kin[-1], e_tot[-1]))
    # do a step
    simulationLAMMPS.step()

# The simulation have now ended, we will plot some results and compare
# with output from LAMMPS:
from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator

d = np.loadtxt('lammps-output.txt.gz')
# step, temperature, press, potential, ekin, etot, pxx, pyy, pzz, pxy, pxz, pyz
n = min(len(v_pot), len(d[:, 0]))

# make figure of energies: potential, kinetic and total:
fig = plt.figure()
ax1 = fig.add_subplot(311)
ax1.set_ylabel('Potential')
ax1.set_title('Energies per particle')
ax1.plot(d[:n, 0], d[:n, 3], lw=4, ls='-',
         color='b', alpha=0.5, label='lammps')
ax1.plot(step[:n], v_pot[:n], lw=4, ls='--',
         color='k', alpha=0.5, label='pyretis')
ax1.legend(loc='lower right')

ax2 = fig.add_subplot(312)
ax2.set_ylabel('Kinetic')
ax2.plot(d[:n, 0], d[:n, 4], lw=4, ls='-',
         color='b', alpha=0.5, label='lammps')
ax2.plot(step[:n], e_kin[:n], lw=4, ls='--',
         color='k', alpha=0.5, label='pyretis')

ax3 = fig.add_subplot(313)
ax3.set_ylabel('Total')
ax3.plot(d[:n, 0], d[:n, 5], lw=4, ls='-',
         color='b', alpha=0.5, label='lammps')
ax3.plot(step[:n], e_tot[:n], lw=4, ls='--',
         color='k', alpha=0.5, label='pyretis')

ax1.set_xticklabels(())
ax2.set_xticklabels(())
ax3.set_xlabel('step no.')
ax1.yaxis.set_major_locator(MaxNLocator(nbins=len(ax1.get_yticklabels()),
                                        prune='lower'))
ax2.yaxis.set_major_locator(MaxNLocator(nbins=len(ax2.get_yticklabels()),
                                        prune='both'))
fig.tight_layout()
plt.subplots_adjust(hspace=0.0)

# make figure of pressure and temperature:
fig2 = plt.figure()
ax1 = fig2.add_subplot(211)
ax1.set_ylabel('Temperature')
ax1.plot(d[:n, 0], d[:n, 1], lw=4, ls='-',
         color='b', alpha=0.5, label='lammps')
ax1.plot(step[:n], temp[:n], lw=4, ls='--',
         color='k', alpha=0.5, label='pyretis')
ax1.legend(loc='upper right')
ax1.set_xticklabels(())

ax2 = fig2.add_subplot(212)
ax2.set_ylabel('Pressure')
ax2.plot(d[:n, 0], d[:n, 2], lw=4, ls='-',
         color='b', alpha=0.5, label='lammps')
ax2.plot(step[:n], pressure[:n], lw=4, ls='--',
         color='k', alpha=0.5, label='pyretis')
plt.subplots_adjust(hspace=0.0)
ax2.set_xlabel('step no.')

ax1.yaxis.set_major_locator(MaxNLocator(nbins=len(ax1.get_yticklabels()),
                                        prune='lower'))
ax2.yaxis.set_major_locator(MaxNLocator(nbins=len(ax2.get_yticklabels()),
                                        prune='upper'))

# make detailed plot of pressure tensor:
pressure_tensor = np.array(pressure_tensor)
fig3 = plt.figure()
presslab = ['pxx', 'pyy', 'pzz', 'pxy', 'pxz', 'pyz']
pressindex = [(0, 0), (1, 1), (2, 2), (0, 1), (0, 2), (1, 2)]
for i, (pi, idx) in enumerate(zip(presslab, pressindex)):
    ax = fig3.add_subplot(int('61{}'.format(i + 1)))
    ax.set_ylabel(pi)
    ax.plot(d[:n, 0], d[:n, i + 6], lw=4, ls='-',
            color='b', alpha=0.5, label='lammps')
    ax.plot(step[:n], pressure_tensor[:n, idx[0], idx[1]], lw=4, ls='--',
            color='k', alpha=0.5, label='pyretis')
    if i == 0:
        ax.legend(loc='lower right')
        ax.yaxis.set_major_locator(MaxNLocator(nbins=len(ax.get_yticklabels()),
                                               prune='lower'))
    if i < 5:
        ax.set_xticklabels(())
    if i > 0:
        ax.yaxis.set_major_locator(MaxNLocator(nbins=len(ax.get_yticklabels()),
                                               prune='both'))
plt.subplots_adjust(hspace=0.0)
plt.show()
