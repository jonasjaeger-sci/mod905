# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""This module defines common methods for the settings handling.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

check_settings
    Check that required simulation settings are actually given.

import_from
    A method to dynamically import method/classes etc. from user
    specified modules.
"""
import sys
import importlib
import imp
import logging
import os
from pyretis.core.common import initiate_instance
from pyretis.core.integrators import integrator_factory
from pyretis.core.orderparameter import order_factory
from pyretis.forcefield.factory import potential_factory
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['check_settings', 'import_from',
           'create_orderparameter', 'create_integrator',
           'create_potential']


def import_from(module_path, function_name):
    """Method to import a method/class from a module.

    This method will dynamically import a specified method/object
    from a module and return it. If the module can not be imported or
    if we can't find the method/class in the module we will raise
    exceptions.

    Parameters
    ----------
    module_path : string
        The path/filename to load from.
    function_name : string
        The name of the method/class to load.

    Returns
    -------
    out : object
        The thing we managed to import.

    Note
    ----
    Here we need to handle different versions of python. This is due
    to the ``imp`` module being deprecated and and the same time
    ``importlib`` is changing between versions 3.4 and 3.5 [#]_.

    References
    ----------
    .. [#] http://bugs.python.org/issue21436
    """
    try:
        module_name = os.path.basename(module_path)
        module_name = os.path.splitext(module_name)[0]
        # imp is deprecated for python 3.5 -> we need to check if we are
        # using python3.5 or earlier:
        if sys.version_info < (3, 5):
            module = imp.load_source(module_name, module_path)
        else:
            spec = importlib.util.spec_from_file_location(module_name,  # pylint: disable=no-member
                                                          module_path)
            module = importlib.util.module_from_spec(spec)  # pylint: disable=no-member
            spec.loader.exec_module(module)
        msg = 'Imported module: {}'.format(module)
        logger.debug(msg)
        return getattr(module, function_name)
    except (ImportError, IOError):
        msg = 'Could not import module: {}'.format(module_path)
        logger.critical(msg)
        raise ValueError(msg)
    except AttributeError:
        msg = 'Could not import "{}" from "{}"'.format(function_name,
                                                       module_path)
        logger.critical(msg)
        raise ValueError(msg)


def check_settings(settings, required):
    """Check that required simulation settings are actually given.

    This method will look for required settings in the given
    `settings`. If one or more keys from the given `required` list of
    strings are not found, this method will return False. Otherwise
    if will return True. Typically, and exception should be raised if
    False is returned, this is handled outside the method in case
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


def create_external(settings, key, factory, required_methods,
                    key_settings=None):
    """Method to create objects from settings.

    This method will handle creation of objects from settings. The
    requested objects can be pyretis internals or defined in external
    modules.

    Parameters
    ----------
    settings : dict
        This dictionary contains the settings for the simulation.
    key : string
        The setting we are creating for.
    factory : callable
        A method to call that can handle the creation of internal
        objects for us.
    required_methods : list of strings
        The methods we need to have if creating an object from external
        files.
    key_settings : dict
        This dictionary contains the settings for specific key we
        are processing. If this is not given, we will try to obtain
        these settings by `settings[key]`. The reason why we make it
        possible to pass these as settings is in case we are processing
        a key which does not give a simple setting, but a list of settings.
        It that case `settings[key]` will give a list to process. That list
        is iterated somewhere else and `key_settings` can then be used to
        process these elements.

    Returns
    -------
    out : object
        This object represents the class we are requesting here.
    """
    if key_settings is None:
        try:
            key_settings = settings[key]
        except KeyError:
            msg = 'No {} settings found. Skipping set-up.'.format(key)
            logger.debug(msg)
            return None
    module = key_settings.get('module', None)
    klass = None
    try:
        klass = key_settings['class']
    except KeyError:
        msg = 'No "{}" setting "class" specified!'.format(key)
        logger.critical(msg)
        raise ValueError(msg)
    if module is None:
        return factory(key_settings)
    else:
        # Here we assume we are to load from a file. Before we import
        # we need to check that the path is ok or if we should include
        # the 'exe-path' from settings.
        # 1) Check if we can find the module:
        if os.path.isfile(module):
            obj = import_from(module, klass)
        else:
            if 'exe-path' in settings:
                module = os.path.join(settings['exe-path'], module)
                obj = import_from(module, klass)
            else:
                msg = 'Could not find module "{}" for {}!'.format(module, key)
                raise ValueError(msg)
        # run some checks:
        for function in required_methods:
            objfunc = getattr(obj, function, None)
            if not objfunc:
                msg = 'Could not find method {}.{}'.format(klass,
                                                           function)
                logger.critical(msg)
                raise ValueError(msg)
            else:
                if not callable(objfunc):
                    msg = 'Method {}.{} is not callable!'.format(klass,
                                                                 function)
                    logger.critical(msg)
                    raise ValueError(msg)
        return initiate_instance(obj, key_settings)


def create_orderparameter(settings):
    """Method to create order parameters from settings.

    Parameters
    ----------
    settings : dict
        This dictionary contains the settings for the simulation.

    Returns
    -------
    out : object like `OrderParameter` from `pyretis.core.orderparameter`.
        This object represents the order parameter.
    """
    return create_external(settings, 'orderparameter', order_factory,
                           ['calculate', 'calculate_velocity'])


def create_integrator(settings):
    """Method to create an integrator from settings.

    Parameters
    ----------
    settings : dict
        This dictionary contains the settings for the simulation.

    Returns
    -------
    out : object like `Integrator` from `pyretis.core.integrators`.
        This object represents the integrator.
    """
    return create_external(settings, 'integrator', integrator_factory,
                           ['integration_step'])


def create_potential(settings, key_settings):
    """Method to create a potential from settings.

    Parameters
    ----------
    settings : dict
        This dictionary contains the settings for the simulation.
    key_settings : dict
        Settings for the potential we are creating.

    Returns
    -------
    out : object like `PotentialFunction` from `pyretis.forcefield`.
        This object represents the order parameter.
    """
    return create_external(settings, 'potential', potential_factory,
                           ['force', 'potential', 'potential_and_force'],
                           key_settings=key_settings)
