#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file contains one-dimensional potentials
"""

import numpy as np
from potential import PotentialFunction

class DoubleWell(PotentialFunction):
    """One dimensional double well potential
    The parameters are: 
        a = 
        b = 
        c =
    """
    def __init__(self, a=1, b=1, c=0.0, desc='1D double well potential'):
        super(DoubleWell, self).__init__(dim=1, desc=desc)
        self.a, self.b, self.c = a, b, c

    def potential(self, r):
        """One-dimensional double well potential"""
        return self.a*r**4-self.b*(r-self.c)**2

    def force(self, r):
        """Force for the one-dimensional double well potential"""
        return -4.0*self.a*r**3+2.0*self.b*(r-self.c)


class RectangularWell(PotentialFunction):
    """One dimensional rectangular well"""
    def __init__(self, left=0.0, right=1.0, largenumber=1e100,
                 desc="1D Rectangular well potential"):
        super(RectangularWell, self).__init__(dim=1, desc=desc)
        self.largenumber = largenumber
        self.left, self.right = left, right
    def potential(self, r):
        if self.left<r<self.right:
            return 0.0
        else:
            return self.largenumber
    def force(self, r):
        pass
        
    
