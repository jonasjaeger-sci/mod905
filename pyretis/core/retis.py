# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
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

high_acc_swap (:py:func:`.high_acc_wap`)
    The function coputes if a path generated via SS can be accepted
    for swapping in accordance to super detail balance.

References
~~~~~~~~~~
.. [RETIS] Titus S. van Erp,
   Phys. Rev. Lett. 98, 26830 (2007),
   http://dx.doi.org/10.1103/PhysRevLett.98.268301

.. [SS+WT] Enrico Riccardi, Oda Dahlen, Titus S. van Erp,
   J. Phys. Chem. letters, 8, 18, 4456, (2017),
   https://doi.org/10.1021/acs.jpclett.7b01617

"""
import copy
import logging
import numpy as np
from pyretis.core.tis import make_tis_step_ensemble, compute_weight_ss
from pyretis.core.common import crossing_counter
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
logger.addHandler(logging.NullHandler())


__all__ = ['make_retis_step']


def make_retis_step(ensembles, order_function, engine, rgen,
                    settings, cycle):
    """Determine and execute the appropriate RETIS move.

    Here we will determine what kind of RETIS moves we should do.
    We have two options:

    1) Do the RETIS swapping moves. This is done by calling
       :py:func:`.retis_moves`.
    2) Do TIS moves, either for all ensembles or for just one, based on
       values of relative shoot frequencies. This is done by calling
       :py:func:`.retis_tis_moves`.

    This function will just determine and execute the appropriate move
    (1 or 2) based on the given swapping frequencies in the `settings`
    and drawing a random number from the random number generator `rgen`.

    Parameters
    ----------
    ensembles : list of objects like :py:class:`.PathEnsemble`
        This is a list of the ensembles we are using in the RETIS method.
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
        logger.info('Performing RETIS swapping move(s).')
        results = retis_moves(ensembles, order_function, engine,
                              rgen, settings, cycle)
    else:
        logger.info('Performing RETIS TIS move(s)')
        results = retis_tis_moves(ensembles, order_function, engine,
                                  rgen, settings, cycle)
    return results


