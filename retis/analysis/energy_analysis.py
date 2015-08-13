# -*- coding: utf-8 -*-
"""
This file contains methods for analysis of energy output
"""
from __future__ import absolute_import
from .analysis import running_average, block_error_corr
from .histogram import histogram_and_avg


__all__ = ['analyse_energy']


def analyse_energy(energy, settings):
    """
    This method will analyse the energies, specifically it will:
    1) Calculate a running average of the energy
    2) Obtain histogram for the energy
    3) Run a block error analysis

    Parameters
    ----------
    energy : numpy.array, 1D
        This numpy.array contain the energies as a function of time
    settings : dict
        This dictionary contains settings for the analysis.

    Returns
    -------
    out : dict
        This dict contains the results.

    Notes
    -----
    This method assumes that the energies has been read into a numpy.array.
    For very large/long simulations this might be memory intensive,
    however, the analysis is fast since we can use numpy functions.

    Also note that range is used here rather than xrange. This is just to
    ease the transition python2 -> python3.
    """
    result = {}
    # 1) Do the running average
    result['running'] = running_average(energy)
    # 2) Obtain distributions:
    result['distribution'] = histogram_and_avg(energy, settings['bins'],
                                               density=True)
    # 3) Do the block error analysis:
    result['blockerror'] = block_error_corr(energy,
                                            maxblock=settings['maxblock'],
                                            blockskip=settings['blockskip'])
    return result


def analyse_all_energies(energies, settings):
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
    """
    results = {}
    for key in energies:
        results[key] = analyse_energy(energies[key], settings)
    return results
