# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""This script will help to copy files for restarting.

Here, we pick out the last accepted path.
"""
import os
import pathlib
import shutil
import tarfile
import tempfile
import colorama
from pyretis.inout import print_to_screen
from pyretis.inout.settings import parse_settings_file
from pyretis.core.pathensemble import generate_ensemble_name


SOURCE = 'run-initialise'
TARGET = os.path.join('run-load', 'initial_path')


def read_path_file(filename):
    """Get index for last accepted path."""
    last_idx = None
    with open(filename, 'r') as fileh:
        for i, lines in enumerate(fileh):
            if i == 0:
                continue
            split = lines.strip().split()
            idx = int(split[0])
            status = split[7]
            if status == 'ACC':
                last_idx = idx
    return last_idx


def get_files_from_directory(ensemble, target):
    """Investigate and copy for the given ensemble."""
    dirname = os.path.join(SOURCE, ensemble)
    print_to_screen('Checking directory: {}'.format(dirname),
                    level='info')
    path_file = os.path.join(dirname, 'pathensemble.txt')
    last_one = read_path_file(path_file)
    print_to_screen('Will use path no. {}'.format(last_one))

    tar_file = os.path.join(dirname, 'traj', 'traj-acc.tar')

    idx = '{}{}'.format(last_one, os.sep)
    filenames = []
    with tempfile.TemporaryDirectory() as tempdir:
        with tarfile.open(tar_file, 'r') as tar:
            files = [i for i in tar.getmembers() if i.name.startswith(idx)]
            tar.extractall(path=tempdir, members=files)
            filenames = [i.name for i in files if i.isfile()]
        for i in filenames:
            src = pathlib.Path(tempdir, i)
            desti = pathlib.Path(i).parts[1:]
            if desti[0] == 'traj':
                dest = pathlib.Path(
                    target, 'accepted', *pathlib.Path(i).parts[2:]
                )
            else:
                dest = pathlib.Path(target, *desti)
            shutil.copy(src, dest)


def main():
    """Copy the files."""
    settings = parse_settings_file(os.path.join(SOURCE, 'retis.rst'))
    nint = len(settings['simulation']['interfaces'])
    for i in range(nint):
        ens = generate_ensemble_name(i)
        target = os.path.join(TARGET, ens)
        target_a = os.path.join(target, 'accepted')
        for path in (target, target_a):
            if not os.path.exists(path):
                os.makedirs(path)
        get_files_from_directory(ens, target)


if __name__ == '__main__':
    colorama.init(autoreset=True)
    main()
