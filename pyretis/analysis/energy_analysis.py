# -*- coding: utf-8 -*-
"""This file contains functions for analysis of energy output."""
from __future__ import absolute_import
from pyretis.analysis.analysis import analyse_data


__all__ = ['analyse_energies']


def analyse_energies(energies, settings):
    """Run the energy analysis on several energy types.

    The function will run the energy analysis on several energy types and
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
    `analyse_data` in `pyretis.analysis.analysis.py`.
    """
    results = {}
    for key in energies:
        results[key] = analyse_data(energies[key], settings)
    return results
