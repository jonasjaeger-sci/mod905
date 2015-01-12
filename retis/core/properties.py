#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file contains a class for a generic property that
is obtained as a function of the system.
"""
import numpy as np

class Property(object):
    """Generic property object"""
    def __init__(self, desc=""):
        self.desc = desc
        self.n = 0 # number of times it has been evaluated
        self.mean = 0.0 # to store average
        self.M2 = 0.0 # helper for variance
        self.variance = 0.0
        self.val = [] # list to store *all* values

    def add(self, v):
        self.n += 1
        self.val.append(v)
        self.update_mean_and_variance()

    def update_mean_and_variance(self):
        """Calculates the mean and variance on the fly.
        see: 
        http://en.wikipedia.org/wiki/Algorithms_for_calculating_variance
        """
        """ Consider if this should be moved/deleted
        and just replaced with a function from the analysis methods.
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
        np.savetxt(filename, self.val)

    def histogram(self, bins=10, limits=(-1,1)):
        """Creates a histogram, using the data stored in 
        self.val
        """
        """ Consider if this should be moved/deleted
        and just replaced with a function from the analysis methods.
        """
        hist, bins = np.histogram(self.val, bins=bins,
                                  range=limits, density=False)
        self.hist = hist
        self.bins = bins
        self.bin_mid = 0.5*(bins[1:]+bins[:-1])

    def __str__(self):
        return self.desc

