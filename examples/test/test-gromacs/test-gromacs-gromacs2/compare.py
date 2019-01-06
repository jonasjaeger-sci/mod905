# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Compare outcome of the two simulations."""
# pylint: disable=C0103
import filecmp
import os
import numpy as np
import colorama
from pyretis.core.pathensemble import PATH_DIR_FMT
from pyretis.inout.common import print_to_screen
from pyretis.inout.writers import EnergyPathWriter

# Folders to consider:
GROMACS1 = 'run-gromacs1'
GROMACS2 = 'run-gromacs2'
# Files to consider:
FILES = ['energy.txt', 'order.txt', 'pathensemble.txt', 'traj.txt']
# Define number of ensembles used:
ENSEMBLES = 6


def compare_energy_term(energy1, energy2, term):
    """Compare a energy term.

    Parameters
    ----------
    energy1 : dictionary of numpy.arrays
        The data from the ``gromacs`` engine.
    energy2 : dictionary of numpy.arrays
        The data from the ``gromacs2`` engine.
    term : string
        The term to compare.
    """
    term1 = energy1['data'][term]
    term2 = energy2['data'][term]
    return np.allclose(term1, term2)


def compare_energies(file1, file2):
    """We do a special comparison for the energies.

    So, when we are continuing simulations, GROMACS does not
    write the dispersion corrections on all steps. In order
    to compare the files, we manually add it from the first step
    in each trajectory.

    Parameters
    ----------
    file1 : string
        The energy file from a GROMACS-continuation run.
        This is the file when using the ``gromacs`` engine.
    file2 : string
        The energy file from a GROMACS run. This is the file
        obtained using the ``gromacs2`` engine.
    """
    ener1 = EnergyPathWriter().load(file1)
    ener2 = EnergyPathWriter().load(file2)
    equal = True
    for block1, block2 in zip(ener1, ener2):
        equal &= (block1['comment'] == block2['comment'])
        termok = False
        for key in block1['data']:
            if key == 'vpot':
                print_to_screen('Skipping potential energy', level='warning')
                continue
            termok = compare_energy_term(block1, block2, key)
            if not termok:
                print_to_screen('Energy terms "{}" differ!'.format(key),
                                level='error')
        equal &= termok
    if equal:
        print_to_screen('Energy terms are equal', level='success')
    return equal


def main():
    """Run the comparison."""
    print('Running comparisons:')
    errors = []
    for i in range(ENSEMBLES):
        ensemble_dir = PATH_DIR_FMT.format(i)
        print_to_screen('\nComparing for ensemble {}'.format(ensemble_dir),
                        level='info')
        for fil in FILES:
            file1 = os.path.join(GROMACS1, ensemble_dir, fil)
            file2 = os.path.join(GROMACS2, ensemble_dir, fil)
            for fili in (file1, file2):
                if not os.path.isfile(fili):
                    msg = 'File "{}" NOT found, skipping...'.format(fili)
                    print_to_screen(msg, level='error')
            print('Comparing: {} {}'.format(file1, file2))
            equal = False
            if fil == 'energy.txt':
                equal = compare_energies(file1, file2)
            else:
                equal = filecmp.cmp(file1, file2)
                if equal:
                    print_to_screen('Files are equal!', level='success')
            if not equal:
                print_to_screen('NOTE: Files are NOT equal!', level='error')
                errors.append((file1, file2))
    if not errors:
        print()
        print_to_screen('Comparison is done and it was successful!',
                        level='success')
    else:
        print()
        print_to_screen('Comparison is done and it FAILED!', level='error')
        for file1, file2 in errors:
            print_to_screen('{} != {}'.format(file1, file2), level='error')


if __name__ == '__main__':
    colorama.init(autoreset=True)
    main()
