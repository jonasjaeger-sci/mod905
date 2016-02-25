# -*- coding: utf-8 -*-
"""This module handles creation of order parameters from settings.

For the order parameters we have two options:

1. We use one of the predefined order parameters.

2. We read one order parameter from a given python module.

Important classes and functions:

- create_orderparameter: A function to create an order parameter object
  from a dictionary of given settings.
"""
from __future__ import absolute_import
import logging
import os
from pyretis.inout.settings.common import import_from, initiate_instance
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['create_orderparameter']


def create_orderparameter(settings):
    """Function to create order parameters from settings.

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
        # Here we assume we are to load from a file.
        # It would be nice to ditch python 2 and just do this:
        # importlib.machinery.SourceFileLoader('module','/path/module.py')
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
    return initiate_instance(orderparameter, args=orderp.get('args', None),
                             kwargs=orderp.get('kwargs', None))
