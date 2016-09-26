# -*- coding: utf-8 -*-
"""Simple gromacs script to compare outcome of two simulations.

The outcome of the md_nve.py simulation should be independent (to numerical
precision) of the units used. This script will test that by comparing:

- the output in `thermo.txt`

- the generated trajectory, `traj.gro`

For the energies, it will create a plot comparing the energies, the pressure
and the temperature.
"""
# pylint: disable=C0103
from __future__ import print_function
import filecmp
import numpy as np
from pyretis.core.units import (create_conversion_factors,
                                generate_system_conversions, CONVERT)
from pyretis.inout.writers.traj import read_gromacs_file
from pyretis.inout.settings import parse_settings_file
# for plotting:
from pyretis.inout.plotting import mpl_set_style
from matplotlib import pyplot as plt
from matplotlib import gridspec as gridspec


def compare_traj(traj1, traj2):
    """A comparison of two trajectories from gromacs.

    The files are both compared using filecmp and by calculating the
    difference between the coordinates for each frame in the files. This, of
    course assumes that the files have the same number of atoms and same
    number of snapshots.

    Parameters
    ----------
    traj1 : string
        A gromacs file to open.
    traj2 : string
        A gromacs file to open.

    Returns
    -------
    None, just prints out the result of the comparison.
    """
    print('Comparing trajectories')
    print('Comparing with filecmp...')
    result = filecmp.cmp(traj1, traj2)
    if result is True:
        result_string = 'Files are equal! :-)'
    else:
        result_string = 'Files are NOT equal!'
    print('Result: {}'.format(result_string))
    print('Checking mean squared error...')
    error = 0.0
    nsnap = 0
    for snap1, snap2 in zip(read_gromacs_file(traj1),
                            read_gromacs_file(traj2)):
        xyz1 = np.column_stack((snap1['x'], snap1['y'], snap1['z']))
        xyz2 = np.column_stack((snap2['x'], snap2['y'], snap2['z']))
        diff = (xyz1 - xyz2)**2
        dsum = np.einsum('ij,ij -> i', diff, diff)
        error += dsum.sum()
        nsnap += 1
    error /= float(nsnap)
    print('Mean error between trajectories: {}'.format(error))


if __name__ == '__main__':
    settings = parse_settings_file('settings.rst')
    UNIT = settings['system']['units']
    create_conversion_factors('lj')
    create_conversion_factors(UNIT)
    generate_system_conversions('lj', UNIT)
    compare_traj('../traj.gro', 'traj.gro')
    ljunits = np.loadtxt('../thermo.txt')
    other_units = np.loadtxt('thermo.txt')
    # convert other_units:
    other_units[:, 1] *= CONVERT['temperature'][UNIT, 'lj']
    other_units[:, 2:5] *= CONVERT['energy'][UNIT, 'lj']
    other_units[:, 5] *= CONVERT['pressure'][UNIT, 'lj']
    # just make a bunch of plots comparing the energies
    mpl_set_style()  # load pyretis style
    fig1 = plt.figure(figsize=(12, 6))
    gs = gridspec.GridSpec(2, 2)
    ax1 = fig1.add_subplot(gs[:, 0])
    ljlab = '"lj"'
    unilab = '"{}"'.format(UNIT)
    ax1.plot([], [], label='Potential', lw=0, alpha=0)
    ax1.plot([], [], label='Kinetic', lw=0, alpha=0)
    ax1.plot([], [], label='Total', lw=0, alpha=0)

    ax1.plot(ljunits[:, 0], ljunits[:, 2], label=ljlab,
             ls='-', lw=7, alpha=0.8)
    ax1.plot(ljunits[:, 0], ljunits[:, 3], label=ljlab,
             ls='-', lw=7, alpha=0.8)
    ax1.plot(ljunits[:, 0], ljunits[:, 4], label=ljlab,
             ls='-', lw=7, alpha=0.8)
    ax1.plot(other_units[:, 0], other_units[:, 2], label=unilab,
             ls='--', lw=3, alpha=0.8)
    ax1.plot(other_units[:, 0], other_units[:, 3], label=unilab,
             ls='--', lw=3, alpha=0.8)
    ax1.plot(other_units[:, 0], other_units[:, 4], label=unilab,
             ls='--', lw=3, alpha=0.8)
    ax1.set_xlabel('Step no.')
    ax1.set_ylabel('Energy per particle')
    leg = ax1.legend(loc='center left', prop={'size': 'small'}, ncol=3)

    ax2 = fig1.add_subplot(gs[0, 1])
    ax2.plot(ljunits[:, 0], ljunits[:, 1], label=ljlab,
             ls='-', lw=7, alpha=0.9)
    ax2.plot(other_units[:, 0], other_units[:, 1], label=unilab,
             ls='--', lw=3, alpha=0.8, color='0.2')
    ax2.set_ylabel('Temperature')
    ax2.legend(loc='upper right', prop={'size': 'small'})
    ax3 = fig1.add_subplot(gs[1, 1])
    ax3.plot(ljunits[:, 0], ljunits[:, 5], label=ljlab,
             ls='-', lw=7, alpha=0.9)
    ax3.plot(other_units[:, 0], other_units[:, 5], label=unilab,
             ls='--', lw=3, alpha=0.8, color='0.2')
    ax3.set_xlabel('Step no.')
    ax3.set_ylabel('Pressure')
    ax3.legend(loc='lower right', prop={'size': 'small'})
    fig1.subplots_adjust(bottom=0.12, right=0.95, top=0.95,
                         left=0.08, wspace=0.2)
    fig1.savefig('compare.png')
    plt.show()
