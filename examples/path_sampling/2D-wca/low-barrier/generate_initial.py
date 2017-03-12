# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Here, we just generate the initial config using PyRETIS tools."""
from pyretis.tools.lattice import generate_lattice
from pyretis.inout.writers.xyzio import write_xyz_file

filename = 'initial.xyz'
density = 9.0 / 15.0
xyz, size = generate_lattice('sq', [3, 3], density=density)
names = ['A', 'A', 'A', 'A', 'A', 'A', 'A', 'B', 'B']
print('Generating for density: {}'.format(density))
print('Box size: {}'.format(size))
print('Writing file: {}'.format(filename))
write_xyz_file(filename, xyz, names=names, header='Initial config')
