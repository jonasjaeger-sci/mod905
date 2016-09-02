# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""This module handles creation of force fields from simulation settings

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

create_potentials
    Method for creating potentials from a dictionary of settings.
"""
from __future__ import absolute_import
import logging
from pyretis.inout.settings.common import create_potential
from pyretis.forcefield import ForceField
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['create_force_field']


def create_potentials(settings):
    """Method to create potential functions from simulations settings.

    This method will basically loop over the given potential settings
    and just run `create_potential` for each setting.

    Parameters
    ----------
    settings : dict
        This dictionary contains the settings for the simulation.

    Returns
    -------
    out[0] : list
        A list of potential functions.
    out[1] : list
        A list of parameters for the potential functions.
    """
    potentials = settings.get('potential', [])
    try:
        ndim = settings['system']['dimensions']
    except KeyError:
        ndim = None
    out_pot, out_par = [], []
    for i, pot_settings in enumerate(potentials):
        potential_function = create_potential(settings, pot_settings)
        if potential_function is None:
            msg = 'The following potential settings were ignored!\n{}'
            msgtxt = msg.format(pot_settings)
            logger.warning(msgtxt)
        pdim = getattr(potential_function, 'dim', None)
        if pdim is not None and ndim is not None:
            if ndim != pdim:
                msg = ('Inconsistent dimensions in potential!'
                       '\nSettings gives: {}D, potential {} is {}D')
                msgtxt = msg.format(ndim, i, pdim)
                logger.error(msgtxt)
                raise ValueError(msgtxt)
        out_pot.append(potential_function)
        out_par.append(pot_settings.get('parameter', None))
    return out_pot, out_par


def create_force_field(settings):
    """Method to create a force field from input settings.

    This method will create the required potential functions with the
    specified parameters from `settings`.

    Parameters
    ----------
    settings : dict
        This dictionary contains the settings for a single potential.

    Returns
    -------
    out : object like `ForceField` from `pyretis.forcefield.forcefield`.
        This object represents the force field.
    """
    try:
        desc = settings['forcefield']['description']
    except KeyError:
        desc = None
    potentials, pot_param = create_potentials(settings)
    ffield = ForceField(desc=desc, potential=potentials, params=pot_param)
    msg = ['Created force field:']
    msg.append('{}'.format(ffield))
    msgtxt = '\n'.join(msg)
    logger.info(msgtxt)
    return ffield
