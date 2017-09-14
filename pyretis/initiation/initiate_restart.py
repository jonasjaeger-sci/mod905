# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""This file contains functions used for initiation of paths.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

initiate_restart (:py:func`.initiate_restart`)
    Method that will get the initial path from the output from
    a previous simulation.
"""
import logging
import os
from pyretis.core.pathensemble import PATH_DIR_FMT
from pyretis.core.common import get_path_class
from pyretis.inout.common import print_to_screen
from pyretis.inout.restart import read_restart_file
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['initiate_restart']


def initiate_restart(simulation, cycle, settings):
    """Initiate paths by loading already generated ones.

    Parameters
    ----------
    simulation : object like :py:class:`.Simulation`
        The simulation we are setting up.
    cycle : integer
        The simulation cycles we are starting at.
    settings : dictionary
        A dictionary with settings for the initiation.
    """
    maxlen = settings['tis']['maxlength']
    klass = get_path_class(simulation.engine.engine_type)
    for ensemble in simulation.path_ensembles:
        name = ensemble.ensemble_name
        logger.info('Loading restart data for path ensemble %s:', name)
        print_to_screen(
            'Loading restart data for path ensemble {}:'.format(name),
            level='warning'
        )
        simulation.engine.exe_dir = ensemble.directory['generate']
        path = klass(simulation.rgen, maxlen=maxlen)
        restart_file = os.path.join(PATH_DIR_FMT.format(ensemble.ensemble),
                                    'ensemble.restart')
        restart_info = read_restart_file(restart_file)
        ensemble.load_restart_info(path, restart_info, cycle=cycle)
        yield True, path, path.status
