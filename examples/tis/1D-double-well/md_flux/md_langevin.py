# -*- coding: utf-8 -*-
"""
This is an example on how to perform a simple MD simulation for determining
the initial flux for a TIS rate calculation.
"""
# pylint: disable=C0103
from __future__ import print_function
import numpy as np
# pyretis imports:
from pyretis.core import Box, System
from pyretis.core.simulation import create_simulation
from pyretis.forcefield import ForceField
from pyretis.forcefield.potentials import DoubleWell
from pyretis.core.orderparameter import OrderParameterPosition
from pyretis.analysis import analyse_flux
from pyretis.inout import generate_report_md


print('MD flux simulation!')
simulation_settings = {'type': 'MDFlux',
                       'integrator': {'name': 'Langevin', 'timestep': 0.002,
                                      'gamma': 0.3, 'seed': 10,
                                      'high-friction': False},
                       'endcycle': 500000,
                       'temperature': 0.2,
                       'interfaces': [-1.0, 0.0, 1.0],
                       'periodic_boundary': [False],
                       'units': 'lj',
                       'generate-vel': {'seed': 0, 'momentum': False,
                                        'distribution': 'maxwell'}}

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
simulation_settings['system'] = system
simulation_settings['orderparameter'] = orderparameter
simulation_settings['beta'] = system.temperature['beta']
simulation_settings['npart'] = system.particles.npart

# create the simulation:
simulation_md = create_simulation(simulation_settings, system)
print('\nCreated:', simulation_md)
# Variable for storing calculated crossing output:
cross = []
print('\nStarting simulation!')
print(('=')*80)
# run simulation :-)
for i, result in enumerate(simulation_md.run()):
    try:
        for cri in result['cross']:
            cross.append((cri[0], cri[1] + 1, -1 if cri[2] == '-' else 1))
    except KeyError:  # cross was not obtained at this step
        pass

analysis_settings = {'skipcross': 1000,
                     'maxblock': 1000,
                     'blockskip': 1,
                     'bins': 1000,
                     'ngrid': 1001}
print(('=')*80)
print('Simulation finished, will do a simple flux analysis:')
results = {}
results['flux'] = analyse_flux(cross, analysis_settings, simulation_settings)
report_txt = generate_report_md(results, output='txt')[0]
print(''.join(report_txt))
