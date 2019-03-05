# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Simple script to compare the outcome of two simulations.

Here we compare a full simulation with one where we have stopped
and restarted after 100 steps.
"""
import os
import math
import colorama
from pyretis.inout import print_to_screen
from pyretis.inout.settings import parse_settings_file
from pyretis.core.pathensemble import generate_ensemble_name


RUN_FULL = 'run-100'
RUN1 = 'run-20'
RUN2 = 'run-load'


def compare_path_lines(line1, line2, rel_tol=1e-5):
    """Compare two path ensemble lines."""
    if line1.startswith('#') and line2.startswith('#'):
        return True
    stuff1 = line1.split()
    stuff2 = line2.split()
    idx = {
        0: int, 3: str, 4: str, 5: str, 7: str, 8: str, 9: float,
        10: float, 11: int, 12: int, 13: float, 14: int, 15: int
    }
    for i, func in idx.items():
        if func == str:
            check = func(stuff1[i]) == func(stuff2[i])
        else:
            check = math.isclose(func(stuff1[i]), func(stuff2[i]),
                                 rel_tol=rel_tol)
        if not check:
            return False
    return True


def compare_num_lines(line1, line2, rel_tol=1e-9):
    """Compare number for two lines."""
    num1 = [float(i) for i in line1.split()]
    num2 = [float(i) for i in line2.split()]
    check = [math.isclose(i, j, rel_tol=rel_tol) for i, j in zip(num1, num2)]
    return all(check)


def compare_files(file1, file2, file3, rel_tol=1e-9):
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
            if not compare_num_lines(lines1, lines3, rel_tol=rel_tol):
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
            if not compare_num_lines(lines2, lines3, rel_tol=rel_tol):
                print_to_screen('\t-> Files are NOT equal!', level='error')
                return
    # ok made it this far, the files are equal!
    print_to_screen('\t-> Files are equal!', level='success')
    return


def compare_pathensemble_files(file1, file2, file3, rel_tol=1e-9):
    """Compare three files.

    Here, we are checking if file1 + file2 is the same as file3, for
    path ensemble files.

    """
    file1h = open(file1, 'r')
    file2h = open(file2, 'r')
    file3h = open(file3, 'r')
    print(file1)
    print(file2)
    print(file3)
    # start comparing file1 and file3
    for lines1, lines3 in zip(file1h, file3h):
        if not compare_path_lines(lines1, lines3, rel_tol=rel_tol):
            print_to_screen('\t-> Files are NOT equal!', level='error')
            return
    next(file2h)
    for lines2, lines3 in zip(file2h, file3h):
        if not compare_path_lines(lines2, lines3, rel_tol=rel_tol):
            print_to_screen('\t-> Files are NOT equal!', level='error')
            return
    print_to_screen('\t-> Files are equal!', level='success')
    return


def compare_ensemble(ensemble):
    """Run the comparison for an ensemble."""
    print_to_screen('Comparing for "{}"'.format(ensemble), level='info')
    for files in ('energy.txt', 'order.txt'):
        print_to_screen('* Comparing {} files...'.format(files))
        file1 = os.path.join(RUN1, ensemble, files)
        file2 = os.path.join(RUN2, ensemble, files)
        file3 = os.path.join(RUN_FULL, ensemble, files)
        compare_files(file1, file2, file3, rel_tol=1e-4)
    print_to_screen('* Comparing {} files...'.format('pathensemble.txt'))
    file1 = os.path.join(RUN1, ensemble, 'pathensemble.txt')
    file2 = os.path.join(RUN2, ensemble, 'pathensemble.txt')
    file3 = os.path.join(RUN_FULL, ensemble, 'pathensemble.txt')
    compare_pathensemble_files(file1, file2, file3, rel_tol=1e-4)


def main():
    """Run full comparison."""
    settings = parse_settings_file(os.path.join(RUN_FULL, 'retis.rst'))
    inter = settings['simulation']['interfaces']
    for inti in range(len(inter)):
        ens = generate_ensemble_name(inti)
        compare_ensemble(ens)


if __name__ == '__main__':
    colorama.init(autoreset=True)
    main()
