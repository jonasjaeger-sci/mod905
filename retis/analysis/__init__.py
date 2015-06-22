# -*- coding: utf-8 -*-
"""
This package defines analysis tools for the pyretis program.

Package structure
=================

Modules:

- __init__.py: Imports from the other modules.

- histogram.py: Defines methods useful for generating histograms.

- analysis.py: Defines methods for numerical analysis.

- path_analysis.py: Defines methods for analysis of path ensembles.
"""
from .histogram import histogram, match_all_histograms
from .analysis import running_average, block_error
from .path_analysis import analyse_path_ensemble, match_probabilities
