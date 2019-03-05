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

SOURCE = 'run-20'
TARGET = pathlib.Path('run-load', 'initial_path')


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


def extract_traj(traj_file, target, last_one):
    """Extract a given path from a file."""
    dirname = '{}{}'.format(last_one, os.sep)
    with tempfile.TemporaryDirectory() as tempdir:
        filenames = []
        with tarfile.open(traj_file, 'r') as tar:
            files = [i for i in tar.getmembers() if i.name.startswith(dirname)]
            tar.extractall(path=tempdir, members=files)
            filenames = [i.name for i in files if i.isfile()]
        for i in filenames:
            src = pathlib.Path(tempdir, i)
            dest1 = pathlib.Path(i).parts[1:]
            if dest1[0] == 'traj':
                dest = pathlib.Path(
                    target, 'accepted', *pathlib.Path(i).parts[2:]
                )
                acc = pathlib.Path(target, 'accepted')
                if not acc.is_dir():
                    try:
                        os.makedirs(acc)
                    except FileExistsError:
                        pass
            else:
                dest = pathlib.Path(target, *dest1)
            shutil.move(src, dest)


def get_files_from_directory(ensemble, target):
    """Investigate and copy for the given ensemble."""
    dirname = pathlib.Path(SOURCE, ensemble)
    print_to_screen('Checking directory: {}'.format(dirname),
                    level='info')
    path_file = pathlib.Path(dirname, 'pathensemble.txt')
    last_one = read_path_file(path_file)
    print_to_screen('Will use path no. {}'.format(last_one))
    traj_file = pathlib.Path(dirname, 'traj', 'traj-acc.tar')
    extract_traj(traj_file, target, last_one)


def main():
    """Copy the files."""
    settings = parse_settings_file(pathlib.Path(SOURCE, 'retis.rst'))
    nint = len(settings['simulation']['interfaces'])
    for i in range(nint):
        ens = generate_ensemble_name(i)
        target = pathlib.Path(TARGET, ens)
        try:
            os.makedirs(target)
        except FileExistsError:
            pass
        for filei in ('pathensemble.txt', 'ensemble.restart'):
            src = pathlib.Path(SOURCE, ens, filei)
            dest = pathlib.Path(target, filei)
            shutil.copy(src, dest)
        get_files_from_directory(ens, target)


if __name__ == '__main__':
    colorama.init(autoreset=True)
    main()
