# -*- coding: utf-8 -*-
"""
This file contains methods for analysis of crossings for the
flux data
"""
from __future__ import absolute_import
from .analysis import analyse_data


__all__ = ['analyse_flux']


def analyse_flux(fluxdata, interfaces):
    """
    This method will run the analysis on several order parameters and
    collect the results into a structure which is convenient for plotting.

    Parameters
    ----------
    fluxdata : numpy.array (N x 3)
        The contents of this array is the data obtained from a MD simulation
        for the fluxes.
    interfaces : list of floats
        These are the interfaces used in the simulation.

    Returns
    -------
    results : numpy.array

    """
    results = None
    print fluxdata
    print interfaces
    return results
