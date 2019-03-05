# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Simple script to compare the outcome of two simulations."""
import math
import os
import sys
import tarfile
import colorama
from pyretis.inout import print_to_screen
from pyretis.inout.settings import parse_settings_file
from pyretis.core.pathensemble import generate_ensemble_name


RUN_FULL = 'run-50'
RUN_LOAD = 'run-25'


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


def load_file(filename):
    """Read an entire file into memory."""
    lines = None
    with open(filename, 'r') as infile:
        lines = [line for line in infile]
    return lines


def compare_files(file1, file2, compare_func):
    """Compare two files."""
    lines1 = load_file(file1)
    lines2 = load_file(file2)
    if not len(lines1) == len(lines2):
        print_to_screen('\t-> Files have different size!', level='error')
        return False
    for i, j in zip(lines1, lines2):
        similar = i == j
        if not similar:
            if not compare_func(i, j, rel_tol=1e-7):
                print_to_screen('\t-> Files are NOT equal!', level='error')
                return False
    print_to_screen('\t-> Files are equal!', level='success')
    return True


def compare_tar_files(file1, file2):
    """Compare the files in two tar archives.

    Parameters
    ----------
    file1 : string
        The path to the first tar archive.
    file2 : string
        The path to the second tar archive.

    Returns
    -------
    out : boolean
        True if the contents of the archive are identical, False
        otherwise.

    """
    contents1 = get_tar_contents(file1)
    filenames1 = [i.name for i in contents1]
    contents2 = get_tar_contents(file2)
    filenames2 = [i.name for i in contents2]
    # Check for same number of files:
    if not len(filenames1) == len(filenames2):
        return False
    # Check for same name of files:
    for i in filenames1:
        if i not in filenames2:
            return False
    return True


def get_tar_contents(tar_file):
    """Return files found in a tar archive."""
    files = []
    with tarfile.open(tar_file, 'r') as tar:
        files = [i for i in tar.getmembers() if i.isfile()]
    return files


def compare_ensemble(ensemble):
    """Run the comparison for an ensemble."""
    print_to_screen('Comparing for "{}"'.format(ensemble), level='info')
    for filei in ('energy.txt', 'order.txt', 'pathensemble.txt'):
        print_to_screen('* Comparing {} files...'.format(filei))
        file1 = os.path.join(RUN_FULL, ensemble, filei)
        file2 = os.path.join(RUN_LOAD, ensemble, filei)
        if filei == 'pathensemble.txt':
            if not compare_files(file1, file2, compare_path_lines):
                return False
        else:
            if not compare_files(file1, file2, compare_num_lines):
                return False
    for filei in ('traj-acc.tar', 'traj-rej.tar'):
        print_to_screen('* Comparing {} files...'.format(filei))
        file1 = os.path.join(RUN_FULL, ensemble, 'traj', filei)
        file2 = os.path.join(RUN_LOAD, ensemble, 'traj', filei)
        if not compare_tar_files(file1, file2):
            return False
        print_to_screen('\t-> Archives contain same files.',
                        level='success')
    return True


def main():
    """Run all comparisons."""
    settings = parse_settings_file(os.path.join(RUN_FULL, 'retis.rst'))
    inter = settings['simulation']['interfaces']
    for i in range(len(inter)):
        ens = generate_ensemble_name(i)
        if not compare_ensemble(ens):
            return 1
    return 0


if __name__ == '__main__':
    colorama.init(autoreset=True)
    sys.exit(main())
