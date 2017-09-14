# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Simple script to compare outcome of two simulations.

Here we compare a full simulation with one where we have stopped
and restarted after 100 steps.
"""
# pylint: disable=C0103
import os
import colorama
from pyretis.inout.common import print_to_screen
from pyretis.inout.settings import parse_settings_file
from pyretis.core.pathensemble import PATH_DIR_FMT

RUN_FULL = 'run-100'
RUN1 = 'run-20'
RUN2 = 'run-load'


def compare_files(file1, file2, file3):
    """Compare three files.

    Here, we are checking if file1 + file2 is the same as file3.
    """
    file1h = open(file1, 'r')
    file3h = open(file3, 'r')
    print(file1)
    print(file2)
    print(file3)
    # start comparing file1 and file3
    similar = True
    for i, (lines1, lines3) in enumerate(zip(file1h, file3h)):
        similar = lines1 == lines3
        if not similar:
            print_to_screen('\t-> Files are NOT equal!', level='error')
            return
    # ok made it this far. Next we skip the first trajectory in file2.
    # this one is already read from file1.
    last_line = None
    with open(file2, 'r') as file2h:
        for i, lines2 in enumerate(file2h):
            if lines2.find('# Cycle') != -1 and i > 0:
                last_line = i
                break
    file2h = open(file2, 'r')
    for i, lines2 in enumerate(file2h):
        if i == last_line - 1:
            break
    for lines2, lines3 in zip(file2h, file3h):
        similar = lines2 == lines3
        if not similar:
            print_to_screen('\t-> Files are NOT equal!', level='error')
            return
    # ok made it this far, the files are equal!
    print_to_screen('\t-> Files are equal!', level='success')
    return


def compare_ensemble(ensemble):
    """Run the comparison for an ensemble"""
    print_to_screen('Comparing for "{}"'.format(ensemble), level='info')
    for files in ('traj.txt', 'energy.txt', 'order.txt'):
        print_to_screen('* Comparing {} files...'.format(files))
        file1 = os.path.join(RUN1, ensemble, files)
        file2 = os.path.join(RUN2, ensemble, files)
        file3 = os.path.join(RUN_FULL, ensemble, files)
        compare_files(file1, file2, file3)


if __name__ == '__main__':
    colorama.init(autoreset=True)
    sett_file = os.path.join(RUN_FULL, 'retis.rst')
    settings = parse_settings_file(sett_file)
    inter = settings['simulation']['interfaces']
    for inti in range(len(inter)):
        ens = PATH_DIR_FMT.format(inti)
        compare_ensemble(ens)
