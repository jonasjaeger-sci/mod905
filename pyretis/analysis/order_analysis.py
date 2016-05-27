# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""Module defining functions for analysis of order parameters.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

analyse_orderp
    Run a simple order parameter analysis.
"""
from __future__ import absolute_import
from pyretis.analysis.analysis import analyse_data, mean_square_displacement


__all__ = ['analyse_orderp']


def analyse_orderp(orderdata, settings):
    """Run the analysis on several order parameters.

    The results are collected into a structure which is convenient for
    plotting.

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
        For each order parameter `key`, `results[key]` contains the
        result from the analysis.

    See Also
    --------
    `analyse_data` in `pyretis.analysis.analysis.py`

    Note
    ----
    We here (and in the plotting routines) make certain assumptions
    about the structure, i.e. the positions are assumed to have a
    specific meaning: column zero is the time, column one the order
    parameter and so on.
    """
    results = []
    for i, data in enumerate(orderdata):
        if i == 0:  # first column is just the time, skip it
            pass
        else:
            result = analyse_data(data, settings)
            if i == 1:  # assume that we want the MSD analysis here:
                ndt = settings.get('maxordermsd')
                result['msd'] = mean_square_displacement(data, ndt=ndt)
            results.append(result)
    return results
