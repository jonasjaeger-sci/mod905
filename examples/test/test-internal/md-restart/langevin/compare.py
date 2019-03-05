# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Simple script to compare the outcome of two simulations.

Here we compare a full simulation with one where we have stopped
and restarted after 100 steps.
"""
import itertools
import os
import sys
import colorama
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import gridspec
from pyretis.inout import print_to_screen
from pyretis.inout.formats.snapshot import SnapshotFile
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
    """Compare two trajectories from PyRETIS.

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
    tol : float
        A tolerance for comparing numbers.

    Returns
    -------
    None, just prints out the result of the comparison.

    """
    print_to_screen('Comparing trajectories', level='info')
    print_to_screen('Checking mean squared error...')
    file11 = SnapshotFile(traj11, 'r').load()
    file12 = SnapshotFile(traj12, 'r').load()
    next(file12)  # skip the first config
    file1 = itertools.chain(file11, file12)
    file2 = SnapshotFile(traj2, 'r').load()
    error, error_v = [], []
    for snap1, snap2 in zip(file1, file2):
        pose, vele = snapshot_difference(snap1, snap2)
        error.append(pose)
        error_v.append(vele)
    val1 = print_error_assessment(np.mean(error), 'positions', tol)
    val2 = print_error_assessment(np.mean(error_v), 'velocities', tol)
    return val1 + val2


def compare_step_output(file11, file12, file2):
    """Compare step-wise output from PyRETIS.

    Here, we assume that the output in file2 is obtained
    by concatenating file11 and file12. file11 and file12
    should have one line in common: the final line in file11
    should be identical to the first line in file12.

    Parameters
    ----------
    file11 : string
        A file to open, part 1.
    file12 : string
        A file to open, part 2.
    file2 : string
        A file to open, we will check if this one is
        equal (line-by-line) to file11+file12.

    Returns
    -------
    None, just prints out the result of the comparison.

    """
    print_to_screen('\nComparing files:', level='info')
    names = [os.path.split(i)[1] for i in (file11, file12, file2)]
    print_to_screen('{} + {} == {}?'.format(*names))
    file11_h = open(file11, 'r')
    file12_h = open(file12, 'r')
    file2_h = open(file2, 'r')
    first_line = next(file12_h)
    error = False
    for i, (data1, data2) in enumerate(zip(itertools.chain(file11_h, file12_h),
                                           file2_h)):
        if not data1 == data2:
            print_to_screen('Error for line no: {}'.format(i), level='error')
            print_to_screen('Lines were:', level='error')
            print_to_screen(data1.strip(), level='error')
            print_to_screen(data2.strip(), level='error')
            error = True
            break
    file11_h.close()
    file12_h.close()
    file2_h.close()
    if not error:
        print_to_screen('Joined files contain same data!')
        last_line, len11 = read_last_line(file11)
        if last_line == first_line:
            print_to_screen('First in {} = last in {}'.format(*names[:2]))
            _, len12 = read_last_line(file12)
            _, len2 = read_last_line(file2)
            if len11 + len12 == len2 + 1:
                print_to_screen('Number of lines are correct.')
                print_to_screen('Files are equal!', level='success')
                return 0
            print_to_screen('Number of lines are incorrect', level='error')
            return 1
        print_to_screen('First in {} != last in {}'.format(*names[:2]),
                        level='error')
        return 1
    return 1


def read_last_line(filename):
    """Read the last line from a file + count number of lines in the file."""
    i = 0
    last_line = None
    with open(filename, 'r') as infile:
        for lines in infile:
            last_line = lines
            i += 1
    return last_line, i


def print_error_assessment(error, what, tol):
    """Print out some error info."""
    if abs(error) < tol:
        lev = 'success'
        val = 0
    else:
        lev = 'error'
        val = 1
    print_to_screen('Mean error - {}: {}'.format(what, error),
                    level=lev)
    return val


def make_fig():
    """Plot for comparison."""
    fig1 = plt.figure(figsize=(12, 6))
    grid = gridspec.GridSpec(2, 2)
    ax1 = fig1.add_subplot(grid[:, 0])
    ax1.plot([], [], label='Potential', lw=0, alpha=0)
    ax1.plot([], [], label='Kinetic', lw=0, alpha=0)
    ax1.plot([], [], label='Total', lw=0, alpha=0)
    ax1.set_xlabel('Step no.')
    ax1.set_ylabel('Energy per particle')
    ax2 = fig1.add_subplot(grid[0, 1])
    ax2.set_ylabel('Temperature')
    ax3 = fig1.add_subplot(grid[1, 1])
    ax3.set_xlabel('Step no.')
    ax3.set_ylabel('Pressure')
    axes = (ax1, ax2, ax3)
    return fig1, axes


def plot_in_ax(axes, infile, lab, fat=False, colors=None, style='-'):
    """Just do some plotting."""
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
        os.path.join('run-full', 'md-full-thermo.txt'),
        'full',
        fat=True,
        style='-'
    )
    lines = plot_in_ax(
        axes,
        os.path.join('run-100', 'md-100-thermo.txt'),
        'restart-part1',
        style='--'
    )
    colors = [i.get_color() for i in lines]
    plot_in_ax(
        axes,
        os.path.join('run-100-1000', 'md-100-1000-thermo.txt'),
        'restart-part2',
        style=':', colors=colors)
    axes[0].legend(prop={'size': 'medium'}, ncol=4)
    axes[1].legend(prop={'size': 'medium'})
    axes[2].legend(prop={'size': 'medium'})
    figure.subplots_adjust(bottom=0.12, right=0.95, top=0.95,
                           left=0.08, wspace=0.2)
    return figure


def main(args):
    """Run the comparison."""
    val1 = compare_traj(
        os.path.join('run-100', 'md-100-traj.xyz'),
        os.path.join('run-100-1000', 'md-100-1000-traj.xyz'),
        os.path.join('run-full', 'md-full-traj.xyz'),
        tol=1e-12
    )
    val2 = compare_step_output(
        os.path.join('run-100', 'md-100-thermo.txt'),
        os.path.join('run-100-1000', 'md-100-1000-thermo.txt'),
        os.path.join('run-full', 'md-full-thermo.txt'),
    )
    val3 = compare_step_output(
        os.path.join('run-100', 'md-100-energy.txt'),
        os.path.join('run-100-1000', 'md-100-1000-energy.txt'),
        os.path.join('run-full', 'md-full-energy.txt'),
    )
    if 'make_plot' in args:
        fig = make_plots()
        fig.savefig('compare.png')
        plt.show()
    return val1 + val2 + val3


if __name__ == '__main__':
    colorama.init(autoreset=True)
    sys.exit(main(sys.argv[1:]))
