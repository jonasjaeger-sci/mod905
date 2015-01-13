#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file contains a class for a generic force field
"""

class ForceField(object):
    """Generic force field object"""

    def __init__(self, dim=1, desc="", potential=None):
        """ 
        Initiates the force field object.
    
        Parameters
        ----------
        self : 
        dim : int, optional. Represents the dimensionality.
        desc : string, optional. Description of the force field.
        potential : list, optional. Potential functions that the force
        filed is built up from.

        Returns
        -------
        N/A 
        """
        self.dim = dim # dimensionality
        self.desc = desc
        self.potential = potential

    def evaluate_force(self, r):
        """ 
        Evaluate the force on the particles.
    
        Parameters
        ----------
        self : 
        r : np.array, the position of the particles.

        Returns
        -------
        f : np.array with the forces.
        """
        f = None
        for ff in self.potential:
            if f is None:
                f = ff.force(r)
            else:
                f += ff.force(r)
        return f

    def evaluate_potential(self, r):
        """ 
        Evaluate the potential energy.
    
        Parameters
        ----------
        self : 
        r : np.array, the position of the particles.

        Returns
        -------
        pot : float equal to the potential energy.
        """
        pot = None
        for ff in self.potential:
            if pot is None:
                pot = ff.potential(r)
            else:
                pot += ff.potential(r)
        return pot

    def __str__(self):
        """ 
        A string representation of the force field. 
        It it returns the string descriptions of the potential functions.
    
        Parameters
        ----------
        self : 

        Returns
        -------
        String with description of force field.
        """
        s = '\n *'.join([ff.desc for ff in self.potential])
        s = 'Force field: {}\nPotential functions: \n *{}'.format(self.desc, s)
        return s

