#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module for Monte Carlo Algorithms
"""

import numpy as np
from numpy.random import RandomState

rnd = RandomState() # this will be the random number generator

def seed_random_generator(seed=1, rnd=rnd):
    rnd.seed(seed)

def accept_reject(system, trial, rnd=rnd):
    """
    Routine for accepting or rejecting a MC move
    """
    vtrial = system.evaluate_potential(trial) # potential energy of trial pos
    deltae = vtrial-system.epot
    pacc = np.exp(-system.beta*deltae)
    throwdice = rnd.rand()
    status = False
    if throwdice < pacc:
        pos, vpot, status = trial, vtrial, True
    return pos, vpot, vtrial, status

def max_displace_step(system, maxdx=0.01, rnd=rnd):
    """
    MC routine. Displace positions randomly. Accept or reject.
    Returns new positions and their corresponding potential energy.
    If move is rejectec, return old positions and potential energy.
    """
    idx = rnd.random_integers(0,system.n-1) # select particle
    trial = np.copy(system.r)
    trial[idx] += 2.0*maxdx*(rnd.rand(system.dim)-0.5) # displace
    r, epot, etrial, status = accept_reject(system, trial)
    return status

