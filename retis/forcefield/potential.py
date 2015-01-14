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
        self.params = None # variable to hold parameters

    def set_parameters(self, **params):
        """ 
        Sets the paramters of the potential, i.e. sets
        self.params to the given parameters. 
    
        Parameters
        ----------
        self : 
        **params : dict, optional. Parameters for
            the potential

        Returns
        -------
        N/A, but updates self.params 
        """
        for par in params:
            self.params[par] = params[par]
 
    def params_to_attr(self):
        """
        Converts from the parameter dictionary to
        attributes of the object.
        
        Parameters
        ----------
        self : 

        Returns
        -------
        N/A, but updates self.params 

        Note
        ----
        Consider removing this method - objects that want to
        set attributes like this can do it them selves; here we
        uncritically just adds all parameters as attributes.
        Keeping it for now to make pylint shut up about the number
        of methods.
        """
        for par in self.params:
            setattr(self, par, self.params[par])

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

