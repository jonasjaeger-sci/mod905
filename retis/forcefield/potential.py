#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file contains a class for a generic potential function
This class is subclassed in all potential functions
"""

class PotentialFunction(object):
    """Generic potential function"""
    def __init__(self, dim=1, desc=""):
        self.dim = dim # dimensionality
        self.desc = desc
    def force(self, *args):
        pass
    def potential(self, *args):
        pass
    def __str__(self):
        return self.desc

