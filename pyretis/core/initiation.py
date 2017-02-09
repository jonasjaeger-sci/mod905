# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""This file contains functions used for initiation of paths.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

generate_initial_path_kick (:py:func:`.generate_initial_path_kick`)
    Function for generating an initial path by repeatedly kicking a
    phase point.

initiate_kick (:py:func:`.initiate_kick`)
    A method for initiating a path ensemble by repeatedly modifying
    velocities to find the crossing with the interfaces.

initiate_kick2 (:py:func:`.initiate_kick2`)
    A method similar to py:meth:`.initiate_kick`. Here, if possible,
    we will use points from the previous paths, closest to the target
    interface.

initiate_path_ensemble_kick (:py:func:`.initiate_path_ensemble_kick`)
    Method to initiate a single path ensemble.

initiate_path_simulation (:py:func:`.initiate_path_simulation`)
    Helper method for initiating a path simulation. This method
    will make use of one of the other initiation methods.
"""
import logging
from pyretis.core.path import paste_paths
from pyretis.core.tis import make_tis_step
from pyretis.core.common import get_path_class
from pyretis.inout.common import print_to_screen
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = [
    'generate_initial_path_kick',
    'initiate_kick',
    'initiate_kick2',
    'initiate_path_ensemble_kick',
    'initiate_path_simulation',
]


def get_initiation_method(settings):
    """Return the initiation method.

    Parameters
    ----------
    settings : dict
        This dictionary contains the settings for the initiation.
    """
    _methods = {'kick': initiate_kick,
                'kick2': initiate_kick2}
    method = settings['initial_path'].lower()
    if method not in _methods:
        logger.error('Unknown initiation method "%s" requrested', method)
        logger.error('Known methods: %s', _methods.keys())
        raise ValueError('Unknown initiation method requested!')
    logtxt = 'Will initiate using method "{}"'.format(method)
    print_to_screen(logtxt)
    logger.info(logtxt)
    return _methods[method]


def initiate_path_simulation(simulation, settings):
    """Helper method to initiate a path simulation.

    Parameters
    ----------
    simulation : object like :py:class:`.PathSimulation`
        The simulation we are doing the initiation for.
    settings : dict
        A dictionary with settings for the initiation.
    """
    cycle = simulation.cycle['step']
    method = get_initiation_method(settings)
    tis_settings = simulation.settings['tis']
    return method(simulation.path_ensembles,
                  simulation.system,
                  simulation.order_function,
                  simulation.engine,
                  simulation.rgen,
                  tis_settings,
                  cycle)


def initiate_kick(path_ensembles, system, order_function, engine,
                  rgen, tis_settings, cycle):
    """This is a helper method to initiate for several ensembles.

    Please see documentation for :py:func:`.initiate_path_ensemble_kick`.
    """
    for ensemble in path_ensembles:
        logger.info('Initiating path ensemble: %s', ensemble.ensemble_name)
        accept, initial_path, status = initiate_path_ensemble_kick(
            ensemble,
            system,
            order_function,
            engine,
            rgen,
            tis_settings,
            cycle)
        yield accept, initial_path, status


def initiate_kick2(path_ensembles, system, order_function, engine,
                   rgen, tis_settings, cycle):
    """This is a helper method to initiate for several ensembles.

    This method is similar to :py:func:`.initiate_kick`, but here we
    update the initial point for an ensemble to use that of the previous
    path (if this exist).

    Please see documentation for :py:func:`.initiate_path_ensemble_kick`.
    """
    last_paths = []
    last_path = None
    for ensemble in path_ensembles:
        logtxt = 'Initiating path ensemble {}'.format(ensemble.ensemble_name)
        print_to_screen(logtxt)
        logger.info(logtxt)
        if len(last_paths) > 0:
            middle = ensemble.interfaces[1]
            # look for phase_point closest to middle, but on the left:
            current = None
            min_dist = float('inf')
            for last_path in last_paths:
                for phase_point in last_path.trajectory():
                    dist = middle - phase_point['order'][0]
                    if 0 < dist < min_dist:
                        min_dist = dist
                        current = phase_point
            if current is not None:
                logtxt = 'Taking initial state: ({})'
                logtxt = logtxt.format(current['order'][0])
                logger.info(logtxt)
                print_to_screen(logtxt)
                system.particles.set_particle_state(current)

        accept, initial_path, status = initiate_path_ensemble_kick(
            ensemble,
            system,
            order_function,
            engine,
            rgen,
            tis_settings,
            cycle)
        last_paths.append(initial_path)
        yield accept, initial_path, status


def initiate_path_ensemble_kick(path_ensemble, system, order_function,
                                engine, rgen, tis_settings, cycle):
    """This function will run the initiate for a given ensemble.

    This function is intended for convenience. It should handle and
    call all the possible initiation methods.

    Parameters
    ----------
    path_ensemble : object like :py:class:`.PathEnsemble`
        The path ensemble to create an initial path for.
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
        This dictionary contain the TIS settings. Here we set the
        setting for the starting condition (``'start_cond'``) according
        to the given path ensemble. We are also using the keyword
        ``'initial_path'`` to determine how the initial path should be
        initiated. The other ``tis_settings`` are just passed on.
    cycle : integer, optional
        The cycle number we are initiating at, typically this will be 0
        which is the default value.

    Returns
    -------
    out[0] : boolean
        True if the initial path was accepted
    out[1] : object like py:class:`.PathBase`
        The initial path.
    out[2] : string
        Sthe status of the path.
    """
    tis_settings['start_cond'] = path_ensemble.get_start_condition()
    initial_path = None
    status = ''
    accept = False
    logger.info('Will generate initial path by kicking')
    engine.exe_dir = path_ensemble.directory['generate']
    initial_path = generate_initial_path_kick(system, order_function,
                                              path_ensemble,
                                              engine, rgen,
                                              tis_settings)
    accept = True
    status = 'ACC'
    path_ensemble.add_path_data(initial_path, status, cycle)
    # Ask the engine to do clean up after the intialization.
    engine.clean_up()
    return accept, initial_path, status


def generate_initial_path_kick(system, order_function, path_ensemble, engine,
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
    system : object like :py:class:`.System`
        This is the system that contains the particles we are
        investigating.
    order_function : object like :py:class:`.OrderParameter`
        The class used for obtaining the order parameter(s).
    path_ensemble : object like :py:class:`.PathEnsemble`
        The path ensemble to create an initial path for.
    engine : object like :py:class:`.EngineBase`
        The engine to use for propagating a path.
    rgen : object like :py:class:`.RandomGenerator`
        This is the random generator that will be used.
    tis_settings : dict
        This dictionary contains settings for TIS. Explicitly used here:

        * `start_cond`: string, starting condition, 'L'eft or 'R'ight
        * `maxlength`: integer, maximum allowed length of paths.

    Returns
    -------
    out : object like :py:class:`.PathBase`
        This is the generated initial path
    """
    initial_state = system.particles.get_particle_state()
    interfaces = path_ensemble.interfaces
    logger.info('Seaching crossing with middle interface.')
    leftpoint, _ = engine.kick_across_middle(system,
                                             order_function,
                                             rgen, interfaces[1],
                                             tis_settings)
    logger.info('Propagating from crossing points.')
    # kick_across_middle will return two points, one immediately
    # left of the interface and one immediately right of the
    # interface. So we have two points (`leftpoint` and the
    # current `system.particles`). We then propagate the current
    # phase point forward:
    maxlen = tis_settings['maxlength']
    klass = get_path_class(engine.engine_type)
    path_forw = klass(rgen, maxlen=maxlen)
    success, msg = engine.propagate(path_forw, system, order_function,
                                    interfaces, reverse=False)
    if not success:
        msgtxt = 'Forward path not successful: {}'.format(msg)
        logger.error(msgtxt)
        raise ValueError(msgtxt)
    # And we propagate the `leftpoint` backward:
    system.particles.set_particle_state(leftpoint)
    path_back = klass(rgen, maxlen=maxlen)
    success, msg = engine.propagate(path_back, system, order_function,
                                    interfaces, reverse=True)
    if not success:
        msgtxt = 'Backward path not successful: {}'.format(msg)
        logger.error(msgtxt)
        raise ValueError(msgtxt)
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
    else:
        # Now we do the other cases:
        if end == tis_settings['start_cond']:
            # Case 3 (and start != start_cond):
            logger.info('Initial path is in the wrong direction.')
            initial_path = initial_path.reverse()
            initial_path.generated = ('ki', 0, 0, 0)
            initial_path.status = 'ACC'
            logger.info('Path has been reversed!')
        elif end == start:
            # Case 2
            logger.info('Initial path start/end at wrong interfaces.')
            logger.info('Will perform TIS moves to try to fix it!')
            initial_path = _fix_path_by_tis(initial_path, system,
                                            order_function, path_ensemble,
                                            engine, rgen, tis_settings)
        else:
            logger.error('Could not generate initial path.')
            raise ValueError('Could not generate initial path.')
    # Reset system:
    system.particles.set_particle_state(initial_state)
    return initial_path


