# -*- coding: utf-8 -*-
"""This module defines common functions for the settings handling.

Important functions defined here:

- check_settings: Check that required simulation settings are actually
  given.

- import_from : A function to dynamically import functions/classes
  etc. from user specified modules.
"""
import importlib
import logging
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['check_settings', 'import_from', 'initiate_instance']


def import_from(module_name, function_name):
    """Function to import a function/class from a module.

    This function will dynamically import a specified function/object
    from a module and return it. If the module can not be imported or
    if we can't find the function/class in the module we will raise
    exceptions.

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
        module = importlib.import_module(module_name)
        msg = 'Imported module: {}'.format(module)
        logger.info(msg)
        try:
            return getattr(module, function_name)
        except AttributeError:
            msg = 'Could not import "{}" from "{}"'.format(function_name,
                                                           module_name)
            logger.critical(msg)
            raise ValueError(msg)
    except ImportError:
        msg = 'Could not import module: {}'.format(module_name)
        logger.critical(msg)
        raise ValueError(msg)


def initiate_instance(klass, args=None, kwargs=None):
    """Function to initiate a class with optional arguments.

    Parameters
    ----------
    klass : class
        The class to initiate.
    args : list, optional
        Positional arguments to `klass.__init__()`.
    kwargs : dict, optional
        The keyword arguments to `klass.__init__()`

    Returns
    -------
    out : instance of `klass`
        Here, we just return the initiated instance of the given class.
    """
    if args is None:
        if kwargs is None:
            msg = 'Initiated {} without arguments.'.format(klass)
            logger.info(msg)
            return klass()
        else:
            msg = 'Initiated {} with keyword arguments.'.format(klass)
            logger.info(msg)
            return klass(**kwargs)
    else:
        if kwargs is None:
            msg = 'Initiated {}  with positional arguments.'.format(klass)
            logger.info(msg)
            return klass(*args)
        else:
            msg = 'Initiated {} with positional and keyword arguments.'
            msg = msg.format(klass)
            logger.info(msg)
            return klass(*args, **kwargs)


def check_settings(settings, required):
    """Check that required simulation settings are actually given.

    This function will look for required settings in the given
    `settings`. If one or more keys from the given `required` list of
    strings are not found, this function will return False. Otherwise
    if will return True. Typically, and exception should be raised if
    False is returned, this is handled outside the function in case
    someone wants to add some magic handling of missing settings.

    Parameters
    ----------
    settings : dict
        This dict contains the given settings
    required : list of strings
        This list contains the settings that are required and which
        we will check the presence of.

    Returns
    -------
    result : boolean
        True if all required settings are present, False otherwise.
    not_found : list of strings
        There are the required settings we did not find.
    """
    result = True
    not_found = []
    for setting in required:
        if setting not in settings:
            result = False
            not_found.append(setting)
    return result, not_found
