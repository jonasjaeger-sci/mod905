# -*- coding: utf-8 -*-
"""This module handles creation of force fields from simulation settings

For the force field we will need to load potential functions. For the potential
functions we can to two things:

1. We use one of the predefined potential functions.

2. We read from a given python module.

Important classes and functions:

- create_potential: A function to create a simulation object from
  a dictionary of given settings.
"""
from __future__ import absolute_import
import logging
import os
from pyretis.inout.settings.common import import_from, initiate_instance
from pyretis.forcefield import ForceField
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = []


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
    for pot_settings in potentials:
        potential_function = create_potential(pot_settings)
        out.append(potential_function)
    return out


def create_potential(settings):
    """Function to create simulations from settings.

    Parameters
    ----------
    settings : dict
        This dictionary contains the settings for a single potential.

    Returns
    -------
    out : object like `PotentialFunction` from `pyretis.forcefield.potential`.
        This object represents the potential function.
    """
    module = settings.get('module', None)
    pot_class = None
    try:
        pot_class = settings['class']
    except KeyError:
        msg = 'No potential function class specified!'
        logger.error(msg)
        return None
    if module is None:
        potential = import_from('pyretis.forcefield.potentials',
                                pot_class)
    else:
        # Here we assume we are to load from a file.
        # It would be nice to ditch python 2 and just do this:
        # importlib.machinery.SourceFileLoader('module','/path/module.py')
        module = os.path.splitext(module)[0]
        potential = import_from(module, pot_class)
        # run some checks:
        for function in ['force', 'potential', 'potential_and_force']:
            functionc = getattr(potential, function, None)
            if not functionc:
                msg = 'Could not find method {}.{}'.format(pot_class,
                                                           function)
                raise ValueError(msg)
            else:
                if not callable(functionc):
                    msg = 'Method {}.{} is not callable!'.format(pot_class,
                                                                 function)
                    raise ValueError(msg)
    return initiate_instance(potential, args=settings.get('args', None),
                             kwargs=settings.get('kwargs', None))


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
    msg = '\n'.join(msg)
    logger.info(msg)
    return ffield
