# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""This file contains functions used in TIS.

This module defines the functions needed to perform TIS simulations.
The algorithms are implemented as described by van Erp et al. [TIS]_.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

make_tis_step (:py:func:`.make_tis_step`)
    A method that will perform a single TIS step.

make_tis_step_ensemble (:py:func:`.make_tis_step_ensemble`)
    A method to perform a TIS step for a path ensemble. It will handle
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
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
logger.addHandler(logging.NullHandler())


__all__ = ['make_tis_step_ensemble',
           'make_tis_step',
           'shoot',
           'time_reversal']


def make_tis_step_ensemble(path_ensemble, order_function, engine,
                           rgen, tis_settings, cycle):
    """Perform a TIS step in a given path ensemble.

    This function will run :py:func:`.make_tis_step` for the
    given path ensemble and handling adding of the path to the path
    ensemble.

    Parameters
    ----------
    path_ensemble : object like :py:class:`.PathEnsemble`
        This is the path ensemble to perform the TIS step for.
    order_function : object like :py:class:`.OrderParameter`
        The class used for obtaining the order parameter(s).
    engine : object like :py:class:`.EngineBase`
        The engine to use for propagating a path.
    rgen : object like :py:class:`.RandomGenerator`
        This is the random generator that will be used.
    tis_settings : dict
        This dictionary contains the TIS settings.
    cycle : int
        The current cycle number.

    Returns
    -------
    out[0] : boolean
        True if the new path can be accepted, False otherwise.
    out[1] : object like :py:class:`.PathBase`
        The generated path.
    out[2] : string
        The status of the path.

    """
    start_cond = path_ensemble.start_condition
    logger.info('TIS move in: %s', path_ensemble.ensemble_name)
    engine.exe_dir = path_ensemble.directory['generate']
    accept, trial, status = make_tis_step(path_ensemble.last_path,
                                          order_function,
                                          path_ensemble.interfaces,
                                          engine,
                                          rgen,
                                          tis_settings,
                                          start_cond)
    if accept:
        logger.info('The move was accepted!')
    else:
        logger.info('The move was rejected! (%s)', status)
    path_ensemble.add_path_data(trial, status, cycle=cycle)
    return accept, trial, status


def make_tis_step(path, order_function, interfaces, engine, rgen,
                  tis_settings, start_cond):
    """Perform a TIS step and generate a new path.

    The new path will be generated from the input path, either by
    performing a time-reversal move or by a shooting move. This is
    determined pseudo-randomly by drawing a random number from a
    uniform distribution using the given random generator.

    Parameters
    ----------
    path : object like :py:class:`.PathBase`
        This is the input path which will be used for generating a
        new path.
    order_function : object like :py:class:`.OrderParameter`
        The class used for obtaining the order parameter(s).
    interfaces : list of floats
        These are the interface positions on ordered form
        ``[left, middle, right]``.
    engine : object like :py:class:`.EngineBase`
        The engine to use for propagating a path when integrating the
        equations of motion.
    rgen : object like :py:class:`.RandomGenerator`
        Random number generator used to determine what TIS move to
        perform.
    tis_settings : dict
        This dictionary contains the settings for the TIS method. Here we
        explicitly use:

        * `freq`: float, the frequency of how often we should do time
          reversal moves.
    start_cond : string
        The starting condition for the path. This is determined by the
        ensemble we are generating for - it is 'R'ight or 'L'eft.

    Returns
    -------
    out[0] : boolean
        True if the new path can be accepted.
    out[1] : object like :py:class:`.PathBase`
        The generated path.
    out[2] : string
        The status of the path.

    """
    if rgen.rand() < tis_settings['freq']:
        logger.info('Performing a time reversal move')
        accept, new_path, status = time_reversal(path, order_function,
                                                 interfaces, start_cond)
    else:
        logger.info('Performing a shooting move.')
        accept, new_path, status = shoot(path, order_function,
                                         interfaces, engine, rgen,
                                         tis_settings, start_cond)
    return accept, new_path, status


def time_reversal(path, order_function, interfaces, start_condition):
    """Perform a time-reversal move.

    Parameters
    ----------
    path : object like :py:class:`.PathBase`
        This is the input path which will be used for generating a
        new path.
    order_function : object like :py:class:`.OrderParameter`
        The class used for obtaining the order parameter(s).
    interfaces : list/tuple of floats
        These are the interface positions of the form
        ``[left, middle, right]``.
    start_condition : string
        The starting condition, 'L'eft or 'R'ight.

    Returns
    -------
    out[0] : boolean
        True if the path can be accepted.
    out[1] : object like :py:class:`.PathBase`
        The time reversed path.
    out[2] : string
        Status of the path, this is one of the strings defined in
        `.path._STATUS`.

    """
    new_path = path.reverse(order_function)
    start, _, _, _ = new_path.check_interfaces(interfaces)
    # Explicitly set how this was generated. Keep the old if loaded.
    if path.get_move() == 'ld':
        new_path.set_move('ld')
    else:
        new_path.generated = ('tr', 0, 0, 0)

    if start == start_condition:
        accept = True
        status = 'ACC'
    else:
        accept = False
        status = 'BWI'  # Backward trajectory end at wrong interface.
    new_path.status = status
    return accept, new_path, status


