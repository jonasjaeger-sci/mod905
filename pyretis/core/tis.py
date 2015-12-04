# -*- coding: utf-8 -*-
"""This file contains functions used in TIS.

This module defines the functions needed to perform TIS simulations.
The algorithms are implemented as described by van Erp et al. [TIS]_.


Important functions defined here:

- make_tis_step: Function that will perform a single TIS step.

- generate_initial_path_kick: Function for generating an initial path by
  repeatedly kicking a phase point.


References
~~~~~~~~~~

.. [TIS] Titus S. van Erp, Daniele Moroni and Peter G. Bolhuis,
   J. Chem. Phys. 118, 7762 (2003),
   https://dx.doi.org/10.1063%2F1.1562614
"""
from __future__ import absolute_import
import numpy as np
from pyretis.core.path import Path, paste_paths, reverse_path
from pyretis.core.montecarlo import metropolis_accept_reject
from pyretis.core.particlefunctions import calculate_kinetic_energy

__all__ = ['make_tis_step', 'generate_initial_path_kick', 'propagate']


def make_tis_step_ensemble(path_ensemble, system, order_function,
                           integrator, rgen, tis_settings, cycle):
    """Function to preform TIS step for a path ensemble.

    This function will run `make_tis_step` for the given path_ensemble.
    It will handle adding of the path. This function is intended for
    convenience when working with path ensembles. If we are using the path
    ensemble ``[0^-]`` then the start condition should be 'R' for right.

    Parameters
    ----------
    path_ensemble : object like `PathEnsemble` from `pyretis.core.path`
        This is the path ensemble to perform the TIS step for.
    system : object like `System` from `pyretis.core.system`
        System is used here since we need access to the temperature
        and to the particle list.
    order_function : function
        This function takes the system as it's argument and returns a float
        which is equal to the order parameter.
    integrator : object like `Integrator` from `pyretis.core.integrators`
        A integrator to use for propagating a path.
    rgen : object like `RandomGenerator` from `pyretis.core.random_gen`
        This is the random generator that will be used.
    tis_settings : dict
        This dictionary contain the TIS settings. Here we set the setting
        for the starting condition (`'start_cond'`) according to the given
        path ensemble. The other `tis_settings` are just passed on.
    cycle : int
        The current cycle number

    Returns
    -------
    out[0] : boolean
        True if new path can be accepted
    out[1] : object like `Path` from `pyretis.core.path`
        The generated path.
    out[2] : string
        The status of the path
    """
    tis_settings['start_cond'] = path_ensemble.get_start_condition()
    accept, trial, status = make_tis_step(path_ensemble.last_path,
                                          system,
                                          path_ensemble.interfaces,
                                          order_function,
                                          integrator,
                                          rgen,
                                          tis_settings)
    path_ensemble.add_path_data(trial, status, cycle=cycle)
    return accept, trial, status


def initiate_path_ensemble(path_ensemble, system, order_function,
                           integrator, rgen, tis_settings, cycle=0):
    """This function will run the initiate for a given ensemble.

    This function is intended for convenience. It should handle and call all
    the possible initiation methods.

    Parameters
    ----------
    path_ensemble : object like `pyretis.core.path.PathEnsemble`
        The path ensemble to create an initial path for.
    system : object like `System` from `pyretis.core.system`
        System is used here since we need access to the temperature
        and to the particle list.
    order_function : function
        This function takes the system as it's argument and returns a float
        which is equal to the order parameter.
    integrator : object like `Integrator` from `pyretis.core.integrators`
        A integrator to use for propagating a path.
    rgen : object like `RandomGenerator` from `pyretis.core.random_gen`
        This is the random generator that will be used.
    tis_settings : dict
        This dictionary contain the TIS settings. Here we set the setting
        for the starting condition (`'start_cond'`) according to the given
        path ensemble. We are also using the keyword `initial_path` to
        determine how the initial path should be initiated.
        The other `tis_settings` are just passed on.
    cycle : integer, optional
        The cycle number we are initiating at, typically this will be 0 which
        is the default value.
    """
    tis_settings['start_cond'] = path_ensemble.get_start_condition()
    initial_path = None
    status = ''
    if tis_settings['initial_path'] not in ['kick']:
        raise ValueError('Unknown initiation method')
    if tis_settings['initial_path'] == 'kick':
        initial_path = generate_initial_path_kick(system,
                                                  path_ensemble.interfaces,
                                                  order_function,
                                                  integrator,
                                                  rgen,
                                                  tis_settings)
        status = 'ACC'
    path_ensemble.add_path_data(initial_path, status, cycle=cycle)