def _get_help(start_cond, interfaces):
    """Defines some methods for :py:func:`._fix_path_by_tis`

    This method returns two methods that :py:func:`._fix_path_by_tis`
    can use to determine if a new path is an improvement compared to
    the current path and if the "fixing" is done.

    Parameters
    ----------
    start_cond : string
        The starting condition (from the TIS settings). Left or Right.
    interfaces : list of floats
        The interfaces, on form [left, middle, right]

    Returns
    -------
    out[0] : method
        The method which determines if a new path represents an
        improvement over the current path.
    out[1] : method
        The method which determines if we are done, that is if we
        can accept the current path.
    """
    left, middle, right = interfaces
    improved, done = None, None
    if start_cond == 'R':
        def improved_r(newp, current):
            """True if new path is an improvement."""
            return (newp.ordermax[0] > current.ordermax[0] and
                    newp.ordermin[0] < middle)

        def done_r(path):
            """True if the path can be accepted."""
            return path.ordermax[0] > right

        improved = improved_r
        done = done_r
    elif start_cond == 'L':
        def improved_l(newp, current):
            """True if new path is an improvement."""
            return (newp.ordermin[0] < current.ordermin[0] and
                    newp.ordermax[0] > middle)

        def done_l(path):
            """True if the path can be accepted."""
            return path.ordermin[0] < left

        improved = improved_l
        done = done_l
    else:
        logger.error('Unknown start condition (should be "R" or "L")')
        raise ValueError('Unknown start condition (should be "R" or "L")')
    return improved, done


