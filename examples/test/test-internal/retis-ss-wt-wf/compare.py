# -*- coding: utf-8 -*-
# Copyright (c) 2023, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Simple script to compare the outcome of two simulations.

Here we compare a RETIS simulation of 250 steps to known results.
"""
from collections import OrderedDict
from math import isclose
import os
import sys
import colorama
import numpy as np
from pyretis.inout import print_to_screen
from pyretis.inout.settings import parse_settings_file
from pyretis.core.pathensemble import generate_ensemble_name
from pyretis.setup.createsimulation import create_ensembles
from pyretis.inout.formats.order import OrderPathFile

RESULTS = '../results/xxx'


def compare_files(fpath1, fpath2):
    """Compare two files."""
    print_to_screen(f'Comparing: {fpath1} {fpath2}')
    similar = True
    with open(fpath1, 'r') as file1, open(fpath2, 'r') as file2:
        for linef1, linef2 in zip(file1, file2):
            linef1 = linef1.rstrip('\r\n')
            linef2 = linef2.rstrip('\r\n')
            # In the case of different numpy versions
            # causing different results for energy and order files:
            if len(linef1.split()) == 10:
                linef1_float = float(linef1.split()[7][:-1])
                linef2_float = float(linef2.split()[7][:-1])
                similar = abs(linef1_float - linef2_float) < 10**-7
            elif linef1 == linef2:
                similar = True
            else:
                print('----------------------')
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
        The path ensemble to check for.

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


def read_path_file(ens):
    """Read information about paths from pathensemble.txt.

    Parameters
    ----------
    ens : object like :py:class:`.PathEnsemble`
        The path ensemble to read data for.

    Returns
    -------
    paths : dict
        Information about the paths in the ensemble.

    """
    print_to_screen('\nReading for {}'.format(ens.ensemble_name))
    filename = os.path.join(generate_ensemble_name(ens.ensemble_number),
                            'pathensemble.txt')
    print_to_screen('Reading: {}'.format(filename))
    paths = OrderedDict()
    path_acc = OrderedDict()
    current_acc = None
    with open(filename, 'r') as inputfile:
        for lines in inputfile:
            if lines.startswith('#'):
                continue
            splitline = lines.strip().split()
            step = int(splitline[0])
            status = splitline[7]
            move = splitline[8]
            paths[step] = {'status': status,
                           'move': move,
                           'parent': current_acc,
                           'swap-parent': (None, None)}
            if status == 'ACC':
                current_acc = step
            path_acc[step] = current_acc
    return paths, path_acc


def get_swap_parent(paths, ensl, ensr, accl, accr):
    """Get the swapping parent for paths."""
    for key in paths:
        idx = key - 1
        if paths[key]['move'] == 's+':
            paths[key]['swap-parent'] = (ensr, accr[idx])
        elif paths[key]['move'] == 's-':
            paths[key]['swap-parent'] = (ensl, accl[idx])


def check_order_swap(data0, data1, special=2):
    """Check that order parameters are consistent for swapping.

    Here, we compare order parameters from paths that are generated by
    swapping.

    Parameters
    ----------
    data0 : numpy.array
        The order parameters from the first path.
    data1 : numpy.array
        The order parameters from the second path.
    special : integer
        For the two cases, [0-] -> [0+] and [0-] <- [0+] we have
        to do special comparisons.

    Returns
    -------
    out : boolean
        True if everything is fine, False otherwise.

    """
    all_ok = False
    if special == 0:
        # for [0-] generated from [0+]:
        # - two last of 0- should equal two first in 0+
        ok0 = isclose(data0[-2][1], data1[0][1])
        ok1 = isclose(data0[-1][1], data1[1][1])
        all_ok = ok0 and ok1
    elif special == 1:
        # for [0+] generated from [0-]:
        # - two first of 0+ should equal two last from 0-
        ok0 = isclose(data0[0][1], data1[-2][1])
        ok1 = isclose(data0[1][1], data1[-1][1])
        all_ok = ok0 and ok1
    else:
        all_ok = np.allclose(data0, data1)
    return all_ok


def get_index(traj):
    """Just return index from a comment."""
    return int(traj['comment'][0].split('Cycle:')[1].split(',')[0])


def check_swaps(paths, accepted, ens, kind):
    """Check accepted right swaps."""
    ofile0 = OrderPathFile(
        os.path.join(generate_ensemble_name(ens), 'order.txt'), 'r'
    )
    traj0 = ofile0.load()
    if kind == 'left':
        special = 1 if ens == 1 else 2
        ens2 = ens - 1
        move = 's-'
    else:
        special = 0 if ens == 0 else 2
        ens2 = ens + 1
        move = 's+'
    ofile1 = OrderPathFile(
        os.path.join(generate_ensemble_name(ens2), 'order.txt'), 'r'
    )
    traj1 = ofile1.load()
    traj1i, idx1 = {}, None
    errors, ok_ones = set(), set()
    everything_is_ok = True
    for traj0i in traj0:
        idx0 = get_index(traj0i)
        if idx0 in accepted and paths[idx0]['move'] == move:
            parent = paths[idx0]['swap-parent']
            if not parent[0] == ens2:
                raise ValueError('Wrong parent!')
            swap_ok = False
            found = False
            if traj1i:
                # just check if we should use this one again:
                if idx1 == parent[1]:
                    found = True
                    swap_ok = check_order_swap(traj0i['data'],
                                               traj1i['data'],
                                               special=special)
            if not found:
                for traj1i in traj1:
                    idx1 = get_index(traj1i)
                    if idx1 == parent[1]:
                        found = True
                        swap_ok = check_order_swap(traj0i['data'],
                                                   traj1i['data'],
                                                   special=special)
                        break
            if not found:
                print_to_screen('Could not find parent for {}'.format(idx0),
                                level='warning')
                everything_is_ok = False
            else:
                if swap_ok:
                    ok_ones.add(idx0)
                else:
                    print_to_screen('Comparison failed for {}'.format(idx0),
                                    level='error')
                    everything_is_ok = False
                    errors.add(idx0)
    if everything_is_ok:
        print_to_screen('All swaps are ok!', level='success')
    else:
        print_to_screen('Error for some swaps:', level='error')
        print_to_screen(errors)
        sys.exit(1)
    return 0


def check_ensemble_swaps(settings):
    """Check swaps for ensembles from settings."""
    ensembles = create_ensembles(settings)
    path_info = {}
    path_acc = {}
    names = []
    for i, ens in enumerate(ensembles):
        pathi, patha = read_path_file(ens['path_ensemble'])
        path_info[i] = pathi
        path_acc[i] = patha
        names.append(ens['path_ensemble'].ensemble_name)
    for i in range(len(ensembles)):
        if i == 0:
            get_swap_parent(path_info[i], None, i+1, None, path_acc[i+1])
            print_to_screen(
                '\nChecking {} <- {} swaps...'.format(names[i], names[i+1]),
                level='info'
            )
            check_swaps(path_info[i], path_acc[i], i, kind='right')
        elif i == len(ensembles) - 1:
            get_swap_parent(path_info[i], i-1, None, path_acc[i-1], None)
            print_to_screen(
                '\nChecking {} <- {} swaps...'.format(names[i], names[i-1]),
                level='info'
            )
            check_swaps(path_info[i], path_acc[i], i, kind='left')
        else:
            get_swap_parent(path_info[i], i-1, i+1,
                            path_acc[i-1], path_acc[i+1])
            print_to_screen(
                '\nChecking {} -> {} swaps...'.format(names[i], names[i+1]),
                level='info'
            )
            check_swaps(path_info[i], path_acc[i], i, kind='right')
            print_to_screen(
                'Checking {} <- {} swaps...'.format(names[i], names[i-1]),
                level='info'
            )
            check_swaps(path_info[i], path_acc[i], i, kind='left')
    return 0


def compare_ens_files(settings, string):
    """Compare comare ensemble text files."""
    inter = settings['simulation']['interfaces']
    retval = 0
    for i in range(len(inter)):
        ens_dir = generate_ensemble_name(i)
        fil1 = os.path.join(ens_dir, string)
        fil2 = os.path.join(RESULTS, ens_dir, string)
        ret = compare_files(fil1, fil2)
        retval += ret
    return retval


def main():
    """Run the full comparison."""
    sets = parse_settings_file('retis.rst')
    print_to_screen('\nComparing pathensemble.txt files', level='message')
    print_to_screen('================================', level='message')
    ret1 = compare_ens_files(sets, 'pathensemble.txt')
    print_to_screen('\nCheck swaps', level='message')
    print_to_screen('===========', level='message')
    ret2 = check_ensemble_swaps(sets)
    print_to_screen('\nCheck accepted paths', level='message')
    print_to_screen('====================', level='message')
    ret3 = run_check_path_file(sets)
    print_to_screen('\nComparing energy.txt files', level='message')
    print_to_screen('================================', level='message')
    ret4 = compare_ens_files(sets, 'energy.txt')
    print_to_screen('\nComparing order.txt files', level='message')
    print_to_screen('================================', level='message')
    ret5 = compare_ens_files(sets, 'order.txt')

    retval = ret1 + ret2 + ret3 + ret4 + ret5
    if retval == 0:
        print_to_screen('\nComparison is successful!', level='success')
    else:
        print_to_screen('\nComparison failed!', level='error')
    return ret1 + ret2 + ret3 + ret4 + ret5


if __name__ == '__main__':
    colorama.init(autoreset=True)
    sys.exit(main())
