# -*- coding: utf-8 -*-
"""
Example of running a MD NVE simulation.
This system considered is a simple Lennard-Jones fluid.
"""
# pylint: disable=C0103
from __future__ import print_function
from pyretis.core.units import (create_conversion_factors,
                                generate_system_conversions, CONVERT)
from pyretis.inout.fileinout.traj import read_gromacs_file
import filecmp
import numpy as np
# for plotting:
from matplotlib import pyplot as plt
from matplotlib import gridspec as gridspec

def compare_traj(traj1, traj2):
    print('Comparing trajectories')
    print('Comparing with filecmp...')
    result = filecmp.cmp(traj1, traj2)
    if result is True:
        result_string = 'Files are equal!'
    else:
        result_string = 'Files are NOT equal!'
    print('Result: {}'.format(result_string))
    print('Checking mean squared error...')
    error = 0.0
    n = 0
    for snap1, snap2 in zip(read_gromacs_file(traj1),
                            read_gromacs_file(traj2)):
        xyz1 = np.column_stack((snap1['x'], snap1['y'], snap1['z']))
        xyz2 = np.column_stack((snap2['x'], snap2['y'], snap2['z']))
        diff = (xyz1 - xyz2)**2
        dsum = np.einsum('ij,ij -> i', diff, diff)
        error += dsum.sum()
        n += 1
    error /= float(n)
    print('Mean error between trajectories: {}'.format(error))
#from pyretis.inout.plotting import mpl_set_style
UNIT = 'lj'
with open('unit.txt', 'r') as fileh:
    for lines in fileh:
        UNIT = lines.strip()
create_conversion_factors('lj')
create_conversion_factors(UNIT)
generate_system_conversions('lj', UNIT)

#mpl_set_style()  # load pyretis style

# compare trajectories
compare_traj('../traj.gro', 'traj.gro')



ljunits = np.loadtxt('../thermo.txt')
other_units = np.loadtxt('thermo.txt')
# convert other_units:
other_units[:, 1] *= CONVERT['temperature'][UNIT, 'lj']
other_units[:, 2:5] *= CONVERT['energy'][UNIT, 'lj']
other_units[:, 5] *= CONVERT['pressure'][UNIT, 'lj']


# just make a bunch of plots comparing the energies
fig1 = plt.figure(figsize=(12, 6))
gs = gridspec.GridSpec(2, 2)
ax1 = fig1.add_subplot(gs[:, 0])
ax1.plot(ljunits[:, 0], ljunits[:, 2], label='Potential - lj',
         ls='-', lw=3, alpha=0.8)
ax1.plot(ljunits[:, 0], ljunits[:, 3], label='Kinetic - lj',
         ls='-', lw=3, alpha=0.8)
ax1.plot(ljunits[:, 0], ljunits[:, 4], label='Total - lj',
         ls='-', lw=3, alpha=0.8)
ax1.plot(other_units[:, 0], other_units[:, 2], label=UNIT,
         ls='--', lw=3, alpha=0.8)
ax1.plot(other_units[:, 0], other_units[:, 3], label=UNIT,
         ls='--', lw=3, alpha=0.8)
ax1.plot(other_units[:, 0], other_units[:, 4], label=UNIT,
         ls='--', lw=3, alpha=0.8)
ax1.set_xlabel('Step no.')
ax1.set_ylabel('Energy per particle')
ax1.legend(loc='center left', prop={'size': 'small'}, ncol=2)

ax2 = fig1.add_subplot(gs[0, 1])
ax2.plot(ljunits[:, 0], ljunits[:, 1], label='lj',
         ls='-', lw=3, alpha=0.8)
ax2.plot(other_units[:, 0], other_units[:, 1], label=UNIT,
         ls='--', lw=3, alpha=0.8)
ax2.set_ylabel('Temperature')
ax2.legend(loc='upper right', prop={'size': 'small'})

ax3 = fig1.add_subplot(gs[1, 1])
ax3.plot(ljunits[:, 0], ljunits[:, 5], label='lj',
         ls='-', lw=3, alpha=0.8)
ax3.plot(other_units[:, 0], other_units[:, 5], label=UNIT,
         ls='--', lw=3, alpha=0.8)
ax3.set_xlabel('Step no.')
ax3.set_ylabel('Pressure')
ax3.legend(loc='lower right', prop={'size': 'small'})
fig1.subplots_adjust(bottom=0.12, right=0.95, top=0.95, left=0.12, wspace=0.3)
plt.show()