def _copy_tis_settings(tis_settings):
    """Copy the input TIS settings.

    Parameters
    ----------
    tis_settings : dict
        The input TIS settings.

    Returns
    -------
    out : dict
        A copy of the input TIS settings.
    """
    copy = {}
    for key, val in tis_settings.items():
        copy[key] = val
    return copy


def _fix_path_by_tis(initial_path, system, order_function, path_ensemble,
                     engine, rgen, tis_settings):
    """Fix a path that starts and ends at the wrong interfaces.

    The fix is performed by making TIS moves and this function is
    intended to be used in a initialization.

    Parameters
    ----------
    initial_path : object like :py:class:`.PathBase`
        This is the initial path to fix. It starts & ends at the
        wrong interface.
    system : object like :py:class:`.System`
        This is the system that contains the particles we are
        investigating
    order_function : object like :py:class:`.OrderParameter`
        The object used for calculating the order parameter(s).
    path_ensemble : object like :py:class:`.PathEnsemble`
        The path ensemble to create an initial path for.
    engine : object like :py:class:`.EngineBase`
        The engine to use for propagating a path.
    rgen : object like :py:class:`.RandomGenerator`
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
    out : object like :py:class:`.PathBase`
        The amended path.
    """
    logger.debug('Attempting to fix path by running TIS moves.')

    local_tis_settings = _copy_tis_settings(tis_settings)
    local_tis_settings['allowmaxlength'] = True
    local_tis_settings['aimless'] = True,
    local_tis_settings['freq'] = 0.5

    improved, check_ok = _get_help(local_tis_settings['start_cond'],
                                   path_ensemble.interfaces)

    backup_path = True
    path_ok = False

    while not path_ok:
        logger.debug('Performing a TIS move to improve the initial path')
        if backup_path:
            # move initial_path to safe place
            logger.debug('Moving initial_path')
            path_ensemble.move_path_to_generated(initial_path, prefix='_')
            backup_path = False
        accept, trial, _ = make_tis_step(initial_path,
                                         system,
                                         order_function,
                                         path_ensemble.interfaces,
                                         engine,
                                         rgen,
                                         local_tis_settings)
        if accept:
            if improved(trial, initial_path):
                logger.debug('TIS move improved path.')
                initial_path = trial
                backup_path = True
            else:
                logger.debug('TIS move did not improve path')
            path_ok = check_ok(initial_path)
        else:
            logger.debug('TIS move did not improve path')
    initial_path.generated = ('ki', 0, 0, 0)
    initial_path.status = 'ACC'
    return initial_path
