# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""This package defines methods for initiating path ensembles.

Package structure
-----------------

Modules
~~~~~~~

__init__.py
    This file, imports from the other modules and defines helper
    methods for the initiation.

initiate_kick.py (:py:mod:`pyretis.initiation.initiate_kick`)
    Methods for initiating using the ``kick`` method.

initiate_load.py (:py:mod:`pyretis.initiation.initiate_load`)
    Methods for initiating by loading already existing paths from
    files.


Important methods defined in this package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

get_initiation_method (:py:func:`.get_initiation_method`)
    Method to select initiation method from settings.

initiate_path_simulation (:py:func:`initiate_path_simulation`)
    Method to initiate a path simulation.

"""
import logging
from pyretis.inout.common import print_to_screen
from .initiate_kick import initiate_kick
from .initiate_load import initiate_load
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
