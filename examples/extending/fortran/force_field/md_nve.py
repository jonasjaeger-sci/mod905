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
from pyretis.core import Box, System
from pyretis.core.units import create_conversion_factors
from pyretis.inout.settings import create_simulation
from pyretis.forcefield import ForceField
from pyretis.inout.writers import FileIO, ThermoTable
from pyretis.inout import create_output
from pyretis.tools import generate_lattice
from pyretis.inout.plotting import mpl_set_style
from ljpotentialf import PairLennardJonesCutF
# define potential function(s) and force field:
create_conversion_factors('lj')
LJPARAMETERS = {0: {'sigma': 1.0, 'epsilon': 1.0, 'rcut': 2.5},
                1: {'sigma': 1.0, 'epsilon': 1.0, 'rcut': 2.5},
                'mixing': 'geometric'}
LJPARAMETERS = {0: {'sigma': 1.0, 'epsilon': 1.0, 'rcut': 2.5}}
POTENTIAL = PairLennardJonesCutF(dim=3, shift=True)

# simulation settings:
settings = {'task': 'md-nve',
            'units': 'lj',
            'integrator': {'name': 'velocityverlet', 'timestep': 0.002},
            'endcycle': 1000,
            'output-modify': [{'name': 'traj', 'when': {'every': 1},
                               'filename': 'traj.gro'}],
            'generate-vel': {'seed': 0, 'momentum': True,
                             'distribution': 'maxwell'}}


# set up a lattice and create a box
lattice, size = generate_lattice('fcc', [3, 3, 3], density=0.9)
box = Box(size, periodic=[True, True, True])
ljsystem = System(temperature=2.0, units='lj', box=box)
ljsystem.forcefield = ForceField(potential=[POTENTIAL],
                                 params=[LJPARAMETERS])
for pos in lattice:
    ljsystem.add_particle(name='Ar', pos=pos, mass=1.0, ptype=0)
msg = 'Created fcc grid with {} atoms.'
print(msg.format(ljsystem.particles.npart))

if 'generate-vel' in settings:
    ljsystem.generate_velocities(**settings['generate-vel'])
    msg = 'Generated temperatures with average: {}'
    print(msg.format(ljsystem.calculate_temperature()))

simulation_nve = create_simulation(settings, ljsystem)

# set up extra output:
table = ThermoTable()
thermo_file = FileIO('thermo.txt', header=table.header)
store_results = []
# also create some other outputs:
output_tasks = [task for task in create_output(settings)]
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
