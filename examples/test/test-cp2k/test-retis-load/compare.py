# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Simple script to compare the outcome of two simulations.

Here we compare a RETIS simulation of 50 cycles to known results.
The initial path is produced via a load sparse and the simulation
tries to genrate new valid paths.
"""
from math import isnan, isinf, isclose
import os
import sys
import colorama
from pyretis.inout import print_to_screen
from pyretis.inout.settings import parse_settings_file
from pyretis.core.pathensemble import generate_ensemble_name


RESULTS = 'results'


def print_message(msg):
    """Print a message to the screen with a text-underline."""
    print_to_screen('\n{}'.format(msg), level='message')
    print_to_screen('=' * len(msg), level='message')


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
            check = isclose(func(stuff1[i]), func(stuff2[i]),
                            rel_tol=rel_tol)
        if not check:
            return False
    return True


def compare_numbers(i, j, rel_tol):
    """Compare two numbers for close-enough-equality."""
    for special in (isnan, isinf):
        if special(i) or special(j):
            return special(i) and special(j)
    return isclose(i, j, rel_tol=rel_tol)


def compare_num_lines(line1, line2, rel_tol=1e-9):
    """Compare number for two lines."""
    if line1.startswith('#') and line2.startswith('#'):
        return True
    num1 = [float(i) for i in line1.split()]
    num2 = [float(i) for i in line2.split()]
    check = [compare_numbers(i, j, rel_tol) for i, j in zip(num1, num2)]
    return all(check)


def compare_data_ensemble_files(file1, file2, line_check=compare_num_lines):
    """Compare the contents of two result files, line-by-line."""
    with open(file1, 'r') as input1:
        with open(file2, 'r') as input2:
            for line1, line2 in zip(input1, input2):
                if not line_check(line1, line2, rel_tol=1e-5):
                    return False
    return True


def compare_files(settings):
    """Compare ouput files."""
    inter = settings['simulation']['interfaces']
    files = ('pathensemble.txt', 'order.txt', 'energy.txt')
    checkers = (compare_path_lines, compare_num_lines, compare_num_lines)
    for i in range(len(inter)):
        ensemble_dir = generate_ensemble_name(i)
        msg = 'Comparing for ensemble: {}'.format(ensemble_dir)
        print_message(msg)
        for file_name, check in zip(files, checkers):
            print_to_screen('* Comparing {} files...'.format(file_name))
            result_old = os.path.join(RESULTS, ensemble_dir, file_name)
            result_new = os.path.join(ensemble_dir, file_name)
            result = compare_data_ensemble_files(result_new, result_old,
                                                 line_check=check)
            if not result:
                print_to_screen('\t-> *Files differ!*', level='error')
                return False
            print_to_screen('\t-> Files are equal!', level='success')
    print_to_screen('All files are equal!', level='success')
    return True


def main():
    """Run the comparison."""
    settings = parse_settings_file('retis.rst')
    print_message('Comparing files for the load example.')
    compare_ok = compare_files(settings)
    if not compare_ok:
        sys.exit(1)


if __name__ == '__main__':
    colorama.init(autoreset=True)
    main()
