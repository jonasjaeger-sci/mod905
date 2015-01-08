#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module for Monte Carlo algorithms
"""

from random import randrange # can perhaps be replaced by numpy
import numpy as np

def accept_reject(system, trial):
    """
    Routine for accepting or rejecting a MC move
    """
    vtrial = system.evaluate_potential(trial) # potential energy of trial pos
    deltae = vtrial-system.epot
    pacc = np.exp(-system.beta*deltae)
    throwdice = np.random.random()
    status = False
    if throwdice < pacc:
        pos, vpot, status = trial, vtrial, True
    return pos, vpot, vtrial, status

def max_displace_step(system, maxdx=0.01):
    """
    MC routine. Displace positions randomly. Accept or reject.
    Returns new positions and their corresponding potential energy.
    If move is rejectec, return old positions and potential energy.
    """
    idx = randrange(0,system.n) # select particle
    trial = np.copy(system.r)
    trial[idx] += 2.0*maxdx*(np.random.random(system.dim)-0.5) # displace
    r, epot, etrial, status = accept_reject(system, trial)
    return status
