# -*- coding: utf-8 -*-
"""This module handles creation of force fields from simulation settings

For the force field we will need to load potential functions.
For the potential functions we can to two things:

1. We use one of the predefined potential functions.

2. We read from a given python module.

Important classes and functions:

- create_potential: A function to create a simulation object from
  a dictionary of given settings.
"""
from __future__ import absolute_import
import logging
from pyretis.inout.settings.common import create_potential
from pyretis.forcefield import ForceField
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['create_force_field']


def create_potentials(settings):
    """Function to create potential functions from simulations settings.

    This function will basically loop over the given potential settings
    and just run `create_potential` for each setting.

    Parameters
    ----------
    settings : dict
        This dictionary contains the settings for the simulation.

    Returns
    -------
    out : list
        A list of potential functions.
    """
    potentials = settings.get('potentials', [])
    out = []
    for i, pot_settings in enumerate(potentials):
        key = 'potential-{}'.format(i)
        settings[key] = pot_settings  # TODO: REMOVE THIS!
        potential_function = create_potential(settings, key)
        if potential_function is None:
            msg = 'The following potential settings were ignored!\n{}'
            msgtxt = msg.format(pot_settings)
            logger.warning(msgtxt)
        out.append(potential_function)
    return out


def create_force_field(settings):
    """Function to create a force field from input settings.

    This function will create the required potential functions with the
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
    ffsettings = settings.get('forcefield', None)
    try:
        desc = ffsettings['desc']
    except KeyError:
        desc = None
    potentials = create_potentials(settings)
    pot_param = settings['potential-parameters']
    ffield = ForceField(desc=desc, potential=potentials, params=pot_param)
    msg = ['Created force field:']
    msg.append('{}'.format(ffield))
    msgtxt = '\n'.join(msg)
    logger.info(msgtxt)
    return ffield
