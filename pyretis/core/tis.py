# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""This file contains functions used in TIS.

This module defines the functions needed to perform TIS simulations.
The algorithms are implemented as described by van Erp et al. [TIS]_.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

make_tis_step (:py:func:`.make_tis_step`)
    A method that will perform a single TIS step.

make_tis_step_ensemble (:py:func:`.make_tis_step_ensemble`)
    A method to preform a TIS step for a path ensemble. It will handle
    adding of the path to a path ensemble object.

shoot (:py:func:`.shoot`)
    A method that will perform a shooting move.

time_reversal (:py:func:`.time_reversal`)
    A method for performing the time reversal move.

References
~~~~~~~~~~

.. [TIS] Titus S. van Erp, Daniele Moroni and Peter G. Bolhuis,
   J. Chem. Phys. 118, 7762 (2003),
   https://dx.doi.org/10.1063%2F1.1562614
"""
import logging
from pyretis.core.path import paste_paths
from pyretis.core.montecarlo import metropolis_accept_reject
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['make_tis_step_ensemble',
           'make_tis_step',
           'shoot',
           'time_reversal']


def make_tis_step_ensemble(path_ensemble, system, order_function, engine,
                           rgen, tis_settings, cycle):
    """Function to preform TIS step for a path ensemble.

    This function will run `make_tis_step` for the given path_ensemble.
    It will handle adding of the path. This function is intended for
    convenience when working with path ensembles. If we are using the
    path ensemble ``[0^-]`` then the start condition should be 'R' for
    right.

    Parameters
    ----------
    path_ensemble : object like :py:class:`.PathEnsemble`
        This is the path ensemble to perform the TIS step for.
    system : object like :py:class:`.System`
        System is used here since we need access to the temperature
        and to the particle list.
    order_function : object like :py:class:`.OrderParameter`
        The class used for obtaining the order parameter(s).
    engine : object like :py:class:`.EngineBase`
        The engine to use for propagating a path.
    rgen : object like :py:class:`.RandomGenerator`
        This is the random generator that will be used.
    tis_settings : dict
        This dictionary contain the TIS settings.
    cycle : int
        The current cycle number

    Returns
    -------
    out[0] : boolean
        True if new path can be accepted
    out[1] : object like :py:class:`.PathBase`
        The generated path.
    out[2] : string
        The status of the path
    """
    tis_settings['start_cond'] = path_ensemble.get_start_condition()
    logger.info('TIS move in: %s', path_ensemble.ensemble_name)
    engine.exe_dir = path_ensemble.directory['generate']
    accept, trial, status = make_tis_step(path_ensemble.last_path,
                                          system,
                                          order_function,
                                          path_ensemble.interfaces,
                                          engine,
                                          rgen,
                                          tis_settings)
    if accept:
        logger.info('The move was accepted!')
    else:
        logger.info('The move was rejected! (%s)', status)
    path_ensemble.add_path_data(trial, status, cycle=cycle)
    return accept, trial, status


def make_tis_step(path, system, order_function, interfaces, engine, rgen,
                  tis_settings):
    """Perform a TIS step and generate a new path/trajectory.

    The new path will be generated from an existing one, either by
    performing a time-reversal move or by shooting. T(h)is is determined
    randomly by drawing a random number from a uniform distribution.

    Parameters
    ----------
    path : object like :py:class:`.PathBase`
        This is the input path which will be used for generating a
        new path.
    system : object like :py:class:`.System`
        System is used here since we need access to the temperature
        and to the particle list.
    order_function : object like :py:class:`.OrderParameter`
        The class used for obtaining the order parameter(s).
    interfaces : list of floats
        These are the interface positions on form [left, middle, right]
    engine : object like :py:class:`.EngineBase`
        The engine to use for propagating a path.
    rgen : object like :py:class:`.RandomGenerator`
        Random number generator used to determine what TIS move to
        perform.
    tis_settings : dict
        This dictionary contain the settings for the TIS method. Here we
        explicitly use:

        * `freq`: float, the frequency of how often we should do time
          reversal moves.
        * `start_cond`: string, starting condition, 'L'eft or 'R'ight

    Returns
    -------
    out[0] : boolean
        True if new path can be accepted
    out[1] : object like :py:class:`.PathBase`
        The generated path.
    out[2] : string
        The status of the path
    """
    if rgen.rand() < tis_settings['freq']:
        logger.info('Performing a time reversal move')
        accept, new_path, status = time_reversal(path, interfaces,
                                                 tis_settings['start_cond'])
    else:
        logger.info('Performing a shooting move.')
        accept, new_path, status = shoot(path, system, order_function,
                                         interfaces, engine, rgen,
                                         tis_settings)
    return accept, new_path, status


def time_reversal(path, interfaces, start_condition):
    """Perform a time-reversal move.

    Parameters
    ----------
    path : object like :py:class:`.PathBase`
        This is the input path which will be used for generating a
        new path.
    interfaces : list/tuple of floats
        These are the interface positions on form [left, middle, right]
    start_condition : string
        The starting condition, 'L'eft or 'R'ight.

    Returns
    -------
    out[0] : boolean
        True if the path can be accepted
    out[1] : object like :py:class:`.PathBase`
        Returns the generated path if something was generated
        `Path` is defined in `.path`.
    out[2] : string
        Status of the path, this is one of the strings defined in
        `.path._STATUS`.
    """
    new_path = path.reverse()
    start, _, _, _ = new_path.check_interfaces(interfaces)
    # explicitly set how this was generated
    new_path.generated = ('tr', 0, 0, 0)
    if start == start_condition:
        accept = True
        status = 'ACC'
    else:
        accept = False
        status = 'BWI'  # backward trajectory end at wrong interface
    new_path.status = status
    return accept, new_path, status


def shoot(path, system, order_function, interfaces, engine, rgen,
          tis_settings):
    """Perform a shooting-move.

    This function will perform the shooting move from a randomly
    selected time-slice.

    Parameters
    ----------
    path : object like :py:class:`.PathBase`
        This is the input path which will be used for generating a
        new path.
    system : object like :py:class:`.System`
        System is used here since we need access to the temperature
        and to the particle list.
    order_function : object like :py:class:`.OrderParameter`.
        The class used to calculate the order parameter.
    interfaces : list/tuple of floats
        These are the interface positions on form
        `[left, middle, right]`.
    engine : object like :py:class:`.EngineBase`
        The engine to use for propagating a path.
    rgen : object like :py:class:`.RandomGenerator`
        This is the random generator that will be used.
    tis_settings : dict
        This contains the settings for TIS. Keys used here:

        * `aimless`: boolean, is the shooting aimless or not?
        * `allowmaxlength`: boolean, should paths be allowed to reach
          maximum length?
        * `start_cond`: string, starting condition, 'L'eft or 'R'ight.
        * `maxlength`: integer, maximum allowed length of paths.

    Returns
    -------
    out[0] : boolean
        True if the path can be accepted
    out[1] : object like :py:class:`.PathBase`
        Returns the generated path.
    out[2] : string
        Status of the path, this is one of the strings defined in
        :py:const:`.path._STATUS`.
    """
    accept, trial_path = False, path.empty_path()  # return values
    shooting_point, idx = path.get_shooting_point()
    orderp = shooting_point['order']
    logger.info('Shooting from: %f', orderp[0])
    system.particles.set_particle_state(shooting_point)
    # store info about this point, just in case we have to return
    # before completing a full new path:
    trial_path.generated = ('sh', orderp[0], idx, 0)
    # Modify the velocities:
    dek, _, = engine.modify_velocities(
        system,
        rgen,
        sigma_v=tis_settings['sigma_v'],
        aimless=tis_settings['aimless'],
        momentum=tis_settings['zero_momentum'],
        rescale=tis_settings['rescale_energy'])
    orderp = engine.calculate_order(order_function, system)
    # We now check if the kick was OK or not:
    # 1) check if the kick was too violent:
    left, _, right = interfaces
    if not left < orderp[0] < right:  # Kicked outside of boundaries!'
        trial_path.append(shooting_point)
        accept, trial_path.status = False, 'KOB'
        return accept, trial_path, trial_path.status
    # 2) If the kick is not aimless, we must check if we reject it or not:
    if not tis_settings['aimless']:
        accept_kick = metropolis_accept_reject(rgen, system, dek)
        # here call bias if needed
        # ... Insert call to bias ...
        if not accept_kick:  # Momenta Change Rejection
            trial_path.append(shooting_point)
            accept, trial_path.status = False, 'MCR'  # just to be explicit
            return accept, trial_path, trial_path.status
    # OK: kick was either aimless or it was accepted by Metropolis
    # we should now generate trajectories, but first check how long
    # it should be:
    if tis_settings['allowmaxlength']:
        maxlen = tis_settings['maxlength']
    else:
        maxlen = int((path.length - 2) / rgen.rand()) + 2
        maxlen = min(maxlen, tis_settings['maxlength'])
    # since forward path must be at least one step, max for backwards is:
    maxlenb = maxlen - 1
    # generate the backward path:
    path_back = path.empty_path(maxlen=maxlenb)
    logger.debug('Propagating backwards for shooting move...')
    success_back, _ = engine.propagate(path_back, system, order_function,
                                       interfaces, reverse=True)

    time_shoot = path.time_origin + idx
    path_back.time_origin = time_shoot
    if not success_back:
        # Something went wrong, most probably the path length was exceeded
        # BTL is backward trajectory too long (maxlenb was exceeded)
        accept, trial_path.status = False, 'BTL'
        # Add the failed path to trial path for analysis:
        trial_path += path_back
        if path_back.length == tis_settings['maxlength'] - 1:
            # BTX is backward tracejctory longer than maximum memory
            trial_path.status = 'BTX'
        return accept, trial_path, trial_path.status
    # Backward seems OK so far, check if the ending point is correct:
    if path_back.get_end_point(left, right) != tis_settings['start_cond']:
        # Nope, backward trajectory end at wrong interface
        accept, trial_path.status = False, 'BWI'
        trial_path += path_back  # just store path for analysis
        return accept, trial_path, trial_path.status
    # Everything seems fine, propagate forward
    maxlenf = maxlen - path_back.length + 1
    path_forw = path.empty_path(maxlen=maxlenf)
    logger.debug('Propagating forwards for shooting move...')
    success_forw, _ = engine.propagate(path_forw, system, order_function,
                                       interfaces, reverse=False)
    path_forw.time_origin = time_shoot
    # Now, the forward could have failed by exceeding `maxlenf`,
    # however, it could also fail when we paste together so that
    # the length is larger than the allowed maximum, we paste first
    # and ask later:
    trial_path = paste_paths(path_back, path_forw, overlap=True,
                             maxlen=tis_settings['maxlength'])
    # Also update information about the shooting:
    trial_path.generated = ('sh', orderp[0], idx, path_back.length - 1)
    if not success_forw:
        accept, trial_path.status = False, 'FTL'
        if trial_path.length == tis_settings['maxlength']:
            trial_path.status = 'FTX'  # exceeds "memory"
        return accept, trial_path, trial_path.status
    # We have made it so far, the last check:
    # Did we cross the middle interface?
    _, _, _, cross = trial_path.check_interfaces(interfaces)
    if not cross[1]:  # not crossed middle
        accept, trial_path.status = False, 'NCR'
    else:
        accept, trial_path.status = True, 'ACC'
    return accept, trial_path, trial_path.status