def make_tis_step(path, system, interfaces, order_function, integrator, rgen,
                  tis_settings):
    """Perform a TIS step and generate a new path/trajectory.

    The new path will be generated from an existing one, either by performing
    a time-reversal move or by shooting. T(h)is is determined randomly by
    drawing a random number from a uniform distribution.

    Parameters
    ----------
    path : object like `Path` from `pyretis.core.path`
        This is the input path which will be used for generating a
        new path.
    system : object like `System` from `pyretis.core.system`
        System is used here since we need access to the temperature
        and to the particle list.
    interfaces : list of floats
        These are the interface positions on form [left, middle, right]
    order_function : function
        This function takes the system as it's argument and returns float(s)
        which is equal to the order parameter(s).
    integrator : object like `Integrator` from `pyretis.core.integrators`
        A integrator to use for propagating a path.
    rgen : object like `RandomGenerator` from `pyretis.core.random_gen`
        Random number generator used to determine what TIS move to perform.
    tis_settings : dict
        This dictionary contain the settings for the TIS method. Here we
        explicitly use:

        * `freq`: float, the frequency of how often we should do time reversal
          moves.

    Returns
    -------
    out[0] : boolean
        True if new path can be accepted
    out[1] : object like `Path` from `pyretis.core.path`
        The generated path.
    out[2] : string
        The status of the path
    """
    if rgen.rand() < tis_settings['freq']:
        # print('Reversing path')
        accept, new_path, status = _time_reversal(path, interfaces,
                                                  tis_settings['start_cond'])
    else:
        # print('Shooting')
        accept, new_path, status = _shoot(path, system, interfaces,
                                          order_function, integrator, rgen,
                                          tis_settings)
    return accept, new_path, status


def _time_reversal(path, interfaces, start_condition):
    """Perform a time-reversal move.

    Parameters
    ----------
    path : object like `Path` from `pyretis.core.path`
        This is the input path which will be used for generating a new path.
    interfaces : list/tuple of floats
        These are the interface positions on form [left, middle, right]
    start_condition : string
        The starting condition, 'L'eft or 'R'ight.

    Returns
    -------
    out[0] : boolean
        True if the path can be accepted
    out[1] : object like `Path` or `None`
        Returns the generated path if something was generated
        `Path` is defined in `pyretis.core.path`.
    out[2] : string
        Status of the path, this is one of the strings defined in
        `pyretis.core.path._STATUS`.
    """
    new_path = reverse_path(path)
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


