# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Simple script to compare the outcome of two simulations.

Here we compare a full simulation with one where we have stopped
and restarted after 100 steps.
"""
import filecmp
import os
import sys
import tarfile
import colorama
from pyretis.inout import print_to_screen
from pyretis.inout.settings import parse_settings_file
from pyretis.core.pathensemble import generate_ensemble_name


RUN_FULL = 'run-25'
RUN_LOAD = 'run-load'


def compare_files(file1, file2):
    """Compare two files."""
    similar = filecmp.cmp(file1, file2)
    if similar:
        print_to_screen('\t-> Files are equal!', level='success')
        return True
    print_to_screen('\t-> Files are NOT equal!', level='error')
    return False


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
    for filei in ('energy.txt', 'order.txt'):
        print_to_screen('* Comparing {} files...'.format(filei))
        file1 = os.path.join(RUN_FULL, ensemble, filei)
        file2 = os.path.join(RUN_LOAD, ensemble, filei)
        if not compare_files(file1, file2):
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
