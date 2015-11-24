# -*- coding: utf-8 -*-
"""This package defines analysis tools for the pyretis program.

The analysis tools are intended to be used for analysis of the
simulation output from the pyretis program. The typically use of this
package is in post-processing of the results from a simulation (or several
simulations).

Package structure
~~~~~~~~~~~~~~~~~

Modules:

- __init__.py: This file, imports from the other modules. The method to
  analyse results from MD flux simulations is defined here since it uses
  analysis tools from `energy_analysis.py` and `order_analysis.py`.

- analysis.py: Defines methods for numerical analysis.

- energy_analysis.py: Defines methods useful for analyzing the energy output.

- histogram.py: Defines methods useful for generating histograms.

- order_analysis.py: Defines methods useful for analysis of order parameters.

- path_analysis.py: Defines methods for analysis of path ensembles.


Important functions defined in this module:

- analyse_energies: Analyse energy data from a simulation.
  It will calculate a running average, a distribution and do a block
  error analysis.

- analyse_flux: Analyse flux data from a MD flux simulation.
  It will calculate a running average, a distribution and do a block
  error analysis.

- analyse_orderp: Analyse order parameter data.
  It will calculate a running average, a distribution and do a block
  error analysis. In addition if will analyse the mean square displacement
  if requested.

- analyse_path_ensemble: Analyse the results from a single path ensemble.
  It will calculate a running average of the probabilities, a crossing
  probability, perform an block error analysis, analyse lengths of paths,
  type of Monte Carlo moves and calculate an efficiency.

- match_probabilities: Method to match probabilities from several
  path simulations. Useful for obtaining the overall crossing probability.

- histogram: Generates histogram, basically a wrapper around numpy's
  histogram.

- match_all_histograms: Function to match histograms from
  umbrella simulations.
"""
from .analysis import running_average, block_error, block_error_corr
from .energy_analysis import analyse_energies
from .flux_analysis import analyse_flux
from .histogram import histogram, match_all_histograms
from .order_analysis import analyse_orderp
from .path_analysis import analyse_path_ensemble, match_probabilities


def analyse_md_flux(crossdata, energydata, orderdata, analysis_settings,
                    simulation_settings):
    """This method will analyse the output from a MD-flux simulation.

    The obtained results will be returned as a convenient structure for
    plotting or reporting.

    Parameters
    ----------
    crossdata : numpy.array
        This is the data containing information about crossings.
    energydata : numpy.array
        This is the raw data for the energies.
    orderdata : numpy.array
        This is the raw data for the order parameter.
    analysis_settings : dict
        This dict contains settings for running the analysis (e.g block
        length for error analysis).
    simulation_settings : dict
        This dict contains settings from the simulation (interfaces,
        time step etc).

    Returns
    -------
    results : dict
        This dict contains the results from the different analysis as a
        dictionary. This dict can be used further for plotting or for
        generating reports.
    """
    results = {}
    results['flux'] = analyse_flux(crossdata, analysis_settings,
                                   simulation_settings)
    results['energy'] = analyse_energies(energydata, analysis_settings)
    results['order'] = analyse_orderp(orderdata, analysis_settings)
    return results
