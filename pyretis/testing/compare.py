# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Methods that might be useful for several tests.

This module defines methods that can be used for comparing results.

"""
import math
import os
import filecmp
import numpy as np
from pyretis.testing.helpers import search_for_files
from pyretis.inout.formats.energy import EnergyPathFile
from pyretis.inout.formats.order import OrderPathFile
from pyretis.inout.formats.path import PathExtFile


# Names of the expected output files in archive directories:
ARCHIVE_FILES = {'energy.txt', 'order.txt', 'traj.txt'}
# Names of other expected output files:
OUTPUT_FILES = {'energy.txt', 'order.txt', 'pathensemble.txt'}
# Define readers for loading data:
READERS = {
    'energy': EnergyPathFile,
    'order': OrderPathFile,
    'traj': PathExtFile,
}


def read_files(*files, read_comments=True):
    """Read files into memory.

    Here, we assume that we are given small files and that we
    can read these into memory.

    Parameters
    ----------
    files : list of strings
        These are the paths to the files we are to read.
    read_comments : boolean
        If False, we skip lines starting with a "#".

    Returns
    -------
    out : list of list of strings
        The data read from the different files.

    """
    all_data = []
    for filename in files:
        data = []
        with open(filename, 'r') as infile:
            for line in infile:
                if not read_comments and line.strip().startswith('#'):
                    continue
                else:
                    data.append(line)
        all_data.append(data)
    return all_data


def compare_files_lines(file1, file2, skip=None):
    """Compare two files, line by line.

    Parameters
    ----------
    file1 : string
        The path to the first file to compare.
    file2 : string
        The path to the second file to compare.
    skip : list of integers, optional
        These are line numbers we are to skip.

    Returns
    -------
    out[0] : boolean
        True if the files are deemed to be equal.
    out[1] : string
        A descriptive message of the result of the comparison.

    """
    all_data = read_files(file1, file2, read_comments=True)
    assert len(all_data) == 2
    data1, data2 = all_data[0], all_data[1]
    if len(data1) != len(data2):
        return False, 'The number of lines in the files differ'
    for i, (linei, linej) in enumerate(zip(data1, data2)):
        if skip and i in skip:
            continue
        if not linei == linej:
            return False, 'Line {} differs: {} != {}'.format(
                i, linei.strip(), linej.strip()
            )
    return True, 'Files are equal'


def compare_files_columns(file1, file2, file_type, skip=None):
    """Compare two output PyRETIS files.

    This method compares files where numbers are stored in columns
    and the columns have specific labels. Here, we also compare
    labels and comments.

    Parameters
    ----------
    file1 : string
        The path to the first file to compare.
    file2 : string
        The path to the second file to compare.
    file_type : string
        A string used to determine the file type.
    skip : list of strings, optional
        A list of items from the loaded data we are to skip.
        This can, for instance, be certain energy terms that are
        not absolute and can't easily be compared.

    Returns
    -------
    out[0] : boolean
        True if the files are deemed to be equal.
    out[1] : string
        A descriptive message of the result of the comparison.

    """
    reader = READERS[file_type]
    data1 = reader(file1, 'r').load()
    data2 = reader(file2, 'r').load()
    # Compare the files by compare the block found in the file:
    for block1, block2 in zip(data1, data2):
        # Start with block comments:
        if block1['comment'] != block2['comment']:
            return False, 'Block comment differs'
        # Compare terms found in the blocks:
        if sorted(block1['data'].keys()) != sorted(block2['data'].keys()):
            return False, 'Different items in block data'
        # Compare numerical data:
        for key, val in block1['data'].items():
            if skip and key in skip:
                continue
            if not np.allclose(val, block2['data'][key]):
                return False, 'Block terms differ'
    return True, 'Files are equal'


def compare_files_numerical(file1, file2):
    """Compare two output PyRETIS files.

    Here, we compare files that contain numerical data. We don't
    care about comments here, we just compare the actual numerical data.

    Parameters
    ----------
    file1 : string
        The path to the first file to compare.
    file2 : string
        The path to the second file to compare.

    Returns
    -------
    out[0] : boolean
        True if the files are deemed to be equal.
    out[1] : string
        A descriptive message of the result of the comparison.

    """
    data1 = np.loadtxt(file1)
    data2 = np.loadtxt(file2)
    if not np.allclose(data1, data2):
        return False, 'Numerical data differ'
    return True, 'Files are equal'


def compare_files(file1, file2, skip=None, mode='line'):
    """Compare two files.

    Parameters
    ----------
    file1 : string
        The path to the first file to compare.
    file2 : string
        The path to the second file to compare.
    skip : list of strings or list of ints, optional
        A list of items that are to be skipped in the comparison.
    mode : string
        A string used to determine how we do the comparison:
        ``'numerical'`` will select a comparison in which the
        file is parsed and numerical data compared;
        ``'line'`` will select a line-by-line comparison;
        anything else will perform a comparison using
        :py:func:`filecmp.cmp`.

    Returns
    -------
    out[0] : boolean
        True if the files were found to be equal, False otherwise.
    out[1] : string
        A string with information about the comparison result.

    """
    if mode == 'numerical':
        equal, msg = compare_files_numerical(file1, file2)
    elif mode == 'line':
        equal, msg = compare_files_lines(file1, file2, skip=skip)
    else:
        equal = filecmp.cmp(file1, file2, shallow=False)
        msg = 'Files are equal' if equal else 'Files are not equal'
    return equal, msg


def compare_traj_archive(dir1, dir2):
    """Compare archived trajectories.

    These archives consist of trajectory information such as
    energies, order parameters and positions. Here, we will not
    compare the actual raw trajectory data, but we verify that
    the output written by PyRETIS is identical in the two cases.

    Parameters
    ----------
    dir1 : string
        The path to the first directory to use in the comparison.
    dir2 : string
        The path to the second directory to use in the comparison.

    Returns
    -------
    out : list of tuples
        This list contains the files which differed, if any.

    """
    errors = []
    files1 = sorted(search_for_files(dir1))
    files2 = sorted(search_for_files(dir2))
    # Are the number of files equal:
    if len(files1) != len(files2):
        errors.append((dir1, dir2))
        return errors
    # Compare the files that are written by PyRETIS:
    for file1, file2 in zip(files1, files2):
        basename1 = os.path.basename(file1)
        basename2 = os.path.basename(file2)
        if basename1 != basename2:
            errors.append((file1, file2))
            continue
        if basename1 in ARCHIVE_FILES:
            equal, _ = compare_files(file1, file2, mode='cmp')
            if not equal:
                errors.append((file1, file2))
    return errors


def compare_pathensemble_files(file1, file2, rel_tol=1e-5, skip=None):
    """Compare two path ensemble files.

    We compare line-by-line, but skip comments and we check that
    numbers are close, as judged by the given relative tolarance.

    Parameters
    ----------
    file1 : string
        The path to the first file to consider in the comparison.
    file2 : string
        The path to the second file to consider in the comparison.
    rel_tol : float, optional
        A relative tolerance which is used to determine if numbers
        are almost equal.
    skip : list of integers, optional
        These are columns we are to skip in the comparison.

    Returns
    -------
    out[0] : boolean
        True if the files are equal, False otherwise.
    out[1] : string
        A message describing the result of the comparison.

    """
    all_data = read_files(file1, file2, read_comments=False)
    assert len(all_data) == 2
    if not len(all_data[0]) == len(all_data[1]):
        return False, 'The number of lines in the files differ'
    # Define the expected data types for the columns in the path
    # ensemble files:
    data_types = {
        0: int, 1: int, 2: int, 3: str, 4: str, 5: str, 6: int, 7: str, 8: str,
        9: float, 10: float, 11: int, 12: int, 13: float, 14: int, 15: int,
    }
    for i, (line1, line2) in enumerate(zip(*all_data)):
        stuff1 = line1.split()
        stuff2 = line2.split()
        for col, func in data_types.items():
            if skip and col in skip:
                continue
            if func == str:
                check = func(stuff1[col]) == func(stuff2[col])
            else:
                check = math.isclose(
                    func(stuff1[col]), func(stuff2[col]), rel_tol=rel_tol
                )
            if not check:
                return False, 'Files differ on line {}, column {}'.format(i,
                                                                          col)
    return True, 'Files are equal'
