# -*- coding: utf-8 -*-
"""
This file contains a class for a generic potential function
This class is subclassed in all potential functions
"""

import warnings


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

    def __init__(self, dim=1, desc=''):
        """ 
        Initiates the potential
    
        Parameters
        ----------
        dim : int, optional. Represents the dimensionality.
        desc : string, optional. Description of the force field.

        Returns
        -------
        N/A 
        """
        self.dim = dim 
        self.desc = desc
        self.params = {}

    def check_parameters(self):
        """
        This function is check on the consistency of
        the parameters. This can be implemented for the
        different potential functions.
        
        Returns
        -------
        True if the check(s) pass
        """
        if len(self.params)==0:
            warnings.warn('No parameters are set for the potential')
            return False
        return True

    def update_parameters(self, params):
        """
        Updates the parameters for the potential. In this generic function,
        it will just try to set attributes for the object. 
    
        Parameters
        ----------
        params : dictionary with the parameters to update

        Note
        ----
        A parameter in params which is not a attribute of the object will be
        ignored.
        """
        if type(params) != type({}):
            msg = 'Did not understand the parameters...'
            warnings.warn(msg)
            return False
        for param in params:
            if hasattr(self, param):
                value = params[param]
                setattr(self, param, value)
                self.params[param]['value'] = value
            else:
                msg = 'Ignoring unknown parameter {}'.format(param)
                warnings.warn(msg)
        return self.check_parameters()

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

    def parameters_to_dict(self):
        """
        This method is intended to generate a dictionary
        containing the parameters for the potential
        
        Returns
        -------
        N/A, but is should modify self.params
        """
        self.params = {}

    def __str__(self):
        """
        Return the string description of the potential. 
    
        Returns
        -------
        self.desc
        """
        return self.desc