def prepare_shooting_point(path, order_function, engine, rgen, tis_settings):
    """Select and modify velocities for a shooting move.

    This method will randomly select a shooting point from a given
    path and modify its velocities.

    Parameters
    ----------
    path : object like :py:class:`.PathBase`
        This is the input path which will be used for generating a
        new path.
    order_function : object like :py:class:`.OrderParameter`
        The class used to calculate the order parameter.
    engine : object like :py:class:`.EngineBase`
        The engine to use for propagating a path.
    rgen : object like :py:class:`.RandomGenerator`
        This is the random generator that will be used.
    tis_settings : dict
        This contains the settings for TIS. Here, we use the
        settings which dictates how we modify the velocities.

    Returns
    -------
    out[0] : object like :py:class:`.System`
        The shooting point with modified velocities.
    out[1] : integer
        The index of the shooting point in the original path.
    out[2] : float
        The change in kinetic energy when modifying the velocities.

    """
    shooting_point, idx = path.get_shooting_point()
    orderp = shooting_point.order
    logger.info('Shooting from order parameter/index: %f, %d', orderp[0], idx)
    # Copy the shooting point, so that we can modify velocities without
    # altering the original path:
    system = shooting_point.copy()
    # Modify the velocities:
    dek, _, = engine.modify_velocities(
        system,
        rgen,
        sigma_v=tis_settings['sigma_v'],
        aimless=tis_settings['aimless'],
        momentum=tis_settings['zero_momentum'],
        rescale=tis_settings['rescale_energy'],
    )
    orderp = engine.calculate_order(order_function, system)
    system.order = orderp
    return system, idx, dek


def check_kick(shooting_point, interfaces, trial_path, rgen, dek,
               tis_settings):
    """Check the modification of the shooting point.

    After generating velocities for a shooting point, we
    do some additional checking to see if the shooting point is
    acceptable.

    Parameters
    ----------
    shooting_point : object like :py:class:`.System`
        The shooting point with modified velocities.
    interfaces : list of floats
        The interfaces used for TIS.
    trial_path : objeckt like :py:class:`.PathBase`
        The path we are currently generating.
    rgen : object like :py:class:`.RandomGenerator`
        This is the random generator that will be used to check if
        we accept the shooting point based on the change in kinetic
        energy.
    dek : float
        The change in kinetic energy when modifying the velocities.
    tis_settings : dict
        This contains the settings for TIS.

    Returns
    -------
    out : boolean
        True if the kick was OK, False otherwise.

    """
    # 1) Check if the kick was too violent:
    left, _, right = interfaces
    if not left < shooting_point.order[0] < right:
        # Shooting point was velocity dependent and was kicked outside
        # of boundaries when modifying velocities.
        trial_path.append(shooting_point)
        trial_path.status = 'KOB'
        return False
    # 2) If the kick is not aimless, we check if we reject it or not:
    if not tis_settings['aimless']:
        accept_kick = metropolis_accept_reject(rgen, shooting_point, dek)
        # If one wish to implement a bias call, this can be done here.
        if not accept_kick:
            trial_path.append(shooting_point)
            trial_path.status = 'MCR'  # Momenta Change Rejection.
            return False
    return True


def shoot_backwards(path_back, trial_path, shooting_point, engine,
                    order_function, interfaces, tis_settings, start_cond):
    """Shoot in the backward time direction.

    Parameters
    ----------
    path_back : object like :py:class:`.PathBase`
        The path we will fill with phase points from the propagation.
    trial_path : object like :py:class:`.PathBase`
        The current trial path generated by the shooting.
    shooting_point : object like :py:class:`.System`
        The shooting point used as the starting point for the
        propagation.
    engine : object like :py:class:`.EngineBase`
        The engine to use for propagating a path.
    order_function : object like :py:class:`.OrderParameter`
        The class used to calculate the order parameter.
    interfaces : list/tuple of floats
        These are the interface positions of the form
        ``[left, middle, right]``.
    tis_settings : dict
        This contains the settings for TIS.
    start_cond : string
        The starting condition for the current ensemble, 'L'eft or
        'R'ight.

    Returns
    -------
    out : boolean
        True if the backward path was generated successfully, False
        otherwise.

    """
    logger.debug('Propagating backwards for the shooting move.')
    path_back.time_origin = trial_path.time_origin
    success_back, _ = engine.propagate(path_back, shooting_point,
                                       order_function, interfaces,
                                       reverse=True)
    if not success_back:
        # Something went wrong, most probably the path length was exceeded.
        trial_path.status = 'BTL'  # BTL = backward trajectory too long.
        # Add the failed path to trial path for analysis:
        trial_path += path_back
        if path_back.length == tis_settings['maxlength'] - 1:
            # BTX is backward tracejctory longer than maximum memory.
            trial_path.status = 'BTX'
        return False
    # Backward seems OK so far, check if the ending point is correct:
    left, _, right = interfaces
    if path_back.get_end_point(left, right) != start_cond:
        # Nope, backward trajectory end at wrong interface.
        trial_path.status = 'BWI'
        trial_path += path_back  # Store path for analysis.
        return False
    return True


