# -*- coding: utf-8 -*-
"""This module handles creation of an integrator from settings.

For the integrator we have two options:

1. We use one of the predefined integrators.

2. We read one from a given python module.

Important classes and functions:

- create_simulation: A function to create a simulation object from
  a dictionary of given settings.
"""
from __future__ import absolute_import
import logging
import os
from pyretis.inout.settings.common import import_from, initiate_instance
import pyretis.core.integrators as integrators
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['create_integrator']


def create_integrator(settings):
    """Function to create simulations from settings.

    Parameters
    ----------
    settings : dict
        This dictionary contains the settings for the simulation.

    Returns
    -------
    out : object like `Integrator` from `pyretis.core.integrators`.
        This object represents the integrator.
    """
    try:
        orderp = settings['integrator']
    except KeyError:
        msg = 'No integrator settings found!'
        logger.critical(msg)
        return None
    module = orderp.get('module', None)
    if module is None:
        # assume that we want to load from the predefined ones:
        integrator = integrators.create_integrator(settings['integrator'])
        return integrator
    else:
        # Here we assume we are to load from a file.
        # It would be nice to ditch python 2 and just do this:
        # importlib.machinery.SourceFileLoader('module','/path/module.py')
        orderclass = None
        try:
            orderclass = orderp['class']
        except KeyError:
            msg = 'No integrator class specified!'
            logger.critical(msg)
            return None
        module = os.path.splitext(module)[0]
        integrator = import_from(module, orderclass)
        # run some checks:
        for function in ['integration_step']:
            orderc = getattr(integrator, function, None)
            if not orderc:
                msg = 'Could not find method {}.{}'.format(orderclass,
                                                           function)
                raise ValueError(msg)
            else:
                if not callable(orderc):
                    msg = 'Method {}.{} is not callable!'.format(orderclass,
                                                                 function)
                    raise ValueError(msg)
        return initiate_instance(integrator, args=orderp.get('args', None),
                                 kwargs=orderp.get('kwargs', None))
