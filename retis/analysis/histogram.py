# -*- coding: utf-8 -*-
"""Histogram methods for data analysis."""

import numpy as np

__all__ = ['histogram', 'match_all_histograms', 'histogram_and_avg']


def histogram(data, bins=10, limits=(-1, 1), density=False,
              weights=None):
    """
    Create a histogram of the given `data`.

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
                              range=limits, density=density, weights=weights)
    bin_mid = 0.5 * (bins[1:] + bins[:-1])
    return hist, bins, bin_mid


def histogram_and_avg(data, bins, density=True):
    """
    Create histogram an return bin, midpoints and simples statistics.

    The simple statistics includes the mean value and the standard deviation.
    The return structure is useful for plotting routines.

    Parameters
    ----------
    data : 1D numpy.array
        This is the data to create the histogram from.
    bins : int
        The number of bins to use for the histogram.
    density : boolean, optional
        If `density` is true, the histogram will be normalized.

    Returns
    -------
    out[0] : numpy.array
        The histogram (frequency) values.
    out[1] : numpy.array
        The mid points for the bins.
    out[2] : tuple of floats
        These are some simple statistics, out[2][0] is the average
        out[2][1] is the standard deviation.

    See Also
    --------
    histogram
    """
    hist, _, bin_mid = histogram(data, bins=bins,
                                 limits=(data.min(), data.max()),
                                 density=density)
    return (hist, bin_mid, (data.mean(), data.std()))


def _match_histograms(histo1, histo2, bin_x, overlap):
    """
    Function to match two histograms.

    The matching is done so that the integral of the overlapping regions of
    the two histograms are equal.

    Parameters
    ----------
    histo1 : numpy.array
        The first histogram.
    histo2 : numpy.arraym
        The second histogram, this is the histogram that will be scaled.
    bin_x : numpy.array
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
    for histi, histj, bin_xi in zip(histo1, histo2, bin_x):
        if overlap[0] <= bin_xi < overlap[1]:
            int1 += histi
            int2 += histj
    if int2 == 0.0:
        scale_factor = 1.0
    else:
        scale_factor = int1 / int2
    return histo2 * scale_factor, scale_factor


def match_all_histograms(histograms, umbrellas):
    """
    Function to mach several histograms from an umbrella sampling.

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
    bin_x = histograms[0][2]
    for i in range(len(umbrellas) - 1):
        limits = (umbrellas[i+1][0], umbrellas[i][1])
        matched, scale = _match_histograms(histograms_s[-1],
                                           histograms[i+1][0], bin_x, limits)
        histograms_s.append(matched)
        scale_factor.append(scale)
    # merge histograms:
    matched_count = []
    for i, bin_xi in enumerate(bin_x):
        hist = 0.0  # histogram value at bin_xi
        norm = 0.0
        for k, umb in enumerate(umbrellas):
            if umb[0] <= bin_xi < umb[1]:
                hist += histograms_s[k][i]
                norm += 1.0
        if norm > 0.0:
            hist /= norm
        matched_count.append(hist)
    return histograms_s, scale_factor, np.array(matched_count)
