# -*- coding: utf-8 -*-
"""
This file contains a class for a generic potential function
This class is subclassed in all potential functions
"""

__all__ = []

class PotentialFunction(object):
    """
    PotentialFunction(object)

    Generic class for potential functions.

    Attributes
    ----------
    desc : string, short description of the potential.
    dim : int, represents the spatial dimensionality of the potential
    params : dict, contains the parameters. This is a variable included
        for convenience in case other methods/classes wants to know all
        the parameters of the potential.
    """
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
        self.params = {}

    def get_parameters(self):
        """ 
        Method that returns information about the parameters for 
        the potential.
        
        Parameters
        ----------
        N/A
        
        Returns
        -------
        A string with information about the parameters
        """
        allinfo = []
        strinfo = '{}: {}, Value: {}'
        for param in sorted(self.params):
            value = self.params[param]['value']
            desc = self.params[param]['desc']
            allinfo.append(strinfo.format(param, desc, value))
        return 'Parameters:\n'+'\n'.join(allinfo)

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
