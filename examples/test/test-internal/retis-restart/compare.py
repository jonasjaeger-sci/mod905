# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Simple script to compare the outcome of two simulations.

Here we compare a full simulation with one where we have stopped
and restarted after 100 steps.
"""
import os
import sys
import colorama
import numpy as np
from pyretis.inout import print_to_screen
from pyretis.inout.settings import parse_settings_file
from pyretis.core.pathensemble import generate_ensemble_name
from pyretis.inout.formats.path import PathIntFile
from pyretis.inout.formats.energy import EnergyPathFile
from pyretis.inout.formats.order import OrderPathFile


def snapshot_difference(snap1, snap2):
    """Calculate difference between two snapshots."""
    diff = (snap1['pos'] - snap2['pos'])**2
    dsum = np.einsum('ij,ij -> i', diff, diff)
    diffv = (snap1['vel'] - snap2['vel'])**2
    dsumv = np.einsum('ij,ij -> i', diffv, diffv)
    return sum(dsum), sum(dsumv)


def compare_traj(traj1, traj2, tol=1e-12):
    """Compare two trajectories from PyRETIS.

    Here we calculate the mean squared error for the two
    trajectories.

    Parameters
    ----------
    traj1 : string
        A trajectory file to open.
    traj2 : string
        A trajectory file to open.
    tol : float
        A tolerance for comparing numbers.

    Returns
    -------
    out : int
        0 if comparison is successful, != 0 otherwise.

    """
    print_to_screen('Comparing trajectories', level='info')
    print_to_screen('Loading files: {} & {}'.format(traj1, traj2))
    print_to_screen('Checking mean squared error...')
    file1 = PathIntFile(traj1, 'r').load()
    file2 = PathIntFile(traj2, 'r').load()
    error, error_v = [], []
    for trj1, trj2 in zip(file1, file2):
        for snap1, snap2 in zip(trj1['data'], trj2['data']):
            pose, vele = snapshot_difference(snap1, snap2)
            error.append(pose)
            error_v.append(vele)
    ret1 = print_error_assessment(np.mean(error), 'positions', tol)
    ret2 = print_error_assessment(np.mean(error_v), 'velocities', tol)
    return ret1 + ret2


def print_error_assessment(error, what, tol):
    """Print out some error info."""
    if abs(error) < tol:
        lev = 'success'
        ret = 0
    else:
        lev = 'error'
        ret = 1
    print_to_screen('Mean error - {}: {}'.format(what, error),
                    level=lev)
    return ret


def compare_energy(traj1, traj2, tol=1e-12):
    """Compare energies from two PyRETIS trajectories.

    Here we calculate the mean squared error for the given files.

    Parameters
    ----------
    traj1 : string
        A trajectory file to open.
    traj2 : string
        A trajectory file to open.

    Returns
    -------
    out : int
        0 if comparison is successful, != 0 otherwise.

    """
    print_to_screen('Comparing energies', level='info')
    print_to_screen('Loading files: {} & {}'.format(traj1, traj2))
    print_to_screen('Checking mean squared error...')
    file1 = EnergyPathFile(traj1, 'r').load()
    file2 = EnergyPathFile(traj2, 'r').load()
    errors = {}
    nsnap = 0
    for trj1, trj2 in zip(file1, file2):
        for key, values in trj1['data'].items():
            if key == 'time':
                continue
            if key not in errors:
                errors[key] = 0.0
            diff = (values - trj2['data'][key])**2
            errors[key] += sum(diff)
            nsnap += 1
    retval = 0
    for key, err in errors.items():
        error = err / float(nsnap)
        ret = print_error_assessment(error, key, tol)
        retval += ret
    return retval


def compare_order(traj1, traj2, tol=1e-12):
    """Compare order parameters from two PyRETIS trajectories.

    Here we calculate the mean squared error for the given files.

    Parameters
    ----------
    traj1 : string
        A trajectory file to open.
    traj2 : string
        A trajectory file to open.

    Returns
    -------
    out : int
        0 if comparison is successful, != 0 otherwise.

    """
    print_to_screen('Comparing order parameters', level='info')
    print_to_screen('Loading files: {} & {}'.format(traj1, traj2))
    print_to_screen('Checking mean squared error...')
    file1 = OrderPathFile(traj1, 'r').load()
    file2 = OrderPathFile(traj2, 'r').load()
    errors = {}
    nsnap = 0
    for trj1, trj2 in zip(file1, file2):
        _, col = trj1['data'].shape
        for key in range(col):
            if key == 0:
                continue
            if key not in errors:
                errors[key] = 0.0
            diff = (trj1['data'][:, key] - trj2['data'][:, key])**2
            errors[key] += sum(diff)
            nsnap += 1
    retval = 0
    for key, err in errors.items():
        error = err / float(nsnap)
        ret = print_error_assessment(error, 'orderp-{}'.format(key), tol)
        retval += ret
    return retval


def compare_ensemble(ensemble):
    """Run the comparison for an ensemble."""
    print_to_screen('Comparing for "{}"'.format(ensemble), level='info')
    traj1 = os.path.join('retis-100-200', ensemble, 'traj.txt')
    traj2 = os.path.join('retis-full', ensemble, 'traj.txt')
    print_to_screen()
    ret1 = compare_traj(traj1, traj2, tol=1e-12)
    ener1 = os.path.join('retis-100-200', ensemble, 'energy.txt')
    ener2 = os.path.join('retis-full', ensemble, 'energy.txt')
    print_to_screen()
    ret2 = compare_energy(ener1, ener2, tol=1e-12)
    order1 = os.path.join('retis-100-200', ensemble, 'order.txt')
    order2 = os.path.join('retis-full', ensemble, 'order.txt')
    print_to_screen()
    ret3 = compare_order(order1, order2, tol=1e-12)
    return ret1 + ret2 + ret3


def main():
    """Run all comparisons."""
    settings = parse_settings_file(os.path.join('retis-full', 'retis.rst'))
    inter = settings['simulation']['interfaces']
    retval = 0
    for intr in range(len(inter)):
        ens = generate_ensemble_name(intr)
        ret = compare_ensemble(ens)
        retval += ret
    if retval == 0:
        print_to_screen('\nAll seems fine!', level='success')
    else:
        print_to_screen('\nComparison failed!', level='error')
    return retval


if __name__ == '__main__':
    colorama.init(autoreset=True)
    sys.exit(main())
