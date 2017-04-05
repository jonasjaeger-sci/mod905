# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Simple script to compare outcome of two simulations.

Here we compare a full simulation with one where we have stopped
and restarted after 100 steps.
"""
# pylint: disable=C0103
import itertools
import colorama
import numpy as np
from pyretis.inout.common import print_to_screen
from pyretis.inout.writers import get_writer
# for plotting:
from matplotlib import pyplot as plt
from matplotlib import gridspec as gridspec
plt.style.use('seaborn')


def snapshot_difference(snap1, snap2):
    """Calculate difference between two snapshots."""
    xyz1 = np.column_stack((snap1['x'], snap1['y'], snap1['z']))
    xyz2 = np.column_stack((snap2['x'], snap2['y'], snap2['z']))
    diff = (xyz1 - xyz2)**2
    dsum = np.einsum('ij,ij -> i', diff, diff)
    vel1 = np.column_stack((snap1['vx'], snap1['vy'], snap1['vz']))
    vel2 = np.column_stack((snap2['vx'], snap2['vy'], snap2['vz']))
    diffv = (vel1 - vel2)**2
    dsumv = np.einsum('ij,ij -> i', diffv, diffv)
    return sum(dsum), sum(dsumv)


def compare_traj(traj11, traj12, traj2, tol=1e-12):
    """A comparison of two trajectories from PyRETIS

    Here we calculate the mean squared error for the two
    trajectories.

    Parameters
    ----------
    traj11 : string
        A trajectory to open, part 1.
    traj12 : string
        A trajectory to open, part 2.
    traj2 : string
        A trajectory file to open.

    Returns
    -------
    None, just prints out the result of the comparison.
    """
    print_to_screen('Comparing trajectories', level='info')
    print('Checking mean squared error...')
    file11 = get_writer('trajtxt', {'write_vel': True}).load(traj11)
    file12 = get_writer('trajtxt', {'write_vel': True}).load(traj12)
    next(file12)  # skip first item
    file1 = itertools.chain(file11, file12)
    file2 = get_writer('trajtxt', {'write_vel': True}).load(traj2)
    error, error_v = 0.0, 0.0
    nsnap = 0
    for snap1, snap2 in zip(file1, file2):
        pose, vele = snapshot_difference(snap1, snap2)
        error += pose
        error_v += vele
        nsnap += 1
    error /= float(nsnap)
    print_what_you_think_about_the_error(error, 'positions', tol)
    print_what_you_think_about_the_error(error_v, 'velocities', tol)


def print_what_you_think_about_the_error(error, what, tol):
    """Print out some error info."""
    if abs(error) < tol:
        lev = 'success'
    else:
        lev = 'error'
    print_to_screen('Mean error - {}: {}'.format(what, error),
                    level=lev)


def make_fig():
    """Plot for comparison."""
    fig1 = plt.figure(figsize=(12, 6))
    gs = gridspec.GridSpec(2, 2)
    ax1 = fig1.add_subplot(gs[:, 0])
    ax1.plot([], [], label='Potential', lw=0, alpha=0)
    ax1.plot([], [], label='Kinetic', lw=0, alpha=0)
    ax1.plot([], [], label='Total', lw=0, alpha=0)
    ax1.set_xlabel('Step no.')
    ax1.set_ylabel('Energy per particle')
    ax2 = fig1.add_subplot(gs[0, 1])
    ax2.set_ylabel('Temperature')
    ax3 = fig1.add_subplot(gs[1, 1])
    ax3.set_xlabel('Step no.')
    ax3.set_ylabel('Pressure')
    axes = (ax1, ax2, ax3)
    return fig1, axes


def plot_in_ax(axes, infile, lab, fat=False, colors=None, style='-'):
    """Just do some plotting"""
    ax1, ax2, ax3 = axes
    data = np.loadtxt(infile)
    if fat:
        width = 7
    else:
        width = 3
    lines = []
    for i, idx in enumerate((2, 3, 4)):
        if colors is None:
            line, = ax1.plot(data[:, 0], data[:, idx], label=lab,
                             ls=style, lw=width, alpha=0.8)
        else:
            line, = ax1.plot(data[:, 0], data[:, idx], label=lab,
                             ls=style, lw=width, alpha=0.8, color=colors[i])
        lines.append(line)
    ax2.plot(data[:, 0], data[:, 1], label=lab, ls=style, lw=width, alpha=0.9)
    ax3.plot(data[:, 0], data[:, 5], label=lab, ls=style, lw=width, alpha=0.9)
    return lines


def make_plots():
    """Just plot some energies for comparison."""
    figure, axes = make_fig()
    plot_in_ax(
        axes,
        'run-full/md-full-thermo.txt',
        'full',
        fat=True,
        style='-'
    )
    lines = plot_in_ax(
        axes,
        'run-100/md-100-thermo.txt',
        'restart-part1',
        style='--'
    )
    colors = [i.get_color() for i in lines]
    plot_in_ax(
        axes,
        'run-100-1000/md-100-1000-thermo.txt',
        'restart-part2',
        style=':', colors=colors)
    axes[0].legend(prop={'size': 'medium'}, ncol=4)
    axes[1].legend(prop={'size': 'medium'})
    axes[2].legend(prop={'size': 'medium'})
    figure.subplots_adjust(bottom=0.12, right=0.95, top=0.95,
                           left=0.08, wspace=0.2)
    return figure


if __name__ == '__main__':
    colorama.init(autoreset=True)
    compare_traj(
        'run-100/md-100-traj.txt',
        'run-100-1000/md-100-1000-traj.txt',
        'run-full/md-full-traj.txt',
        tol=1e-12
    )
    fig = make_plots()
    fig.savefig('compare.png')
    plt.show()
