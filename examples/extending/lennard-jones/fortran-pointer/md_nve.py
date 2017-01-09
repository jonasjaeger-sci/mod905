# -*- coding: utf-8 -*-
"""Example of running a MD NVE simulation.

This system considered is a simple Lennard-Jones fluid.
"""
# pylint: disable=C0103
from pyretis.core.units import create_conversion_factors
from pyretis.inout.settings import (create_simulation, create_system,
									create_engine, create_force_field,
                                    create_output_tasks)
from pyretis.inout.writers import FileIO, ThermoTable
settings = {}
settings['simulation'] = {'task': 'md-nve', 'steps': 1000}
settings['system'] = {'units': 'lj', 'temperature': 2.0,
                      'dimensions': 3}
settings['engine'] = {'class': 'velocityverlet',
                      'timestep': 0.002}
settings['output'] = {'backup': False,
                      'write_vel': False,
                      'energy-file': 1,
                      'energy-screen': 10,
                      'trajectory-file': 10}
settings['potential'] = [{'class': 'PairLennardJonesCutFp',
                          'module': 'ljpotentialfp.py',
                          'dim': 3,
                          'shift': True,
                          'parameter': {0: {'sigma': 1,
                                            'epsilon': 1,
                                            'factor': 2.5}}}]
settings['particles'] = {'position': {'generate': 'fcc',
                                      'repeat': [3, 3, 3],
                                      'density': 0.9},
                         'velocity': {'generate': 'maxwell',
                                      'momentum': True,
                                      'seed': 0}}
create_conversion_factors(settings['system']['units'])
print('# Creating system from settings.')
ljsystem = create_system(settings)
ljsystem.forcefield = create_force_field(settings)
print('# Creating simulation from settings.')
sim_args = {'system': ljsystem, 'engine': create_engine(settings)}
simulation_nve = create_simulation(settings, sim_args)
print('# Creating output tasks from settings.')
output_tasks = [task for task in create_output_tasks(settings)]
msg = 'Created fcc grid with {} atoms.'
print(msg.format(ljsystem.particles.npart))
# set up extra output:
table = ThermoTable()
thermo_file = FileIO('thermo.txt', header=table.header)
store_results = []
# run the simulation :-)
for result in simulation_nve.run():
    stepno = result['cycle']['stepno']
    for lines in table.generate_output(stepno, result['thermo']):
        thermo_file.write(lines)
    result['thermo']['stepno'] = stepno
    store_results.append(result['thermo'])
    for task in output_tasks:
        task.output(result)
