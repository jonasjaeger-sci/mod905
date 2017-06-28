# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Simple script to compare outcome of two simulations.

Here we compare a full simulation with one where we have stopped
and restarted after 100 steps.
"""
# pylint: disable=C0103
import itertools
import os
import colorama
import numpy as np
from pyretis.inout.common import print_to_screen
from pyretis.inout.writers import get_writer
# for plotting:
from matplotlib import pyplot as plt
from matplotlib import gridspec as gridspec
plt.style.use('seaborn')


def compare_crossings():
    """Compare the crossings found."""
    cross11 = os.path.join('run-step1', 'cross.txt')
    cross12 = os.path.join('run-step2', 'cross.txt')
    cross2 = os.path.join('run-full', 'cross.txt')
    file11 = get_writer('cross').load(cross11)
    file12 = get_writer('cross').load(cross12)
    file1 = itertools.chain(file11, file12)
    file2 = get_writer('cross').load(cross2)

    all_ok = True
    for block1, block2 in zip(file1, file2):
        for data1, data2 in zip(block1['data'], block2['data']):
            isok = [i == j for i, j in zip(data1, data2)]
            if not isok:
                print_to_screen('Crossing files do not match!', level='error')
                all_ok = False
                break
    if all_ok:
        print_to_screen('Crossing files match!', level='success')


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
    ax3.set_ylabel('Order parameter.')
    ax3.plot([], [], label=r'$\lambda$', lw=0, alpha=0)
    ax3.plot([], [], label=r'$\dot{\lambda}}$', lw=0, alpha=0)
    axes = (ax1, ax2, ax3)
    return fig1, axes


def plot_in_ax(axes, infile, lab, fat=False, colors=None, style='-'):
    """Just do some plotting"""
    ax1, ax2, _ = axes
    data = np.loadtxt(infile)
    if fat:
        width = 7
    else:
        width = 3
    lines = []
    for i, idx in enumerate((1, 2, 3)):
        if colors is None:
            line, = ax1.plot(data[:, 0], data[:, idx], label=lab,
                             ls=style, lw=width, alpha=0.8)
        else:
            line, = ax1.plot(data[:, 0], data[:, idx], label=lab,
                             ls=style, lw=width, alpha=0.8, color=colors[i])
        lines.append(line)
    ax2.plot(data[:, 0], data[:, 4], label=lab, ls=style, lw=width, alpha=0.9)
    return lines


def plot_in_ax_op(axes, infile, lab, fat=False, colors=None, style='-'):
    """Just do some plotting"""
    _, _, ax3 = axes
    data = np.loadtxt(infile)
    if fat:
        width = 7
    else:
        width = 3
    lines = []
    for i, idx in enumerate((1, 2)):
        if colors is None:
            line, = ax3.plot(data[:, 0], data[:, idx], label=lab,
                             ls=style, lw=width, alpha=0.8)
        else:
            line, = ax3.plot(data[:, 0], data[:, idx], label=lab,
                             ls=style, lw=width, alpha=0.8, color=colors[i])
        lines.append(line)
    return lines


def make_plots():
    """Just plot some energies for comparison."""
    figure, axes = make_fig()

    plot_in_ax(
        axes,
        'run-full/energy.txt',
        'full',
        fat=True,
        style='-'
    )
    lines = plot_in_ax(
        axes,
        'run-step1/energy.txt',
        'restart-part1',
        style='--'
    )
    colors = [i.get_color() for i in lines]
    plot_in_ax(
        axes,
        'run-step2/energy.txt',
        'restart-part2',
        style=':', colors=colors
    )

    plot_in_ax_op(
        axes,
        'run-full/order.txt',
        'full',
        fat=True,
        style='-'
    )
    lines = plot_in_ax_op(
        axes,
        'run-step1/order.txt',
        'restart-part1',
        style='--'
    )
    colors = [i.get_color() for i in lines]
    plot_in_ax_op(
        axes,
        'run-step2/order.txt',
        'restart-part2',
        style=':', colors=colors
    )

    axes[0].legend(prop={'size': 'medium'}, ncol=4)
    axes[1].legend(prop={'size': 'medium'})
    axes[2].legend(prop={'size': 'medium'}, ncol=4)
    figure.subplots_adjust(bottom=0.12, right=0.95, top=0.95,
                           left=0.08, wspace=0.2)
    return figure


if __name__ == '__main__':
    colorama.init(autoreset=True)
    compare_crossings()
    fig = make_plots()
    fig.savefig('compare.png')
    plt.show()
