#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file contains a class for a generic potential function
"""

class PotentialFunction(object):
    """Generic potential function"""
    def __init__(self, dim=1, desc=""):
        self.dim = dim # dimensionality
        self.desc = desc
        self.forcefield = []
    def force(self):
        pass
    def potential(self):
        pass
    def __str__(self):
        return self.desc

