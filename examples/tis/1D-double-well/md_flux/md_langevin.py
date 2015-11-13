# -*- coding: utf-8 -*-
"""Example on calculating the initial flux from effective crossings.

This is an example on how to perform a simple MD simulation for determining
the initial flux for a TIS rate calculation.

It will simulate a one particle in a double well potential using the
Langvin integrator.
"""
# pylint: disable=C0103
from __future__ import print_function
import numpy as np
# pyretis imports:
# for setting up the simulation
from pyretis.core import Box, System
from pyretis.core.simulation import create_simulation
from pyretis.forcefield import ForceField
from pyretis.forcefield.potentials import DoubleWell
from pyretis.core.orderparameter import OrderParameterPosition
# for analysing and output:
from pyretis.analysis import analyse_flux
from pyretis.inout import generate_report
from pyretis.inout import create_output, store_settings_as_py


print('MD flux simulation!')
simulation_settings = {'type': 'mdflux',
                       'integrator': {'name': 'Langevin', 'timestep': 0.002,
                                      'gamma': 0.3, 'seed': 0,
                                      'high-friction': False},
                       'endcycle': 10000000,
                       'temperature': 0.07,
                       'interfaces': [-0.9, -0.8, -0.7, -0.6, -0.5,
                                      -0.4, -0.3, 1.0],
                       'periodic_boundary': [False],
                       'units': 'lj',
                       'generate-vel': {'seed': 0, 'momentum': False,
                                        'distribution': 'maxwell'},
                       'output': [{'type': 'traj', 'target': 'file',
                                   'format': 'gro',
                                   'when': {'every': 100},
                                   'filename': 'traj.gro',
                                   'header': 'MD FLUX simulation. Step: {}'}]}

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
    print(msg.format(system.calculate_temperature()))

# Set up force field:
double_well = DoubleWell(a=1.0, b=2.0, c=0.0)
forcefield = ForceField(potential=[double_well], desc='Double Well')
system.forcefield = forcefield
print('\nCreated:', system.forcefield)
# add order parameter:
orderparameter = OrderParameterPosition('position', 0, dim='x', periodic=False)
print('\nCreated:', orderparameter)
# add more info to the settings:
simulation_settings['beta'] = system.temperature['beta']
simulation_settings['npart'] = system.particles.npart
simulation_settings['dim'] = system.get_dim()

simulation_settings['system'] = system
simulation_settings['orderparameter'] = orderparameter

# create the simulation:
simulation_md = create_simulation(simulation_settings, system)
print('\nCreated:', simulation_md)
# create outputs for this simulation:
output = [task for task in create_output(system, simulation_settings)]
# store the settings we used, in case we need it later (e.g. for analysis).
settings_file = 'settings.py'
print('Storing the simulation settings in: {}'.format(settings_file))
store_settings_as_py(simulation_settings, settings_file, 'settings')

cross = []  # variable for storing the crossing output
print('\nStarting simulation!')
print(('=')*79)
for i, result in enumerate(simulation_md.run()):
    try:
        for cri in result['cross']:
            cross.append((cri[0], cri[1] + 1, -1 if cri[2] == '-' else 1))
    except KeyError:  # cross was not obtained at this step
        pass
    for task in output:
        task.output(result)
print(('=')*79)
print('Simulation finished, will do a simple flux analysis:')
analysis_settings = {'skipcross': 1000,
                     'maxblock': 1000,
                     'blockskip': 1,
                     'bins': 1000,
                     'ngrid': 1001}
results = {}
results['cross'] = analyse_flux(cross, analysis_settings, simulation_settings)
report_txt = generate_report('mdflux', results, 'txt')
print(''.join(report_txt))
