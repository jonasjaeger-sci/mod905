# -*- coding: utf-8 -*-
"""
Example of running a MD NVE simulation.
This system considered is a simple Lennard-Jones fluid.
"""
# pylint: disable=C0103
from __future__ import print_function
from retis.core import Box, System
from retis.core import create_simulation
from retis.forcefield import ForceField
from retis.forcefield.pairpotentials import PairLennardJonesCutnp
from retis.inout import (get_predefined_table, FileWriter)
from retis.tools import latticefcc
import numpy as np
# for plotting:
from matplotlib import pyplot as plt
from matplotlib import gridspec as gridspec
from retis.inout import mpl_set_style
# define potential function(s) and force field:
LJPARAMETERS = {'Ar': {'sigma': 1.0, 'epsilon': 1.0, 'rcut': 2.5}}
POTENTIAL = PairLennardJonesCutnp(shift=True)  # use a shifted LJ potential
# set up a lattice and create a box
lattice, size = latticefcc(density=0.9, nrx=3, nry=3, nrz=3)
box = Box(size, periodic=[True, True, True])
ljsystem = System(temperature=2.0, units='lj', box=box)
ljsystem.forcefield = ForceField(potential=[POTENTIAL],
                                 params=[LJPARAMETERS])
for pos in lattice:
    ljsystem.add_particle(name='Ar', pos=pos, mass=1.0, ptype='Ar')
# adjust DOF since we are in "NVEMG" with periodic boundaries
ljsystem.adjust_dof([1, 1, 1])
ljsystem.generate_velocities(seed=0, momentum=True)
msg = 'Created fcc grid with {} atoms.'
print(msg.format(ljsystem.particles.npart))
msg = 'Generated temperatures with average: {}'
print(msg.format(ljsystem.calculate_temperature()))

# set up simulation:
settings = {'type': 'NVE',
            'system': ljsystem,
            'integrator': {'name': 'velocityverlet', 'timestep': 0.002},
            'endcycle': 100,
            'output': [{'target': 'file', 'type': 'traj', 'every': 1,
                        'format': 'gro'}]}

simulation_nve = create_simulation(settings)

# set up output:
table = get_predefined_table('energies')
thermo_file = FileWriter('thermo.txt', 'table',
                         header={'text': table.get_header()})

# write/display table header:
store_results = []
# run the simulation :-)
for result in simulation_nve.run():
    step = result['cycle']['stepno']
    result['thermo']['stepno'] = step
    if step % 1 == 0:
        thermo_file.write_line(table(result['thermo']))
        store_results.append(result['thermo'])

# as an example, do some plotting:
mpl_set_style()  # load pytismol style

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
