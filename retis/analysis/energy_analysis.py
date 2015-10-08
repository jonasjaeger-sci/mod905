# -*- coding: utf-8 -*-
"""
This file contains methods for analysis of energy output
"""
from __future__ import absolute_import
from retis.analysis.analysis import analyse_data


__all__ = ['analyse_energies']


def analyse_energies(energies, settings):
    """
    This method will run the energy analysis on several energies and
    collect the energies into a structure which is convenient for plotting
    them.

    Parameters
    ----------
    energies : dict
        This dict contains the energies to analyse.
    settings : dict
        This dictionary contains settings for the analysis.

    Returns
    -------
    results : dict
        For each energy key `results[key]` contains the result from the energy
        analysis.

    See Also
    --------
    analyse_data in .analysis.py
    """
    results = {}
    for key in energies:
        results[key] = analyse_data(energies[key], settings)
    return results