def _relative_shoots_select(ensembles, rgen, relative):
    """Randomly select the ensemble for 'relative' shooting moves.

    Here we select the ensemble to do the shooting in based on relative
    probabilities. We draw a random number in [0, 1] which is used to
    select the ensemble.

    Parameters
    ----------
    ensembles : list of objects like :py:class:`.PathEnsemble`
        This is a list of the ensembles we are using in the RETIS
        method.
    rgen : object like :py:class:`.RandomGenerator`
        This is a random generator. Here we assume that we can call
        `rgen.rand()` to draw random uniform numbers.
    relative : list of floats
        These are the relative probabilities for the ensembles. We
        assume here that these numbers are normalised.

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
    for i, path_freq in enumerate(relative):
        cumulative += path_freq
        if freq < cumulative:
            idx = i
            break
    try:
        path_ensemble = ensembles[idx]
    except TypeError:
        raise ValueError('Error in relative shoot frequencies! Aborting!')
    return idx, path_ensemble


def retis_tis_moves(ensembles, order_function, engine, rgen,
                    settings, cycle):
    """Execute the TIS steps in the RETIS method.

    This function will execute the TIS steps in the RETIS method. These
    differ slightly from the regular TIS moves since we have two options
    on how to perform them. These two options are controlled by the
    given settings:

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
        This is a list of the ensembles we are using in the RETIS
        method.
    system : object like :py:class:`.System`
        The system is used here since we need access to the temperature
        and to the particle list.
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
    output : list of lists
        `output[i]` contains the result for ensemble `i`. output[i][0]
        gives information on what kind of move was tried.

    """
    relative = settings['retis'].get('relative_shoots', None)
    if relative is not None:
        idx, path_ensemble = _relative_shoots_select(
            ensembles,
            rgen,
            relative
        )
        accept, trial, status = make_tis_step_ensemble(
            path_ensemble, order_function, engine, rgen,
            settings['tis'], cycle
        )
        result = {
            'ensemble': idx,
            'retis-move': 'tis',
            'status': status,
            'trial': trial,
            'accept': accept
        }
        yield result
        # Do null moves in the other ensembles, if requested:
        if settings['retis']['nullmoves']:
            for path_ensemble in ensembles:
                other = path_ensemble.ensemble_number
                if other != idx:
                    accept, trial, status = null_move(path_ensemble, cycle)
                    result = {
                        'ensemble': other,
                        'retis-move': 'nullmove',
                        'status': status,
                        'trial': trial,
                        'accept': accept,
                    }
                    yield result
    else:  # Do TIS in all ensembles:
        for path_ensemble in ensembles:
            accept, trial, status = make_tis_step_ensemble(
                path_ensemble, order_function, engine,
                rgen, settings['tis'], cycle
            )
            result = {
                'ensemble': path_ensemble.ensemble_number,
                'retis-move': 'tis',
                'status': status,
                'trial': trial,
                'accept': accept,
            }
            yield result


def retis_moves(ensembles, order_function, engine, rgen,
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
        This is a list of the ensembles we are using in the RETIS
        method.
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
        `out[i]` contains the results of the swapping/null move for path
        ensemble no. `i`.

    """
    if settings['retis']['swapsimul']:
        # Here we have two schemes:
        # 1) scheme == 0: [0^-] <-> [0^+], [1^+] <-> [2^+], ...
        # 2) scheme == 1: [0^+] <-> [1^+], [2^+] <-> [3^+], ...
        if len(ensembles) < 3:
            # Small number of ensembles, can only do the [0^-] <-> [0^+] swap:
            scheme = 0
        else:
            scheme = 0 if rgen.rand() < 0.5 else 1
        for idx in range(scheme, len(ensembles) - 1, 2):
            accept, trial, status = retis_swap(
                ensembles, idx, order_function, engine,
                settings, cycle, rgen
            )
            result = {
                'ensemble': idx,
                'retis-move': 'swap',
                'status': status,
                'trial': trial[0],
                'accept': accept,
                'swap-with': idx + 1,
            }
            yield result
            result = {
                'ensemble': idx + 1,
                'retis-move': 'swap',
                'status': status,
                'trial': trial[1],
                'accept': accept,
                'swap-with': idx,
            }
            yield result
        # We might have missed some ensembles in the two schemes.
        # Here, we do null moves in these, if requested:
        if settings['retis']['nullmoves']:
            if len(ensembles) % 2 != scheme:  # Missed last ensemble:
                # This is perhaps strange but it is equivalent to:
                # (scheme == 0 and len(ensembles) % 2 != 0) or
                # (scheme == 1 and len(ensembles) % 2 == 0)
                accept, trial, status = null_move(ensembles[-1], cycle)
                result = {
                    'ensemble': ensembles[-1].ensemble_number,
                    'retis-move': 'nullmove',
                    'status': status,
                    'trial': trial,
                    'accept': accept,
                }
                yield result
            # We always miss the first ensemble in scheme 1:
            if scheme == 1:
                accept, trial, status = null_move(ensembles[0], cycle)
                result = {
                    'ensemble': ensembles[0].ensemble_number,
                    'retis-move': 'nullmove',
                    'status': status,
                    'trial': trial,
                    'accept': accept,
                }
                yield result
    else:  # Just swap two ensembles:
        idx = rgen.random_integers(0, len(ensembles) - 2)
        accept, trial, status = retis_swap(
            ensembles, idx, order_function, engine,
            settings, cycle, rgen
        )
        result = {
            'ensemble': idx,
            'retis-move': 'swap',
            'status': status,
            'trial': trial[0],
            'accept': accept,
            'swap-with': idx + 1,
        }
        yield result
        result = {
            'ensemble': idx + 1,
            'retis-move': 'swap',
            'status': status,
            'trial': trial[1],
            'accept': accept,
            'swap-with': idx,
        }
        yield result
        # Do null moves in the other ensembles, if requested:
        if settings['retis']['nullmoves']:
            for path_ensemble in ensembles:
                idx2 = path_ensemble.ensemble_number
                if idx2 not in (idx, idx + 1):
                    accept, trial, status = null_move(path_ensemble, cycle)
                    result = {
                        'ensemble': idx2,
                        'retis-move': 'nullmove',
                        'status': status,
                        'trial': trial,
                        'accept': accept,
                    }
                    yield result


