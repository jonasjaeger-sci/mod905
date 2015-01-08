#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
system.py
"""

class System(object):
    """
    This class defines a system
    """
    def __init__(self, N=None, dim=None, r=None, v=None, f=None, p=None,
                 forcefield=None):
        self.N = N # number of particles
        self.dim = dim
        self.r = r # positions of particles
        self.v = v # velocities of particles
        self.f = f # forces on partiles
        self.p = p # particle types/id's 
        self.forcefield = forcefield
        # Note for future: might consider making a
        # particle object, but its very convenient
        # for numpy to have d*N arrays with r, v, f, ... 
        # rather than a list of particles to loop over
    def force(self):
        """
        This function evaluates the force on the particles
        in the system.
        Note: May be beneficial to call forcefield(system) later
        """
        self.f = self.forcefield.force(self.r)
