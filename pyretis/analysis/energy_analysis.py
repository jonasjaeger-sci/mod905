# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""Methods for analysis of energy simulation results.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

analyse_energies
    Run a energy analysis for energies (kinetic, potential etc.).
"""
from __future__ import absolute_import
import numpy as np
from scipy.stats import gamma  # pylint: disable=E0611
from pyretis.analysis.analysis import analyse_data


__all__ = ['analyse_energies']


def analyse_energies(energies, settings):
    """Run the energy analysis on several energy types.

    The function will run the energy analysis on several energy types
    and collect the energies into a structure which is convenient for
    plotting the results.

    Parameters
    ----------
    energies : dict
        This dict contains the energies to analyse.
    settings : dict
        This dictionary contains settings for the analysis.

    Returns
    -------
    results : dict
        For each energy key `results[key]` contains the result from the
        energy analysis.

    See Also
    --------
    `analyse_data` in `pyretis.analysis.analysis.py`.
    """
    results = {}
    for key in energies:
        results[key] = analyse_data(energies[key], settings)
    # For the energy analysis it is also useful to add some
    # theoretical distributions:
    alp = (0.5 * settings['npart'] * settings['dimensions'])
    scale = {'ekin': 1.0 / settings['beta'],
             'temp': settings['temperature'] / alp}
    for key in scale:
        if key in results:
            dist = results[key]['distribution']
            pos = np.linspace(min(0.0, dist[1].min()), dist[1].max(), 1000)
            tdist = gamma.pdf(pos, alp, loc=0, scale=scale[key])
            results[key]['boltzmann-dist'] = [tdist, pos, (0.0, scale[key])]
    return results