def retis_swap(ensembles, idx, order_function, engine,
               settings, cycle, rgen=None):
    """Perform a RETIS swapping move for two ensembles.

    The RETIS swapping move will attempt to swap accepted paths between
    two ensembles in the hope that path from [i^+] is an acceptable path
    for [(i+1)^+] as well. We have two cases:

    1) If we try to swap between [0^-] and [0^+] we need to integrate
       the equations of motion.
    2) Otherwise, we can just swap and accept if the path from [i^+] is
       an acceptable path for [(i+1)^+]. The path from [(i+1)^+] is
       always acceptable for [i^+] (by construction).

    Parameters
    ----------
    ensembles : list of objects like :py:class:`.PathEnsemble`
        This is a list of the ensembles we are using in the RETIS
        method.
    idx : integer
        Definition of what path ensembles to swap. We will swap
        `ensembles[idx]` with `ensembles[idx+1]`. If `idx == 0` we have
        case 1) defined above.
    order_function : object like :py:class:`.OrderParameter`
        The class used for calculating the order parameter(s).
    engine : object like :py:class:`.EngineBase`
        The engine to use for propagating a path.
    rgen : object like :py:class:`.RandomGenerator`, optional
        This is a random generator.
    settings : dict
        This dict contains the settings for the RETIS method.
    cycle : integer
        Current cycle number.

    Returns
    -------
    out[0] : boolean
        Should the path be accepted or not?
    out[1] : list of object like :py:class:`.PathBase`
        The trial paths.
    out[2] : string
        The status for the trial paths.

    Note
    ----
    Note that path.generated is **NOT** updated here. This is because
    we are just swapping references and not the paths. In case the
    swap is rejected updating this would invalidate the last accepted
    path.

    """
    logger.info(
        'Swapping: %s <-> %s',
        ensembles[idx].ensemble_name,
        ensembles[idx+1].ensemble_name
    )
    if rgen is None:
        rgen = np.random.RandomState()
    if idx == 0:
        return retis_swap_zero(ensembles, order_function, engine,
                               settings, cycle)
    ensemble1 = ensembles[idx]
    ensemble2 = ensembles[idx + 1]
    path1 = ensemble1.last_path
    path2 = ensemble2.last_path
    # Check if path1 can be accepted in ensemble 2:
    cross = path1.check_interfaces(ensemble2.interfaces)[-1]
    accept = cross[1]

    status = 'NCR'

    if accept and 'high_accept' in settings['tis'] and \
            settings['tis']['high_accept']:
        accept, status = high_acc_swap(path1, path2, rgen,
                                       ensemble1.interfaces[1],
                                       ensemble2.interfaces[1],
                                       ensemble2.interfaces[-1])

    if accept:  # Accept the swap:
        status = 'ACC'
        # Do the swap:
        for trial, ensemble in zip((path2, path1), (ensemble1, ensemble2)):
            if trial.get_move() == 'ss':
                trial.weight = compute_weight_ss(trial, ensemble.interfaces)
            else:
                trial.weight = 1
        # And set moves:
        if path2.get_move() != 'ld':
            path2.set_move('s+')  # Came from right.
        if path1.get_move() != 'ld':
            path1.set_move('s-')  # Came from left.
        logger.info('Swap was accepted.')
        # To avoid overwriting files, we move the paths to the
        # generate directory here. They will be moved into the
        # accepted directory by the `add_path_data` below.
        ensemble1.move_path_to_generated(path2)
        ensemble2.move_path_to_generated(path1)
        ensemble1.add_path_data(path2, status, cycle=cycle)
        ensemble2.add_path_data(path1, status, cycle=cycle)
        return accept, (path2, path1), status

    logger.info('Swap was rejected. (%s)', status)
    # Make shallow copies:
    trial1 = copy.copy(path2)
    trial2 = copy.copy(path1)

    trial1.set_move('s+')  # Came from right:
    trial2.set_move('s-')  # Came from left:
    ensemble1.add_path_data(trial1, status, cycle=cycle)
    ensemble2.add_path_data(trial2, status, cycle=cycle)

    return accept, (trial1, trial2), status


