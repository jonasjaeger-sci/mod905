# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""Module for Monte Carlo Algorithms and other "random" functions.

In this module, Monte Carlo Algorithms are defined. Note that some
derived or "random" functions are also defined in the TIS module.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

metropolis_accept_reject
    Accept/reject a energy change according to the metropolis rule.

max_displace_step
    Monte Carlo routine for displacing particles. It will select and
    displace one particle randomly.
"""
from __future__ import absolute_import
import numpy as np


__all__ = ['metropolis_accept_reject', 'max_displace_step']


def accept_reject_displace(rgen, system, trial):
    """Routine for accepting or rejecting a MC move.

    This routine will accept or reject a Monte Carlo move based on a
    the Metropolis accept/reject criterion as defined in the function
    `metropolis_accept_reject`. Here, the change in potential energy is
    used as input to `metropolis_accept_reject`.

    Parameters
    ----------
    rgen : object like `RandomGenerator` from `pyretis.core.random_gen`
        The random number generator.
    system : object like `System` from `pyretis.core.system`
        The system object we are investigating.
    trial : numpy.array
        The the trial position(s)

    Returns
    -------
    out[0] : numpy.array, same shape as input `trial`
        The accepted positions (trial or the original positions).
    out[1] : float
        The energy corresponding to the accepted positions.
    out[2] : numpy.array
        The trial positions.
    out[3] : float
        The potential energy of the trial positions.
    out[4] : boolean
        True if move is accepted, False otherwise.
    """
    pos = np.copy(system.particles.pos)
    system.particles.pos = trial
    v_trial = system.evaluate_potential()
    system.particles.pos = pos
    deltae = v_trial - system.v_pot
    if metropolis_accept_reject(rgen, system, deltae):
        return trial, v_trial, trial, v_trial, True
    else:
        return system.particles.pos, system.v_pot, trial, v_trial, False


def accept_reject_momenta(rgen, system, dke, aimless=True):
    """Accept/reject momenta change based on a change in kinetic energy.

    Parameters
    ----------
    rgen : object like `RandomGenerator` from `pyretis.core.random_gen`
        The random number generator.
    system : object like `System` from `pyretis.core.system`
        The system object we are investigating. This is used
        to access the beta factor.
    dke : float
        The change in kinetic energy.
    aimless : boolean
        This variable can be used to override the acceptance rule and
        if it's True, all changes will be accepted.

    Returns
    -------
    out : boolean
        True if the move is accepted, False otherwise.
    """
    if aimless:  # for the aimless shooting we accept
        return True
    else:
        return metropolis_accept_reject(rgen, system, dke)


def metropolis_accept_reject(rgen, system, deltae):
    """Accept/reject a energy change according to the metropolis rule.

    FIXME: Check if metropolis really is a good name here.

    Parameters
    ----------
    rgen : object like `RandomGenerator` from `pyretis.core.random_gen`
        The random number generator.
    system : object like `System` from `pyretis.core.system`
        The system object we are investigating. This is used
        to access the beta factor.
    deltae : float
        The change in energy.

    Returns
    -------
    out : boolean
        True if the move is accepted, False otherwise.

    Notes
    -----
    A overflow is possible when using `numpy.exp()` here.
    This can for instance happen in a umbrella simulation
    where the bias potential is infinite or very large.
    Right now, this is just ignored.
    """
    if deltae < 0.0:  # short-cut to avoid calculating np.exp()
        return True
    else:
        pacc = np.exp(-system.temperature['beta'] * deltae)
        return rgen.rand() < pacc


def max_displace_step(rgen, system, maxdx=0.1, idx=None):
    """Monte Carlo routine for displacing particles.

    It selects and displaces one particle randomly.
    If the move is accepted, the new positions and energy are
    return. Otherwise, the move is rejected and the old positions
    and potential energy is returned.
    The function accept_reject is used to accept/reject the move.

    Parameters
    ----------
    rgen : object like `RandomGenerator` from `pyretis.core.random_gen`
        The random number generator.
    system : object like `System` from `pyretis.core.system`
        The system object to operate on
    maxdx : float, optional
        The maximum displacement (default is 0.1).
    idx : int, optional.
        Index of particle to displace. If `idx` is not given, the
        particle is chosen randomly.

    Returns
    -------
    out : boolean
        The outcome of applying the function `accept_reject` to the
        system and trial position.
    """
    if idx is None:
        idx = rgen.random_integers(0, system.particles.npart - 1)
    trial = np.copy(system.particles.pos)
    trial[idx] += 2.0 * maxdx * (rgen.rand(system.get_dim()) - 0.5)
    return accept_reject_displace(rgen, system, trial)
