# -*- coding: utf-8 -*-
"""
This is a convenience script for creating TIS simulations.
"""
# pylint: disable=C0103
from __future__ import print_function
import os
import multiprocessing
import numpy as np
from pyretis.core.path import create_path_ensembles
from pyretis.core import Box, System
from pyretis.inout.settings import create_simulation
from pyretis.forcefield import ForceField
from pyretis.forcefield.potentials import DoubleWell
from pyretis.inout import create_output


simulation_settings = {'task': 'TIS',
                       'integrator': {'name': 'Langevin', 'timestep': 0.002,
                                      'gamma': 0.3, 'seed': 10,
                                      'high-friction': False},
                       'endcycle': 20000,
                       'temperature': 0.07,
                       'interfaces': [-0.9, -0.8, -0.7, -0.6,
                                      -0.5, -0.4, -0.3, 1.0],
                       'periodic_boundary': [False],
                       'units': 'lj',
                       'generate-vel': {'seed': 0, 'momentum': False,
                                        'distribution': 'maxwell'},
                       'orderparameter': {'class': 'OrderParameterPosition',
                                          'args': ['position', 0],
                                          'kwargs': {'dim': 'x',
                                                     'periodic': False}},
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


def set_up_tis_simulation(settings):
    """Method to do set-up for the TIS simulations"""
    box = Box(periodic=settings['periodic_boundary'])
    system = System(temperature=settings['temperature'],
                    units=settings['units'],
                    box=box)
    system.add_particle(name='A', pos=np.array([-1.0]))
    msg = 'Added one particle {} at position: {}'
    if 'generate-vel' in settings:
        system.generate_velocities(**settings['generate-vel'])
        msg = 'Generated temperatures with average: {}'
    # Set up force field:
    double_well = DoubleWell(a=1.0, b=2.0, c=0.0)
    forcefield = ForceField(potential=[double_well], desc='Double Well')
    system.forcefield = forcefield
    # add order parameter:
    simulation_tis = create_simulation(settings, system)
    return simulation_tis


def run_simulation(simulation, settings):
    ensemble = simulation.path_ensemble.ensemble
    interfaces = simulation.path_ensemble.interfaces
    output = [task for task in create_output(simulation.system, settings)]
    print('Running:', ensemble)
    for result in simulation.run(output=output):
        step = result['cycle']
        #result['traj'] = simulation.system
        #for task in output:
        #    task.output(result)
    print('Done with:', ensemble)
    return True


if __name__ == '__main__':
    print('Simulation type: {}'.format(simulation_settings['task']))
    print('Setting up TIS simulations:')
    interfaces = simulation_settings['interfaces']
    ensembles, detect = create_path_ensembles(interfaces, include_zero=False)

    simulations = []

    for i, path_ensemble in enumerate(ensembles):
        ensemble = '{:03d}'.format(i+1)
        print('\nPath ensemble: {} (no. {})'.format(path_ensemble.ensemble,
                                                    ensemble))
        # create a home for the simulation:
        if not os.path.exists(ensemble):
            print('* Creating folder "{}"'.format(ensemble))
            os.makedirs(ensemble)
        else:
            print('* Folder "{}" already exist, will use it.'.format(ensemble))
        path_file = os.path.join(ensemble, 'path.dat')
        ensemble_file = os.path.join(ensemble, 'pathensemble.dat')
        settings = {'task': 'TIS',
                    'integrator': {'name': 'Langevin', 'timestep': 0.002,
                                   'gamma': 0.3, 'seed': 10,
                                   'high-friction': False},
                    'endcycle': 20000,
                    'temperature': 0.07,
                    'periodic_boundary': [False],
                    'units': 'lj',
                    'generate-vel': {'seed': 0, 'momentum': False,
                                     'distribution': 'maxwell'},
                    'orderparameter': {'class': 'OrderParameterPosition',
                                       'args': ['position', 0],
                                       'kwargs': {'dim': 'x',
                                                  'periodic': False}},
                    'tis': {'start_cond': 'L',
                            'freq': 0.5,
                            'maxlength': 10000,
                            'aimless': True,
                            'allowmaxlength': False,
                            'sigma_v': -1,
                            'seed': 10,
                            'initial_path': 'kick'}}
        settings['path-ensemble'] = path_ensemble
        settings['interfaces'] = path_ensemble.interfaces
        settings['output'] = [{'type': 'pathensemble',
                               'target': 'file',
                               'filename': ensemble_file, 'use': True}]
        simulation_tis = set_up_tis_simulation(settings)
        proc = multiprocessing.Process(target=run_simulation,
                                       args=(simulation_tis, settings))
        simulations.append(proc)
        proc.start()
    #    simulations.append(simulation_tis)
    #pool = multiprocessing.Pool(processes=4)              # start 4 worker processes
    #result =  pool.map(run_simulation, simulations)
    #for proc in simulations:
    #    proc.join()
    #    print('name: {}, exit-code: {}'.format(proc.name, proc.exitcode))
    #print('Hello')
    #for sim in simulations:
    #    sim.join()
    #    print('{} exitcode = {}'.format(sim.name, sim.exitcode))


#    for sim in simulations:
#        print(sim.output_task[0].writer)
#        print(sim.output_task[0].writer.get_mode())
#    pool = multiprocessing.Pool(processes=3)
#results = pool.map_async(run_simulation, simulations)
#results = pool.map(run_simulation, simulations)
#    results = [pool.apply(run_simulation, args=(sim,)) for sim in simulations]
#print(results)
