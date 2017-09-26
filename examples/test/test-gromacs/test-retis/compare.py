# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Simple script to compare outcome of two simulations.

Here we compare a RETIS simulation of 250 steps to known results.
"""
import os
import sys
import tarfile
import colorama
from pyretis.inout.common import print_to_screen
from pyretis.inout.settings import parse_settings_file
from pyretis.core.pathensemble import PATH_DIR_FMT


RESULTS = 'results'
RESULTS_TGZ = {
    '2016': 'results-2016.tgz',
    '5': 'results-5.x.x.tgz',
}


def read_tarfile(tar_file, file_to_extract):
    """Extract and read the requested file from a .tgz archive.

    Parameters
    ----------
    tar_file : string
        Path to the .tgz file to open,
    file_to_extract : string
        The file we are going to extract.

    Returns
    -------
    out : list of strings
        The file we read.

    Note
    ----
    This will read the contents of the requested file into memory.
    """
    data = None
    with tarfile.open(tar_file, 'r:gz') as tar:
        for member in tar.getmembers():
            if member.isreg() and member.name == file_to_extract:
                tfile = tar.extractfile(member)
                data = tfile.read()
    return data


def compare_files(settings, root, results_tgz):
    """Compare ouput files."""
    inter = settings['simulation']['interfaces']
    for i in range(len(inter)):
        for files in ('pathensemble.txt', 'energy.txt',
                      'order.txt', 'traj.txt'):
            result = compare_file_contents(root, i, files, results_tgz)
            if not result:
                print_to_screen('\t-> *Files differ!*', level='error')
                return False
    print_to_screen('All files are equal!', level='success')
    return True


def compare_file_contents(root, ensemble, file_name, results_tgz):
    """Compare files for a given ensemble inside a given directory.

    Parameters
    ----------
    root : string
        The directory where we will do the comparison.
    ensemble : integer
        The ensemble we are comparing for (0, 1, 2, ...)
    file_name : string
        The file we will compare.
    results_tgz : string
        The file containing the correct results we compare to.
        This is a tgz-archive.

    Returns
    -------
    result : boolean
        True if the files are equal, False otherwise.
    """
    tgz_file = os.path.join(root, results_tgz)
    ensemble_dir = PATH_DIR_FMT.format(ensemble)
    file2 = os.path.join(RESULTS, ensemble_dir, file_name)
    data2 = read_tarfile(tgz_file, file2)
    file1 = os.path.join(root, ensemble_dir, file_name)
    print_to_screen('Comparing for: {}'.format(file1))
    return open(file1, 'rb').read() == data2


def main(args):
    """Run the comparison."""
    try:
        gmx_version = args[1].split()[-1]
    except IndexError:
        gmx_version = '5.1.4'
    print_to_screen('GROMACS version family: {}'.format(gmx_version),
                    level='info')
    correct = RESULTS_TGZ[gmx_version.split('.')[0]]
    print_to_screen('Using results from: {}'.format(correct), level='info')

    for dirname in ('gromacs1', 'gromacs2'):
        sets = parse_settings_file(os.path.join(dirname, 'retis.rst'))
        head = 'Comparing files for: {}'.format(dirname)
        print_to_screen('\n{}'.format(head), level='message')
        print_to_screen('=' * len(head), level='message')
        compare_ok = compare_files(sets, dirname, correct)
        if not compare_ok:
            sys.exit(1)


if __name__ == '__main__':
    colorama.init(autoreset=True)
    main(sys.argv)
