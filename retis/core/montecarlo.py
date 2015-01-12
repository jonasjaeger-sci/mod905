#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module for Monte Carlo Algorithms
"""

import numpy as np
from numpy.random import RandomState
import warnings # for debugging: to catch overflow in numpy

warnings.simplefilter("error", RuntimeWarning) # just to catch warnings
rnd = RandomState() # this will be the random number generator

def seed_random_generator(seed=1, rnd=rnd):
    """ Helper function to seed the random number generator

    Keyword arguments:
    seed: the seed value, integer (default is 1)
    rnd: the random number generator (default is the global one)
    """
    rnd.seed(seed)

def accept_reject(system, r, rnd=rnd):
    """Routine for accepting or rejecting a MC move

    Arguments:
    system: the system we are investigating
    r: the trial positions

    Keyword arguments:
    rnd: the random number generator (default is the global one)

    Returns:
    r: the accepted positions (can be equal to the previous positions)
    v_pot: potential energy corresponding to positions r
    v_trial: potential energy of trial positions
    status: True if move is acceped, False otherwise
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
    """ Monte Carlo routine. 
    Select one particle randomly and displaces it's position randomly.
    Returns the new positions and their corresponding potential energy,
    it the move is accepted. Otherwise, it returns the old positions
    and potential energy.
    The function accept_reject is used to accept/reject the move.

    Arguments:
    system: the system to operate on
    
    Keyword arguments:
    maxdx: the maximum displacement (default is 0.1)
    rnd: the random number generator (default is the global one)

    Returns:
    r: the accepted positions (can be equal to the previous positions)
    v_pot: potential energy corresponding to positions r
    v_trial: potential energy of trial positions
    status: True if move is acceped, False otherwise
    
    """
    idx = rnd.random_integers(0,system.n-1) # select particle randomly
    trial = np.copy(system.r) # copy positions
    trial[idx] += 2.0*maxdx*(rnd.rand(system.dim)-0.5) # displace selected
    r, v_pot, v_trial, status = accept_reject(system, trial)
    return r, v_pot, v_trial, status

