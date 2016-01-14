# -*- coding: utf-8 -*-
"""This module handles creation of simulations from settings.

The different simulations re defined as objects which inherits from
the base Simulation object defined in `pyretis.core.simulation.simulation`.

Important classes and functions:

- create_simulation: A function to create a simulation object from
  a dictionary of given settings.
"""
from __future__ import absolute_import
import logging
from pyretis.core.random_gen import RandomGenerator
from pyretis.core.integrators import create_integrator
from pyretis.inout.settings.common import check_settings
from pyretis.inout.settings.createorderparameter import create_orderparameter
from pyretis.core.simulation.mc_simulation import UmbrellaWindowSimulation
from pyretis.core.simulation.md_simulation import (SimulationNVE,
                                                   SimulationMDFlux)
from pyretis.core.simulation.path_simulation import SimulationTIS
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['create_simulation']

# Define known simulations and give them a 'family'
# the family is used to set up the simulations
_KNOWN_SIMULATIONS = {'md-nve': 'md',
                      'md-flux': 'md',
                      'umbrella': 'mc',
                      'umbrellawindow': 'mc',
                      'tis': 'path',
                      'retis': 'path'}


# Define required settings for known simulations:
_REQUIRED = {'umbrellawindow': ['umbrella', 'over', 'rgen', 'seed',
                                'maxdx', 'mincycle'],
             'md-nve': ['endcycle', 'integrator'],
             'md-flux': ['endcycle', 'integrator', 'interfaces',
                         'orderparameter'],
             'tis': ['endcycle', 'tis', 'integrator', 'interfaces']}


def create_simulation(settings, system):
    """Function to create simulations from settings and system.

    This function will set up some common simulation types.
    It is meant as a helper function to automate some very common set-up
    task. It will here check what kind of simulation we are to perform and
    then call the appropriate function for setting that type of simulation up.
    The rationale here is that different families of functions may handle the
    settings and especially "missing" settings differently.

    Parameters
    ----------
    settings : dict
        This dictionary contains the settings for the simulation.
    system : object like `System` from `pyretis.core.system`
        This is the system for which the simulation will run.

    Returns
    -------
    out : object like `Simulation` from `pyretis.core.simulation.simulation`.
        This object will correspond to the selected simulation type.
    """
    sim_type = settings['task'].lower()
    settings['task'] = sim_type  # just to be consistent
    family = None
    simulation = None
    try:
        family = _KNOWN_SIMULATIONS[sim_type]
    except KeyError:
        msg = 'Unknown simulation task {} requested'.format(sim_type)
        raise ValueError(msg)
    if family == 'md':
        simulation = create_md_simulation(settings, system, sim_type)
    elif family == 'mc':
        simulation = create_mc_simulation(settings, system, sim_type)
    elif family == 'path':
        simulation = create_path_simulation(settings, system, sim_type)
    else:
        msg = 'Unknown simulation task {}'.format(sim_type)
        raise ValueError(msg)
    msg = ['Created simulation:']
    msg += ['{}'.format(simulation)]
    msgtxt = '\n'.join(msg)
    logger.info(msgtxt)
    return simulation


def create_mc_simulation(settings, system, sim_type):
    """Create a MC simulation from the given settings.

    This is a helper function that will do some checks and set up one
    of the MC simulations defined in this module based on the given settings.

    Parameters
    ----------
    settings : dict
        This dictionary contains the settings for the simulation.
    system : object like `System` from `pyretis.core.system`
        This is the system for which the simulation will run.
    sim_type : string
        This defines the task we are to set up a simulation for. Note that
        the task is also given in `settings['task']`. It is given here since
        we typically call this function after checking the task.

    Returns
    -------
    out : object like `Simulation` from `pyretis.core.simulation`.
        This object will correspond to the selected task.

    Note
    ----
    We are duplicating code here - the checking of required settings is
    identical to the checking in other simulation creators, for instance
    the `create_path_simulation` in `pyretis.core.simulation.path_simulation`.
    This is just in case someone wants to add some magic that amends missing
    settings.
    """
    simulation = None
    required, not_found = check_settings(settings, _REQUIRED[sim_type])
    if sim_type == 'umbrellawindow':
        if 'seed' in not_found or 'rgen' in not_found:
            # one or both of these keywords were present
            # things are OK if there is no other missing
            not_found = set(not_found) - set(['seed', 'rgen'])
            required = len(not_found) == 0
    if not required:
        msg = 'Settings not found: {}'.format(not_found)
        logger.critical(msg)
        raise ValueError('Required settings not found!')
    if sim_type == 'umbrellawindow':
        try:
            rgen = settings['rgen']
        except KeyError:
            if 'seed' not in settings:
                msg = 'No random seed given. Will just use "0"'
                logger.warning(msg)
            rgen = RandomGenerator(seed=settings.get('seed', 0))
        simulation = UmbrellaWindowSimulation(system,
                                              settings['umbrella'],
                                              settings['over'],
                                              rgen,
                                              settings['maxdx'],
                                              mincycle=settings['mincycle'])
    else:
        msg = 'Unknown MC simulation: {}'.format(sim_type)
        raise ValueError(msg)
    return simulation


