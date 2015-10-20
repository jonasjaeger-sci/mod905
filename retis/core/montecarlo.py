# -*- coding: utf-8 -*-
"""Module for Monte Carlo Algorithms and other "random" functions."""
from __future__ import absolute_import
import numpy as np


__all__ = ('metropolis_accept_reject', 'max_displace_step')


def accept_reject_displace(rgen, system, trial):
    """
    Routine for accepting or rejecting a MC move.

    Parameters
    ----------
    rgen : object
        The random number generator.
    system : object
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
        True if move is acceped, False otherwise.

    Notes
    -----
    A overflow is possible when using np.exp() here.
    This can for instance happen in a umbrella simulation
    where the bias potential is infinite or very large.
    Right now, this is just ignored.
    """
    v_trial = system.evaluate_potential(pos=trial)
    deltae = v_trial - system.v_pot
    if metropolis_accept_reject(rgen, system, deltae):
        return trial, v_trial, trial, v_trial, True
    else:
        return system.particles.pos, system.v_pot, trial, v_trial, False


def accept_reject_momenta(rgen, system, dke, aimless=True):
    """
    Accept or reject a change in momenta based on the given change
    in kinetic energy.

    Parameters
    ----------
    rgen : object of type RandomGenerator
        The random number generator.
    system : object of type System
        The system object we are investigating. This is used
        to access the beta factor.
    dke : float
        The change in kinetic energy.
    """
    if aimless:  # for the aimless shooting we accept
        return True
    else:
        return metropolis_accept_reject(rgen, system, dke)


def metropolis_accept_reject(rgen, system, deltae):
    """
    Accept or reject a change of energy according
    to the metropolis rule.

    FIXME: Check if metropolis really is a good name here.

    Parameters
    ----------
    rgen : object of type RandomGenerator
        The random number generator.
    system : object of type System
        The system object we are investigating. This is used
        to access the beta factor.
    deltae : float
        The change in energy.
    """
    if deltae < 0.0:  # short-cut to avoid calculating np.exp()
        return True
    else:
        pacc = np.exp(-system.temperature['beta'] * deltae)
        return rgen.rand() < pacc


def max_displace_step(rgen, system, maxdx=0.1, idx=None):
    """
    Monte Carlo routine for diplacing particles.

    It selects and displaces one particle randomly.
    If the move is accepted, the new positions and energy are
    return. Otherwise, the move is rejected and the old positions
    and potential energy is returned.
    The function accept_reject is used to accept/reject the move.

    Parameters
    ----------
    rgen : object of type RandomGenerator
        The random number generator.
    system : object
        The system object to operate on
    maxdx : float, optional
        The maximum displacement (default is 0.1).
    idx : int, optional.
        Index of particle to displace. If idx is not given, the particle
        is chosen randomly.

    Returns
    -------
    out : The outcome of applying the function accept_reject to the system
        and trial position.
    """
    if idx is None:
        idx = rgen.random_integers(0, system.particles.npart - 1)
    trial = np.copy(system.particles.pos)
    trial[idx] += 2.0 * maxdx * (rgen.rand(system.get_dim()) - 0.5)
    return accept_reject_displace(rgen, system, trial)
