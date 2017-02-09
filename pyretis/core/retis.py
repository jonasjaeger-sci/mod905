# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""This module contains functions for RETIS.

This module defines functions that are needed to perform Replica
Exchange Transition Interface Sampling (RETIS). The algorithms
implemented here and the description of RETIS was first described by
van Erp [RETIS]_.


Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

make_retis_step (:py:func:`.make_retis_step`)
    Function to select and execute the RETIS move.

retis_tis_moves (:py:func:`.retis_tis_moves`)
    Function to execute the TIS steps in the RETIS algorithm.

retis_moves (:py:func:`.retis_moves`)
    Function to perform RETIS swapping moves - it selects what scheme
    to use, i.e. ``[0^-] <-> [0^+], [1^+] <-> [2^+], ...`` or
    ``[0^+] <-> [1^+], [2^+] <-> [3^+], ...``.

retis_swap (:py:func:`.retis_swap`)
    The function that actually swaps two path ensembles.

retis_swap_zero (:py:func:`.retis_swap_zero`)
    The function that performs the swapping for the
    ``[0^-] <-> [0^+]`` swap.

References
~~~~~~~~~~

.. [RETIS] Titus S. van Erp,
   Phys. Rev. Lett. 98, 26830 (2007),
   http://dx.doi.org/10.1103/PhysRevLett.98.268301
