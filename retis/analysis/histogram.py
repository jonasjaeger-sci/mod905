#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file contains methods for data analysis
"""

import numpy as np

def histogram(data, bins=10, limits=(-1,1)):
    """Creates a histogram, using the data stored in 
    data
    """
    hist, bins = np.histogram(data, bins=bins,
                              range=limits, density=False)
    bin_mid = 0.5*(bins[1:]+bins[:-1])
    return hist, bins, bin_mid

def match_histograms(histo1, histo2, xval, rangex):
    int1, int2 = 0.0, 0.0
    for hi, hj, xi in zip(histo1, histo2, xval):
        if rangex[0] <= xi < rangex[1]:
            int1 += hi
            int2 += hj
    if int2 == 0.0:
        scale_factor = 1.0
    else:
        scale_factor = int1/int2
    return histo2*scale_factor, scale_factor
