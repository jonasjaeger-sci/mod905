# -*- coding: utf-8 -*-
"""
This is an example on how to analyse the output from a MD flux simulation.
"""
from pyretis.inout.analysisio import run_md_flux_analysis
from pyretis.inout.settings.createoutput import read_json_file

RAW_DATA = {'files': {'cross': 'cross.dat', 'energy': 'energy.dat',
                      'order': 'order.dat'}}
ANALYSIS_SETTINGS = {'skipcross': 1001,
                     'maxblock': 1000,
                     'blockskip': 1,
                     'bins': 1000,
                     'ngrid': 1001,
                     'maxordermsd': 100,
                     'plot': {'plotter': 'mpl', 'output': 'png',
                              'style': 'pyretis', 'backup': False},
                     'txt-output': {'fmt': 'txt.gz', 'backup': False},
                     'report': ['latex', 'rst', 'html']}
simulation_settings = read_json_file('settings.json')
print(simulation_settings)
run_md_flux_analysis(ANALYSIS_SETTINGS, simulation_settings, RAW_DATA)
