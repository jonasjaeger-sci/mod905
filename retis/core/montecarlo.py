#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module for Monte Carlo Algorithms
"""
import numpy as np
from numpy.random import RandomState
import warnings # for debugging: to catch overflow in numpy

__all__ = ["seed_random_generator", "accept_reject", "max_displace_step"]

warnings.simplefilter("error", RuntimeWarning) # just to catch warnings
rnd = RandomState() # this will be the random number generator


def seed_random_generator(seed=1, rnd=rnd):
    """ 
    Helper function to seed the random number generator

    Parameters
    ----------
    seed : int, optional
        seed for the random number generator rnd
    rnd : random number generator

    Returns
    -------
    None, however ``rnd`` is seeded with the given seed.
    """
    rnd.seed(seed)

def accept_reject(system, r, rnd=rnd):
    """
    Routine for accepting or rejecting a MC move

    Parameters
    ----------
    system : the system object we are investigating
    r : the trial positions, assumed to be a numpy array
    rnd : random number generator, optional
        (default is the global one for this module)

    Returns
    -------
    r : the accepted positions (can be equal to the previous positions).
    v_pot : potential energy corresponding to positions r
    v_trial : potential energy of trial positions
    status : True if move is acceped, False otherwise

    Notes
    -----
    A overflow is possible when using numpy.exp() here. 
    This can for instance happen in a umbrella simulation
    where the bias potential is infinite or very large. 
    The warnings module is here used to catch numpy warnings for
    this and to deal with it.
    """
    v_trial = system.evaluate_potential(r) 
    dE = v_trial - system.v_pot
    try:
        pacc = np.exp(-system.beta * dE)
    except RuntimeWarning, e:
        if 'overflow encountered in exp' in e: 
            pacc = 42.0 # works, rnd.rand() is < 1 anyway
            # if the error is something else, we do not set pacc
            # and make the program crash.
    if rnd.rand() < pacc:
        return r, v_trial, v_trial, True
    else:
        return system.r, system.v_pot, v_trial, False

def max_displace_step(system, maxdx=0.1, rnd=rnd):
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
    rnd : the random number generator (default is the global one)

    Returns
    -------
    This function just returns the outcome if applying the
    function accept_reject to the system and trial position.
    """
    idx = rnd.random_integers(0,system.n-1) # select particle randomly
    trial = np.copy(system.r) # copy positions
    trial[idx] += 2.0*maxdx*(rnd.rand(system.dim)-0.5) # displace selected
    return accept_reject(system, trial)
    #r, v_pot, v_trial, status = accept_reject(system, trial)
    #return r, v_pot, v_trial, status

