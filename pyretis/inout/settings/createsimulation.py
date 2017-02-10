# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""This module handles creation of simulations from settings.

The different simulations are defined as objects which inherits from the
base :py:class:`.Simulation` class defined in
:py:mod:`pyretis.simulation.simulation`.
Here, we are treat each simulation with a special case since they are
indeed special :-)

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

create_simulation (:py:func:`.create_simulation`)
    Method for creating a simulation object from settings.
"""
from __future__ import absolute_import
import logging
from pyretis.core.random_gen import create_random_generator
from pyretis.simulation.md_simulation import (SimulationNVE,
                                              SimulationMDFlux)
from pyretis.simulation.mc_simulation import UmbrellaWindowSimulation
from pyretis.simulation.path_simulation import (SimulationSingleTIS,
                                                SimulationRETIS)
from pyretis.core.pathensemble import (get_path_ensemble_class,
                                       PATH_DIR_FMT)
from pyretis.inout.settings.common import create_orderparameter
from pyretis.inout.settings.settings import copy_settings, is_single_tis
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['create_simulation']


def create_path_ensemble(settings, ensemble_type):
    """Create a new path ensemble from simulation settings.

    Parameters
    ----------
    settings : dict
        This dict contains the settings needed to create the path
        ensemble.
    ensemble_type : string
        The kind of ensemble we are creating. This is typically defined
        by the engine.

    Returns
    -------
    out : object like :py:class:`.PathEnsemble`
        An object that can be used as a path ensemble in simulations.
    """
    interfaces = settings['simulation']['interfaces']
    exe_dir = settings['simulation'].get('exe-path', '')
    if len(interfaces) != 3:
        msgtxt = ('Wrong number of interfaces given. Expected 3 '
                  'got {}'.format(len(interfaces)))
        logger.error(msgtxt)
        raise ValueError(msgtxt)
    if 'detect' not in settings['simulation']:
        detect = interfaces[-1]
        msgtxt = ('Detect-interface not specified, '
                  'using "product" interface: {}'.format(detect))
        logger.warning(msgtxt)
    else:
        detect = settings['simulation']['detect']
    if 'ensemble' not in settings['simulation']:
        ensemble_name = 1
        msgtxt = ('Ensemble name not specified, '
                  'using default ensemble "{}"'.format(ensemble_name))
        logger.warning(msgtxt)
    else:
        ensemble_name = int(settings['simulation']['ensemble'])
    klass = get_path_ensemble_class(ensemble_type)
    return klass(ensemble_name, interfaces,
                 detect=detect, exe_dir=exe_dir)


def create_path_ensembles(interfaces, ensemble_type, include_zero=False,
                          exe_dir=None):
    """Create a list of `PathEnsemble` objects given a list of interfaces.

    This function will create and return a set of objects representing
    path ensembles for a given set of interfaces. This is useful when
    setting up simulations like RETIS. Here we assume that the given
    interfaces define the path ensembles as follows:
    ``[0^-] | [0^+] | [1^+] | ... | [(n-1)^+] | state B``, where ``|``
    is the specified interface locations in the input `interfaces`.
    We assume that the reactant is to the left of `interfaces[0]` and
    that the product is to the right of `interfaces[-1]`. Given ``n``
    interfaces we generate ``n`` or ``n-1`` path ensembles, the former
    if we include the [0^-] ensemble.

    Parameters
    ----------
    interfaces : list of floats
        `interfaces[i]` separates the [(i-1)^+] and [i^+] interfaces.
    ensemble_type : string
        The kind of ensemble we are creating. This is typically defined
        by the engine.
    include_zero : boolean, optional
        If `include_zero` is True, we include path ensemble [0^-].
    exe_dir : string, optional
        This string can be used to tell the path ensemble object
        where it is executed.

    Returns
    -------
    ensembles : list of objects like :py:class:`.PathEnsemble`
        The generated (empty) path ensemble objects.
    detect : list of floats
        These are interfaces that can be used for an analysis, i.e. for
        detection and matching of probabilities.
    """
    detect = []
    ensembles = []
    reactant = interfaces[0]
    product = interfaces[-1]
    klass = get_path_ensemble_class(ensemble_type)
    if include_zero:
        interface = [-float('inf'), reactant, reactant]
        path_ensemble = klass(0, interface, detect=None, exe_dir=exe_dir)
        ensembles.append(path_ensemble)
    for i, middle in enumerate(interfaces[:-1]):
        interface = [reactant, middle, product]
        try:
            detect.append(interfaces[i+1])
        except IndexError:
            detect.append(product)
        path_ensemble = klass(i + 1, interface, detect=detect[-1],
                              exe_dir=exe_dir)
        ensembles.append(path_ensemble)
    return ensembles, detect


def create_nve_simulation(settings, system, engine):
    """This will set up and create a NVE simulation.

    Parameters
    ----------
    settings : dict
        The settings needed to set up the simulation.
    system : object like :py:class:`.System`
        The system we are going to simulate.
    engine : object like :py:class:`.EngineBase`
        The engine to use for the simulation.

    Returns
    -------
    out : object like :py:class:`.SimulationNVE`
        The object representing the simulation to run.
    """
    sim = settings['simulation']
    for key in ('steps',):
        if key not in sim:
            msgtxt = 'Simulation setting "{}" is missing!'.format(key)
            logger.critical(msgtxt)
            raise ValueError(msgtxt)
    return SimulationNVE(system, engine, steps=sim['steps'],
                         startcycle=sim.get('startcycle', 0))


def create_mdflux_simulation(settings, system, engine):
    """This will set up and create a MD FLUX simulation.

    Parameters
    ----------
    settings : dict
        The settings needed to set up the simulation.
    system : object like :py:class:`.System`
        The system we are going to simulate.
    engine : object like :py:class:`.EngineBase`
        The engine to use for the simulation.

    Returns
    -------
    out : object like :py:class:`.SimulationMDFlux`
        The object representing the simulation to run.
    """
    order_function = create_orderparameter(settings)
    if order_function is None:
        msgtxt = 'No order parameter created!'
        logger.critical(msgtxt)
        raise ValueError(msgtxt)
    sim = settings['simulation']
    return SimulationMDFlux(system, order_function, engine,
                            sim['interfaces'],
                            steps=sim['steps'],
                            startcycle=sim.get('startcycle', 0))


def create_umbrellaw_simulation(settings, system):
    """This will set up and create a Umbrella Window simulation.

    Parameters
    ----------
    settings : dict
        The settings needed to set up the simulation.
    system : object like :py:class:`.System`
        The system we are going to simulate.

    Returns
    -------
    out : list of object(s) like :py:class:`.UmbrellaWindowSimulation`
        The object(s) representing the simulation(s) to run.
    """
    sim = settings['simulation']
    rgen = create_random_generator(sim)
    return UmbrellaWindowSimulation(system, sim['umbrella'],
                                    sim['over'], rgen,
                                    sim['maxdx'],
                                    mincycle=sim['mincycle'],
                                    startcycle=sim.get('startcycle', 0))


def create_tis_simulations(settings, system, engine):
    """This will set up and create a series of TIS simulations.

    This method will for each interface set up a single TIS simulation.
    These simulations can then be run in series, parallel or written
    out as settings files that pyretis can run.

    Parameters
    ----------
    settings : dict
        The settings needed to set up the simulation.
    system : object like :py:class:`.System`
        The system we are going to simulate.
    engine : object like :py:class:`.EngineBase`
        The engine to use for the simulation.

    Returns
    -------
    sim_settings : list of dicts
        `sim_settings[i]` is a dictionary with settings for running
        simulation i. Note that the actual simulation object is not
        created here.
    """
    sim_settings = []
    interfaces = settings['simulation']['interfaces']
    reactant = interfaces[0]
    product = interfaces[-1]
    if is_single_tis(settings):
        return _create_tis_single_simulation(settings, system, engine)
    else:
        for i, middle in enumerate(interfaces[:-1]):
            lsetting = copy_settings(settings)
            lsetting['simulation']['interfaces'] = [reactant, middle, product]
            lsetting['simulation']['ensemble'] = i + 1
            lsetting['output']['directory'] = PATH_DIR_FMT.format(i + 1)
            try:
                lsetting['simulation']['detect'] = interfaces[i + 1]
            except IndexError:
                lsetting['simulation']['detect'] = product
            sim_settings.append(lsetting)
        return sim_settings


def _create_tis_single_simulation(settings, system, engine):
    """This will set up and create a single TIS simulation.

    Parameters
    ----------
    settings : dict
        The settings needed to set up the simulation.
    system : object like :py:class:`.System`
        The system we are integrating.
    engine : object like :py:class`.EngineBase`
        The engine to use for the simulation.

    Returns
    -------
    out : object like :py:class:`.SimulationSingleTIS`
        The object representing the simulation to run.
    """
    order_function = create_orderparameter(settings)
    if order_function is None:
        msgtxt = 'No order parameter created!'
        logger.critical(msgtxt)
        raise ValueError(msgtxt)
    if 'path-ensemble' in settings:
        path_ensemble = settings['path-ensemble']
    else:
        path_ensemble = create_path_ensemble(settings, engine.engine_type)
    rgen = create_random_generator(settings['tis'])
    sim = settings['simulation']
    return SimulationSingleTIS(system, order_function, engine,
                               path_ensemble,
                               rgen,
                               settings,
                               steps=sim['steps'],
                               startcycle=sim.get('startcycle', 0))


def create_retis_simulation(settings, system, engine):
    """This will set up and create a RETIS simulation.

    Parameters
    ----------
    settings : dict
        The settings needed to set up the simulation.
    system : object like :py:class:`.System`
        The system we are going to simulate.
    engine : object like :py:class:`.EngineBase`
        The engine to use for the simulation.

    Returns
    -------
    out : object like :py:class:`.SimulationRETIS`
        The object representing the simulation to run.
    """
    order_function = create_orderparameter(settings)
    if order_function is None:
        msgtxt = 'No order parameter created!'
        logger.critical(msgtxt)
        raise ValueError(msgtxt)
    sim = settings['simulation']
    exe_dir = sim.get('exe-path', '')
    path_ensembles, _ = create_path_ensembles(sim['interfaces'],
                                              engine.engine_type,
                                              include_zero=True,
                                              exe_dir=exe_dir)
    rgen = create_random_generator(settings['tis'])
    return SimulationRETIS(system, order_function, engine,
                           path_ensembles,
                           rgen,
                           settings,
                           steps=sim['steps'],
                           startcycle=sim.get('startcycle', 0))


def create_simulation(settings, kwargs):
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
    kwargs : dict
        This dict contains objects that might be needed to initialize
        the simulation for instance:

        * system : object like :py:class:`.System`
            This is the system for which the simulation will run.

        * engine : object like :py:class:`.EngineBase`
            The engine to use for the simulation.

    Returns
    -------
    out : object like :py:class:`.Simulation`
        This object will correspond to the selected simulation type.
    """
    sim_type = settings['simulation']['task'].lower()

    sim_map = {
        'md-nve': {'function': create_nve_simulation,
                   'args': ('system', 'engine')},
        'md-flux': {'function': create_mdflux_simulation,
                    'args': ('system', 'engine')},
        'umbrellawindow': {'function': create_umbrellaw_simulation,
                           'args': ('system',)},
        'tis': {'function': create_tis_simulations,
                'args': ('system', 'engine')},
        'retis': {'function': create_retis_simulation,
                  'args': ('system', 'engine')}
    }

    if sim_type not in sim_map:
        msgtxt = 'Unknown simulation task {}'.format(sim_type)
        logger.error(msgtxt)
        raise ValueError(msgtxt)
    else:
        function = sim_map[sim_type]['function']
        arg_name = sim_map[sim_type]['args']
        args = []
        msgtxt = 'Simulation "{}" requires a "{}"'
        for key in arg_name:
            if key not in kwargs or kwargs[key] is None:
                msg = msgtxt.format(sim_type, key)
                logger.error(msg)
                raise ValueError(msg)
            else:
                args.append(kwargs[key])
        simulation = function(settings, *args)
        msgtxt = ('Created simulation:\n'
                  '{}'.format(simulation))
        logger.info(msgtxt)
        return simulation
