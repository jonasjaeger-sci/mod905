# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""This module handles creation of simulations from settings.

The different simulations are defined as objects which inherits from the
base Simulation object defined in `pyretis.core.simulation.simulation`.
Here, we are treat each simulation with a special case since they are
indeed special :-)

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

create_simulation
    Method for creating a simulation object from settings.
"""
from __future__ import absolute_import
import logging
from pyretis.core.random_gen import RandomGenerator
from pyretis.core.simulation.md_simulation import (SimulationNVE,
                                                   SimulationMDFlux)
from pyretis.core.simulation.mc_simulation import UmbrellaWindowSimulation
from pyretis.core.simulation.path_simulation import (SimulationSingleTIS,
                                                     SimulationRETIS)
from pyretis.core.pathensemble import (PathEnsemble,
                                       PATH_DIR_FMT,
                                       create_path_ensembles)
from pyretis.inout.settings.common import create_integrator
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['create_simulation']


def create_nve_simulation(settings, system):
    """This will set up and create a NVE simulation.

    Parameters
    ----------
    settings : dict
        The settings needed to set up the simulation.
    system : object like `System`
        The system we are going to simulate.

    Returns
    -------
    out : object like `Simulation`
        The object representing the simulation to run.
    """
    if 'integrator' not in settings:
        msgtxt = 'No integrator settings found!'
        logger.critical(msgtxt)
        raise ValueError(msgtxt)
    integ = create_integrator(settings)
    if integ is None:
        msgtxt = 'No integrator created!'
        logger.critical(msgtxt)
        raise ValueError(msgtxt)
    sim = settings['simulation']
    for key in ('steps',):
        if key not in sim:
            msgtxt = 'Simulation setting "{}" is missing!'.format(key)
            logger.critical(msgtxt)
            raise ValueError(msgtxt)
    return SimulationNVE(system, integ, steps=sim['steps'],
                         startcycle=sim.get('startcycle', 0))


def create_mdflux_simulation(settings, system):
    """This will set up and create a MD FLUX simulation.

    Parameters
    ----------
    settings : dict
        The settings needed to set up the simulation.
    system : object like `System`
        The system we are going to simulate.

    Returns
    -------
    out : object like `Simulation`
        The object representing the simulation to run.
    """
    integ = create_integrator(settings)
    if integ is None:
        msgtxt = 'No integrator created!'
        logger.critical(msgtxt)
        raise ValueError(msgtxt)
    return SimulationMDFlux(system, integ, settings['interfaces'],
                            steps=settings['steps'],
                            startcycle=settings.get('startcycle', 0))


def create_umbrellaw_simulation(settings, system):
    """This will set up and create a Umbrella Window simulation.

    Parameters
    ----------
    settings : dict
        The settings needed to set up the simulation.
    system : object like `System`
        The system we are going to simulate.

    Returns
    -------
    out : list of object(s) like `Simulation`
        The object(s) representing the simulation(s) to run.
    """
    sim_sett = settings['simulation']
    try:
        rgen = sim_sett['rgen']
    except KeyError:
        msg = 'No random generator specified, will initiate one.'
        logger.info(msg)
        if 'seed' not in sim_sett:
            msg = 'No random seed given. Will just use "0"'
            logger.warning(msg)
        rgen = RandomGenerator(seed=sim_sett.get('seed', 0))
    return UmbrellaWindowSimulation(system, sim_sett['umbrella'],
                                    sim_sett['over'], rgen,
                                    sim_sett['maxdx'],
                                    mincycle=sim_sett['mincycle'],
                                    startcycle=sim_sett.get('startcycle', 0))


def create_tis_single_simulation(settings, system):
    """This will set up and create a single TIS simulation.

    Parameters
    ----------
    settings : dict
        The settings needed to set up the simulation.
    system : object like `System`
        The system we are going to simulate.

    Returns
    -------
    out : object like `Simulation`
        The object representing the simulation to run.
    """
    integ = create_integrator(settings)
    if integ is None:
        msgtxt = 'No integrator created!'
        logger.critical(msgtxt)
        raise ValueError(msgtxt)
    if 'path-ensemble' in settings:
        path_ensemble = settings['path-ensemble']
    else:
        path_ensemble = create_path_ensemble(settings)
    return SimulationSingleTIS(system, integ,
                               path_ensemble,
                               settings['tis'],
                               steps=settings['steps'],
                               startcycle=settings.get('startcycle', 0))


def create_retis_simulation(settings, system):
    """This will set up and create a RETIS simulation.

    Parameters
    ----------
    settings : dict
        The settings needed to set up the simulation.
    system : object like `System`
        The system we are going to simulate.

    Returns
    -------
    out : object like `Simulation`
        The object representing the simulation to run.
    """
    integ = create_integrator(settings)
    if integ is None:
        msgtxt = 'No integrator created!'
        logger.critical(msgtxt)
        raise ValueError(msgtxt)
    path_ensembles, _ = create_path_ensembles(settings['interfaces'],
                                              include_zero=True)
    return SimulationRETIS(system, integ,
                           path_ensembles,
                           settings['tis'],
                           settings['retis'],
                           steps=settings['steps'],
                           startcycle=settings.get('startcycle', 0))


def create_path_ensemble(settings):
    """Create a new path ensemble from simulation settings.

    Parameters
    ----------
    settings : dict
        This dict contains the settings needed to create the path
        ensemble.

    Returns
    -------
    out : object like `PathEnsemble`.
        An object that can be used as a path ensemble in simulations.
    """
    interfaces = settings['interfaces']
    if len(interfaces) != 3:
        msgtxt = ('Wrong number of interfaces given. Expected 3 '
                  'got {}'.format(len(interfaces)))
        logger.error(msgtxt)
        raise ValueError(msgtxt)
    if 'detect' not in settings:
        detect = interfaces[-1]
        msgtxt = ('Detect-interface not specified, '
                  'using "product" interface: {}'.format(detect))
        logger.warning(msgtxt)
    else:
        detect = settings['detect']
    if 'ensemble' not in settings:
        ensemble_name = 1
        msgtxt = ('Ensemble name not specified, '
                  'using default ensemble "{}"'.format(ensemble_name))
        logger.warning(msgtxt)
    else:
        ensemble_name = int(settings['ensemble'])
    return PathEnsemble(ensemble_name, interfaces, detect=detect)


def create_tis_simulations(settings):
    """This will set up and create a series of TIS simulations.

    This method will for each interface set up a single TIS simulation.
    These simulations can then be run in series, parallel or written
    out as settings files that pyretis can run.

    Parameters
    ----------
    settings : dict
        The settings needed to set up the simulation.

    Returns
    -------
    sim_settings : list of dicts
        `sim_settings[i]` is a dictionary with settings for running
        simulation i. Note that the actual simulation object is not
        created here.
    """
    sim_settings = []
    interfaces = settings['interfaces']
    reactant = interfaces[0]
    product = interfaces[-1]
    for i, middle in enumerate(interfaces[:-1]):
        local_settings = {}
        for key in settings:  # this common for all simulations:
            local_settings[key] = settings[key]
        local_settings['task'] = 'tis-single'
        local_settings['ensemble'] = i + 1
        local_settings['interfaces'] = [reactant, middle, product]
        local_settings['output-dir'] = PATH_DIR_FMT.format(i + 1)
        try:
            local_settings['detect'] = interfaces[i + 1]
        except IndexError:
            local_settings['detect'] = product
        sim_settings.append(local_settings)
    return sim_settings


def create_simulation(settings, system):
    """Function to create simulations from settings and system.

    This function will set up some common simulation types.
    It is meant as a helper function to automate some very common set-up
    task. It will here check what kind of simulation we are to perform
    and then call the appropriate function for setting that type of
    simulation up.

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
    sim_type = settings['simulation']['task'].lower()
    sim_map = {'md-nve': {'create': create_nve_simulation,
                          'single': True},
               'md-flux': {'create': create_mdflux_simulation,
                           'single': True,
                           'required': ('steps', 'integrator', 'interfaces')},
               'umbrellawindow': {'create': create_umbrellaw_simulation,
                                  'single': True,
                                  'required': ('umbrella', 'over', 'maxdx',
                                               'mincycle')},
               'tis': {'create': create_tis_simulations,
                       'single': False,
                       'required': ('steps', 'tis', 'integrator',
                                    'interfaces')},
               'tis-single': {'create': create_tis_single_simulation,
                              'single': True,
                              'required': ('steps', 'tis', 'integrator',
                                           'interfaces')},
               'retis': {'create': create_retis_simulation,
                         'single': True,
                         'required': ('steps', 'tis', 'integrator',
                                      'interfaces', 'retis')}}

    if sim_type not in sim_map:
        msgtxt = 'Unknown simulation task {}'.format(sim_type)
        logger.error(msgtxt)
        raise ValueError(msgtxt)
    else:
        sim = sim_map[sim_type]
        if sim['single']:
            simulation = sim['create'](settings, system)
            msgtxt = ('Created simulation:\n'
                      '{}'.format(simulation))
            logger.info(msgtxt)
        else:
            simulation = sim['create'](settings)
        return simulation
