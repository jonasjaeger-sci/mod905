# -*- coding: utf-8 -*-
"""
Example of running a MD NVE simulation.
This system considered is a simple Lennard-Jones fluid.
"""
# pylint: disable=C0103
from __future__ import print_function
from pyretis.core.units import (create_conversion_factors,
                                generate_system_conversions, CONVERT)
import numpy as np
# for plotting:
from matplotlib import pyplot as plt
from matplotlib import gridspec as gridspec
from pyretis.inout.plotting import mpl_set_style
create_conversion_factors('lj')
create_conversion_factors('real')
generate_system_conversions('lj', 'real')

mpl_set_style()  # load pyretis style

ljunits = np.loadtxt('../thermo.txt')
realunits = np.loadtxt('thermo.txt')
# convert realunits:
realunits[:, 1] *= CONVERT['temperature']['real', 'lj']
realunits[:, 2:5] *= CONVERT['energy']['real', 'lj']
realunits[:, 5] *= CONVERT['pressure']['real', 'lj']


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
ax1.plot(realunits[:, 0], realunits[:, 2], label='real',
         ls='--', lw=3, alpha=0.8)
ax1.plot(realunits[:, 0], realunits[:, 3], label='real',
         ls='--', lw=3, alpha=0.8)
ax1.plot(realunits[:, 0], realunits[:, 4], label='real',
         ls='--', lw=3, alpha=0.8)
ax1.set_xlabel('Step no.')
ax1.set_ylabel('Energy per particle')
ax1.legend(loc='center left', prop={'size': 'small'}, ncol=2)

ax2 = fig1.add_subplot(gs[0, 1])
ax2.plot(ljunits[:, 0], ljunits[:, 1], label='lj',
         ls='-', lw=3, alpha=0.8)
ax2.plot(realunits[:, 0], realunits[:, 1], label='real',
         ls='--', lw=3, alpha=0.8)
ax2.set_ylabel('Temperature')
ax2.legend(loc='upper right', prop={'size': 'small'})

ax3 = fig1.add_subplot(gs[1, 1])
ax3.plot(ljunits[:, 0], ljunits[:, 5], label='lj',
         ls='-', lw=3, alpha=0.8)
ax3.plot(realunits[:, 0], realunits[:, 5], label='real',
         ls='--', lw=3, alpha=0.8)
ax3.set_xlabel('Step no.')
ax3.set_ylabel('Pressure')
ax3.legend(loc='lower right', prop={'size': 'small'})
fig1.subplots_adjust(bottom=0.12, right=0.95, top=0.95, left=0.12, wspace=0.3)
plt.show()
