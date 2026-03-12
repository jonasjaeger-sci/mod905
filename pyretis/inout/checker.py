# -*- coding: utf-8 -*-
# Copyright (c) 2026, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""This module checks that the inputs are meaningful.

Main methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~

check_ensemble (:py:func:`.check_ensemble`)
    Function to check the ensemble settings.

check_interfaces (:py:func:`.check_interfaces`)
    Function to check engine set-up.

check_for_bullshitt (:py:func:`.check_for_bullshitt`)
    Function to compare nested dicts and lists.

check_engine (:py:func:`.check_engine`)
    Function to check engine set-up.

"""
import logging

logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())

__all__ = ['check_interfaces', 'check_for_bullshitt',
           'check_engine', 'check_ensemble']
ENSEMBLE_TASKS = ['retis', 'tis', 'repptis', 'pptis']


def check_ensemble(settings):
    """Check that the ensemble input parameters are complete.

    Parameters
    ----------
    settings : dict
        The settings needed to set up the simulation.

    """
    if 'ensemble' in settings:
        savelambda = []
        for ens in settings['ensemble']:
            if 'interface' in ens:
                savelambda.append(ens['interface'])

                if not ens['interface'] \
                        in settings['simulation']['interfaces']:
                    msg = f"The ensemble interface {ens['interface']} "\
                        "is not present in the simulation interface list"
                    break

            else:
                msg = "An ensemble is present without reference interface"
                break

        if not is_sorted(savelambda):
            msg = "Interface positions in the ensemble simulation "\
                "are NOT properly sorted (ascending order)"

    else:
        msg = "No ensemble in settings"

    if 'msg' in locals():
        raise ValueError(msg)

    return True


def check_engine(settings):
    """Check the engine settings.

    Checks that the input engine settings are correct, and
    automatically determine the 'internal' or 'external'
    engine setting.

    Parameters
    ----------
    settings : dict
        The current input settings.

    """
    msg = []
    if 'engine' not in settings:
        msg += ['The section engine is missing']

    elif settings['engine'].get('type') == 'external':

        if 'input_path' not in settings['engine']:
            msg += ['The section engine requires an input_path entry']

        if 'gmx' in settings['engine'] and \
                'gmx_format' not in settings['engine']:
            msg += ['File format is not specified for the engine']
        elif 'cp2k' in settings['engine'] and \
                'cp2k_format' not in settings['engine']:
            msg += ['File format is not specified for the engine']

    if msg:
        msgtxt = '\n'.join(msg)
        logger.critical(msgtxt)
        return False

    return True


def check_for_bullshitt(settings):
    """Do what is stated.

    Just for the input settings.

    Parameters
    ----------
    settings : dict
        The current input settings.

    """
    if (settings['simulation']['task'] in ENSEMBLE_TASKS and
            len(settings['simulation']['interfaces']) < 3):
        msg = "Insufficient number of interfaces for "\
            f"{settings['simulation']['task']}"

    elif settings['simulation']['task'] in ENSEMBLE_TASKS:
        if not is_sorted(settings['simulation']['interfaces']):
            msg = "Interface lambda positions in the simulation "\
                "entry are NOT sorted (small to large)"

        if 'ensemble' in settings:
            savelambda = []
            for i_ens, ens in enumerate(settings['ensemble']):
                if 'ensemble_number' not in ens and \
                        'interface' not in ens:
                    msg = "An ensemble has been introduced without "\
                        "references (interface in ensemble settings)"
                else:
                    savelambda.append(settings['simulation']['interfaces']
                                      [i_ens])
                    if 'interface' in ens and ens['interface'] \
                            not in settings['simulation']['interfaces']:
                        msg = "An ensemble has been introduced with an "\
                            "interface not listed in the simulation interfaces"

    if 'msg' in locals():
        raise ValueError(msg)


def check_interfaces(settings):
    """Check that the interfaces are properly defined.

    Parameters
    ----------
    settings : dict
        The current input settings.

    """
    msg = []
    if settings['simulation'].get('flux', False) and \
            not settings['simulation']['zero_ensemble']:
        msg += ['Settings for flux and zero_ensemble are inconsistent.']

    if settings['simulation']['task'] in ENSEMBLE_TASKS:
        if len(settings['simulation']['interfaces']) < 3:
            msg += ['Insufficient number of interfaces for {}'
                    .format(settings['simulation']['task'])]

        if not is_sorted(settings['simulation']['interfaces']):
            msg += ['Interface positions in the simulation interfaces ']
            msg += ['input are NOT properly sorted (ascending order)']

    if msg:
        msgtxt = '\n'.join(msg)
        logger.critical(msgtxt)
        return False

    return True


def is_sorted(lll):
    """Check if a list is sorted."""
    return all(aaa <= bbb for aaa, bbb in zip(lll[:-1], lll[1:]))
