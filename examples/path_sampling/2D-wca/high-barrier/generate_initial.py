# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Here, we just generate the initial config using pyretis tools."""
from pyretis.tools.lattice import generate_lattice
from pyretis.inout.writers.traj import write_xyz_file

filename = 'initial.xyz'
density = 0.7
xyz, size = generate_lattice('sq', [5, 5], density=density)
names = ['B', 'B'] + ['A'] * 23
print('Generating for density: {}'.format(density))
print('Box size: {}'.format(size))
print('Writing file: {}'.format(filename))
write_xyz_file(filename, xyz, names=names, header='Initial config.')
