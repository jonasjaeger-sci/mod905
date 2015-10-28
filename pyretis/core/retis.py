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


__all__ = ['make_retis_step']


def make_retis_step(ensembles, rgen, settings, cycle):
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
    settings : dict
        This dict contains the settings for the RETIS method.
    cycle : integer
        The current cycle number

    Returns
    -------
    """
    if rgen.rand() < settings['swapfreq']:
        # Do RETIS moves
        print('Will execute RETIS moves')
        retis_moves(ensembles, rgen, settings, cycle)
    else:
        print('Will execute TIS moves')
        retis_tis_moves(ensembles, rgen, settings, cycle)


def retis_tis_moves(ensembles, rgen, settings, cycle):
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
    settings : dict
        This dict contains the settings for the RETIS method.
    cycle : integer
        The current cycle number

    Returns
    -------
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
        print('Do TIS for', path_ensemble.ensemble)
        if settings.get('nullmoves', 'False'):
            for other, path_ensemble in enumerate(ensembles):
                if other != idx:
                    null_move(path_ensemble, cycle)
    else:  # just do TIS for them all
        for path_ensemble in ensembles:
            print('Do TIS for', path_ensemble.ensemble)


def retis_moves(ensembles, rgen, settings, cycle):
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
            retis_swap(ensembles, idx, cycle)

        if settings['nullmoves']:
            if len(ensembles) % 2 != scheme:  # missed last
                null_move(ensembles[-1], cycle)
                # this is perhaps strange but it's equal to:
                # (scheme == 0 and len(ensembles) % 2 != 0) or
                # (scheme == 1 and len(ensembles) % 2 == 0)
            if scheme == 1:  # we did not include [0^-]
                null_move(ensembles[0], cycle)
    else:
        idx = rgen.random_integers(0, len(ensembles) - 2)
        retis_swap(ensembles, idx, cycle)
        if settings['nullmoves']:
            for idxo, path_ensemble in enumerate(ensembles):
                if idxo != idx and idxo != idx + 1:
                    null_move(path_ensemble, cycle)


def retis_swap(ensembles, idx, cycle):
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
    cycle : integer
        Current cycle number
    """
    print('Do swapping: {} <-> {}'.format(ensembles[idx].ensemble,
                                          ensembles[idx+1].ensemble))
    if idx == 0:
        pass
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
