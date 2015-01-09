#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file contains a class for a generic force field
"""

class ForceField(object):
    """Generic force field object"""

    def __init__(self, dim=1, desc="", potential=None):
        self.dim = dim # dimensionality
        self.desc = desc
        self.potential = potential

    def evaluate_force(self, r):
        f = None
        for ff in self.potential:
            if f is None:
                f = ff.force(r)
            else:
                f += ff.force(r)
        return f

    def evaluate_potential(self, r):
        pot = None
        for ff in self.potential:
            if pot is None:
                pot = ff.potential(r)
            else:
                pot += ff.potential(r)
        return pot


    def __str__(self):
        s = '\n *'.join([ff.desc for ff in self.potential])
        return 'Force field: {}\nPotential functions: \n *{}'.format(self.desc,s)

