# -*- coding: utf-8 -*-
"""This module contains methods for RETIS.

This module defines methods that are needed to perform Replica Exchange
Transition Interface Sampling (RETIS). The algorithms implemented here and
the description of RETIS can be found in van Erp [RETIS]_.

Important classes and functions
-------------------------------

- make_retis_step : A function to determine and execute the RETIS move.

References
----------

.. [RETIS] Titus S. van Erp
           Phys. Rev. Lett. 98, 26830 (2007)
           http://dx.doi.org/10.1103/PhysRevLett.98.268301
"""
from __future__ import print_function
from pyretis.core.tis import make_tis_step_ensemble, propagate
from pyretis.core.path import Path, reverse_path
import numpy as np

__all__ = ['make_retis_step']


def make_retis_step(ensembles, rgen, system, order_function, integrator,
                    settings, cycle):
    """Determine and execute the approprate RETIS move.

    Here we will determine what kind of RETIS moves we should do.
    We have two options:

    1) Do the RETIS swapping moves. This is done by calling
       `name_of_function`
    2) Do TIS moves, either for all ensembles or for just one, based on
       values of relative shoot frequencies. This is done by calling
       `make_retis_tis_steps`.

    This method will just determine and execute the approriate move (1 or 2)
    based on the given swapping frequencies in the `settings` and drawing a
    random number from the random number generator `rgen`.

    Parameters
    ----------
    ensembles : list of objects like `PathEnsemble` from `pyretis.core.path`
        This is a list of the ensembles we are using in the RETIS method
    rgen : object like `RandomGenerator` from `pyretis.core.random_gen`
        This is a random generator. Here we assume that we can call
        `rgen.rand()` to draw random uniform numbers.
    system : object like `System` from `pyretis.core.system`
        System is used here since we need access to the temperature
        and to the particle list
    order_function : function
        This function takes the system as it's argument and returns a float
        which is equal to the order parameter.
    integrator : object like `Integrator` from `pyretis.core.integrators`
        A integrator to use for propagating a path.
    settings : dict
        This dict contains the settings for the RETIS method.
    cycle : integer
        The current cycle number

    Returns
    -------
    """
    if rgen.rand() < settings['retis']['swapfreq']:
        # Do RETIS moves
        print('Will execute RETIS moves')
        retis_moves(ensembles, rgen, system, order_function, integrator,
                    settings['retis'], cycle)
    else:
        print('Will execute TIS moves')
        retis_tis_moves(ensembles, rgen, system, order_function,
                        integrator, settings, cycle)


def retis_tis_moves(ensembles, rgen, system, order_function, integrator,
                    settings, cycle):
    """Method to execute TIS steps in the RETIS method.

    This method will execute the TIS steps in the RETIS method. These
    differ slightly from the regular TIS moves since we have two options
    on how to perform them. These two options are controlled by the given
    `settings`:

    1) If `relative_shoots` is given in the input settings, then we will
       pick at random what ensemble we will perform TIS on. For all the
       other ensembles we again have two options based on the given
       `settings['nullmoves']`:

       a) Do a 'null move' in all other ensembles.
       b) Do nothing for all other ensembles.

       Performing the null move in an ensemble will simply just accept the
       previously accepted path in that ensemble again.

    2) If `relative_shoots` is not given in the input settings, then we
       will perform TIS moves for all path ensembles.

    Parameters
    ----------
    ensembles : list of objects like `PathEnsemble` from `pyretis.core.path`
        This is a list of the ensembles we are using in the RETIS method
    rgen : object like `RandomGenerator` from `pyretis.core.random_gen`
        This is a random generator. Here we assume that we can call
        `rgen.rand()` to draw random uniform numbers.
    system : object like `System` from `pyretis.core.system`
        System is used here since we need access to the temperature
        and to the particle list
    order_function : function
        This function takes the system as it's argument and returns a float
        which is equal to the order parameter.
    integrator : object like `Integrator` from `pyretis.core.integrators`
        A integrator to use for propagating a path.
    settings : dict
        This dict contains the settings for the RETIS method.
    cycle : integer
        The current cycle number
    """
    relative = settings.get('relative_shoots', None)
    if relative is not None:
        # will to relative shootings
        freq = rgen.rand()
        cumulative = 0.0
        idx = None
        for idx, path_freq in enumerate(relative):
            cumulative += path_freq
            if freq < cumulative:
                break
        # do TIS for the given ensemble
        try:
            path_ensemble = ensembles[idx]
        except TypeError:  # idx == None may happen if something is very wrong
            msg = 'Error in relative shoot frequencies! Aborting!'
            raise ValueError(msg)
        make_tis_step_ensemble(path_ensemble, rgen, system,
                               order_function, integrator,
                               settings['tis'], cycle)
        if settings.get('nullmoves', 'False'):
            for other, path_ensemble in enumerate(ensembles):
                if other != idx:
                    null_move(path_ensemble, cycle)
    else:  # just do TIS for them all
        for path_ensemble in ensembles:
            make_tis_step_ensemble(path_ensemble, rgen, system,
                                   order_function, integrator,
                                   settings['tis'], cycle)


