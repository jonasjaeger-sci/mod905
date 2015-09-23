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
from .analysis import running_average, block_error, block_error_corr
from .histogram import histogram, match_all_histograms
from .energy_analysis import analyse_energies
from .order_analysis import analyse_orderp
from .path_analysis import analyse_path_ensemble, match_probabilities
from .flux_analysis import analyse_flux