def _shoot(path, system, interfaces, order_function, integrator, rgen,
           tis_settings):
    """Perform a shooting-move.

    This function will perform the shooting move from a randomly selected
    time-slice.

    Parameters
    ----------
    path : object like `Path` from `pyretis.core.path`
        This is the input path which will be used for generating a new path.
    system : object like `System` from `pyretis.core.system`
        System is used here since we need access to the temperature
        and to the particle list.
    interfaces : list/tuple of floats
        These are the interface positions on form `[left, middle, right]`.
    order_function : function
        This function takes the system as it's argument and returns a float
        which is equal to the order parameter.
    integrator : object like `Integrator` from `pyretis.core.integrators`
        The integrator is used to propagate a path.
    rgen : object like `RandomGenerator` from `pyretis.core.random_gen`
        This is the random generator that will be used.
    tis_settings : dict
        This contains the settings for TIS. Keys used here:

        * `aimless`: boolean, is the shooting aimless or not?
        * `allowmaxlength`: boolean, should paths be allowed to reach
          maximum length?
        * `start_cond`: string, starting condition, 'L'eft or 'R'ight
        * `maxlength`: integer, maximum allowed length of paths.

    Returns
    -------
    out[0] : boolean
        True if the path can be accepted
    out[1] : object like `Path` or `None`
        Returns the generated path if something was generated.
        `Path` is defined in `pyretis.core.path`.
    out[2] : string
        Status of the path, this is one of the strings defined in
        `pyretis.core.path._STATUS`.
    """
    accept, trial_path = False, Path()  # return values
    # trial_path is just an empty path for now
    # Select the shooting point from path at random.
    # We do not include the end point as these are out of bounds - i.e. they
    # have crossed the interface. See also the documentation for RETIS.
    idx = rgen.random_integers(1, len(path.path) - 2)
    pos, vel, orderp = path.path[idx][0:3]  # extract phase point
    system.particles.vel = np.copy(vel)
    system.particles.pos = np.copy(pos)
    system.potential_and_force()  # update forces and potential
    # store info about this point, just in case we have to return
    # before completing a full new path:
    trial_path.generated = ('sh', orderp[0], idx, 0)
    # kick the timeslice:
    dke = _kick_timeslice(system, rgen, aimless=tis_settings['aimless'],
                          momentum=False)[0]
    # update the order parameter since it could depend on velocity
    orderp = order_function(system)
    # We now check if the kick was OK or not:
    # 1) check if the kick was too violent:
    left, _, right = interfaces
    if not left < orderp[0] < right:  # Kicked outside of boundaries!'
        trial_path.append(pos, vel, orderp, system.v_pot)  # add shooting point
        accept, trial_path.status = False, 'KOB'  # just to be explicit
        return accept, trial_path, trial_path.status
    # 2) If the kick is not aimless, we much check if we reject it or not:
    if not tis_settings['aimless']:
        accept_kick = metropolis_accept_reject(rgen, system, dke)
        # here call bias if needed
        # ... Insert call to bias ...
        if not accept_kick:  # Momenta Change Rejection
            trial_path.append(pos, vel, orderp, system.v_pot)
            accept, trial_path.status = False, 'MCR'  # just to be explicit
            return accept, trial_path, trial_path.status
    # OK: kick was either aimless or it was accepted by Metropolis
    # we should now generate trajectories, but first check how long
    # it should be:
    if tis_settings['allowmaxlength']:
        maxlen = tis_settings['maxlength']
    else:
        maxlen = int((len(path.path) - 2) / rgen.rand()) + 2
        maxlen = min(maxlen, tis_settings['maxlength'])
    # since forward path must be at least one step, max for backwards is:
    maxlenb = maxlen - 1
    # generate the backward path:
    path_back, success_back, _ = propagate(system, interfaces,
                                           order_function,
                                           integrator,
                                           maxlen=maxlenb,
                                           reverse=True)
    time_shoot = path.time_origin + idx
    path_back.time_origin = time_shoot
    if not success_back:
        # something went wrong, most probably the path length was exceeded
        accept, trial_path.status = False, 'BTL'
        trial_path += path_back  # just store path for analysis
        # BTL is backward trajectory too long (maxlenb "too small")
        if len(path_back.path) == tis_settings['maxlength'] - 1:
            trial_path.status = 'BTX'  # exceeds maximum memory length
        return accept, trial_path, trial_path.status
    # backward seems OK so far, check if the ending point is correct:
    if path_back.get_end_point(left, right) != tis_settings['start_cond']:
        # backward trajectory end at wrong interface
        accept, trial_path.status = False, 'BWI'
        trial_path += path_back  # just store path for analysis
        return accept, trial_path, trial_path.status
    # everything seems fine, propagate forward
    maxlenf = maxlen - len(path_back.path) + 1
    path_forw, success_forw, _ = propagate(system,
                                           interfaces,
                                           order_function,
                                           integrator,
                                           maxlen=maxlenf,
                                           reverse=False)
    path_forw.time_origin = time_shoot
    # now, the forward could have failed by exceeding maxlenf
    # however, it could also fail when we paste together so that
    # the length is larger than the allowed maximum, we paste first
    # and ask later:
    trial_path = paste_paths(path_back, path_forw, overlap=True,
                             maxlen=tis_settings['maxlength'])
    # Also update information about the shooting:
    trial_path.generated = ('sh', orderp[0], idx, len(path_back.path) - 1)
    if not success_forw:
        accept, trial_path.status = False, 'FTL'
        if len(trial_path.path) == tis_settings['maxlength']:
            trial_path.status = 'FTX'  # exceeds "memory"
        return accept, trial_path, trial_path.status
    # we have made it so far, check if we cross middle interface
    # finally, check if middle interface was crossed:
    _, _, _, cross = trial_path.check_interfaces(interfaces)
    if not cross[1]:  # not crossed middle
        accept, trial_path.status = False, 'NCR'
    else:
        accept, trial_path.status = True, 'ACC'
    return accept, trial_path, trial_path.status


