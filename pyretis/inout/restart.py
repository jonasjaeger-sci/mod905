# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""This module defines how we write and read restart files.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

read_restart_file (:py:func:`.read_restart_file`)
    Method for reading restart information from a file.

write_restart_file (:py:func:`.write_restart_file`)
    Method for writing the restart file.

write_path_ensemble_restart (:py:func`.write_path_ensemble_restart`)
    Method for writing restart files for path ensembles.
"""
import logging
import os
import pickle
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = [
    'read_restart_file',
    'write_restart_file',
    'write_path_ensemble_restart'
]


def write_restart_file(filename, simulation):
    """Write restart info for a simulation.

    Parameters
    ----------
    filename : string
        The file we are going to write to.
    simulation : object like :py:class:`.Simulation`
        A simulation object we will get information from.
    """
    info = {
        'simulation': simulation.restart_info(),
        'system': simulation.system.restart_info(),
    }
    with open(filename, 'wb') as outfile:
        pickle.dump(info, outfile)


def write_path_ensemble_restart(path_ensemble):
    """Write a restart file for a path ensemble.

    Parameters
    ----------
    path_ensemble : object like :py:class:`.PathEnsemble`
        The path ensemble we are writing restart info for.
    """
    filename = os.path.join(
        path_ensemble.ensemble_name_simple,
        'ensemble.restart'
    )
    with open(filename, 'wb') as outfile:
        pickle.dump(path_ensemble.restart_info(), outfile)


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
