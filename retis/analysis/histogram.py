# -*- coding: utf-8 -*-
"""
This file contains methods for data analysis
"""

import numpy as np

__all__ = ['histogram', 'match_all_histograms']


def histogram(data, bins=10, limits=(-1, 1), density=False):
    """
    Function to create a histogram of the data stored
    in data.

    Parameters
    ----------
    data : numpy.array
        The data for making the histogram.
    bins : int,
        The number of bins to divide the data into.
    limits : touple/list
        The max/min values to consider.
    density : boolean
        If True the histogram will be normalized.

    Returns
    -------
    hist : numpy.array
        The binned counts.
    bins : numpy.array
        The edges of the bins.
    bin_mid : numpy.array
        The midpoint of the bins.
    """
    hist, bins = np.histogram(data, bins=bins,
                              range=limits, density=density)
    bin_mid = 0.5 * (bins[1:] + bins[:-1])
    return hist, bins, bin_mid


def _match_histograms(histo1, histo2, x, overlap):
    """
    Function to mach two histograms. The matching is done
    so that the integral of the overlapping regions of
    the two histograms are equal.

    Parameters
    ----------
    histo1 : numpy.array
        The first histogram.
    histo2 : numpy.arraym
        The second histogram, this is the histogram that will be scaled.
    x : numpy.array
        This is the bin mid-points of the histograms. Note that we
        assume here that histo1 and histo2 are obtained using the same
        number of bins and limits.
    overlap : list/touple/numpy.array
        This is the overlapping region.

    Returns
    -------
    out[0] : numpy.array
        A scaled version of histo2.
    out[1] : float
        The calculated scale factor.
    """
    int1, int2 = 0.0, 0.0
    for hi, hj, xi in zip(histo1, histo2, x):
        if overlap[0] <= xi < overlap[1]:
            int1 += hi
            int2 += hj
    if int2 == 0.0:
        scale_factor = 1.0
    else:
        scale_factor = int1 / int2
    return histo2 * scale_factor, scale_factor


def match_all_histograms(histograms, umbrellas):
    """
    Function to mach several histograms from a umbrella
    sampling.

    Parameters
    ----------
    histograms : list of numpy.arrays
        The histograms to match.
    umbrellas : list of lists
        The umbrellas used in the computation.

    Returns
    -------
    histograms_s : list of numpy.arrays
        The scaled histograms.
    scale_factor : list of floats.
        The scale factors.
    matched_count : numpy.array
        Count for overall matched histogram - a "averaged" histogram.
    """
    histograms_s, scale_factor = [histograms[0][0]], [1.0]
    x = histograms[0][2]
    for i in range(len(umbrellas) - 1):
        limits = (umbrellas[i+1][0], umbrellas[i][1])
        matched, s = _match_histograms(histograms_s[-1],
                                       histograms[i+1][0], x, limits)
        histograms_s.append(matched)
        scale_factor.append(s)
    # merge histograms:
    matched_count = []
    for i, xi in enumerate(x):
        h = 0.0
        n = 0.0
        for k, u in enumerate(umbrellas):
            if u[0] <= xi < u[1]:
                h += histograms_s[k][i]
                n += 1.0
        if n > 0.0:
            h /= n
        matched_count.append(h)
    return histograms_s, scale_factor, np.array(matched_count)