def retis_moves(ensembles, rgen, system, integrator, order_function,
                settings, cycle):
    """Perform RETIS moves on the given ensembles.

    This method will perform RETIS moves on the given ensembles.
    First we have to strategies based on `settings['swapsimul']`:

    1) If `settings['swapsimul']` is True we will perform several swaps,
       either ``[0^-] <-> [0^+], [1^+] <-> [2^+], ...`` or
       ``[0^+] <-> [1^+], [2^+] <-> [3^+], ...``. Which one of these two swap
       options we use is determined randomly and they have equal probability.
    2) If `settings['swapsimul']` is False we will just perform one swap for
       randomly chosen ensembles, i.e. we pick a random ensemble and try to
       swap with the ensemble to the right. Here we may also perform null
       moves if the `settings['nullmove']` specifies so.

    Parameters
    ----------
    ensembles : list of objects like `PathEnsemble` from `pyretis.core.path`
        This is a list of the ensembles we are using in the RETIS method
    rgen : object like `RandomGenerator` from `pyretis.core.random_gen`
        This is a random generator. Here we assume that we can call
        `rgen.rand()` to draw random uniform numbers.
    system : object like `System` from `pyretis.core.system`
        System is used here since we need access to the temperature
        and to the particle list
    integrator : object like `Integrator` from `pyretis.core.integrators`
        A integrator to use for propagating a path.
    order_function : function
        This function takes the system as it's argument and returns a float
        which is equal to the order parameter.
    settings : dict
        This dict contains the settings for the RETIS method.
    cycle : integer
        The current cycle number
    """
    if settings['swapsimul']:
        if len(ensembles) < 3:
            # only two ensembles, we don't have choice and will do a
            # [0^-] <-> [0^+] swap
            scheme = 0
        else:
            scheme = 0 if rgen.rand() < 0.5 else 1
            # scheme == 0 is the swaps: [0^-] <-> [0^+], [1^+] <-> [2^+], ...
            # scheme == 1 is the swaps: [0^+] <-> [1^+], [2^+] <-> [3^+], ...
        for idx in range(scheme, len(ensembles) - 1, 2):
            retis_swap(ensembles, idx, system, order_function, integrator,
                       settings, cycle)

        if settings['nullmoves']:
            if len(ensembles) % 2 != scheme:  # missed last
                # this is perhaps strange but it's equal to:
                # (scheme == 0 and len(ensembles) % 2 != 0) or
                # (scheme == 1 and len(ensembles) % 2 == 0)
                null_move(ensembles[-1], cycle)
            if scheme == 1:  # we did not include [0^-]
                null_move(ensembles[0], cycle)
    else:
        idx = rgen.random_integers(0, len(ensembles) - 2)
        retis_swap(ensembles, idx, system, order_function, integrator,
                   settings, cycle)
        if settings['nullmoves']:
            for idxo, path_ensemble in enumerate(ensembles):
                if idxo != idx and idxo != idx + 1:
                    null_move(path_ensemble, cycle)


def retis_swap(ensembles, idx, system, order_function, integrator,
               settings, cycle):
    """Perform a RETIS swapping move for two ensembles.

    The RETIS swapping move will attempt to swap accepted paths between two
    ensembles in the hope that path from [i^+] is an acceptable path for
    [(i+1)^+] as well. We have two cases:

    1) If we try to swap between [0^-] and [0^+] we need to integrate the
       equations of motion.
    2) Otherwise we can just swap and accept if the path from [i^+] is an
       acceptable path for [(i+1)^+]. The path from [(i+1)^+] is always
       acceptable for [i^+] (by construction).

    Parameters
    ----------
    ensembles : list of objects like `PathEnsemble` from `pyretis.core.path`
        This is a list of the ensembles we are using in the RETIS method
    idx : integer
        Definition of what path ensembles to swap. We will swap
        `ensembles[idx]` with `ensembles[idx+1]`. If `idx == 0` we have
        case 1) defined above.
    system : object like `System` from `pyretis.core.system`
        System is used here since we need access to the temperature
        and to the particle list
    order_function : function
        This function takes the system as it's argument and returns a float
        which is equal to the order parameter.
    integrator : object like `Integrator` from `pyretis.core.integrators`
        A integrator to use for propagating a path.
    settings : dict
        This dict contains the settings for the RETIS method.
    cycle : integer
        Current cycle number
    """
    print('Do swapping: {} <-> {}'.format(ensembles[idx].ensemble,
                                          ensembles[idx+1].ensemble))
    if idx == 0:
        retis_swap_zero(ensembles, system, order_function, integrator,
                        settings, cycle)
    else:
        ensemble1 = ensembles[idx]
        ensemble2 = ensembles[idx + 1]
        path1 = ensemble1.last_path
        path2 = ensemble2.last_path
        # Check if path1 crosses correctly for ensemble 2:
        cross = path1.check_interfaces(ensemble2.interfaces)[-1]
        # Do the swap
        path1, path2 = path2, path1
        path1.set_move('s+')  # came from right
        path2.set_move('s-')  # came from left
        if cross[1]:  # accept the swap
            status = 'ACC'
        else:  # reject:
            status = 'NCR'
        ensemble1.add_path_data(path1, status, cycle=cycle)
        ensemble2.add_path_data(path2, status, cycle=cycle)


