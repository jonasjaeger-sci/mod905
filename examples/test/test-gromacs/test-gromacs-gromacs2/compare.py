# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Compare the outcome of the two simulations."""
import filecmp
from functools import reduce
import itertools
import operator
import os
import sys
import tarfile
import numpy as np
import colorama
from pyretis.core.pathensemble import generate_ensemble_name
from pyretis.inout import print_to_screen
from pyretis.inout.formats.energy import EnergyPathFile

# Folders to consider:
GROMACS1 = 'run-gromacs1'
GROMACS2 = 'run-gromacs2'
# Files to consider:
FILES = ['energy.txt', 'order.txt', 'pathensemble.txt']
TAR_FILES = [os.path.join('traj', i) for i in ('traj-acc.tar', 'traj-rej.tar')]
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
    ener1 = EnergyPathFile(file1, 'r').load()
    ener2 = EnergyPathFile(file2, 'r').load()
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


def get_tar_contents(tar_file):
    """Return files found in a tar archive."""
    files = []
    with tarfile.open(tar_file, 'r') as tar:
        files = [i for i in tar.getmembers() if i.isfile()]
    return files


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


def files_missing(file1, file2):
    """Check if two files are present.

    If one is present, but not the other, then something is wrong.
    If both are missing, however, this can just be case of the
    files not being produced due to no relevant output data.

    Parameters
    ----------
    out[0] : boolean
        True if we are missing files and should abort.
    out[1] : boolean
        True if both files are missing.

    """
    present = []
    for i in (file1, file2):
        file_present = os.path.isfile(i)
        present.append(file_present)
        if not file_present:
            print_to_screen(
                'Expected file "{}" not found.'.format(i),
                level='warning'
            )
    missing = reduce(operator.xor, present)
    return missing, not all(present)


def compare_files(file1, file2, file_type):
    """Helper method to compare two existing files."""
    print_to_screen('Comparing: {} {}'.format(file1, file2))
    equal = False
    if file_type == 'energy.txt':
        equal = compare_energies(file1, file2)
    else:
        if file_type.endswith('.tar'):
            equal = compare_tar_files(file1, file2)
            if equal:
                print_to_screen('Tar archive contains same files.',
                                level='success')
        else:
            equal = filecmp.cmp(file1, file2)
            if equal:
                print_to_screen('Files are equal!', level='success')
    return equal


def main():
    """Run the comparison."""
    print_to_screen('Running comparisons:')
    errors = []
    for i in range(ENSEMBLES):
        ensemble_dir = generate_ensemble_name(i)
        print_to_screen('\nComparing for ensemble {}'.format(ensemble_dir),
                        level='info')
        for fil in itertools.chain(FILES, TAR_FILES):
            file1 = os.path.join(GROMACS1, ensemble_dir, fil)
            file2 = os.path.join(GROMACS2, ensemble_dir, fil)

            missing, missing_both = files_missing(file1, file2)
            if missing:
                errors.append((file1, file2))
                continue
            if missing_both:
                print_to_screen(
                    'Both "{}" and "{}" are missing. Skipping test.'.format(
                        file1,
                        file2
                    ),
                    level='warning'
                )
                continue
            equal = compare_files(file1, file2, fil)
            if not equal:
                print_to_screen('NOTE: Files are NOT equal!', level='error')
                errors.append((file1, file2))
    if not errors:
        print_to_screen()
        print_to_screen('Comparison is done and it was successful!',
                        level='success')
        return 0
    print_to_screen()
    print_to_screen('Comparison is done and it FAILED!', level='error')
    for file1, file2 in errors:
        print_to_screen('{} != {}'.format(file1, file2), level='error')
    return 1


if __name__ == '__main__':
    colorama.init(autoreset=True)
    sys.exit(main())
