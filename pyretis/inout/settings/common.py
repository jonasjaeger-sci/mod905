# -*- coding: utf-8 -*-
"""This module defines common functions for the settings handling

Important functions defined here:

- import_from : A function to dynamically import functions/classes etc. from
  user specified modules.
"""
import logging

logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['import_from']


def import_from(module_name, function_name):
    """Function to import a function/class from a module.

    This function will dynamically import a specified function/object from a
    module and return it. If the module can not be imported or if we can't
    find the function/class in the module we will raise exceptions.

    Parameters
    ----------
    module_name : string
        The name of the module to load from.
    function_name : string
        The name of the function/class to load.

    Returns
    -------
    out : object
        The thing we managed to import.
    """
    try:
        module = __import__(module_name, fromlist=[function_name])
        return getattr(module, function_name)
    except AttributeError:
        msg = 'Could not import "{}" from "{}"'.format(function_name,
                                                       module_name)
        raise ValueError(msg)
    except ImportError:
        msg = 'Could not import module "{}"'.format(module_name)
        raise ValueError(msg)
