# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""This script will help copying files for restarting.

Here, we pick out the last accepted path.
"""
# pylint: disable=C0103
import os
import colorama
from pyretis.inout.common import print_to_screen
from pyretis.inout.settings import parse_settings_file
from pyretis.core.pathensemble import PATH_DIR_FMT
from pyretis.inout.writers import prepare_load, get_writer


SOURCE = 'retis-100'
TARGET = os.path.join('retis-100-200', 'restart')


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


def extract_energy(energy_file, target_energy, last_one):
    """Extract a given path from a file."""
    writer = get_writer('pathenergy')
    with open(target_energy, 'w') as output:
        energy = prepare_load('pathenergy', energy_file)
        for idx, path in enumerate(energy):
            if idx == last_one:
                for lines in path['comment']:
                    output.write('{}\n'.format(lines))
                ekin = path['data']['ekin']
                vpot = path['data']['vpot']
                time = path['data']['time']
                for i, timei in enumerate(time):
                    energy = {'ekin': ekin[i], 'vpot': vpot[i]}
                    output.write('{}\n'.format(writer.format_data(int(timei),
                                                                  energy)))


def extract_order(order_file, target_order, last_one):
    """Extract a given path from a file."""
    writer = get_writer('pathorder')
    with open(target_order, 'w') as output:
        order = prepare_load('pathorder', order_file)
        for idx, path in enumerate(order):
            if idx == last_one:
                for lines in path['comment']:
                    output.write('{}\n'.format(lines))
                for stuff in path['data']:
                    step = int(stuff[0])
                    order = stuff[1:]
                    output.write('{}\n'.format(writer.format_data(step,
                                                                  order)))


def extract_traj(traj_file, target_traj, last_one):
    """Extract a given path from a file."""
    fmt = None
    with open(target_traj, 'w') as output:
        traj = prepare_load('pathtrajint', traj_file)
        for idx, path in enumerate(traj):
            if idx == last_one:
                for lines in path['comment']:
                    output.write('{}\n'.format(lines))
                for i, snapshot in enumerate(path['data']):
                    output.write('Snapshot: {}\n'.format(i))
                    pos = snapshot['pos']
                    vel = snapshot['vel']
                    for posj, velj in zip(pos, vel):
                        if fmt is None:
                            fmt = ('{} ' * (len(posj) + len(velj))).strip()
                            fmt += '\n'
                        output.write(fmt.format(*posj, *velj))


def get_files_from_directory(ensemble, target):
    """Investigate and copy for the given ensemble."""
    dirname = os.path.join(SOURCE, ensemble)
    print_to_screen('Checking directory: {}'.format(dirname),
                    level='info')
    path_file = os.path.join(dirname, 'pathensemble.txt')
    last_one = read_path_file(path_file)
    print_to_screen('Will use path no. {}'.format(last_one))

    energy_file = os.path.join(dirname, 'energy.txt')
    target_energy = os.path.join(target, 'energy.txt')
    extract_energy(energy_file, target_energy, last_one)

    order_file = os.path.join(dirname, 'order.txt')
    target_order = os.path.join(target, 'order.txt')
    extract_order(order_file, target_order, last_one)

    traj_file = os.path.join(dirname, 'traj.txt')
    target_traj = os.path.join(target, 'traj.txt')
    extract_traj(traj_file, target_traj, last_one)


def main():
    """Copy the files :-)"""
    settings = parse_settings_file(os.path.join(SOURCE, 'retis.rst'))
    nint = len(settings['simulation']['interfaces'])
    for i in range(nint):
        ens = PATH_DIR_FMT.format(i)
        target = os.path.join(TARGET, ens)
        if not os.path.exists(target):
            os.makedirs(target)
        get_files_from_directory(ens, target)


if __name__ == '__main__':
    colorama.init(autoreset=True)
    main()
