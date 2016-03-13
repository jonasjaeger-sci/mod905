# -*- coding: utf-8 -*-
"""Example of running a MD NVE simulation.

This system considered is a simple Lennard-Jones fluid.
"""
# pylint: disable=C0103
from __future__ import print_function
from pyretis.core.units import create_conversion_factors
from pyretis.inout.settings import (create_simulation, create_system,
                                    create_force_field, create_output)
from pyretis.inout.writers import FileIO, ThermoTable
# simulation settings:
settings = {'task': 'md-nve',
            'units': 'lj',
            'integrator': {'class': 'velocityverlet', 'timestep': 0.002},
            'endcycle': 100,
            'output-modify': [{'name': 'traj', 'when': {'every': 10},
                               'filename': 'traj.gro'}],
            'particles-velocity': {'generate': 'maxwell', 'momentum': True,
                                   'seed': 0},
            'temperature': 2.0,
            'potentials': [{'class': 'PairLennardJonesCutFp',
                            'kwargs': {'dim': 3, 'shift': True},
                            'module': 'ljpotentialfp.py'}],
            'potential-parameters': [{0: {'sigma': 1.0, 'epsilon': 1.0,
                                          'rcut': 2.5}}],
            'particles-position': {'generate': 'fcc', 'repeat': [10, 10, 10],
                                   'density': 0.9}}
# Set up simulation:
create_conversion_factors(settings['units'])
print('# Creating system from settings.')
ljsystem = create_system(settings)
ljsystem.forcefield = create_force_field(settings)
print('# Creating simulation from settings.')
simulation_nve = create_simulation(settings, ljsystem)
print('# Creating output tasks from settings.')
output_tasks = [task for task in create_output(settings)]
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
