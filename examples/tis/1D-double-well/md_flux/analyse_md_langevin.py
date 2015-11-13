# -*- coding: utf-8 -*-
"""
This is an example on how to analyse the output from a MD flux simulation.
"""
from pyretis.inout.analysisio import run_md_flux_analysis
from settings import settings as simulation_settings

RAW_DATA = {'files': {'cross': 'cross.dat', 'energy': 'energy.dat',
                      'order': 'order.dat'}}
ANALYSIS_SETTINGS = {'skipcross': 1001,
                     'maxblock': 1000,
                     'blockskip': 1,
                     'bins': 1000,
                     'ngrid': 1001,
                     'maxordermsd': 100,
                     'plot': {'plotter': 'mpl', 'output': 'png',
                              'style': 'pyretis'},
                     'txt-output': 'txt.gz',
                     'report': ['latex', 'rst', 'html']}
run_md_flux_analysis(ANALYSIS_SETTINGS, simulation_settings, RAW_DATA)