def generate_initial_path_kick(system, interfaces, order_function,
                               integrator, rgen, tis_settings):
    """Simple function to generate an initial path.

    This function will generate an initial path by repeatedly kicking a
    phase-space point until the middle interface is crossed.
    The point before and after kicking are stored, so when the
    middle interface is crossed we have two points we can integrate
    forward and backward in time. This function is intended for use with
    TIS. For use with RETIS one should set the appropriate `tis_settings`
    so that the starting conditions are fine (i.e. for the [0^-] ensemble
    it might be different for the other ensembles).

    Parameters
    ----------
    system : object like `System` from `pyretis.core.system`
        This is the system that contains the particles we are investigating
    interfaces : list of floats
        These are the interface positions on form [left, middle, right]
    order_function : function
        This is a function that calculates the order parameter for a
        system.
    integrator : object like `Integrator` from `pyretis.core.integrators`
        This is the propagator of the simulation
    rgen : object like `RandomGenerator` from `pyretis.core.random_gen`
        This is the random generator that will be used.
    tis_settings : dict
        This dictionary contains settings for TIS. Explicitly used here:

        * `start_cond`: string, starting condition, 'L'eft or 'R'ight
        * `maxlength`: integer, maximum allowed length of paths.

        Note that also `_fix_path_by_tis` will use the `tis_settings`.

    Returns
    -------
    out : object of type `Path` from `pyretis.core.path`
        This is the generated initial path
    """
    previous, _ = _kick_across_middle(system, order_function, integrator,
                                      rgen, interfaces[1])
    # note: current point is stored in system
    # Loop is done, we have two points (previous and the
    # current system.particles)
    # we can propagate current phase point forward:
    path_forw, success, msg = propagate(system, interfaces, order_function,
                                        integrator,
                                        maxlen=tis_settings['maxlength'])
    if not success:
        raise ValueError('Forward path not successful.', msg)
    # and previous phase point backward.
    # First we set system to be at this point:
    system.particles.set_phase_point(previous)
    # then propagate :-)
    path_back, success, msg = propagate(system, interfaces, order_function,
                                        integrator,
                                        maxlen=tis_settings['maxlength'],
                                        reverse=True)
    if not success:
        raise ValueError('Backward path not successful.', msg)
    # Merge backward and forward, here we do not set maxlen since
    # both backward and forward may have this length
    initial_path = paste_paths(path_back, path_forw, overlap=False)
    if len(initial_path.path) == tis_settings['maxlength']:
        raise ValueError('Initial path too long len(path) >= NX')
    start, end, _, _ = initial_path.check_interfaces(interfaces)
    # ok, now its time to check the path:
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
        # print('Initial path is in the wrong direction: Reversing it!')
        initial_path = reverse_path(initial_path)
        initial_path.status = 'ACC'
    elif end == start:  # case 2
        # print('Initial path start & end at wrong interface')
        # print('Running TIS to fix initial path:')
        initial_path = _fix_path_by_tis(initial_path, system, interfaces,
                                        order_function, integrator, rgen,
                                        tis_settings)
    else:
        raise ValueError('Could not generate initial path')
    return initial_path


