# -*- coding: utf-8 -*-
"""
This files contains methods that will output results from the
path analysis and the energy analysis.

Important methods defined here:

- run_md_flux_analysis: Method to run the MD flux analysis on a set
  of files. It will plot the results and generate a MD-flux report.
"""


def run_md_flux_files(analysis_settings, simulation_settings,
                      crossfile, energyfile, orderfile):
    """
    This method will analyse the output from a MD-flux simulation, by reading
    in raw data from output files obtained in the MD-flux simulation.
    This method will output a series of plots and generate a report based on
    the analysis.

    Parameters
    ----------
    analysis_settings : dict
        This dict contains settings which dictates how the
        analysis should be performed.
    simulation_settings : dict
        This dict contains information on how the simulatino
        was performed.
    crossfile : string
        The file with the crossing data
    energyfile : string
        The file with the energy data
    orderfile : string
        The file with the order parameter data
    """
    pass
