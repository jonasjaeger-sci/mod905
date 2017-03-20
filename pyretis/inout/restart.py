# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""This module defines how we write and read restart files.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

read_restart_file (:py:func:`.read_restart_file`)
    Method for reading restart information from a file.

write_restart_file (:py:func:`.write_restart_file`)
    Method for writing the restart file.
"""
import logging
import pickle
from pyretis.inout.settings import SECTIONS
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['read_restart_file', 'write_restart_file']


def write_restart_file(filename, simulation):
    """Write restart info for a simulation.

    Parameters
    ----------
    filename : string
        The file we are going to write to.
    simulation : object like :py:class:`.Simulation`
        A simulation object we will get information from.
    """
    info = simulation.restart_info()
    try:
        info['box'] = simulation.system.box.restart_info()
    except AttributeError:
        pass
    with open(filename, 'wb') as outfile:
        pickle.dump(info, outfile)


def read_restart_file(filename):
    """Read restart info for a simulation.

    Parameters
    ----------
    filename : string
        The file we are going to read from.
    """
    with open(filename, 'rb') as infile:
        info = pickle.load(infile)
    return info


def add_restart_settings(settings, restart_file):
    """Add restart settings to simulation settings.

    This method will add simulation settings from a restart file
    to an already existing settings dictionary.

    Parameters
    ----------
    settings : dict
        A dictionary with simulation settings.
    restart_file : string
        The restart file to open.
    """
    info = read_restart_file(restart_file)
    for section, values in info.items():
        if section in SECTIONS:
            logger.info('Using restart data for %s settings', section)
            settings[section] = {}
            for key, val in values.items():
                settings[section][key] = val
    return info


def add_restart_objects(restart_info, simulation):
    """Add restart objects to a simulation.

    This method will add more complex restart information to
    a simulation. This is information about the state of the
    random number generators etc.

    Parameters
    ----------
    restart_info : dict
        The restart information read from the restart file.
    simulation : object like :py:class:`.Simulation`
        The simulation we will update with restart objects.
    """
    if 'rgen' in restart_info:
        logger.info('Random number generator read from restart!')
        simulation.rgen.set_state(restart_info['rgen'])
    if 'engine_rgen' in restart_info:
        logger.info('Engine random number generator read from restart!')
        simulation.engine.rgen.set_state(restart_info['engine_rgen'])
    for key, val in restart_info['cycle'].items():
        if key != 'end':
            simulation.cycle[key] = val
