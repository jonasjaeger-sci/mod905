# -*- coding: utf-8 -*-
"""
Module for Monte Carlo Algorithms and other 
"random" functions.
"""
import numpy as np
from numpy.random import RandomState

__all__ = ['seed_random_generator', 'accept_reject', 'max_displace_step', 'random_normal']

RANDOMGENERATOR = RandomState()  # this will be the random number generator


def seed_random_generator(seed=1, rgen=RANDOMGENERATOR):
    """
    Helper function to seed the random number generator

    Parameters
    ----------
    seed : int, optional.
        The seed for the random number generator.
    rgen : object, optional.
        The random number generator. Default is the global one in this module.

    Returns
    -------
    None, however ``rgen`` is seeded with the given seed.
    """
    rgen.seed(seed)


def accept_reject(system, trial, rgen=RANDOMGENERATOR):
    """
    Routine for accepting or rejecting a MC move

    Parameters
    ----------
    system : object
        The system object we are investigating.
    trial : numpy.array
        The the trial position(s)
    rgen : object, optional.
        The random number generator. Default is the global one in this module.

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
    pacc = np.exp(-system.temperature['beta'] * deltae)
    if rgen.rand() < pacc:
        return trial, v_trial, trial, v_trial, True
    else:
        return system.particles.pos, system.v_pot, trial, v_trial, False


def max_displace_step(system, maxdx=0.1, idx=None, rgen=RANDOMGENERATOR):
    """
    Monte Carlo routine for diplacing particles.

    It selects and displaces one particle randomly.
    If the move is accepted, the new positions and energy are
    return. Otherwise, the move is rejected and the old positions
    and potential energy is returned.
    The function accept_reject is used to accept/reject the move.

    Parameters
    ----------
    system : object
        The system object to operate on
    maxdx : float, optional
        The maximum displacement (default is 0.1).
    rgen : object, optional.
        The random number generator. Default is the global one in this module.
    idx : int, optional.
        Index of particle to displace. If idx is not given, the particle
        is choosen randomly.

    Returns
    -------
    out : The outcome of applying the function accept_reject to the system
        and trial position.
    """
    if idx is None:
        idx = rgen.random_integers(0, system.particles.npart - 1)
    trial = np.copy(system.particles.pos)
    trial[idx] += 2.0 * maxdx * (rgen.rand(system.get_dim()) - 0.5)
    return accept_reject(system, trial)


def random_normal(loc=0.0, scale=1.0, size=None, rgen=RANDOMGENERATOR):
    """
    Function to return numbers from a normal distribution.
    This function will actually just call np.random.normal
    the reason for including it here as a function is that we
    might want to use the random number generator with a specified
    seed.


    Parameters
    ----------
    loc : float, optional
        Mean of the distribution.
    scale : float, optional
        Standard deviation of the distribution.
    size : int or tuple of ints, optional
        Output shape. Default is None, in which case a single value is
        returned.
    rgen : object, optional
        The random number generator

    Returns
    -------
    out : float or numpy.array of floats
        The random numbers drawn.
    """
    return rgen.normal(loc=loc, scale=scale, size=size)
