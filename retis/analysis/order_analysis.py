# -*- coding: utf-8 -*-
"""
This file contains methods for analysis of order parameter
"""
from __future__ import absolute_import
from .analysis import analyse_data


__all__ = ['analyse_orderp']


def analyse_orderp(orderdata, settings):
    """
    This method will run the analysis on several order parameters and
    collect the results into a structure which is convenient for plotting.

    Parameters
    ----------
    orderdata : list of numpy.arrays
        The contents of this list is the data read from the order
        parameter file.
    settings : dict
        This dictionary contains settings for the analysis.

    Returns
    -------
    results : numpy.array
        For each order parameter `key`, `results[key]` contains the result
        from the analysis.

    See Also
    --------
    analyse_data in .analysis.py

    Note
    ----
    We here (and in the subsequent plotting) make certain assumptions about
    the structure, i.e. the positions are assumed to have a specific meaning.
    (column zero is the time, column one the order parameter etc...)
    """
    results = []
    for i, data in enumerate(orderdata):
        if i == 0:  # first column is just the time, skip it
            pass
        else:
            results.append(analyse_data(data, settings))
    return results
