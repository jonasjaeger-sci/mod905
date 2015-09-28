# -*- coding: utf-8 -*-
"""
This package defines analysis tools for the pytismol program.

Package structure
=================

Modules:

- __init__.py: Imports from the other modules.

- analysis.py: Defines methods for numerical analysis.

- energy_analysis.py: Defines methods useful for analysing the energy output.

- histogram.py: Defines methods useful for generating histograms.

- order_analysis.py: Defines methods useful for analysis of order parameters.

- path_analysis.py: Defines methods for analysis of path ensembles.
"""
from __future__ import print_function
from .analysis import running_average, block_error, block_error_corr
from .histogram import histogram, match_all_histograms
from .energy_analysis import analyse_energies
from .order_analysis import analyse_orderp
from .path_analysis import analyse_path_ensemble, match_probabilities
from .flux_analysis import analyse_flux


def analyse_md_flux(crossdata, energydata, orderdata, analysis_settings,
                    simulation_settings):
    """
    This method will analyse the output from a MD-flux simulation and return
    the results as a convenient structure for plotting or reporting.

    Parameters
    ----------
    crossdata : numpy.array
        This is the data containing information about crossings.
    energydata : numpy.array
        This is the raw data for the energies.
    orderdata : numpy.array
        This is the raw data for the order parameter.

    Returns
    -------
    results : dict
        This dict contains the results from the different analysis as a
        dictionary. This dict can be used further for plotting or for
        generating reports.
    """
    results = {}
    print('Analysing flux data')
    results['flux'] = analyse_flux(crossdata, analysis_settings,
                                   simulation_settings)
    print('Analysing energy data')
    results['energy'] = analyse_energies(energydata, analysis_settings)
    print('Order parameter data')
    results['order'] = analyse_orderp(orderdata, analysis_settings)
    return results
