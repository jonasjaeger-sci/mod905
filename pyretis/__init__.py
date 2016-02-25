# -*- coding: utf-8 -*-
"""
#######
pyretis
#######

This is pyretis - a library/simulation package for performing rare event
simulations with python.

pyretis structure
~~~~~~~~~~~~~~~~~

Modules:

- __init__.py: This is the main pyretis module. It will import useful
  sub-packages and define the version number.

Sub-Packages:

- core: The core classes and functions used for running the rare
  event simulations. This includes classes defining the system,
  a system box, simulations etc.

- forcefield: This package define forcefields and how they are
  calculated.

- tools: This package defines some functions which can be useful for
  setting up simple systems, for example functions for generating
  lattices.

- inout: This package defines the io for the pyretis program.
  This includes generating output from the analysis and reading
  input-files etc.

- analysis: This package defines the analysis tools for calculating
  crossing probabilities, rates etc.
"""
from __future__ import absolute_import
# pyretis imports:
from . import core
from . import forcefield
from . import analysis
from . import tools
__version__ = '0.1.0'
__version_details__ = 'pre-release'
__program_name__ = 'pyretis'
__url__ = 'http://www.pyretis.org'
__git_url__ = 'https://gitlab.com/andersle/pyretis'
__cite__ = """
[1] A. A., B. B and C. C., Journal Name, 42, pp. 101--102
    doi: doi/number/here
[2] A. A. and B. B, Journal Name, 43, pp. 101-102
    doi: doi/number/here
"""
