# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""This file contains functions used in TIS.

This module defines the functions needed to perform TIS simulations.
The algorithms are implemented as described by van Erp et al. [TIS]_.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

make_tis_step
    Function that will perform a single TIS step.

make_tis_step_ensemble
    Function to preform a TIS step for a path ensemble. It will handle
    adding of the path to a path ensemble object.

generate_initial_path_kick
    Function for generating an initial path by repeatedly kicking a
    phase point.

References
~~~~~~~~~~

.. [TIS] Titus S. van Erp, Daniele Moroni and Peter G. Bolhuis,
   J. Chem. Phys. 118, 7762 (2003),
   https://dx.doi.org/10.1063%2F1.1562614
"""
from __future__ import absolute_import
import logging
import numpy as np
from pyretis.core.path import Path, paste_paths
from pyretis.core.montecarlo import metropolis_accept_reject
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['make_tis_step_ensemble', 'make_tis_step',
           'generate_initial_path_kick']


def make_tis_step_ensemble(path_ensemble, system, order_function, integrator,
                           rgen, tis_settings, cycle):
    """Function to preform TIS step for a path ensemble.

    This function will run `make_tis_step` for the given path_ensemble.
    It will handle adding of the path. This function is intended for
    convenience when working with path ensembles. If we are using the
    path ensemble ``[0^-]`` then the start condition should be 'R' for
    right.

    Parameters
    ----------
    path_ensemble : object like :py:class:`.pathensemble.PathEnsemble`
        This is the path ensemble to perform the TIS step for.
    system : object like :py:class:`.system.System`
        System is used here since we need access to the temperature
        and to the particle list.
    order_function : object like :py:class:`OrderParameter`
        The class used for obtaining the order parameter(s).
    integrator : object like :py:class:`Integrator`
        A integrator to use for propagating a path.
    rgen : object like :py:class:`random_gen.RandomGenerator`
        This is the random generator that will be used.
    tis_settings : dict
        This dictionary contain the TIS settings. Here we set the
        setting for the starting condition (`'start_cond'`) according to
        the given path ensemble. The other `tis_settings` are just
        passed on.
    cycle : int
        The current cycle number

    Returns
    -------
    out[0] : boolean
        True if new path can be accepted
    out[1] : object like :py:class:`Path`
        The generated path.
    out[2] : string
        The status of the path
    """
    tis_settings['start_cond'] = path_ensemble.get_start_condition()
    msgtxt = 'TIS move in: {}'.format(path_ensemble.ensemble_name)
    logger.debug(msgtxt)
    accept, trial, status = make_tis_step(path_ensemble.last_path,
                                          system,
                                          order_function,
                                          path_ensemble.interfaces,
                                          integrator,
                                          rgen,
                                          tis_settings)
    if accept:
        msgtxt = 'The move was accepted'
    else:
        msgtxt = 'The move was rejected ({})'.format(status)
    logger.debug(msgtxt)
    path_ensemble.add_path_data(trial, status, cycle=cycle)
    return accept, trial, status


def initiate_path_ensemble(path_ensemble, system, order_function,
                           integrator, rgen, tis_settings, cycle=0):
    """This function will run the initiate for a given ensemble.

    This function is intended for convenience. It should handle and
    call all the possible initiation methods.

    Parameters
    ----------
    path_ensemble : object like :py:class:`PathEnsemble`
        The path ensemble to create an initial path for.
    system : object like :py:class:`System`
        System is used here since we need access to the temperature
        and to the particle list.
    order_function : object like :py:class:`OrderParameter`
        The class used for obtaining the order parameter(s).
    integrator : object like :py:class:`Integrator`
        A integrator to use for propagating a path.
    rgen : object like :py:class:`RandomGenerator`
        This is the random generator that will be used.
    tis_settings : dict
        This dictionary contain the TIS settings. Here we set the
        setting for the starting condition (`'start_cond'`) according
        to the given path ensemble. We are also using the keyword
        `initial_path` to determine how the initial path should be
        initiated. The other `tis_settings` are just passed on.
    cycle : integer, optional
        The cycle number we are initiating at, typically this will be 0
        which is the default value.
    """
    tis_settings['start_cond'] = path_ensemble.get_start_condition()
    initial_path = None
    status = ''
    if tis_settings['initial_path'] not in ['kick']:
        logger.error('Unknown initiation method')
        raise ValueError('Unknown initiation method')
    if tis_settings['initial_path'] == 'kick':
        initial_path = generate_initial_path_kick(system, order_function,
                                                  path_ensemble.interfaces,
                                                  integrator, rgen,
                                                  tis_settings)
        status = 'ACC'
    path_ensemble.add_path_data(initial_path, status, cycle=cycle)


def make_tis_step(path, system, order_function, interfaces, integrator, rgen,
                  tis_settings):
    """Perform a TIS step and generate a new path/trajectory.

    The new path will be generated from an existing one, either by
    performing a time-reversal move or by shooting. T(h)is is determined
    randomly by drawing a random number from a uniform distribution.

    Parameters
    ----------
    path : object like :py:class:`Path`
        This is the input path which will be used for generating a
        new path.
    system : object like :py:class:`System`
        System is used here since we need access to the temperature
        and to the particle list.
    order_function : object like :py:class:`OrderParameter`
        The class used for obtaining the order parameter(s).
    interfaces : list of floats
        These are the interface positions on form [left, middle, right]
    integrator : object like :py:class:`Integrator`
        A integrator to use for propagating a path.
    rgen : object like :py:class:`RandomGenerator`
        Random number generator used to determine what TIS move to
        perform.
    tis_settings : dict
        This dictionary contain the settings for the TIS method. Here we
        explicitly use:

        * `freq`: float, the frequency of how often we should do time
          reversal moves.

    Returns
    -------
    out[0] : boolean
        True if new path can be accepted
    out[1] : object like :py:class:`Path`
        The generated path.
    out[2] : string
        The status of the path
    """
    if rgen.rand() < tis_settings['freq']:
        logger.debug('Selected a time reversal move.')
        accept, new_path, status = _time_reversal(path, interfaces,
                                                  tis_settings['start_cond'])
    else:
        logger.debug('Selected a shooting move.')
        accept, new_path, status = _shoot(path, system, order_function,
                                          interfaces, integrator, rgen,
                                          tis_settings)
    return accept, new_path, status


def _time_reversal(path, interfaces, start_condition):
    """Perform a time-reversal move.

    Parameters
    ----------
    path : object like :py:class:`Path`
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
    out[1] : object like :py:class:`.path.Path`
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


