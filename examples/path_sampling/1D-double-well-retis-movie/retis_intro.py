# -*- coding: utf-8 -*-
# Copyright (c) 2016, PyRETIS Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""This is a simple RETIS example.

Here we do nothing fancy, we will just get to know
some of the objects in PyRETIS.

Have fun!
"""
from pyretis.core import System, create_box, Particles
from pyretis.initiation import initiate_path_simulation
from pyretis.inout.setup import (create_force_field, create_engine,
                                 create_orderparameter, create_simulation)
import numpy as np

# Let us define the simulation:
SETTINGS = {}
# Basic settings for the simulation:
SETTINGS['simulation'] = {'task': 'retis',
                          'steps': 10,
                          'interfaces': [-0.9, -0.8, -0.7,
                                         -0.6, -0.5, -0.4,
                                         -0.3, 1.0]}
# Basic settings for the system:
SETTINGS['system'] = {'units': 'reduced', 'temperature': 0.07}
# Basic settings for the Langevin integrator:
SETTINGS['engine'] = {'class': 'Langevin',
                      'gamma': 0.3,
                      'high_friction': False,
                      'seed': 0,
                      'timestep': 0.002}
# Potential parameters:
# The potential is: `V_\text{pot} = a x^4 - b (x - c)^2`
SETTINGS['potential'] = [{'a': 1.0, 'b': 2.0, 'c': 0.0,
                          'class': 'DoubleWell'}]
# Settings for the order parameter:
SETTINGS['orderparameter'] = {'class': 'OrderParameterPosition',
                              'dim': 'x', 'index': 0,
                              'periodic': False}
# TIS specific settings:
SETTINGS['tis'] = {'freq': 0.5,
                   'maxlength': 20000,
                   'aimless': True,
                   'allowmaxlength': False,
                   'sigma_v': -1,
                   'seed': 0,
                   'zero_momentum': False,
                   'rescale_energy': False}
SETTINGS['initial-path'] = {'method': 'kick'}
# RETIS specific settings:
SETTINGS['retis'] = {'swapfreq': 0.5,
                     'relative_shoots': None,
                     'nullmoves': True,
                     'swapsimul': True}


def set_up_system(settings):
    """Just a method to help set up the system.

    Parameters
    ----------
    settings : dict
        The settings required to set up the system.

    Returns
    -------
    sys : object like :py:class:`.System`
        A system object we can use in a simulation.
    """
    box = create_box(periodic=[False])
    sys = System(temperature=settings['system']['temperature'],
                 units=settings['system']['units'], box=box)
    sys.forcefield = create_force_field(settings)
    sys.order_function = create_orderparameter(settings)
    sys.particles = Particles(dim=1)
    sys.add_particle(np.array([-1.0]), mass=1, name='Ar', ptype=0)
    return sys


def print_step_results(ensembles, retis_result):
    """A function to print out RETIS results.

    Parameters
    ----------
    ensembles : list of enemble objects
        The different path ensembles we are simulating.
    retis_result : list of lists
        The results from a RETIS simulation step
    """
    for i, result in enumerate(retis_result):
        name = ensembles[i].ensemble_name
        print('Move in {}'.format(name))
        name_of_move = result[0]
        accepted = result[1]
        print('\tType: {}'.format(name_of_move))
        if name_of_move == 'swap':
            name2 = ensembles[result[-1]].ensemble_name
            print('\tSwapping: {} -> {}'.format(name2, name))
        elif name_of_move == 'tis':
            trial_path = result[2]
            if trial_path.generated[0] == 'sh':
                tis_move = 'shooting'
            elif trial_path.generated[0] == 'tr':
                tis_move = 'time-reversal'
            else:
                tis_move = 'unknown'
            print('\tTIS move: {}'.format(tis_move))
        print('\tResult: {}'.format(accepted))


def main():
    """Just run the simulation :-)"""
    print('# CREATING SYSTEM...')
    system = set_up_system(SETTINGS)
    print('# CREATING SIMULATION...')
    sim_args = {'system': system, 'engine': create_engine(SETTINGS)}
    simulation = create_simulation(SETTINGS, sim_args)
    print(simulation)
    print('# INITIATING TRAJECTORIES...')

    ensembles = simulation.path_ensembles
    for i, _ in enumerate(initiate_path_simulation(simulation, SETTINGS)):
        ensemble = ensembles[i]
        name = ensemble.ensemble_name
        print('Info about ensemble {}:'.format(name))
        print(ensemble)
        print('Info about the initial path:')
        print(ensemble.last_path)
        print('')
    # We can interact directly with points in trajectories,
    # here is a simple example
    path = ensembles[2].last_path
    first = True
    for i, point in enumerate(path.trajectory()):
        order = point['order'][0]
        pos = point['pos']
        vel = point['vel']
        if order > -0.8 and first:
            print('First crossing of -0.8 for [1^+]:')
            print('\tStep: {}'.format(i))
            print('\tlambda: {}'.format(order))
            print('\tPosition and velocity: {}  {}'.format(pos, vel))
            first = False

    # Let us do one more step:
    print('Running a single RETIS step...')
    result = simulation.step()
    for i, retis_result in enumerate(result['retis']):
        name = ensembles[i].ensemble_name
        print('Move in {}'.format(name))
        name_of_move = retis_result[0]
        accepted = retis_result[1]
        # `accepted` is equal to "ACC" if the move is accepted
        # otherwise it will be one of:
        # 'MCR': 'Momenta change rejection',
        # 'BWI': 'Backward trajectory end at wrong interface',
        # 'BTL': 'Backward trajectory too long (detailed balance condition)',
        # 'BTX': 'Backward trajectory too long (max-path exceeded)',
        # 'KOB': 'Kicked outside of boundaries',
        # 'FTL': 'Forward trajectory too long (detailed balance condition)',
        # 'FTX': 'Forward trajectory too long (max-path exceeded)',
        # 'NCR': 'No crossing with middle interface'
        print('\tType: {}'.format(name_of_move))
        if name_of_move == 'swap':
            # If this is the case, the result is on the form
            # [move, accpeted, swap-with] where swap-with is the ensemble
            # we are trying to swap with.
            name2 = ensembles[retis_result[-1]].ensemble_name
            print('\tSwapping: {} -> {}'.format(name2, name))
        elif name_of_move == 'tis':
            trial_path = retis_result[2]
            if trial_path.generated[0] == 'sh':
                tis_move = 'shooting'
            elif trial_path.generated[0] == 'tr':
                tis_move = 'time-reversal'
            else:
                tis_move = 'unknown'
            print('\tTIS move: {}'.format(tis_move))
        print('\tResult: {}'.format(accepted))

    # Run the rest of the simulation:
    while not simulation.is_finished():
        result = simulation.step()
        print('Simulation step: {}'.format(result['cycle']['step']))
        print_step_results(ensembles, result['retis'])
        print('')

if __name__ == '__main__':
    main()
