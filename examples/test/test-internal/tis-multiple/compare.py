# -*- coding: utf-8 -*-
# Copyright (c) 2026, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Simple script to compare the outcome of two simulations.
Here we compare a TIS simulation of 50 steps to known results.
"""
import tempfile
import fileinput
import os
import sys
import colorama
from pyretis.inout import print_to_screen
from pyretis.inout.settings import parse_settings_file
from pyretis.core.pathensemble import generate_ensemble_name
from pyretis.setup.createsimulation import create_ensembles


RESULTS = 'results'


def compare_files(fpath1, fpath2):
    """Compare two files."""
    print_to_screen('Comparing: {} {}'.format(fpath1, fpath2))
    similar = True
    with open(fpath1, 'r') as file1, open(fpath2, 'r') as file2:
        for i, (linef1, linef2) in enumerate(zip(file1, file2)):
            linef1 = linef1.rstrip('\r\n')
            linef2 = linef2.rstrip('\r\n')
            if linef1 != linef2:
                print('----------------------')
                print(f'Line number: {i} ')
                print(linef1.strip())
                print(linef2.strip())
                similar = False

        if similar:
            similar = next(file1, None) is None and next(file2, None) is None

    if similar:
        print_to_screen('\t-> Files are equal!', level='success')
    else:
        print_to_screen('\t-> Files are NOT equal!', level='error')
        sys.exit(1)
    return 0


def check_path_file(ens):
    """Check that the accepted paths seem ok.

    Parameters
    ----------
    ens : object like :py:class:`.PathEnsemble`
        The path ensemble to plot for.

    Returns
    -------
    paths : dict
        Information about the paths in the ensemble.

    """
    print_to_screen('\nReading for {}'.format(ens.ensemble_name))
    filename = os.path.join(generate_ensemble_name(ens.ensemble_number),
                            'pathensemble.txt')
    print_to_screen('Reading: {}'.format(filename))
    start = ens.start_condition
    end = ('R') if ens.ensemble_number == 0 else ('R', 'L')
    something_weird = False
    with open(filename, 'r') as inputfile:
        for lines in inputfile:
            if lines.startswith('#'):
                continue
            splitline = lines.strip().split()
            status = splitline[7]
            if status != 'ACC':
                continue
            step = int(splitline[0])
            left = splitline[3]
            middle = splitline[4]
            right = splitline[5]
            length = int(splitline[6])
            mino = float(splitline[9])
            maxo = float(splitline[10])

            if length < 3:
                print_to_screen('Suspicious length for path {}'.format(step),
                                level='error')
                something_weird = True
            if start != left:
                print_to_screen(
                    'Inconsistent start: {} != {} (step {})'.format(start,
                                                                    left,
                                                                    step),
                    level='error')
                something_weird = True
            if middle != 'M':
                print_to_screen(
                    'Middle differ: M != {} (step {})'.format(middle,
                                                              step),
                    level='error')
                something_weird = True
            if right not in end:
                print_to_screen(
                    'Inconsistent end: {} (step {})'.format(right, step),
                    level='error')
                something_weird = True
            cross = [mino < interpos < maxo for interpos in ens.interfaces]
            if ens.ensemble_number == 0:
                idx1, idx2 = 1, 2
            else:
                idx1, idx2 = 0, 1
            if not cross[idx1] or not cross[idx2]:
                something_weird = True
                print_to_screen(
                    'Inconsistent crossings: {} {} (step {})'.format(
                        cross[idx1],
                        cross[idx2],
                        step
                    ),
                    level='error'
                )
    if not something_weird:
        print_to_screen('Accepted paths are OK!', level='success')
    else:
        sys.exit(1)
    return 0


def run_check_path_file(settings):
    """Check paths using given simulation settings."""
    ensembles = create_ensembles(settings)
    retval = [check_path_file(ens['path_ensemble']) for ens in ensembles]
    return sum(retval)


def compare_path_files(settings):
    """Compare pathensemble.txt files."""
    inter = settings['simulation']['interfaces']
    retval = 0
    for i in range(1, len(inter)):
        ens_dir = generate_ensemble_name(i)
        fil1 = os.path.join(ens_dir, 'pathensemble.txt')
        fil2 = os.path.join(RESULTS, ens_dir, 'pathensemble.txt')
        ret = compare_files(fil1, fil2)
        retval += ret
    return retval


def compare_rst_files(settings):
    """Compare tis.rst files."""
    inter = settings['simulation']['interfaces']
    retval = 0
    for i in range(1, len(inter)):
        fil1 = os.path.join(('tis-00{}.rst').format(i))
        for line in fileinput.input(fil1, inplace=1):
            if 'exe_path' in line.split():
                line = ''
            sys.stdout.write(line)
        fil2 = os.path.join(RESULTS, ('tis-00{}.rst').format(i))
        for line in fileinput.input(fil2, inplace=1):
            if 'exe_path' in line.split():
                line = ''
            sys.stdout.write(line)
        ret = compare_files(fil1, fil2)
        retval += ret
    return retval


def compare_prob_files():
    """Compare probabilities files."""
    names = ['tis-multiple_report.html',
             'tis-multiple_report.rst',
             'tis-multiple_report.tex']
    # Skip the lines that contain the time when the command was called
    skips = [lambda i: i in [701, 702],
             lambda i: i in [4, 5],
             lambda i: i in [24, 25]]
    retval = 0
    for name, skip in zip(names, skips):
        fil1 = os.path.join('report', name)
        fil2 = os.path.join(RESULTS, name)
        basename, ext = os.path.splitext(name)
        basename += '_'
        with tempfile.NamedTemporaryFile(prefix=basename, suffix=ext) as tmp:
            with open(tmp.name, 'wb') as outfile:
                with open(fil1, 'rb') as infile:  # This one fail?
                    for i, line in enumerate(infile):
                        if not skip(i):
                            outfile.write(line)
            ret = compare_files(tmp.name, fil2)
            retval += ret
    return retval


def main():
    """Run the full comparison."""
    sets = parse_settings_file('tis-multiple.rst')
    print_to_screen('\nCheck crossing probabilities', level='message')
    print_to_screen('============================', level='message')
    ret4 = compare_prob_files()
    print_to_screen('\nComparing tis.rst files', level='message')
    print_to_screen('=======================', level='message')
    ret1 = compare_rst_files(sets)
    print_to_screen('\nComparing pathensemble.txt files', level='message')
    print_to_screen('================================', level='message')
    ret2 = compare_path_files(sets)
    print_to_screen('\nCheck accepted paths', level='message')
    print_to_screen('====================', level='message')
    ret3 = run_check_path_file(sets)
    return ret1 + ret2 + ret3 + ret4


if __name__ == '__main__':
    colorama.init(autoreset=True)
    sys.exit(main())
