# -*- coding: utf-8 -*-
"""
This is an example on how to analyse the output from a MD flux simulation.
"""
from pyretis.inout import run_md_flux_analysis
RAW_DATA = {'files': {'cross': 'cross.dat', 'energy': 'energy.dat',
                      'order': 'order.dat'}}
ANALYSIS_SETTINGS = {'skipcross': 1001,
                     'maxblock': 1000,
                     'blockskip': 1,
                     'bins': 1000,
                     'ngrid': 1001,
                     'maxordermsd': 100,
                     'report': ['latex', 'rst', 'html']}
SIMULATION_SETTINGS = {'interfaces': [-1.0, 0.0, 1.0],
                       'integrator': {'timestep': 0.002},
                       'endcycle': 500000,
                       'npart': 1.0,
                       'dim': 1.0,
                       'temperature': 0.07,
                       'beta': 1.0/0.07}
run_md_flux_analysis(ANALYSIS_SETTINGS, SIMULATION_SETTINGS, RAW_DATA)
