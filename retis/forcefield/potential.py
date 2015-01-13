#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file contains a class for a generic potential function
This class is subclassed in all potential functions
"""

class PotentialFunction(object):
    """Generic potential function"""
    def __init__(self, dim=1, desc=""):
        """ 
        Initiates the potential
    
        Parameters
        ----------
        self : 
        dim : int, optional. Represents the dimensionality.
        desc : string, optional. Description of the force field.

        Returns
        -------
        N/A 
        """
        self.dim = dim # dimensionality
        self.desc = desc
    def force(self, *args):
        """ 
        Function to evaluate the force.
    
        Parameters
        ----------
        self : 
        *args : Not defined here, it's defined in the derived potentials.

        Returns
        -------
        N/A 
        """
        pass
    def potential(self, *args):
        """ 
        Function to evaluate the force.
    
        Parameters
        ----------
        self : 
        *args : Not defined here, it's defined in the derived potentials.

        Returns
        -------
        N/A 
        """
        pass
    def __str__(self):
        """
        Return the string description of the potential. 
    
        Parameters
        ----------
        self : 

        Returns
        -------
        self.desc
        """
        return self.desc