def retis_swap_zero(ensembles, system, order_function, integrator,
                    settings, cycle):
    """The retis swapping move for ``[0^-] <-> [0^+]`` swaps.

    The retis swapping move for ensembles [0^-] and [0^+] requires some extra
    integration. Here we are generating new paths for [0^-] and [0^+] in
    the following way:

    1) For [0^-] we take the initial point in [0^+] and integrate backward in
       time. This is merged with the second point in [0^+] to give the final
       path. The initial point in [0^+] starts to the left of the interface
       and the second point is on the right side - i.e. the path will cross
       the interface at the end points. If we let the last point in [0^+] be
       called ``A_0`` and the second last point ``B``, and we let
       ``A_1, A_2, ...`` be the points on the backward trajectory generated
       from ``A_0`` then the final path will be made up of the points
       ``[..., A_2, A_1, A_0, B]``. Here, ``B`` will be on the right side of
       the interface and the first point of the path will also be on the right
       side.

    2) For [0^+] we take the last point of [0^-] and use that as an initial
       point to generate a new trajectory for [0^+] by integration forward
       in time. We also include the second last point of the [0^-] trajectory
       which is on the left side of the interface.
       We let the second last point be ``B`` (this is on the left side of
       the interface), the last point ``A_0`` and the points generated
       from ``A_0`` we denote by ``A_1, A_2, ...``. Then the resulting path
       will be ``[B, A_0, A_1, A_2, ...]``. Here, ``B`` will be on the left
       side of the interface and the last point of the path will also be on
       the left side of the interface.

    Parameters
    ----------
    ensembles : list of objects like `PathEnsemble` from `pyretis.core.path`
        This is a list of the ensembles we are using in the RETIS method
    system : object like `System` from `pyretis.core.system`
        System is used here since we need access to the temperature
        and to the particle list
    order_function : function
        This function takes the system as it's argument and returns a float
        which is equal to the order parameter.
    integrator : object like `Integrator` from `pyretis.core.integrators`
        A integrator to use for propagating a path.
    settings : dict
        This dict contains the settings for the RETIS method.
    cycle : integer
        The current cycle number
    """
    ensemble0 = ensembles[0]
    ensemble1 = ensembles[1]
    # 1) Generate path for [0^-] from [0^+]:
    # Set the system at the initial point of path in [0^+]:
    pos, vel = ensemble1.last_path[0][0:2]
    system.particles.vel = np.copy(vel)
    system.particles.pos = np.copy(pos)
    system.potential_and_force()  # update forces and potential
    # Propagate it backward in time:
    maxlenb = settings['maxlength'] - 1
    path0 = propagate(system, integrator,
                      order_function,
                      ensemble0.interfaces,
                      maxlen=maxlenb,
                      reverse=True)[0]
    # Reverse this path:
    path0 = reverse_path(path0)
    # and add second point from [0^+] at the end:
    path0.append(*ensemble1.last_path[1])
    # 2) Generate path for [0^+] from [0^-]:
    # We start the generation from the last point
    pos, vel = ensemble0.last_path[-1][0:2]
    system.particles.vel = np.copy(vel)
    system.particles.pos = np.copy(pos)
    system.potential_and_force()  # update forces and potential
    # Propagate forward in time, here we begin by creating a path and
    # adding the second last point from the [0^-] path to it. This is to
    # avoid adding it later since we know that this will be the first point
    # in the trajectory.
    path1 = Path(maxlen=settings['maxlength'])
    path1.append(*ensemble0.last_path[-2])
    # propagate forward, note that the maxlen is there set to
    # settings['maxlength'] but since we already have one point
    # in the path, propagate will at most do ``settings[maxlength'] - 1``
    # steps.
    propagate(system, integrator,
              order_function,
              ensemble1.interfaces,
              maxlen=settings['maxlength'],
              reverse=False,
              path=path1)
    # update status, etc
    path1.set_move('s-')
    if len(path1.path) == settings['maxlength']:
        path1.status = 'FTX'
    else:
        path1.status = 'ACC'
    ensemble1.add_path_data(path1, path1.status, cycle=cycle)

    path0.set_move('s+')
    if len(path0.path) == settings['maxlength']:
        path0.status = 'BTX'
    else:
        path0.status = 'ACC'
    ensemble0.add_path_data(path0, path0.status, cycle=cycle)


def null_move(path_ensemble, cycle):
    """Perform a null move for an path ensemble.

    The null move simply consist of accepting the last accepted path again.

    Parameters
    ----------
    path_ensemble : object like `pyretis.core.path.PathEnsemble`
        This is the path ensemble to update with the null move
    cycle : integer
        The current cycle number

    Returns
    -------
    N/A but update the given `path_ensemble` with a new accepted path.
    """
    print('Null move for {}'.format(path_ensemble.ensembles))
    path = path_ensemble.last_path
    path.set_move('00')
    path_ensemble.add_path(path, 'ACC', cycle=cycle)