def _kick_across_middle(system, order_function, integrator, rgen, middle):
    """Repeatedly kick a phase point so that it crosses the middle interface.

    Parameters
    ----------
    system : object like `System` from `pyretis.core.system`
        This is the system that contains the particles we are investigating
    order_function : function
        This is a function that calculates the order parameter for a
        system.
    integrator : object like `Integrator` from `pyretis.core.integrators`
        This is the propagator of the simulation
    rgen : object like `RandomGenerator` from `pyretis.core.random_gen`
        This is the random generator that will be used.
    middle : float
        This is the value for the middle interface.

    Returns
    -------
    out[0] : dict
        This dict contains the phase-point just before the interface.
        It is obtained by calling the `get_phase_point()` of the particles
        object.
    out[1] : dict.
        This dict contains the phase-point just after the interface.
        It is obtained by calling the `get_phase_point()` of the particles
        object.

    Note
    ----
    This function will update the system state so that the
    `system.particles.get_phase_point() == out[1]`. This is more convenient
    for the following usage in the `generate_initial_path_kick` function.
    """
    # first we search for crossing with the middle interface
    # this is done by sequentially kicking the initial phase point
    particles = system.particles
    curr = order_function(system)[0]
    while True:
        # save current state:
        previous = particles.get_phase_point()
        previous['order'] = curr
        # kick the time slice
        _kick_timeslice(system, rgen, aimless=True, momentum=True)
        # integrate forward one step:
        integrator.integration_step(system)
        # compare previous order parameter and the new one:
        prev = curr
        curr = order_function(system)[0]
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


def _kick_timeslice(system, rgen, sigma_v=None, aimless=True, momentum=False):
    """Make a random modification to a time slice (modify the velocities).

    Parameters
    ----------
    system : object like `System` from `pyretis.core.system`
        System is used here since we need access to the temperature
        and to the particle list.
    rgen : object like `RandomGenerator` from `pyretis.core.random_gen`
        This is the random generator that will be used.
    sigma_v : numpy.array
        These values can be used to set a standard deviation (one for each
        particle) for the generated velocities.
    aimless : boolean, optional
        Determines if we should do aimless shooting or not.
    momentum : boolean, optional
        This handles resetting of the momentum.

    Returns
    -------
    dek : float
        The change in the kinetic energy
    kin_new : float
        The new kinetic energy
    """
    # NOTE: kin_old might be set/obtained differently according to
    # the dynamics. E.g. In NVE it is just E-Epot.
    particles = system.particles
    kin_old = calculate_kinetic_energy(particles)
    if aimless:
        vel, _ = rgen.draw_maxwellian_velocities(system)
        particles.vel = vel
    else:  # soft velocity change, add from Gaussian dist
        dvel, _ = rgen.draw_maxwellian_velocities(system, sigma_v=sigma_v)
        particles.vel = particles.vel + dvel
    if momentum:
        pass
    kin_new = calculate_kinetic_energy(particles)
    # NOTE velocity should for some dynamics be rescaled
    dek = kin_new[0] - kin_old[0]
    return dek, kin_new


