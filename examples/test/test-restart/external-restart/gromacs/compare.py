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
import colorama
import numpy as np
from pyretis.inout.common import print_to_screen
from pyretis.inout.settings import parse_settings_file
from pyretis.core.pathensemble import PATH_DIR_FMT


def compare_files(file1, file2):
    """Compare two files."""
    similar = filecmp.cmp(file1, file2)
    if similar:
        print_to_screen('\t-> Files are equal!', level='success')
    else:
        print_to_screen('\t-> Files are NOT equal!', level='error')


def compare_ensemble(ensemble):
    """Run the comparison for an ensemble"""
    print_to_screen('Comparing for "{}"'.format(ensemble), level='info')
    traj1 = os.path.join('run-25', ensemble, 'traj.txt')
    traj2 = os.path.join('run-restart', ensemble, 'traj.txt')
    print_to_screen('* Comparing traj.txt files...')
    compare_files(traj1, traj2)

    print_to_screen('* Comparing traj.txt files...')
    ener1 = os.path.join('run-25', ensemble, 'energy.txt')
    ener2 = os.path.join('run-restart', ensemble, 'energy.txt')
    compare_files(ener1, ener2)

    print_to_screen('* Comparing order.txt files...')
    order1 = os.path.join('run-25', ensemble, 'order.txt')
    order2 = os.path.join('run-restart', ensemble, 'order.txt')
    compare_files(order1, order2)


if __name__ == '__main__':
    colorama.init(autoreset=True)
    settings = parse_settings_file('run-25/retis.rst')
    inter = settings['simulation']['interfaces']
    for i in range(len(inter)):
        ens = PATH_DIR_FMT.format(i)
        compare_ensemble(ens)
