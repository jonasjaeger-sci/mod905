# -*- coding: utf-8 -*-
"""
Example of running a MD NVE simulation.
This system considered is a simple Lennard-Jones fluid.
"""
# pylint: disable=C0103
from __future__ import print_function
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import gridspec as gridspec
from pyretis.core.units import create_conversion_factors
from pyretis.inout.settings import (create_simulation, create_force_field,
                                    create_system)
from pyretis.inout.writers import FileIO, ThermoTable
from pyretis.inout import create_output
# for plotting:
from pyretis.inout.plotting import mpl_set_style
# simulation settings:
settings = {}
settings['simulation'] = {'task': 'md-nve',
                          'steps': 100000,
                          'exe-path': None}
settings['system'] = {'units': 'gromacs',
                      'temperature': 0.5,
                      'dimensions': 2}
settings['integrator'] = {'class': 'velocityverlet', 'timestep': 0.005}
settings['output'] = {'backup': False,
                      'write_vel': False,
                      'energy-file': 1,
                      'energy-screen': 10,
                      'trajectory-file': 10}
settings['potential'] = [{'class': 'DoublePendulumn',
                          'module': 'doublependulum.py',
                          'g': 1.0, 'l1': 1.0, 'l2': 1.0}]
settings['particles'] = {'position': {'file': 'initial2.gro'}}

create_conversion_factors(settings['system']['units'])
print('# Creating system from settings.')
dsystem = create_system(settings)
dsystem.forcefield = create_force_field(settings)
msg = '# Created fcc grid with {} atoms.'
print(msg.format(dsystem.particles.npart))
simulation_nve = create_simulation(settings, dsystem)

# set up extra output:
table = ThermoTable()
thermo_file = FileIO('thermo.dat', header=table.header)
store_results = []
# also create some other outputs:
output_tasks = [task for task in create_output(settings)]
# run the simulation :-)

for result in simulation_nve.run():
    theta1 = dsystem.particles.pos[0, 0]
    theta2 = dsystem.particles.pos[1, 0]
    x1 = np.sin(theta1)
    y1 = -np.cos(theta1)
    x2 = x1 + np.sin(theta2)
    y2 = y1 - np.cos(theta2)
    dsystem.particles.pos[0, 0] = x1
    dsystem.particles.pos[0, 1] = y1
    dsystem.particles.pos[1, 0] = x2
    dsystem.particles.pos[1, 1] = y2
    stepno = result['cycle']['stepno']
    for lines in table.generate_output(stepno, result['thermo']):
        thermo_file.write(lines)
    result['thermo']['stepno'] = stepno
    store_results.append(result['thermo'])
    for task in output_tasks:
        task.output(result)
    dsystem.particles.pos[0, 0] = theta1
    dsystem.particles.pos[1, 0] = theta2
# We are now done with the actual simulation. Let us now do some
# simple plotting of energies:
mpl_set_style()  # load pyretis style
step = [res['stepno'] for res in store_results]
pot_e = [res['vpot'] for res in store_results]
kin_e = [res['ekin'] for res in store_results]
tot_e = [res['etot'] for res in store_results]
pressure = [res['press'] for res in store_results]
temp = [res['temp'] for res in store_results]
# first figure - some energies
fig1 = plt.figure()
gs = gridspec.GridSpec(2, 2)
ax1 = fig1.add_subplot(gs[:, 0])
ax1.plot(step, pot_e, label='Potential')
ax1.plot(step, kin_e, label='Kinetic')
ax1.plot(step, tot_e, label='Total')
ax1.set_xlabel('Step no.')
ax1.set_ylabel('Energy per particle')
ax1.legend(loc='center left', prop={'size': 'small'})

ax2 = fig1.add_subplot(gs[0, 1])
ax2.plot(step, temp)
ax2.set_ylabel('Temperature')

ax3 = fig1.add_subplot(gs[1, 1])
ax3.plot(step, pressure)
ax3.set_xlabel('Step no.')
ax3.set_ylabel('Pressure')

fig1.subplots_adjust(bottom=0.12, right=0.95, top=0.95, left=0.12, wspace=0.3)
# second figure, momentum in different directions
momentum = np.array([res['mom'] for res in store_results])
fig2 = plt.figure()
ax4 = fig2.add_subplot(111)
ax4.plot(step, momentum[:, 0], lw=4, alpha=0.7, label='x')
ax4.plot(step, momentum[:, 1], lw=4, alpha=0.7, label='y')
ax4.plot(step, momentum[:, 2], lw=4, alpha=0.7, label='z')
ax4.set_xlabel('Step')
ax4.set_ylabel('Linear momentum')
ax4.legend(loc='upper center', prop={'size': 'small'}, ncol=3)
plt.show()
