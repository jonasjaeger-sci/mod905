# -*- coding: utf-8 -*-
"""
Example of running a MD NVE simulation.
This system considered is a simple Lennard-Jones fluid.
"""
# pylint: disable=C0103
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import gridspec as gridspec
from pyretis.core.units import create_conversion_factors
from pyretis.inout.writers import FileIO, ThermoTable
from pyretis.inout.settings import (create_system, create_simulation,
                                    create_engine, create_force_field,
                                    create_output_tasks)
# for plotting:
from pyretis.inout.plotting import mpl_set_style
# Define simulation settings:
settings = {}
settings['simulation'] = {'task': 'md-nve', 'steps': 1000}
settings['system'] = {'units': 'lj', 'temperature': 2.0,
                      'dimensions': 3}
settings['engine'] = {'class': 'VelocityVerletF',
                      'delta_t': 0.002,
                      'module': 'vvintegratorf.py'}
settings['output'] = {'backup': False,
                      'write_vel': False,
                      'energy-file': 1,
                      'energy-screen': 10,
                      'trajectory-file': 1}
settings['potential'] = [{'class': 'PairLennardJonesCutnp', 'dim': 3,
                          'shift': True,
                          'parameter': {0: {'sigma': 1,
                                            'epsilon': 1,
                                            'factor': 2.5}}}]
settings['particles'] = {'position': {'generate': 'fcc',
                                      'repeat': [3, 3, 3],
                                      'density': 0.9},
                         'velocity': {'generate': 'maxwell',
                                      'momentum': True,
                                      'seed': 0}}
create_conversion_factors(settings['system']['units'])
print('# Creating system from settings.')
ljsystem = create_system(settings)
ljsystem.forcefield = create_force_field(settings)
print('# Creating simulation from settings.')
sim_args = {'system': ljsystem, 'engine': create_engine(settings)}
simulation_nve = create_simulation(settings, sim_args)
print('# Creating output tasks from settings.')
output_tasks = [task for task in create_output_tasks(settings)]
msg = 'Created fcc grid with {} atoms.'
print(msg.format(ljsystem.particles.npart))

# set up extra output:
table = ThermoTable()
thermo_file = FileIO('thermo.txt', header=table.header)
store_results = []
# run the simulation :-)
for result in simulation_nve.run():
    stepno = result['cycle']['stepno']
    for lines in table.generate_output(stepno, result['thermo']):
        thermo_file.write(lines)
    result['thermo']['stepno'] = stepno
    store_results.append(result['thermo'])
    for task in output_tasks:
        task.output(result)
# the rest is now just plotting:
# as an example, do some plotting:
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