def shoot(path, order_function, interfaces, engine, rgen,
          tis_settings, start_cond):
    """Perform a shooting-move.

    This function will perform the shooting move from a randomly
    selected time-slice.

    Parameters
    ----------
    path : object like :py:class:`.PathBase`
        This is the input path which will be used for generating a
        new path.
    order_function : object like :py:class:`.OrderParameter`
        The class used to calculate the order parameter.
    interfaces : list/tuple of floats
        These are the interface positions of the form
        ``[left, middle, right]``.
    engine : object like :py:class:`.EngineBase`
        The engine to use for propagating a path.
    rgen : object like :py:class:`.RandomGenerator`
        This is the random generator that will be used.
    tis_settings : dict
        This contains the settings for TIS. Keys used here:

        * `aimless`: boolean, is the shooting aimless or not?
        * `allowmaxlength`: boolean, should paths be allowed to reach
          maximum length?
        * `maxlength`: integer, maximum allowed length of paths.
    start_cond : string
        The starting condition for the current ensemble, 'L'eft or
        'R'ight.

    Returns
    -------
    out[0] : boolean
        True if the path can be accepted.
    out[1] : object like :py:class:`.PathBase`
        Returns the generated path.
    out[2] : string
        Status of the path, this is one of the strings defined in
        :py:const:`.path._STATUS`.

    """
    trial_path = path.empty_path()  # The trial path we will generate.
    shooting_point, idx, dek = prepare_shooting_point(
        path, order_function, engine, rgen, tis_settings
    )
    # Store info about this point, just in case we have to return
    # before completing a full new path:
    trial_path.generated = ('sh', shooting_point.order[0], idx, 0)
    trial_path.time_origin = path.time_origin + idx
    # We now check if the kick was OK or not:
    if not check_kick(shooting_point, interfaces, trial_path, rgen, dek,
                      tis_settings):
        return False, trial_path, trial_path.status
    # OK: kick was either aimless or it was accepted by Metropolis
    # we should now generate trajectories, but first check how long
    # it should be (if the path comes from a load, it is assumed to not
    # respect the detail balance anyway):
    if path.get_move() == 'ld' or tis_settings['allowmaxlength']:
        maxlen = tis_settings['maxlength']
    else:
        maxlen = min(int((path.length - 2) / rgen.rand()) + 2,
                     tis_settings['maxlength'])
    # Since the forward path must be at least one step, the maximum
    # length for the backward path is maxlen-1.
    # Generate the backward path:
    path_back = path.empty_path(maxlen=maxlen-1)
    if not shoot_backwards(path_back, trial_path, shooting_point, engine,
                           order_function, interfaces, tis_settings,
                           start_cond):
        return False, trial_path, trial_path.status
    # Everything seems fine, now propagate forward.
    # Note that the length of the forward path is adjusted to
    # account for the fact that it shares a point with the backward
    # path (i.e. the shooting point). The duplicate point is just
    # counted once when the paths are merged by the method
    # `paste_paths` by setting `overlap=True` (which indicates that
    # the forward and backward paths share a point).
    path_forw = path.empty_path(maxlen=(maxlen - path_back.length + 1))
    logger.debug('Propagating forwards for shooting move...')
    success_forw, _ = engine.propagate(path_forw, shooting_point,
                                       order_function, interfaces,
                                       reverse=False)
    path_forw.time_origin = trial_path.time_origin
    # Now, the forward propagation could have failed by exceeding the
    # maximum length for the forward path. However, it could also fail
    # when we paste together so that the length is larger than the
    # allowed maximum. We paste first and ask later:
    trial_path = paste_paths(path_back, path_forw, overlap=True,
                             maxlen=tis_settings['maxlength'])
    # Also update information about the shooting:
    trial_path.generated = ('sh', shooting_point.order[0], idx,
                            path_back.length - 1)
    if not success_forw:
        trial_path.status = 'FTL'
        # If we reached this point, the backward path was successful,
        # but the forward was not. For the case where the forward was
        # also successful, the length of the trial path cannot exceed
        # the maximum length given in the TIS settings. Thus we only
        # need to check this here, i.e. when given that the backward
        # was successful and the forward not:
        if trial_path.length == tis_settings['maxlength']:
            trial_path.status = 'FTX'  # exceeds "memory".
        return False, trial_path, trial_path.status
    # Last check - Did we cross the middle interface?
    if not trial_path.check_interfaces(interfaces)[-1][1]:
        # No, we did not cross the middle interface:
        trial_path.status = 'NCR'
        return False, trial_path, trial_path.status
    trial_path.status = 'ACC'
    return True, trial_path, trial_path.status
