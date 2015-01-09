#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
system.py
"""
import constants

class System(object):
    """
    This class defines a system
    """
    def __init__(self, N=None, dim=None, r=None, v=None, f=None, p=None,
                 forcefield=None, periodic=False, box=None, temperature=None,
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
        self.epot = 0.0 # stores the potential energy of the system
        self.temperature = temperature
        self.beta = 1.0/(self.temperature*constants._kB[units])

    def force(self):
        self.f = self.evaluate_force()

    def potential(self):
        self.epot = self.evaluate_potential()

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