def create_md_simulation(settings, system, sim_type):
    """Create a MD simulation from the given settings.

    This is a helper function that will do some checks and set up one of the
    MD simulations defined in this module based on the given settings.

    Parameters
    ----------
    settings : dict
        This dictionary contains the settings for the simulation.
    system : object like `System` from `pyretis.core.system`
        This is the system for which the simulation will run.
    sim_type : string
        This defines the task we are to set up a simulation for. Note that
        the task is also given in `settings['task']`. It is given here since
        we typically call this function after checking the task.

    Returns
    -------
    out : object like `Simulation` from `pyretis.core.simulation`.
        This object will correspond to the selected task.

    Note
    ----
    We are duplicating code here - the checking of required settings is
    identical to the checking in other simulation creators, for instance
    the `create_path_simulation`. This is just in case someone wants to
    add some magic that amends missing settings.
    """
    simulation = None
    required, not_found = check_settings(settings, _REQUIRED[sim_type])
    if not required:
        msg = '{} settings not found: {}'.format(sim_type, not_found)
        logger.critical(msg)
        raise ValueError('Please update settings!')
    if sim_type == 'md-nve':
        intg = create_integrator(settings.get('integrator'), sim_type)
        simulation = SimulationNVE(system, intg,
                                   endcycle=settings['endcycle'],
                                   startcycle=settings.get('startcycle', 0))
    elif sim_type == 'md-flux':
        intg = create_integrator(settings.get('integrator'), sim_type)
        orderp = create_orderparameter(settings)
        simulation = SimulationMDFlux(system, intg, settings['interfaces'],
                                      orderp, endcycle=settings['endcycle'],
                                      startcycle=settings.get('startcycle', 0))
    else:
        msg = 'Unknown MD simulation: {}'.format(sim_type)
        raise ValueError(msg)
    return simulation


def create_path_simulation(settings, system, sim_type):
    """Create a path simulation from the given settings.

    This is a helper function that will do some checks and set up one of the
    path simulations defined in this module based on the given settings.

    Parameters
    ----------
    settings : dict
        This dictionary contains the settings for the simulation.
    system : object like `System` from `pyretis.core.system`
        This is the system for which the simulation will run.
    sim_type : string
        This defines the task we are to set up a simulation for. Note that
        the task is also given in `settings['task']`. It is given here since
        we typically call this function after checking the task.

    Returns
    -------
    out : object like `Simulation` from `pyretis.core.simulation`.
        This object will correspond to the selected task.

    Note
    ----
    We are duplicating code here - the checking of required settings is
    identical to the checking in other simulation creators, for instance
    the `create_md_simulation` in `pyretis.core.simulation.md_simulation`.
    This is just in case someone wants to add some magic that amends missing
    settings.
    """
    simulation = None
    required, not_found = check_settings(settings, _REQUIRED[sim_type])
    if not required:
        msg = '{} settings not found: {}'.format(sim_type, not_found)
        logger.critical(msg)
        raise ValueError('Please update settings!')
    if sim_type == 'tis':
        intg = create_integrator(settings['integrator'], sim_type)
        orderp = create_orderparameter(settings)
        simulation = SimulationTIS(system, intg, orderp, settings,
                                   endcycle=settings['endcycle'],
                                   startcycle=settings.get('startcycle', 0))
    else:
        msg = 'Unknown path simulation: {}'.format(sim_type)
        raise ValueError(msg)
    return simulation
