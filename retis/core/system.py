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
    This class defines a generic system for simulation.
    """
    def __init__(self, N=0, dim=0, r=None, v=None, f=None, p=[],
                 forcefield=[], periodic=False, box=[], temperature=None,
                 units=None):
        """ 
        Initialization of the system.
    
        Parameters
        ----------
        self : 
        N : int, optional. Number of particles.
        dim : int optional. The dimensionality.
        r : numpy.array, optional. The positions of the particles.
        v : numpy.array, optional. The velocities of the particles.
        f : numpy.array, optional. The forces on the particles.
        p : list, optional. The id of the particles in a list.
        forcefield : list, optional. The potential functions that consitute the 
            force field. 
        periodic : boolean, optional. True = the system has periodic boundaries. 
        box : list, optional. System boundaries in the self.dim dimensions.
        temperature : float, optional. The temperature of the system.

        Returns
        -------
        N/A, but sets derived variables:
        self.beta : float, inverse of (kB*T).
        """
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
        """ 
        Adds a particle to the system.
    
        Parameters
        ----------
        self : 
        r : numpy.array, optional. The positions of the particle.
        v : numpy.array, optional. The velocities of the particle.
        f : numpy.array, optional. The forces on the particle.
        name : string, optional. The id of the particle.

        Returns
        -------
        N/A, but increments self.N and updates
        self.r, self.v, self.f and self.p

        Note
        ----
        If no arguments are given a particle with id='?' will be
        created.
        """
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

    def evaluate_force(self, r=None):
        """ 
        Evaluate the forces
    
        Parameters
        ----------
        self : 
        r : numpy.array, optional. The positions of the particle.
            If r is not given, self.r will be used.

        Returns
        -------
        The forces as a numpy.array
        """
        if r is None:
            return self.forcefield.evaluate_force(self.r)
        else:
            return self.forcefield.evaluate_force(r)

    def force(self):
        """ 
        Updates self.f by calling self.evaluate_force()
    
        Parameters
        ----------
        self : 
        
        Returns
        -------
        N/A, but updates self.f
        """
        self.f = self.evaluate_force()

    def evaluate_potential(self, r=None):
        """
        Evaluate the potential energy
    
        Parameters
        ----------
        self : 
        r : numpy.array, optional. The positions of the particle.
            If r is not given, self.r will be used.
        
        Returns
        -------
        The scalar potential energy correspoding to the given r.
        """   
        if r is None:
            return self.forcefield.evaluate_potential(self.r)
        else:
            return self.forcefield.evaluate_potential(r)

    def potential(self):
        """ 
        Updates self.v_pot by calling self.evaluate_potential()
    
        Parameters
        ----------
        self : 
        
        Returns
        -------
        N/A, but updates self.f
        """
        self.v_pot = self.evaluate_potential()
