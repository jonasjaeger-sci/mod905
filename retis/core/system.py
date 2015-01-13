#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
system.py
"""
import constants
import numpy as np

__all__ = ['System']

class System(object):
    """
    This class defines a system
    """
    def __init__(self, N=0, dim=0, r=None, v=None, f=None, p=[],
                 forcefield=[], periodic=False, box=[], temperature=None,
                 units=None):
        self.N = N # number of particles
        self.dim = dim # dimensionality
        self.r = r # positions of particles
        self.v = v # velocities of particles
        self.f = f # forces on particles
        self.p = p # particle types/id's 
        self.forcefield = forcefield
        # Note for future: might consider making a
        # particle object, but its very convenient
        # for numpy to have d*N arrays with r, v, f, ... 
        # rather than a list of particles to loop over
        self.periodic = periodic # use periodic boundaries?
        self.box = box # simulation box
        self.v_pot = 0.0 # stores the potential energy of the system
        self.temperature = temperature
        if not self.temperature:
            self.beta = None
        else:
            self.beta = 1.0/(self.temperature*constants._kB[units])

    def add_particle(self, r=None, v=None, f=None, name=None):
        if not r: r = np.zeros(self.dim)
        if not v: v = np.zeros(self.dim)
        if not f: f = np.zeros(self.dim)
        if not name: name = '?'
        self.p.append(name)
        if len(self.p)==1:
            self.r = r
            self.v = v
            self.f = f
        else:
            self.r = np.vstack([self.r, r])
            self.v = np.vstack([self.v, v])
            self.f = np.vstack([self.f, f])
        self.N += 1

    def force(self):
        self.f = self.evaluate_force()

    def potential(self):
        self.v_pot = self.evaluate_potential()

    def evaluate_force(self, r=None):
        """
        This function evaluates the force on the particles
        in the system.
        If r is given, these positions are used rather than
        self.r to evaluate the force. This might be beneficial
        for trial moves etc. in MC routines
        Note: May be beneficial to call forcefield(system) later
        """
        if r is None:
            return self.forcefield.evaluate_force(self.r)
        else:
            return self.forcefield.evaluate_force(r)

    def evaluate_potential(self, r=None):
        """
        This function evaluate the potential energy of the system
        If r is given, these positions are used rather than
        self.r to evaluate the potential. This might be beneficial
        for trial moves etc. in MC routines
        """   
        if r is None:
            return self.forcefield.evaluate_potential(self.r)
        else:
            return self.forcefield.evaluate_potential(r)
