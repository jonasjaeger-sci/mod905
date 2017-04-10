# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Simple script to compare outcome of two simulations.

Here we compare a full simulation with one where we have stopped
and restarted after 100 steps.
"""
# pylint: disable=C0103
import filecmp
import os
import itertools
import colorama
from pyretis.inout.common import print_to_screen
from pyretis.inout.settings import parse_settings_file
from pyretis.core.pathensemble import PATH_DIR_FMT

RUN_FULL = 'run-50'
RUN_RESTART = 'run-25'


def compare_files(file1, file2):
    """Compare two files."""
    similar = filecmp.cmp(file1, file2)
    if similar:
        print_to_screen('\t-> Files are equal!', level='success')
    else:
        print_to_screen('\t-> Files are NOT equal!', level='error')


def comment(line):
    return line.startswith('#')
    

def compare_files_lines(file1, file2):
    """Compare line by line but skip comments."""
    with open(file1, 'r') as infile1, open(file2, 'r') as infile2:
        lines1 = itertools.filterfalse(comment, infile1)
        lines2 = itertools.filterfalse(comment, infile2)
        similar = all([i == j for i, j in zip(lines1, lines2)])
        if similar:
            print_to_screen('\t-> Path ensemble files contain same data!',
                            level='success')
        else:
            print_to_screen('\t-> Path ensemble files differ!',
                            level='error')


def compare_ensemble(ensemble):
    """Run the comparison for an ensemble"""
    print_to_screen('Comparing for "{}"'.format(ensemble), level='info')
    traj1 = os.path.join(RUN_FULL, ensemble, 'traj.txt')
    traj2 = os.path.join(RUN_RESTART, ensemble, 'traj.txt')
    print_to_screen('* Comparing traj.txt files...')
    compare_files(traj1, traj2)

    print_to_screen('* Comparing traj.txt files...')
    ener1 = os.path.join(RUN_FULL, ensemble, 'energy.txt')
    ener2 = os.path.join(RUN_RESTART, ensemble, 'energy.txt')
    compare_files(ener1, ener2)

    print_to_screen('* Comparing order.txt files...')
    order1 = os.path.join(RUN_FULL, ensemble, 'order.txt')
    order2 = os.path.join(RUN_RESTART, ensemble, 'order.txt')
    compare_files(order1, order2)
    
    print_to_screen('* Comparing pathensemble.txt files...')
    pathe1 = os.path.join(RUN_FULL, ensemble, 'pathensemble.txt')
    pathe2 = os.path.join(RUN_RESTART, ensemble, 'pathensemble.txt')
    compare_files_lines(pathe1, pathe2)


if __name__ == '__main__':
    colorama.init(autoreset=True)
    sett_file = os.path.join(RUN_FULL, 'retis.rst')
    settings = parse_settings_file(sett_file)
    inter = settings['simulation']['interfaces']
    for i in range(len(inter)):
        ens = PATH_DIR_FMT.format(i)
        compare_ensemble(ens)
