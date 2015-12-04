# -*- coding: utf-8 -*-
"""This module handles creation of order parameters from simulation settings.

For the order parameters we have two options:

1. We use one of the predefined order parameters.

2. We read one order parameter from a given python module.

Important classes and functions:

- create_simulation: A function to create a simulation object from
  a dictionary of given settings.
"""
from __future__ import absolute_import
import logging
import os
from pyretis.inout.settings.common import import_from
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['create_orderparameter']


def create_orderparameter(settings):
    """Function to create simulations from settings.

    Parameters
    ----------
    settings : dict
        This dictionary contains the settings for the simulation.

    Returns
    -------
    out : object like `OrderParameter` from `pyretis.core.orderparameter`.
        This object represents the order parameter.
    """
    try:
        orderp = settings['orderparameter']
    except KeyError:
        msg = 'No order parameter settings found!'
        logger.critical(msg)
        return None
    module = orderp.get('module', None)
    orderclass = None
    try:
        orderclass = orderp['class']
    except KeyError:
        msg = 'No order parameter class specified!'
        logger.critical(msg)
        return None
    if module is None:
        orderparameter = import_from('pyretis.core.orderparameter', orderclass)
    else:
        module = os.path.splitext(module)[0]
        orderparameter = import_from(module, orderclass)
        # run some checks:
        for function in ['calculate', 'calculate_velocity']:
            orderc = getattr(orderparameter, function, None)
            if not orderc:
                msg = 'Could not find method {}.{}'.format(orderclass,
                                                           function)
                raise ValueError(msg)
            else:
                if not callable(orderc):
                    msg = 'Method {}.{} is not callable!'.format(orderclass,
                                                                 function)
                    raise ValueError(msg)
    args = orderp.get('args', None)
    kwargs = orderp.get('kwargs', None)
    if args is None:
        if kwargs is not None:
            return orderparameter(**kwargs)
        else:
            return orderparameter()
    else:
        if kwargs is not None:
            return orderparameter(*args, **kwargs)
        else:
            return orderparameter(*args)
