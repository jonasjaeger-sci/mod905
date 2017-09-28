# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Example of interaction with a Path."""
import numpy as np
from pyretis.core.path import Path
from pyretis.core.random_gen import RandomGenerator

rgen = RandomGenerator(seed=0)  # Create random generator
path = Path(rgen)  # Create empty path

# Add some phase points to the path:
# (A phase point is just the order parameter, the positions and
# velocities and energies.)
for i in range(10):
    phasepoint = {'order': [i],
                  'pos': np.zeros(3),
                  'vel': np.zeros(3),
                  'vpot': i,
                  'ekin': i}
    path.append(phasepoint)

# Loop over the path using .trajectory()
print('Looping forward:')
for phasepoint in path.trajectory():
    print(phasepoint['vpot'])

# Loop over the path using .trajectory()
print('Looping backward:')
for phasepoint in path.trajectory(reverse=True):
    print(phasepoint['vpot'])

# Get some randomly chosen shooting points:
print('Getting shooting points:')
for i in range(10):
    point, idx = path.get_shooting_point()
    print('Shooting point {}: index = {}, vpot = {}'.format(i, idx,
                                                            point['vpot']))