def propagate(system, interfaces, order_function, integrator,
              maxlen=None, reverse=False, path=None):
    """Propagate a system in time.

    During the propagation, the system will be modified. However, at the end,
    the positions, velocities and forces will be reset to the initial state.
    We are here are generating a path and we assume that we are starting with
    a empty path or we are appending to a existing path. Here, we will stop
    the propagation if any of the following happens:

    * We have exceeded the maximum length given in `maxlen`.

    * The point we propagated to crossed the left interface.

    * The point we propagated to crossed the right interface.

    Parameters
    ----------
    system : object like `System` from `pyretis.core.system`
        The system object given is assumed to be defined with the correct
        particle list for the system to be propagated. It is also assumed
        to contain the force field.
    interfaces : list/tuple of floats
        These are the interface positions on form [left, middle, right]
    order_function : function
        This function takes the system as it's argument and returns a float
        which is equal to the order parameter.
    integrator : object like `Integrator` from `pyretis.core.integrators`
        The integrator will be used to propagate the system. It is assumed
        to be correctly set up for the system under consideration.
    maxlen : float
        The maximum length of the path
    reverse : boolean
        If True, the system will be propagated backwards in time
    path : object like `Path` from `pyretis.core.path`.
        If `path` is given, we assume that we want to append the
        propagated trajectory to an already existing path and we do not
        generate a completely new path.

    Returns
    -------
    out[0] : object of type `Path` from `pyretis.core.path`
        The generated path from integrating the system in time
    out[1] : boolean
        False if something in propagate went wrong. This is described
        in out[2].
    out[2] : string
        Human representation of the result.
    """
    # first we store the initial pos, vel and forces for the system:
    initial_system = system.particles.get_phase_point()
    left, _, right = interfaces
    if path is None:
        path = Path(maxlen=maxlen)
        status = 'Empty path'
    else:
        status = 'Appending to old path'
    while True:
        orderp = order_function(system)
        add = path.append(system.particles.pos, system.particles.vel,
                          orderp, system.v_pot)
        if not add:
            if len(path.path) >= path.maxlen:
                status = 'Max. path length exceeded'
            else:
                status = 'Could not add for unknown reason'
            success = False
            break
        if orderp[0] < left:
            status = 'Crossed left interface!'
            success = True
            break
        elif orderp[0] > right:
            status = 'Crossed right interface!'
            success = True
            break
        if reverse:
            system.particles.vel = -1.0 * system.particles.vel
            integrator(system)
            system.particles.vel = -1.0 * system.particles.vel
        else:
            integrator(system)
    # reset the system to initial state
    system.particles.set_phase_point(initial_system)
    return path, success, status


def _fix_path_by_tis(initial_path, system, interfaces, order_function,
                     integrator, rgen, tis_settings):
    """Fix a path that starts and ends at the wrong interfaces.

    The fix is performed by making TIS moves and this function is intended
    to be used in a initialization.

    Parameters
    ----------
    initial_path : object like `Path` from `pyretis.core.path`
        This is the initial path to fix. It starts & ends at the
        wrong interface.
    system : object like `System` from `pyretis.core.system`
        This is the system that contains the particles we are investigating
    interfaces : list of floats
        These are the interface positions on form [left, middle, right]
    order_function : function
        This is a function that calculates the order parameter for a
        system.
    integrator : object like `Integrator` from `pyretis.core.integrators`
        This is the propagator of the simulation
    rgen : object like `RandomGenerator` from `pyretis.core.random_gen`
        This is the random generator that will be used.
    tis_settings : dict
        Settings for TIS method, here we explicitly use:

        * `start_cond`: string which defines the start condition.
        * `maxlength`: integer which give the maximum allowed path length.

        Note that we here explicitly set some local TIS settings for use in
        the `make_tis_step` function.

    Returns
    -------
    out : object of type `Path` from `pyretis.core.path`
        The amended path.
    """
    left, middle, right = interfaces
    path_ok = False
    local_tis_settings = {'allowmaxlength': True,
                          'aimless': True,
                          'freq': 0.5,
                          'start_cond': tis_settings['start_cond'],
                          'maxlength': tis_settings['maxlength']}
    while not path_ok:
        accept, trial, _ = make_tis_step(initial_path,
                                         system,
                                         interfaces,
                                         order_function,
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
                raise ValueError('Unknown start_cond')
    initial_path.status = 'ACC'
    return initial_path
