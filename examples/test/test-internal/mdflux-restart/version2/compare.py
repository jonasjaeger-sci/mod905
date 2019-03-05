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
import tempfile
import colorama
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import gridspec
from pyretis.inout import print_to_screen
from pyretis.inout.formats.cross import CrossFile
plt.style.use('seaborn')


def files_overlap(file1, file2):
    """Check for overlap between two files.

    Here, the overlap is defined as the last line of file1 and
    the first line of file2.

    Parameters
    ----------
    file1 : string
        The file to read the last line from.
    file2 : string
        The file to read the first line from.

    """
    last_line = None
    with open(file1, 'r') as infile1:
        for lines in infile1:
            last_line = lines
    first_line = None
    with open(file2, 'r') as infile2:
        for lines in infile2:
            first_line = lines
            break
    return last_line == first_line


def compare_lists(list1, list2):
    """Compare contents of two lists."""
    if len(list1) == len(list2):
        for i, j in zip(list1, list2):
            if not i == j:
                return 1
        return 0
    return 1


def compare_lists_lists(list1, list2):
    """Compare contents of lists of lists."""
    if len(list1) == len(list2):
        for list1i, list2i in zip(list1, list2):
            if len(list1i) == len(list2i):
                for i, j in zip(list1i, list2i):
                    if not i == j:
                        return 1
            else:
                return 1
        return 0
    return 1


def compare_crossings(file11, file12, file2):
    """Compare the crossings found.

    Here, we expect that the contents of file11 and file12 together
    equals the contents of file2. In some cases, there can be an
    overlap between file11 and file12, and we check for that as well.

    Parameters
    ----------
    file11 : string
        The file containing the first part of the crossing data.
    file12 : string
        The file containing the second part of the crossing data.
    file2 : string
        The file containing the full crossing data.

    """
    data1 = []
    with tempfile.NamedTemporaryFile(prefix='cross_', suffix='.txt') as tmp:
        print_to_screen(
            'Joining: {} + {} -> {}'.format(file11, file12, tmp.name),
            level='info'
        )
        with open(tmp.name, 'w') as outfile:
            with open(file11, 'r') as infile:
                for lines in infile:
                    outfile.write(lines)
            skip = files_overlap(file11, file12)
            with open(file12, 'r') as infile:
                for i, lines in enumerate(infile):
                    if i == 0:
                        if not skip:
                            outfile.write(lines)
                    else:
                        outfile.write(lines)
        data1 = [i for i in CrossFile(tmp.name, 'r').load()]
    data2 = [i for i in CrossFile(file2, 'r').load()]
    if len(data1) != len(data2):
        print_to_screen('Different number of blocks in crossing data!',
                        level='error')
        return 1
    # Compare blocks
    for block1, block2 in zip(data1, data2):
        ret = compare_lists(block1['comment'], block2['comment'])
        if ret != 0:
            print_to_screen('Comment in crossing files do not match!',
                            level='error')
            return ret
        ret = compare_lists_lists(block1['data'], block2['data'])
        if ret != 0:
            print_to_screen('Crossing files do not match!', level='error')
            return ret
    print_to_screen('Crossing files match!', level='success')
    return 0


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
    names = [i for i in (file11, file12, file2)]
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
    ax3.set_ylabel('Order parameter.')
    ax3.plot([], [], label=r'$\lambda$', lw=0, alpha=0)
    ax3.plot([], [], label=r'$\dot{\lambda}}$', lw=0, alpha=0)
    axes = (ax1, ax2, ax3)
    return fig1, axes


def plot_in_ax(axes, infile, lab, fat=False, colors=None, style='-'):
    """Just do some plotting."""
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
    """Just do some plotting."""
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
        os.path.join('run-full', 'energy.txt'),
        'full',
        fat=True,
        style='-'
    )
    lines = plot_in_ax(
        axes,
        os.path.join('run-step1', 'energy.txt'),
        'restart-part1',
        style='--'
    )
    colors = [i.get_color() for i in lines]
    plot_in_ax(
        axes,
        os.path.join('run-step2', 'energy.txt'),
        'restart-part2',
        style=':', colors=colors
    )

    plot_in_ax_op(
        axes,
        os.path.join('run-full', 'order.txt'),
        'full',
        fat=True,
        style='-'
    )
    lines = plot_in_ax_op(
        axes,
        os.path.join('run-step1', 'order.txt'),
        'restart-part1',
        style='--'
    )
    colors = [i.get_color() for i in lines]
    plot_in_ax_op(
        axes,
        os.path.join('run-step2', 'order.txt'),
        'restart-part2',
        style=':', colors=colors
    )

    axes[0].legend(prop={'size': 'medium'}, ncol=4)
    axes[1].legend(prop={'size': 'medium'})
    axes[2].legend(prop={'size': 'medium'}, ncol=4)
    figure.subplots_adjust(bottom=0.12, right=0.95, top=0.95,
                           left=0.08, wspace=0.2)
    return figure


def main(args):
    """Run comparisons."""
    result = 0
    ret = compare_crossings(
        os.path.join('run-step1', 'cross.txt'),
        os.path.join('run-step2', 'cross.txt'),
        os.path.join('run-full', 'cross.txt'),
    )
    result += ret

    ret = compare_step_output(
        os.path.join('run-step1', 'energy.txt'),
        os.path.join('run-step2', 'energy.txt'),
        os.path.join('run-full', 'energy.txt'),
    )
    result += ret

    ret = compare_step_output(
        os.path.join('run-step1', 'order.txt'),
        os.path.join('run-step2', 'order.txt'),
        os.path.join('run-full', 'order.txt'),
    )
    result += ret
    if 'make_plot' in args:
        fig = make_plots()
        fig.savefig('compare.png')
        plt.show()
    if result != 0:
        print_to_screen('\nComparison failed!', level='error')
    else:
        print_to_screen('\nComparison was successful!', level='success')
    return result


if __name__ == '__main__':
    colorama.init(autoreset=True)
    sys.exit(main(sys.argv[1:]))
