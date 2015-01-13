#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file contains one-dimensional potentials
"""

import numpy as np
from potential import PotentialFunction

class DoubleWell(PotentialFunction):
    """One dimensional double well potential"""
    def __init__(self, a=1.0, b=1.0, c=0.0, desc='1D double well potential'):
        """ 
        Initiates the one dimensional double well potential.
        
        Parameters
        ---------- 
        self : 
        a : float, optional. 
        b : float, optional. 
        c : float, optional. 
        desc : string, optional. Description of the force field.
        
        Returns
        -------
        N/A
        """
        super(DoubleWell, self).__init__(dim=1, desc=desc)
        self.a, self.b, self.c = a, b, c

    def potential(self, r):
        """ 
        Evaluate the potential for the one-dimensional double well potential.
        
        Parameters
        ---------- 
        self : 
        r : the position.
        
        Returns
        -------
        The potential energy
        """
        v_pot = self.a*r**4-self.b*(r-self.c)**2
        return v_pot.sum()

    def force(self, r):
        """ 
        Evaluate the force for the one-dimensional double well potential.
        
        Parameters
        ---------- 
        self : 
        r : the position.
        
        Returns
        -------
        N/A 
        """
        return -4.0*self.a*r**3+2.0*self.b*(r-self.c)


class RectangularWell(PotentialFunction):
    """One dimensional rectangular well"""
    def __init__(self, left=0.0, right=1.0, largenumber=1e10,
                 desc="1D Rectangular well potential"):
        """ 
        Initiates a one-dimensional rectangular well.
    
        Parameters
        ----------
        self : 
        left : float, optional. The left boundary of the potential.
        right : float, optional. The right boundary of the potential.
        largenumber : float, optional. The value of the potential outside 
            (left, right).
        desc : string, optional. Description of the force field.

        Returns
        -------
        N/A 
        """
        super(RectangularWell, self).__init__(dim=1, desc=desc)
        self.largenumber = largenumber
        #self.largenumber = float('inf') # possible to use this, NOTE FOR LATER
        self.left, self.right = left, right
    def update_left_right(self, left, right):
        """ 
        Updates the boundaries.
        
        Parameters
        ---------- 
        self : 
        left : float. The left boundary of the potential.
        right : float. The right boundary of the potential.
        
        Returns
        -------
        N/A 
        """
        self.left = left
        self.right = right
    def potential(self, r):
        """ 
        Evaluate the potential. 
        
        Parameters
        ---------- 
        self : 
        r : the position.
        
        Returns
        -------
        The potential energy
        """
        v_pot = np.where(np.logical_and(r > self.left, r < self.right), 
                        0.0, self.largenumber)
        return v_pot.sum()
    def force(self, r):
        """ 
        Evaluate the force. 
        
        Parameters
        ---------- 
        self : 
        r : the position.
        
        Returns
        -------
        N/A 
        """
        pass
    
