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
from pyretis.core.simulation.path_simulation import SimulationTIS
from pyretis.core.pathensemble import create_path_ensembles
from pyretis.inout.common import make_dirs
from pyretis.inout.settings.common import (create_integrator,
                                           create_orderparameter,
                                           check_settings)
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
        The object representing the simulation we would like to run.
    """
    integ = create_integrator(settings)
    return SimulationNVE(system, integ, steps=settings['steps'],
                         startcycle=settings.get('startcycle', 0))


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
        The object representing the simulation we would like to run.
    """
    integ = create_integrator(settings)
    orderp = create_orderparameter(settings)
    return SimulationMDFlux(system, integ, orderp, settings['interfaces'],
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
    out : object like `Simulation`
        The object representing the simulation we would like to run.
    """
    try:
        rgen = settings['rgen']
    except KeyError:
        msg = 'No random generator specified, will initiate one.'
        logger.info(msg)
        if 'seed' not in settings:
            msg = 'No random seed given. Will just use "0"'
            logger.warning(msg)
        rgen = RandomGenerator(seed=settings.get('seed', 0))
    return UmbrellaWindowSimulation(system, settings['umbrella'],
                                    settings['over'], rgen,
                                    settings['maxdx'],
                                    mincycle=settings['mincycle'],
                                    startcycle=settings.get('startcycle', 0))


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
        The object representing the simulation we would like to run.
    """
    integ = create_integrator(settings)
    orderp = create_orderparameter(settings)
    return SimulationTIS(system, integ, orderp,
                         settings['path-ensemble'],
                         settings['tis'],
                         steps=settings['steps'],
                         startcycle=settings.get('startcycle', 0))


def create_tis_simulations(settings, system):
    """This will set up and create a series of TIS simulations.

    This method will for each interface set up a single TIS simulation.
    These simulations can then be run in series, parallel or written
    out as settings files that pyretis can run.

    Parameters
    ----------
    settings : dict
        The settings needed to set up the simulation.
    system : object like `System`
        The system we are going to simulate.

    Returns
    -------
    out : object like `Simulation`
        The object representing the simulation we would like to run.
    """
    ensembles, detect = create_path_ensembles(settings['interfaces'],
                                              include_zero=False)
    for i, (path_ensemble, idetect) in enumerate(zip(ensembles, detect)):
        ensemble = '{:03d}'.format(i+1)
        local_settings = {}
        for key in settings:  # this common for all simulations:
            local_settings[key] = settings[key]
        # things we change for each simulation
        local_settings['path-ensemble'] = path_ensemble
        local_settings['ensemble'] = path_ensemble.ensemble
        local_settings['interfaces'] = path_ensemble.interfaces
        local_settings['output-dir'] = ensemble
        local_settings['task'] = 'tis-single'
        local_settings['detect'] = idetect
        tis_simulation = create_tis_single_simulation(local_settings, system)
        msg_dir = make_dirs(ensemble)
        msgtxt = ('Creating directories:\n'
                  '* {}'.format(msg_dir))
        logger.info(msgtxt)
        return tis_simulation
        #print(local_settings)


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
    sim_type = settings['task'].lower()
    settings['task'] = sim_type  # just to be consistent
    sim_map = {'md-nve': {'create': create_nve_simulation,
                          'required': ('steps', 'integrator')},
               'md-flux': {'create': create_mdflux_simulation,
                           'required': ('steps', 'integrator', 'interfaces',
                                        'orderparameter')},
               'umbrellawindow': {'create': create_umbrellaw_simulation,
                                  'required': ('umbrella', 'over', 'maxdx',
                                               'mincycle')},
               'tis': {'create': create_tis_simulations,
                       'required': ('steps', 'tis', 'integrator',
                                    'interfaces')}}

    if sim_type not in sim_map:
        msgtxt = 'Unknown simulation task {}'.format(sim_type)
        logger.error(msgtxt)
        raise ValueError(msgtxt)
    else:
        sim = sim_map[sim_type]
        settings_ok, not_found = check_settings(settings, sim['required'])
        if not settings_ok:
            msgtxt = '{} settings not found: {}'.format(sim_type, not_found)
            logger.error(msgtxt)
            raise ValueError('Required simulation setting not found!')
        simulation = sim['create'](settings, system)
        msg = ['Created simulation:']
        msg += ['{}'.format(simulation)]
        msgtxt = '\n'.join(msg)
        logger.info(msgtxt)
        return simulation
