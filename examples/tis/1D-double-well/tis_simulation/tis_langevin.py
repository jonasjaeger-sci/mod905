# -*- coding: utf-8 -*-
"""
This is an example on how to perform a simple TIS simulation.
"""
# pylint: disable=C0103
from __future__ import print_function
import numpy as np
# retis imports:
from retis.core import Box, System
from retis.core.simulation import create_simulation
from retis.forcefield import ForceField
from retis.forcefield.potentials import DoubleWell
from retis.core.orderparameter import OrderParameterPosition


simulation_settings = {'type': 'TIS',
                       'integrator': {'name': 'Langevin', 'timestep': 0.002,
                                      'gamma': 0.3, 'seed': 0,
                                      'high-friction': False},
                       'endcycle': 10000,
                       'temperature': 0.07,
                       'interfaces': [-1.0, 0.0, 1.0],
                       'ensemble': '001',
                       'periodic_boundary': [False],
                       'units': 'lj',
                       'generate-vel': {'seed': 0, 'momentum': False,
                                        'distribution': 'maxwell'},
                       'tis': {'start_cond': 'L',
                               'freq': 0.5,
                               'maxlength': 10000,
                               'aimless': True,
                               'allowmaxlength': False,
                               'sigma_v': -1,
                               'seed': 10,
                               'initial_path': 'kick'},
                       'output': [{'type': 'pathensemble', 'target': 'file',
                                   'when': {'every': 10}}]}

# set up simulation
box = Box(periodic=simulation_settings['periodic_boundary'])
print('\nCreated:', box)
system = System(temperature=simulation_settings['temperature'],
                units=simulation_settings['units'],
                box=box)

system.add_particle(name='A', pos=np.array([-1.0]))
msg = 'Added one particle {} at position: {}'
print(msg.format(system.particles.name, system.particles.pos))
if 'generate-vel' in simulation_settings:
    system.generate_velocities(**simulation_settings['generate-vel'])
    msg = 'Generated temperatures with average: {}'

# Set up force field:
double_well = DoubleWell(a=1.0, b=2.0, c=0.0)
forcefield = ForceField(potential=[double_well], desc='Double Well')
system.forcefield = forcefield
print('\nCreated:', system.forcefield)
# add order parameter:
orderparameter = OrderParameterPosition('position', 0, dim='x', periodic=False)
simulation_settings['orderparameter'] = orderparameter
print('\nCreated:', orderparameter)

simulation_tis = create_simulation(simulation_settings, system)
print('\nCreated:', simulation_tis)

for result in simulation_tis.run():
    print(result['cycle']['step'], result['status'])
