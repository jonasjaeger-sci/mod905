#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file contains one-dimensional potentials
"""

class DoubleWell(object):
    """Double well potential
    The parameters are: 
        a = 
        b = 
        c =
    """
    def __init__(self, a=1, b=1, c=0.0):
        self.dim = 1 # dimensionality, can be used for checking consistency
        self.a, self.b, self.c = a, b, c

    def potential(self, r):
        """One-dimensional double well potential"""
        return self.a*r**4-self.b*(r-self.c)**2

    def force(self, r):
        """Force for the one-dimensional double well potential"""
        return -4.0*self.a*r**3+2.0*self.b*(r-self.c)

