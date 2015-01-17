# -*- coding: utf-8 -*-
"""
This file contains a class for a generic potential function
This class is subclassed in all potential functions
"""

__all__ = []

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
