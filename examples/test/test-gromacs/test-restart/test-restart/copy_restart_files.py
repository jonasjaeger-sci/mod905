# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""This script will help to copy files for restarting.

Here, we copy the last accepted paths.
"""
import os
import shutil
import pickle
from pyretis.inout.settings import parse_settings_file
from pyretis.core.pathensemble import generate_ensemble_name


SOURCE = 'run-20'
TARGET = 'run-restart'


def main():
    """Copy the files."""
    settings = parse_settings_file(os.path.join(SOURCE, 'retis.rst'))
    nint = len(settings['simulation']['interfaces'])
    for i in range(nint):
        ens = generate_ensemble_name(i)
        target = os.path.join(TARGET, ens)
        source = os.path.join(SOURCE, ens)
        shutil.copytree(source, target)
        # Read restart file and update paths:
        restart = os.path.join(target, 'ensemble.restart')
        info = {}
        with open(restart, 'rb') as infile:
            info = pickle.load(infile)
        newpos = []
        for phasepoint in info['last_path']['phasepoints']:
            filename, idx = phasepoint['particles']['config']
            name = os.path.basename(filename)
            abs_path = os.path.abspath(os.path.join(target, 'accepted', name))
            newpos.append((abs_path, idx))
        for phasepoint, pos in zip(info['last_path']['phasepoints'], newpos):
            phasepoint['particles']['config'] = pos
        with open(restart, 'wb') as outfile:
            pickle.dump(info, outfile)


if __name__ == '__main__':
    main()
