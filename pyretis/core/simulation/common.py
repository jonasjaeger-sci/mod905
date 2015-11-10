# -*- coding: utf-8 -*-
"""Some common functions for the simulations.

This helper functions for setting up simulations.

Important functions
-------------------

check_settings : Check that required simulation settings are actually given.
"""
import warnings


__all__ = ['check_settings']


def check_settings(settings, required):
    """Check that required simulation settings are actually given.

    This function will look for required settings in the given
    `settings`. If one or more keys from the given `required` list of
    strings are not found, this function will return False. Otherwise
    if will return True. Typically, and exception should be raised if False
    is returned, this is handled outside the function in case someone wants to
    add some magic handling of missing settings.

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
            warnings.warn('Setting `{}` not found!'.format(setting))
            result = False
            not_found.append(setting)
    return result, not_found
