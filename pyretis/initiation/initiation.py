# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""This file contains functions used for initiation of paths.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

get_initiation_method (:py:func:`.get_initiation_method`)
    Method to select initiation method from settings.

initiate_path_simulation (:py:func:`initiate_path_simulation`)
    Method to initiate a path simulation.

"""
import logging
import os
import shutil
from pyretis.core.path import paste_paths
from pyretis.core.pathensemble import PATH_DIR_FMT
from pyretis.core.tis import make_tis_step
from pyretis.core.common import get_path_class
from pyretis.inout.common import print_to_screen
from pyretis.inout.writers import prepare_load
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['initiate_path_simulation', 'get_initiation_method']


def get_initiation_method(settings):
    """Return the initiation method.

    Parameters
    ----------
    settings : dict
        This dictionary contains the settings for the initiation.
    """
    _methods = {'kick': initiate_kick,
                'load': initiate_load}
    method = settings['initial-path']['method'].lower()
    if method not in _methods:
        logger.error('Unknown initiation method "%s" requrested', method)
        logger.error('Known methods: %s', _methods.keys())
        raise ValueError('Unknown initiation method requested!')
    logtxt = 'Will initiate using method "{}"'.format(method)
    print_to_screen(logtxt)
    logger.info(logtxt)
    return _methods[method]


def initiate_path_simulation(simulation, settings):
    """Helper method to initiate a path simulation.

    Parameters
    ----------
    simulation : object like :py:class:`.PathSimulation`
        The simulation we are doing the initiation for.
    settings : dict
        A dictionary with settings for the initiation.
    """
    cycle = simulation.cycle['step']
    method = get_initiation_method(settings)
    return method(simulation, cycle, settings)
