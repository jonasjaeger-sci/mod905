# -*- coding: utf-8 -*-
"""
Module for Monte Carlo Algorithms
"""
import numpy as np
from numpy.random import RandomState

__all__ = ["seed_random_generator", "accept_reject", "max_displace_step"]

random_generator = RandomState() # this will be the random number generator


def seed_random_generator(seed=1, rgen=random_generator):
    """ 
    Helper function to seed the random number generator

    Parameters
    ----------
    seed : int, optional
        seed for the random number generator
    rgen : random number generator

    Returns
    -------
    None, however ``rgen`` is seeded with the given seed.
    """
    rgen.seed(seed)

def accept_reject(system, trial, rgen=random_generator):
    """
    Routine for accepting or rejecting a MC move

    Parameters
    ----------
    system : the system object we are investigating
    trial : the trial positions, assumed to be a numpy array
    rgen : random number generator, optional
        (default is the global one for this module)

    Returns
    -------
    the accepted positions (trial or the original system.particles['r']):
    v_pot : potential energy corresponding to positions r
    v_trial : potential energy of trial positions
    status : True if move is acceped, False otherwise

    Notes
    -----
    A overflow is possible when using numpy.exp() here. 
    This can for instance happen in a umbrella simulation
    where the bias potential is infinite or very large. 
    Right now, this is just ignored.
    """
    v_trial = system.evaluate_potential(r=trial) 
    dE = v_trial - system.v_pot
    pacc = np.exp(-system.beta * dE)
    if rgen.rand() < pacc:
        return trial, v_trial, v_trial, True
    else:
        return system.particles['r'], system.v_pot, v_trial, False

def max_displace_step(system, maxdx=0.1, rgen=random_generator):
    """ 
    Monte Carlo routine for diplacing particles.

    It selects and displaces one particle randomly.
    If the move is accepted, the new positions and energy are
    return. Otherwise, the move is rejected and the old positions
    and potential energy is returned.
    The function accept_reject is used to accept/reject the move.

    Parameters
    ----------
    system : the system object to operate on
    maxdx : the maximum displacement (default is 0.1)
    rgen : the random number generator (default is the global one)

    Returns
    -------
    This function just returns the outcome if applying the
    function accept_reject to the system and trial position.
    """
    idx = rgen.random_integers(0, system.npart-1) # select particle randomly
    trial = np.copy(system.particles['r']) # copy positions
    trial[idx] += 2.0 * maxdx * (rgen.rand(system.dim) - 0.5) # displace
    return accept_reject(system, trial)
