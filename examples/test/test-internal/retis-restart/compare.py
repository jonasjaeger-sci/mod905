# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Simple script to compare outcome of two simulations.

Here we compare a full simulation with one where we have stopped
and restarted after 100 steps.
"""
# pylint: disable=C0103
import itertools
import os
import colorama
import numpy as np
from pyretis.inout.common import print_to_screen
from pyretis.inout.writers import get_writer
from pyretis.inout.settings import parse_settings_file
from pyretis.core.pathensemble import PATH_DIR_FMT


def snapshot_difference(snap1, snap2):
    """Calculate difference between two snapshots."""
    diff = (snap1['pos'] - snap2['pos'])**2
    dsum = np.einsum('ij,ij -> i', diff, diff)
    diffv = (snap1['vel'] - snap2['vel'])**2
    dsumv = np.einsum('ij,ij -> i', diffv, diffv)
    return sum(dsum), sum(dsumv)


def compare_traj(traj11, traj12, traj2, tol=1e-12):
    """A comparison of two trajectories from PyRETIS

    Here we calculate the mean squared error for the two
    trajectories.

    Parameters
    ----------
    traj11 : string
        A trajectory to open, part 1.
    traj12 : string
        A trajectory to open, part 2.
    traj2 : string
        A trajectory file to open.

    Returns
    -------
    None, just prints out the result of the comparison.
    """
    print_to_screen('Comparing trajectories', level='info')
    print('Checking mean squared error...')
    file11 = get_writer('pathtrajint').load(traj11)
    file12 = get_writer('pathtrajint').load(traj12)
    next(file12)  # skip first item
    file1 = itertools.chain(file11, file12)
    file2 = get_writer('pathtrajint').load(traj2)
    error, error_v = 0.0, 0.0
    nsnap = 0
    for traj1, traj2 in zip(file1, file2):
        for snap1, snap2 in zip(traj1['data'], traj2['data']):
            pose, vele = snapshot_difference(snap1, snap2)
            error += pose
            error_v += vele
            nsnap += 1
    error /= float(nsnap)
    print_what_you_think_about_the_error(error, 'positions', tol)
    print_what_you_think_about_the_error(error_v, 'velocities', tol)


def print_what_you_think_about_the_error(error, what, tol):
    """Print out some error info."""
    if abs(error) < tol:
        lev = 'success'
    else:
        lev = 'error'
    print_to_screen('Mean error - {}: {}'.format(what, error),
                    level=lev)


def compare_energy(traj11, traj12, traj2, tol=1e-12):
    """A comparison of energies/orderparameters from PyRETIS

    Here we calculate the mean squared error for the given files.

    Parameters
    ----------
    traj11 : string
        A trajectory to open, part 1.
    traj12 : string
        A trajectory to open, part 2.
    traj2 : string
        A trajectory file to open.

    Returns
    -------
    None, just prints out the result of the comparison.
    """
    print_to_screen('Comparing energies', level='info')
    print('Checking mean squared error...')
    file11 = get_writer('pathenergy').load(traj11)
    file12 = get_writer('pathenergy').load(traj12)
    next(file12)  # skip first item
    file1 = itertools.chain(file11, file12)
    file2 = get_writer('pathenergy').load(traj2)
    errors = {}
    nsnap = 0
    for traj1, traj2 in zip(file1, file2):
        for key, values in traj1['data'].items():
            if key == 'time':
                continue
            if key not in errors:
                errors[key] = 0.0
            diff = (values - traj2['data'][key])**2
            errors[key] += sum(diff)
            nsnap += 1
    for key, err in errors.items():
        error = err / float(nsnap)
        print_what_you_think_about_the_error(error, key, tol)


def compare_order(traj11, traj12, traj2, tol=1e-12):
    """A comparison of energies/orderparameters from PyRETIS

    Here we calculate the mean squared error for the given files.

    Parameters
    ----------
    traj11 : string
        A trajectory to open, part 1.
    traj12 : string
        A trajectory to open, part 2.
    traj2 : string
        A trajectory file to open.

    Returns
    -------
    None, just prints out the result of the comparison.
    """
    print_to_screen('Comparing order parameters', level='info')
    print('Checking mean squared error...')
    file11 = get_writer('pathorder').load(traj11)
    file12 = get_writer('pathorder').load(traj12)
    next(file12)  # skip first item
    file1 = itertools.chain(file11, file12)
    file2 = get_writer('pathorder').load(traj2)
    errors = {}
    nsnap = 0
    for traj1, traj2 in zip(file1, file2):
        _, col = traj1['data'].shape
        for key in range(col):
            if key == 0:
                continue
            if key not in errors:
                errors[key] = 0.0
            diff = (traj1['data'][:, key] - traj2['data'][:, key])**2
            errors[key] += sum(diff)
            nsnap += 1
    for key, err in errors.items():
        error = err / float(nsnap)
        print_what_you_think_about_the_error(error,
                                             'orderp-{}'.format(key),
                                             tol)


def compare_ensemble(ensemble):
    """Run the comparison for an ensemble"""
    print_to_screen('Comparing for "{}"'.format(ensemble), level='info')
    traj11 = os.path.join('retis-100', ensemble, 'traj.txt')
    traj12 = os.path.join('retis-100-200', ensemble, 'traj.txt')
    traj2 = os.path.join('retis-full', ensemble, 'traj.txt')
    compare_traj(traj11, traj12, traj2, tol=1e-12)
    ener11 = os.path.join('retis-100', ensemble, 'energy.txt')
    ener12 = os.path.join('retis-100-200', ensemble, 'energy.txt')
    ener2 = os.path.join('retis-full', ensemble, 'energy.txt')
    compare_energy(ener11, ener12, ener2, tol=1e-12)
    order11 = os.path.join('retis-100', ensemble, 'order.txt')
    order12 = os.path.join('retis-100-200', ensemble, 'order.txt')
    order2 = os.path.join('retis-full', ensemble, 'order.txt')
    compare_order(order11, order12, order2, tol=1e-12)
    print()


if __name__ == '__main__':
    colorama.init(autoreset=True)
    settings = parse_settings_file('retis-full/retis.rst')
    inter = settings['simulation']['interfaces']
    for i in range(len(inter)):
        ens = PATH_DIR_FMT.format(i)
        compare_ensemble(ens)