"""
import logging
from pyretis.core.tis import make_tis_step_ensemble
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['make_retis_step']


def make_retis_step(ensembles, system, order_function, engine, rgen,
                    settings, cycle):
    """Determine and execute the appropriate RETIS move.

    Here we will determine what kind of RETIS moves we should do.
    We have two options:

    1) Do the RETIS swapping moves. This is done by calling
       `retis_move`
    2) Do TIS moves, either for all ensembles or for just one, based on
       values of relative shoot frequencies. This is done by calling
       `make_retis_tis_steps`.

    This function will just determine and execute the appropriate move
    (1 or 2) based on the given swapping frequencies in the `settings`
    and drawing a random number from the random number generator `rgen`.

    Parameters
    ----------
    ensembles : list of objects like :py:class:`.PathEnsemble`
        This is a list of the ensembles we are using in the RETIS method
    system : object like :py:class:`.System`
        System is used here since we need access to the temperature
        and to the particle list
    order_function : object like :py:class:`.OrderParameter`
        The class used for calculating the order parameter(s).
    engine : object like :py:class:`.EngineBase`
        The engine to use for propagating a path.
    rgen : object like :py:class:`.RandomGenerator`
        This is a random generator. Here we assume that we can call
        `rgen.rand()` to draw random uniform numbers.
    settings : dict
        This dict contains the settings for the RETIS method.
    cycle : integer
        The current cycle number.

    Returns
    -------
    out : list of lists
        `out[i]` contains the result after performing the move for path
        ensemble no. `i`.
    """
    if rgen.rand() < settings['retis']['swapfreq']:
        # Do RETIS moves
        logger.info('Performing RETIS swapping move(s).')
        return retis_moves(ensembles, system, order_function, engine,
                           rgen, settings, cycle)
    else:
        logger.info('Performing RETIS TIS move(s)')
        return retis_tis_moves(ensembles, system, order_function, engine,
                               rgen, settings, cycle)


def _relative_shoots_select(ensembles, rgen, relative):
    """Randomly select the ensemble for 'relative' shooting moves.

    Here we select the ensemble to do the shooting in based on relative
    probabilities. We draw a random number in [0, 1] which is used to
    select the ensemble.

    Parameters
    ----------
    ensembles : list of objects like :py:class:`.PathEnsemble`
        This is a list of the ensembles we are using in the RETIS method
    rgen : object like :py:class:`.RandomGenerator`
        This is a random generator. Here we assume that we can call
        `rgen.rand()` to draw random uniform numbers.
    relative : list of floats
        These are the relative probabilities for the ensembles. We
        assume here that these numbers are normalized.

    Returns
    -------
    out[0] : integer
        The index of the path ensemble to shoot in.
    out[1] : object like :py:class:`.PathEnsemble`
        The selected path ensemble for shooting.
    """
    freq = rgen.rand()
    cumulative = 0.0
    idx = None
    for idx, path_freq in enumerate(relative):
        cumulative += path_freq
        if freq < cumulative:
            break
    # just a sanity check, we should crash if idx is None
    try:
        path_ensemble = ensembles[idx]
    except TypeError:
        msg = 'Error in relative shoot frequencies! Aborting!'
        raise ValueError(msg)
    return idx, path_ensemble


def retis_tis_moves(ensembles, system, order_function, engine, rgen,
                    settings, cycle):
    """Execute the TIS steps in the RETIS method.

    This function will execute the TIS steps in the RETIS method. These
    differ slightly from the regular TIS moves since we have two options
    on how to perform them. These two options are controlled by the
    given `settings`:

    1) If `relative_shoots` is given in the input settings, then we will
       pick at random what ensemble we will perform TIS on. For all the
       other ensembles we again have two options based on the given
       `settings['nullmoves']`:

       a) Do a 'null move' in all other ensembles.
       b) Do nothing for all other ensembles.

       Performing the null move in an ensemble will simply just accept
       the previously accepted path in that ensemble again.

    2) If `relative_shoots` is not given in the input settings, then we
       will perform TIS moves for all path ensembles.

    Parameters
    ----------
    ensembles : list of objects like :py:class:`.PathEnsemble`
        This is a list of the ensembles we are using in the RETIS method
    system : object like :py:class:`.System`
        System is used here since we need access to the temperature
        and to the particle list
    order_function : object like :py:class:`.OrderParameter`
        The class used for calculating the order parameter(s).
    engine : object like :py:class:`.EngineBase`
        The engine to use for propagating a path.
    rgen : object like :py:class:`.RandomGenerator`
        This is a random generator. Here we assume that we can call
        `rgen.rand()` to draw random uniform numbers.
    settings : dict
        This dict contains the settings for the RETIS method.
    cycle : integer
        The current cycle number

    Returns
    -------
    output : list of lists
        `output[i]` contains the result for ensemble `i`. output[i][0]
        gives information on what kind of move was tried.
    """
    relative = settings['retis'].get('relative_shoots', None)
    if relative is not None:
        output = [None for path_ensemble in ensembles]
        idx, path_ensemble = _relative_shoots_select(ensembles, rgen,
                                                     relative)
        accept, trial, status = make_tis_step_ensemble(path_ensemble, system,
                                                       order_function,
                                                       engine, rgen,
                                                       settings['tis'], cycle)
        output[idx] = ['tis', status, trial, accept]
        # and do null moves for the others if requested:
        if settings['retis']['nullmoves']:
            for other, path_ensemble in enumerate(ensembles):
                if other != idx:
                    accept, trial, status = null_move(path_ensemble, cycle)
                    output[idx] = ['nullmove', status, trial, accept]
    else:  # just do TIS for them all
        output = []
        for path_ensemble in ensembles:
            accept, trial, status = make_tis_step_ensemble(path_ensemble,
                                                           system,
                                                           order_function,
                                                           engine,
                                                           rgen,
                                                           settings['tis'],
                                                           cycle)
            output.append(['tis', status, trial, accept])
    return output


def retis_moves(ensembles, system, order_function, engine, rgen,
                settings, cycle):
    """Perform RETIS moves on the given ensembles.

    This function will perform RETIS moves on the given ensembles.
    First we have two strategies based on
    `settings['retis']['swapsimul']`:

    1) If `settings['retis']['swapsimul']` is True we will perform
       several swaps, either ``[0^-] <-> [0^+], [1^+] <-> [2^+], ...``
       or ``[0^+] <-> [1^+], [2^+] <-> [3^+], ...``. Which one of these
       two swap options we use is determined randomly and they have
       equal probability.

    2) If `settings['retis']['swapsimul']` is False we will just
       perform one swap for randomly chosen ensembles, i.e. we pick a
       random ensemble and try to swap with the ensemble to the right.
       Here we may also perform null moves if the
       `settings['retis']['nullmove']` specifies so.

    Parameters
    ----------
    ensembles : list of objects like :py:class:`.PathEnsemble`
        This is a list of the ensembles we are using in the RETIS method
    system : object like :py:class:`.System`
        System is used here since we need access to the temperature
        and to the particle list
    order_function : object like :py:class:`.OrderParameter`
        The class used for calculating the order parameter(s).
    engine : object like :py:class:`.EngineBase`
        The engine to use for propagating a path.
    rgen : object like :py:class:`.RandomGenerator`
        This is a random generator. Here we assume that we can call
        `rgen.rand()` to draw random uniform numbers.
    settings : dict
        This dict contains the settings for the RETIS method.
    cycle : integer
        The current cycle number

    Returns
    -------
    out : list of lists
        `out[i]` contains the results of the swapping/nullmove for path
        ensemble no. `i`.
    """
    output = [None for path_ensemble in ensembles]
    if settings['retis']['swapsimul']:
        # here we have to schemes:
        # scheme == 0: [0^-] <-> [0^+], [1^+] <-> [2^+], ...
        # scheme == 1: [0^+] <-> [1^+], [2^+] <-> [3^+], ...
        if len(ensembles) < 3:
            # Low number of ensembles, can only do the [0^-] <-> [0^+] swap
            scheme = 0
        else:
            scheme = 0 if rgen.rand() < 0.5 else 1
        for idx in range(scheme, len(ensembles) - 1, 2):
            accept, trial, status = retis_swap(ensembles, idx, system,
                                               order_function, engine,
                                               settings, cycle)
            output[idx] = ['swap', status, trial[0], accept, idx+1]
            output[idx+1] = ['swap', status, trial[1], accept, idx]
        if settings['retis']['nullmoves']:
            if len(ensembles) % 2 != scheme:  # missed last
                # this is perhaps strange but it's equal to:
                # (scheme == 0 and len(ensembles) % 2 != 0) or
                # (scheme == 1 and len(ensembles) % 2 == 0)
                accept, trial, status = null_move(ensembles[-1], cycle)
                output[-1] = ['nullmove', status, trial, accept]
            if scheme == 1:  # we did not include [0^-]
                accept, trial, status = null_move(ensembles[0], cycle)
                output[0] = ['nullmove', status, trial, accept]
    else:  # just swap two ensembles:
        idx = rgen.random_integers(0, len(ensembles) - 2)
        accept, trial, status = retis_swap(ensembles, idx, system,
                                           order_function,
                                           engine, settings, cycle)
        output[idx] = ['swap', status, trial[0], accept, idx+1]
        output[idx+1] = ['swap', status, trial[1], accept, idx]
        if settings['retis']['nullmoves']:
            # Do null moves in the rest
            for i, path_ensemble in enumerate(ensembles):
                if i != idx and i != idx + 1:
                    accept, trial, status = null_move(path_ensemble, cycle)
                    output[i] = ['nullmove', status, trial, accept]
    return output


def retis_swap(ensembles, idx, system, order_function, engine,
               settings, cycle):
    """Perform a RETIS swapping move for two ensembles.

    The RETIS swapping move will attempt to swap accepted paths between
    two ensembles in the hope that path from [i^+] is an acceptable path
    for [(i+1)^+] as well. We have two cases:

    1) If we try to swap between [0^-] and [0^+] we need to integrate
       the equations of motion.
    2) Otherwise we can just swap and accept if the path from [i^+] is
       an acceptable path for [(i+1)^+]. The path from [(i+1)^+] is
       always acceptable for [i^+] (by construction).

    Parameters
    ----------
    ensembles : list of objects like :py:class:`.PathEnsemble`
        This is a list of the ensembles we are using in the RETIS method
    idx : integer
        Definition of what path ensembles to swap. We will swap
        `ensembles[idx]` with `ensembles[idx+1]`. If `idx == 0` we have
        case 1) defined above.
    system : object like :py:class:`.System`
        System is used here since we need access to the temperature
        and to the particle list
    order_function : object like :py:class:`.OrderParameter`
        The class used for calculating the order parameter(s).
    engine : object like :py:class:`.EngineBase`
        The engine to use for propagating a path.
    settings : dict
        This dict contains the settings for the RETIS method.
    cycle : integer
        Current cycle number

    Returns
    -------
    out[0] : boolean
        Should the path be accepted or not?
    out[1] : list of object like :py:class:`.PathBase`
        The trial paths.
    out[2] : string
        The status for the trial paths.
    """
    logger.info('Swapping: %s <-> %s', ensembles[idx].ensemble_name,
                ensembles[idx+1].ensemble_name)
    status = None
    if idx == 0:
        return retis_swap_zero(ensembles, system, order_function, engine,
                               settings, cycle)
    else:
        ensemble1 = ensembles[idx]
        ensemble2 = ensembles[idx + 1]
        path1 = ensemble1.last_path
        path2 = ensemble2.last_path
        # Check if path1 can be accepted in ensemble 2:
        cross = path1.check_interfaces(ensemble2.interfaces)[-1]
        # Do the swap
        path1, path2 = path2, path1
        accept = cross[1]
        if accept:  # accept the swap
            status = 'ACC'
            logger.info('Swap was accepted.')
            path1.set_move('s+')  # came from right
            path2.set_move('s-')  # came from left
            # To avoid overwriting files, we move the paths to the
            # generate directory here. They will be moved into the
            # accepted directory by the `add_path_data` below.
            ensemble1.move_path_to_generated(path1)
            ensemble2.move_path_to_generated(path2)
        else:  # reject:
            status = 'NCR'
            logger.info('Swap was rejected. (%s)', status)
        ensemble1.add_path_data(path1, status, cycle=cycle)
        ensemble2.add_path_data(path2, status, cycle=cycle)
        return accept, (path1, path2), status


def retis_swap_zero(ensembles, system, order_function, engine,
                    settings, cycle):
    """The retis swapping move for ``[0^-] <-> [0^+]`` swaps.

    The retis swapping move for ensembles [0^-] and [0^+] requires some
    extra integration. Here we are generating new paths for [0^-] and
    [0^+] in the following way:

    1) For [0^-] we take the initial point in [0^+] and integrate
       backward in time. This is merged with the second point in [0^+]
       to give the final path. The initial point in [0^+] starts to the
       left of the interface and the second point is on the right
       side - i.e. the path will cross the interface at the end points.
       If we let the last point in [0^+] be called ``A_0`` and the
       second last point ``B``, and we let ``A_1, A_2, ...`` be the
       points on the backward trajectory generated from ``A_0`` then
       the final path will be made up of the points
       ``[..., A_2, A_1, A_0, B]``. Here, ``B`` will be on the right
       side of the interface and the first point of the path will also
       be on the right side.

    2) For [0^+] we take the last point of [0^-] and use that as an
       initial point to generate a new trajectory for [0^+] by
       integration forward in time. We also include the second last
       point of the [0^-] trajectory which is on the left side of the
       interface. We let the second last point be ``B`` (this is on the
       left side of the interface), the last point ``A_0`` and the
       points generated from ``A_0`` we denote by ``A_1, A_2, ...``.
       Then the resulting path will be ``[B, A_0, A_1, A_2, ...]``.
       Here, ``B`` will be on the left side of the interface and the
       last point of the path will also be on the left side of the
       interface.

    Parameters
    ----------
    ensembles : list of objects like :py:class:`.PathEnsemble`
        This is a list of the ensembles we are using in the RETIS method
    system : object like :py:class:`.System`
        System is used here since we need access to the temperature
        and to the particle list
    order_function : object like :py:class:`.OrderParameter`
        The class used for calculating the order parameter(s).
    engine : object like :py:class:`.EngineBase`
        The engine to use for propagating a path.
    settings : dict
        This dict contains the settings for the RETIS method.
    cycle : integer
        The current cycle number

    Returns
    -------
    out : string
        The result of the swapping move.
    """
    ensemble0 = ensembles[0]
    ensemble1 = ensembles[1]
    # 1) Generate path for [0^-] from [0^+]:
    # We generate from the first point of the path in [0^+]:
    logger.debug('Creating path for [0^-]')
    system.particles.set_particle_state(ensemble1.last_path.phasepoint(0))
    # Propagate it backward in time:
    maxlen = settings['tis']['maxlength']
    path_tmp = ensemble1.last_path.empty_path(maxlen=maxlen-1)
    engine.exe_dir = ensemble0.directory['generate']
    logger.debug('Propagating for [0^-]')
    engine.propagate(path_tmp, system, order_function,
                     ensemble0.interfaces, reverse=True)
    path0 = path_tmp.empty_path(maxlen=maxlen)
    for phasepoint in path_tmp.trajectory(reverse=True):
        _ = path0.append(phasepoint)
    # And add second point from [0^+] at the end:
    phase_point = ensemble1.last_path.phasepoint(1)
    engine.dump_phasepoint(phase_point, 'second')
    path0.append(phase_point)
    path0.status = 'BTX' if path0.length == maxlen else 'ACC'
    path0.set_move('s+')
    # 2) Generate path for [0^+] from [0^-]:
    logger.debug('Creating path for [0^+]')
    # This path will be generated starting from the LAST point of [0^-] which
    # should be on the right side of the interface. We will also add the
    # SECOND LAST point from [0^-] which should be on the left side of the
    # interface, this is added after we have generated the path and we
    # save space for this point by letting maxlen = maxlen-1 here:
    path_tmp = path0.empty_path(maxlen=maxlen-1)
    # We start the generation from the LAST point
    system.particles.set_particle_state(ensemble0.last_path.phasepoint(-1))
    engine.exe_dir = ensemble1.directory['generate']
    logger.debug('Propagating for [0^+]')
    engine.propagate(path_tmp, system, order_function,
                     ensemble1.interfaces, reverse=False)
    # Ok, now we need to just add the SECOND LAST point from [0^-] as
    # the first point for the path:
    path1 = path_tmp.empty_path(maxlen=maxlen)
    phase_point = ensemble0.last_path.phasepoint(-2)
    engine.dump_phasepoint(phase_point, 'second_last')
    path1.append(phase_point)
    path1 += path_tmp  # add rest of the path
    path1.set_move('s-')
    path1.status = 'FTX' if path1.length == maxlen else 'ACC'
    # Update status, etc
    status = 'ACC'  # we are optimistic and hope that this is the default
    accept = True
    if path0.status == 'BTX':
        path1.status = 'BTX'
        status = 'BTX'
        accept = False
        logger.debug('Rejecting path in [0^-], BTX')
    if path1.status == 'FTX':
        path0.status = 'FTX'
        status = 'FTX'
        accept = False
        logger.debug('Rejecting path in [0^+], FTX')
    ensemble0.add_path_data(path0, status, cycle=cycle)
    ensemble1.add_path_data(path1, status, cycle=cycle)
    return accept, (path0, path1), status


def null_move(path_ensemble, cycle):
    """Perform a null move for an path ensemble.

    The null move simply consist of accepting the last accepted path
    again.

    Parameters
    ----------
    path_ensemble : object like :py:class:`.PathEnsemble`
        This is the path ensemble to update with the null move
    cycle : integer
        The current cycle number

    Returns
    -------
    out[0] : boolean
        Should the path be accepted or not? Here, it's always True
        since the null move is always accepted.
    out[1] : object like :py:class:`.PathBase`
        The generated path.
    out[2] : string
        The status, which here will be 'ACC', since we just accept
        the last accepted path again in this move.
    """
    logger.info('Null move for: %s', path_ensemble.ensemble_name)
    status = 'ACC'
    path = path_ensemble.last_path
    path.set_move('00')
    path_ensemble.add_path_data(path, status, cycle=cycle)
    return True, path, status