def _shoot(path, system, order_function, interfaces, integrator, rgen,
           tis_settings):
    """Perform a shooting-move.

    This function will perform the shooting move from a randomly
    selected time-slice.

    Parameters
    ----------
    path : object like :py:class:`.path.Path`
        This is the input path which will be used for generating a
        new path.
    system : object like :py:class:`.system.System`
        System is used here since we need access to the temperature
        and to the particle list.
    order_function : object like :py:class:`OrderParameter`.
        The class used to calculate the order parameter.
    interfaces : list/tuple of floats
        These are the interface positions on form
        `[left, middle, right]`.
    integrator : object like :py:class:`Integrator`
        The integrator is used to propagate a path.
    rgen : object like :py:class:`.random_gen.RandomGenerator`
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
    out[1] : object like :py:class:`.path.PathBase`
        Returns the generated path.
    out[2] : string
        Status of the path, this is one of the strings defined in
        :py:const:`.path._STATUS`.
    """
    accept, trial_path = False, path.empty_path()  # return values
    orderp, pos, vel, vpot, idx = path.get_shooting_point()
    system.particles.pos = np.copy(pos)  # REPLACE to work with file names
    system.particles.vel = np.copy(vel)  # REPLACE ---------- "" ---------
    system.v_pot = vpot  # REPLACE to possibly work with file names
    # store info about this point, just in case we have to return
    # before completing a full new path:
    trial_path.generated = ('sh', orderp[0], idx, 0)
    # Modify the velocities:
    dek, _, = integrator.modify_velocities(
        system,
        rgen,
        sigma_v=tis_settings['sigma_v'],
        aimless=tis_settings['aimless'],
        momentum=tis_settings['zero_momentum'],
        rescale=tis_settings['rescale_energy'])
    orderp = integrator.calculate_order(order_function, system)
    # We now check if the kick was OK or not:
    # 1) check if the kick was too violent:
    left, _, right = interfaces
    if not left < orderp[0] < right:  # Kicked outside of boundaries!'
        trial_path.append(orderp, pos, vel, vpot)
        accept, trial_path.status = False, 'KOB'
        return accept, trial_path, trial_path.status
    # 2) If the kick is not aimless, we must check if we reject it or not:
    if not tis_settings['aimless']:
        accept_kick = metropolis_accept_reject(rgen, system, dek)
        # here call bias if needed
        # ... Insert call to bias ...
        if not accept_kick:  # Momenta Change Rejection
            trial_path.append(orderp, pos, vel, vpot)
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
    success_back, _ = integrator.propagate(path_back, system, order_function,
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
    success_forw, _ = integrator.propagate(path_forw, system, order_function,
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


def _kick_across_middle(system, order_function, integrator, rgen, middle,
                        tis_settings):
    """Force a phase point across the middle interface.

    This is accomplished by repeatedly kicking the pahse point so
    that it crosses the middle interface.

    Parameters
    ----------
    system : object like :py:class:`.system.System`
        This is the system that contains the particles we are
        investigating
    order_function : object like :py:class:`OrderParameter`
        The object used for calculating the order parameter.
    integrator : object like :py:class:`Integrator`
        The object used for integrating the equations of motion.
    rgen : object like :py:class:`.random_gen.RandomGenerator`
        This is the random generator that will be used.
    middle : float
        This is the value for the middle interface.
    tis_settings : dict
        This dictionary contains settings for TIS. Explicitly used here:

        * `zero_momentum`: boolean, determines if the momentum is zeroed
        * `rescale_energy`: boolean, determines if energy is rescaled.

    Returns
    -------
    out[0] : dict
        This dict contains the phase-point just before the interface.
        It is obtained by calling the `get_phase_point()` of the
        particles object.
    out[1] : dict
        This dict contains the phase-point just after the interface.
        It is obtained by calling the `get_phase_point()` of the
        particles object.

    Note
    ----
    This function will update the system state so that the
    `system.particles.get_phase_point() == out[1]`. This is more
    convenient for the following usage in the
    `generate_initial_path_kick` function.
    """
    # We search for crossing with the middle interface and do this
    # by sequentially kicking the initial phase point:
    previous = None
    particles = system.particles
    curr = integrator.calculate_order(order_function, system)[0]
    while True:
        # save current state:
        previous = particles.get_phase_point()
        previous['order'] = curr
        # Modify velocities
        integrator.modify_velocities(system,
                                     rgen,
                                     sigma_v=None,
                                     aimless=True,
                                     momentum=tis_settings['zero_momentum'],
                                     rescale=tis_settings['rescale_energy'])
        # Integrate forward one step:
        integrator.integration_step(system)
        # Compare previous order parameter and the new one:
        prev = curr
        curr = integrator.calculate_order(order_function, system)[0]
        if (prev <= middle < curr) or (curr < middle <= prev):
            # have crossed middle interface, just stop the loop
            break
        elif (prev <= curr < middle) or (middle < curr <= prev):
            # are getting closer, keep the new point
            pass
        else:  # we did not get closer, fall back to previous point
            particles.set_phase_point(previous)
            curr = previous['order']
    return previous, particles.get_phase_point()


def generate_initial_path_kick(system, order_function, interfaces, integrator,
                               rgen, tis_settings):
    """Simple function to generate an initial path.

    This function will generate an initial path by repeatedly kicking a
    phase-space point until the middle interface is crossed.
    The point before and after kicking are stored, so when the
    middle interface is crossed we have two points we can integrate
    forward and backward in time. This function is intended for use with
    TIS. For use with RETIS one should set the appropriate
    `tis_settings` so that the starting conditions are fine (i.e. for
    the [0^-] ensemble it might be different for the other ensembles).

    Parameters
    ----------
    system : object like :py:class:`.system.System`
        This is the system that contains the particles we are
        investigating.
    order_function : object like :py:class:`OrderParameter`
        The class used for obtaining the order parameter(s).
    interfaces : list of floats
        These are the interface positions on form
        `[left, middle, right]`.
    integrator : object like :py:class:`Integrator`
        This is the propagator of the simulation
    rgen : object like :py:class:`.random_gen.RandomGenerator`
        This is the random generator that will be used.
    tis_settings : dict
        This dictionary contains settings for TIS. Explicitly used here:

        * `start_cond`: string, starting condition, 'L'eft or 'R'ight
        * `maxlength`: integer, maximum allowed length of paths.

        Note that also `_fix_path_by_tis` and `kick_across_middle`
        will use `tis_settings`.

    Returns
    -------
    out : object like :py:class:`.path.PathBase`
        This is the generated initial path
    """
    leftpoint, _ = _kick_across_middle(system, order_function, integrator,
                                       rgen, interfaces[1], tis_settings)
    # kick_across_middle will return two points, one immediately
    # left of the interface and one immediately right of the
    # interface. So we have two points (`leftpoint` and the
    # current `system.particles`). We then propagate the current
    # phase point forward:
    maxlen = tis_settings['maxlength']
    path_forw = Path(rgen, maxlen=maxlen)
    success, msg = integrator.propagate(path_forw, system, order_function,
                                        interfaces, reverse=False)
    if not success:
        msgtxt = 'Forward path not successful: {}'.format(msg)
        logger.error(msgtxt)
        raise ValueError('Forward path not successful.', msg)
    # And we propagate the `leftpoint` backward:
    system.particles.set_phase_point(leftpoint)
    path_back = Path(rgen, maxlen=maxlen)
    success, msg = integrator.propagate(path_back, system, order_function,
                                        interfaces, reverse=True)
    if not success:
        msgtxt = 'Backward path not successful: {}'.format(msg)
        logger.error(msgtxt)
        raise ValueError('Backward path not successful.', msg)
    # Merge backward and forward, here we do not set maxlen since
    # both backward and forward may have this length
    initial_path = paste_paths(path_back, path_forw, overlap=False)
    if initial_path.length >= maxlen:
        msgtxt = 'Initial path too long (exceeded "MAXLEN").'
        logger.error(msgtxt)
        raise ValueError(msgtxt)
    start, end, _, _ = initial_path.check_interfaces(interfaces)
    # OK, now its time to check the path:
    # 0) We can start at the starting condition, pass the middle
    # and continue all the way to the end - perfect!
    # 1) we can start at the starting condition, pass the middle
    # and return to starting condition - this is perfectly fine
    # 2) We can start at the wrong interface, pass the middle and
    # end at the same (wrong) interface - we now need to do some shooting moves
    # 3) We can start at wrong interface and end and the starting condition
    # we just have to reverse the path then.
    if start == tis_settings['start_cond']:  # case 0 and 1
        initial_path.generated = ('ki', 0, 0, 0)
        initial_path.status = 'ACC'
        return initial_path
    # Now we do the other cases:
    if end == tis_settings['start_cond']:  # case 3 (and start != start_cond)
        msgtxt = 'Initial path is in the wrong direction: Reversing it!'
        logger.info(msgtxt)
        initial_path = initial_path.reverse()
        initial_path.generated = ('ki', 0, 0, 0)
        initial_path.status = 'ACC'
    elif end == start:  # case 2
        msgtxt = ('Initial path start & end at wrong interface.' +
                  '\nRunning TIS to fix it!')
        logger.info(msgtxt)
        initial_path = _fix_path_by_tis(initial_path, system,
                                        order_function, interfaces,
                                        integrator, rgen, tis_settings)
    else:
        logger.error('Could not generate initial path.')
        raise ValueError('Could not generate initial path.')
    return initial_path


def _fix_path_by_tis(initial_path, system, order_function, interfaces,
                     integrator, rgen, tis_settings):
    """Fix a path that starts and ends at the wrong interfaces.

    The fix is performed by making TIS moves and this function is
    intended to be used in a initialization.

    Parameters
    ----------
    initial_path : object like :py:class:`.path.Path`
        This is the initial path to fix. It starts & ends at the
        wrong interface.
    system : object like :py:class:`.system.System`
        This is the system that contains the particles we are
        investigating
    order_function : object like :py:class:`OrderParameter`
        The object used for calculating the order parameter(s).
    interfaces : list of floats
        These are the interface positions on form
        `[left, middle, right]`.
    integrator : object like :py:class:`Integrator`
        This is the propagator of the simulation
    rgen : object like :py:class:`.random_gen.RandomGenerator`
        This is the random generator that will be used.
    tis_settings : dict
        Settings for TIS method, here we explicitly use:

        * `start_cond`: string which defines the start condition.
        * `maxlength`: integer which give the maximum allowed path
          length.

        Note that we here explicitly set some local TIS settings for
        use in the `make_tis_step` function.

    Returns
    -------
    out : object like :py:class:`.path.PathBase`
        The amended path.
    """
    left, middle, right = interfaces
    path_ok = False
    local_tis_settings = {'allowmaxlength': True,
                          'aimless': True,
                          'freq': 0.5}
    for key in ('start_cond', 'maxlength', 'zero_momentum', 'rescale_energy'):
        local_tis_settings[key] = tis_settings[key]

    while not path_ok:
        accept, trial, _ = make_tis_step(initial_path,
                                         system,
                                         order_function,
                                         interfaces,
                                         integrator,
                                         rgen,
                                         local_tis_settings)
        if accept:
            if tis_settings['start_cond'] == 'R':
                # if new path is better, use it:
                if (trial.ordermax[0] > initial_path.ordermax[0] and
                        trial.ordermin[0] < middle):
                    initial_path = trial
                path_ok = initial_path.ordermax[0] > right
            elif tis_settings['start_cond'] == 'L':
                # if new path is better, use it:
                if (trial.ordermin[0] < initial_path.ordermin[0] and
                        trial.ordermax[0] > middle):
                    initial_path = trial
                path_ok = initial_path.ordermin[0] < left
            else:
                logger.error('Unknown start condition (should be R/L')
                raise ValueError('Unknown start condition (should be R/L)')
    initial_path.generated = ('ki', 0, 0, 0)
    initial_path.status = 'ACC'
    return initial_path
