# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""This script will help copying files for restarting.

Here, we pick out the last accepted path.
"""
# pylint: disable=C0103
import os
import shutil
import pickle
from pyretis.inout.settings import parse_settings_file
from pyretis.core.pathensemble import PATH_DIR_FMT


SOURCE = 'run-initialise'
TARGET = 'run-restart'


def main():
    """Copy the files :-)"""
    settings = parse_settings_file(os.path.join(SOURCE, 'retis.rst'))
    nint = len(settings['simulation']['interfaces'])
    for i in range(nint):
        ens = PATH_DIR_FMT.format(i)
        target = os.path.join(TARGET, ens)
        source = os.path.join(SOURCE, ens)
        shutil.copytree(source, target)
        # read restart file and update paths:
        restart = os.path.join(target, 'ensemble.restart')
        info = {}
        with open(restart, 'rb') as infile:
            info = pickle.load(infile)
        newpos = []
        for pos in info['last_path']['pos']:
            name = os.path.basename(pos[0])
            abs_path = os.path.abspath(os.path.join(target, 'accepted', name))
            newpos.append((abs_path, pos[1]))
        info['last_path']['pos'] = newpos
        with open(restart, 'wb') as outfile:
            pickle.dump(info, outfile)


if __name__ == '__main__':
    main()
