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
    orderdata : dict
        This dict contains the order parameters to analyse.
    settings : dict
        This dictionary contains settings for the analysis.

    Returns
    -------
    results : dict
        For each order parameter `key`, `results[key]` contains the result
        from the analysis.

    See Also
    --------
    analyse_data in .analysis.py

    Note
    ----
    Currently, this is identical to energy_analysis.analyse_energies.
    This might be changed in the near future with a more sophisticated
    analysis.
    """
    results = {}
    for key in orderdata:
        results[key] = analyse_data(orderdata[key], settings)
    return results