def retis_swap_zero(ensembles, order_function, engine,
                    settings, cycle):
    """Perform the RETIS swapping for ``[0^-] <-> [0^+]`` swaps.

    The RETIS swapping move for ensembles [0^-] and [0^+] requires some
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
        This is a list of the ensembles we are using in the RETIS method.
    order_function : object like :py:class:`.OrderParameter`
        The class used for calculating the order parameter(s).
    engine : object like :py:class:`.EngineBase`
        The engine to use for propagating a path.
    settings : dict
        This dict contains the settings for the RETIS method.
    cycle : integer
        The current cycle number.

    Returns
    -------
    out : string
        The result of the swapping move.

    """
    ensemble0 = ensembles[0]
    ensemble1 = ensembles[1]
    # 1. Generate path for [0^-] from [0^+]:
    # We generate from the first point of the path in [0^+]:
    logger.debug('Creating path for [0^-] from [0^+]')
    # Note: The copy below is not really needed as the
    # propagate method will not alter the initial state:
    system = ensemble1.last_path.phasepoints[0].copy()
    logger.debug('Initial point is: %s', system)
    # Propagate it backward in time:
    maxlen = settings['tis']['maxlength']
    path_tmp = ensemble1.last_path.empty_path(maxlen=maxlen-1)
    engine.exe_dir = ensemble0.directory['generate']
    logger.debug('Propagating for [0^-]')
    engine.propagate(path_tmp, system, order_function,
                     ensemble0.interfaces, reverse=True)
    path0 = path_tmp.empty_path(maxlen=maxlen)
    for phasepoint in reversed(path_tmp.phasepoints):
        path0.append(phasepoint)
    # Add second point from [0^+] at the end:
    logger.debug('Adding second point from [0^+]:')
    # Here we make a copy of the phase point, as we will update
    # the configuration and append it to the new path:
    phase_point = ensemble1.last_path.phasepoints[1].copy()
    logger.debug('Point is %s', phase_point)
    engine.dump_phasepoint(phase_point, 'second')
    path0.append(phase_point)
    if path0.length == maxlen:
        path0.status = 'BTX'
    elif path0.length < 3:
        path0.status = 'BTS'
    elif 'L' in path0.check_interfaces(ensemble0.interfaces)[:2]:
        path0.status = '0-L'
    else:
        path0.status = 'ACC'
    # 2. Generate path for [0^+] from [0^-]:
    logger.debug('Creating path for [0^+] from [0^-]')
    # This path will be generated starting from the LAST point of [0^-] which
    # should be on the right side of the interface. We will also add the
    # SECOND LAST point from [0^-] which should be on the left side of the
    # interface, this is added after we have generated the path and we
    # save space for this point by letting maxlen = maxlen-1 here:
    path_tmp = path0.empty_path(maxlen=maxlen-1)
    # We start the generation from the LAST point:
    # Again, the copy below is not needed as the propagate
    # method will not alter the initial state.
    system = ensemble0.last_path.phasepoints[-1].copy()
    logger.debug('Initial point is %s', system)
    engine.exe_dir = ensemble1.directory['generate']
    logger.debug('Propagating for [0^+]')
    engine.propagate(path_tmp, system, order_function,
                     ensemble1.interfaces, reverse=False)
    # Ok, now we need to just add the SECOND LAST point from [0^-] as
    # the first point for the path:
    path1 = path_tmp.empty_path(maxlen=maxlen)
    phase_point = ensemble0.last_path.phasepoints[-2].copy()
    logger.debug('Add second last point: %s', phase_point)
    engine.dump_phasepoint(phase_point, 'second_last')
    path1.append(phase_point)
    path1 += path_tmp  # Add rest of the path.
    if ensembles[1].last_path.get_move() != 'ld':
        path0.set_move('s+')
    else:
        path0.set_move('ld')

    if ensembles[0].last_path.get_move() != 'ld':
        path1.set_move('s-')
    else:
        path1.set_move('ld')
    if path1.length == maxlen:
        path1.status = 'FTX'
    elif path1.length < 3:
        path1.status = 'FTS'
    else:
        path1.status = 'ACC'
    # Final checks:
    status = 'ACC'  # We are optimistic and hope that this is the default.
    accept = True

    # These should be 1 unless length of paths equals 3.
    # This technicality is not yet fixed. (An issue in open as a remidner)
    path0.weight, path1.weight = 1., 1.
    if path0.status != 'ACC':
        path1.status = path0.status
        status = path0.status
        accept = False
        logger.debug('Rejecting swap path in [0^-], %s', path0.status)
    if path1.status != 'ACC':
        path0.status = path1.status
        status = path1.status
        accept = False
        logger.debug('Rejecting swap path in [0^+], %s', path1.status)
    logger.debug('Done with swap zero!')
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
        This is the path ensemble to update with the null move.
    cycle : integer
        The current cycle number.

    Returns
    -------
    out[0] : boolean
        Should the path be accepted or not? Here, it's always True
        since the null move is always accepted.
    out[1] : object like :py:class:`.PathBase`
        The generated path.
    out[2] : string
        The status will here be 'ACC' since we just accept
        the last accepted path again in this move.

    """
    logger.info('Null move for: %s', path_ensemble.ensemble_name)
    status = 'ACC'
    path = path_ensemble.last_path
    if not path.get_move() == 'ld':
        path.set_move('00')
    path_ensemble.add_path_data(path, status, cycle=cycle)
    return True, path, status


def high_acc_swap(path1, path2, rgen, interface1, interface2, interfaceb):
    """Accept or Reject a swap move with High Acceptance Stone Skipping.

    Parameters
    ----------
    path1 : object like :py:class:`.PathBase`
        The path in the LOWER ensemble to exchange.
    path2 : object like :py:class:`.PathBase`
        The path in the UPPER ensemble to exchange.
    rgen : object like :py:class:`.RandomGenerator`
        This is a random generator.
    interface1: float
        The position of the interface defining the LOWER ensemble.
    interface2: float
        The position of the interface defining the UPPER ensemble.
    interfaceb: float
        The position of the interface defining State B.

    Returns
    -------
    out[0] : boolean
        True if th move should be accepted.

    Notes
    -----
     -  This function is needed only when paths generated via Stone Skipping
            are involved.
      - In the case that a path bears a flag 'ld', the swap is accepted,
            but the flag will be unchanged.

    """
    if path1.generated[0] == 'ss' and path2.generated[0] == 'ss':
        # Crossing before the move
        c1_old = crossing_counter(path1, interface1)
        c2_old = crossing_counter(path2, interface2)
        # Crossing if the move would be accepted
        c1_new = crossing_counter(path2, interface1)
        c2_new = crossing_counter(path1, interface2)
        p_swap_acc = c1_new*c2_new/(c1_old*c2_old)

    elif path1.generated[0] == 'ss':
        c1_old = crossing_counter(path1, interface1)
        c1_new = crossing_counter(path2, interface1)
        p_swap_acc = c1_new/c1_old
        if path2.get_end_point(interfaceb) == 'R':
            p_swap_acc *= 2
        if path1.get_end_point(interfaceb) == 'R':
            p_swap_acc *= 0.5

    elif path2.generated[0] == 'ss':
        c2_old = crossing_counter(path2, interface2)
        c2_new = crossing_counter(path1, interface2)
        p_swap_acc = c2_new/c2_old
        if path1.get_end_point(interfaceb) == 'R':
            p_swap_acc *= 2
        if path2.get_end_point(interfaceb) == 'R':
            p_swap_acc *= 0.5

    else:
        p_swap_acc = 1

    # Finally, randomly decide what to do:
    if rgen.rand() < p_swap_acc:
        return True, 'ACC'  # Accepted

    return False, 'HAS'  # Rejected
