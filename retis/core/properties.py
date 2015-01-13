#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file contains a class for a generic property.
"""
import numpy as np

__all__ = ["Property"]

class Property(object):
    """Generic property object"""
    def __init__(self, desc=""):
        """ 
        Initialize the property. 

        Parameters
        ----------
        self : 
        desc : optional text description of the object
        
        Returns
        -------
        N/A
        """
        self.desc = desc
        self.n = 0 # number of times it has been evaluated
        self.mean = 0.0 # to store average
        self.M2 = 0.0 # helper for variance
        self.variance = 0.0
        self.val = [] # list to store *all* values

    def add(self, v):
        """ 
        Adds a element/value to the property
        and updated the mean and variance.

        Parameters
        ----------
        self : 
        v : the value to add
        
        Returns
        -------
        None, but updated the mean and variance
        """
        self.n += 1
        self.val.append(v)
        self.update_mean_and_variance()

    def update_mean_and_variance(self):
        """ 
        Calculates the mean and variance on the fly.
        Source:
        http://en.wikipedia.org/wiki/Algorithms_for_calculating_variance

        Parameters
        ----------
        self : 

        Returns
        -------
        None, however, the mean and variance is updated.

        Note
        ----
        Consider if this should be moved/deleted and just
        replaced with a function from the analysis method.
        """
        x = self.val[-1] # most recent value
        delta = x-self.mean
        self.mean += delta/float(self.n)
        self.M2 += delta*(x-self.mean)
        if (self.n<2):
            self.variance = float('inf')
        else:
            self.variance = self.M2/float(self.n-1)

    def dump_to_file(self, filename):
        """ 
        Dumpts the contents in self.val to a file.

        Parameters
        ----------
        self : 
        filename : name/path of file to write.

        Returns
        -------
        N/A

        Note
        ----
        Consider if this should be moved/deleted and just
        replaced with a function from a more general input-output
        module
        """
        np.savetxt(filename, self.val)

    def __str__(self):
        return self.desc

