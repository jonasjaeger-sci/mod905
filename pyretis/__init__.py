# -*- coding: utf-8 -*-
"""
#######
pyretis
#######

This is pyretis - a library/simulation package for performing rare event
simulations with python.

pyretis Structure
=================

Modules
-------

- __init__.py: This is the main pyretis module. It will import useful
  subpackages and define the version number.

Subpackages
-----------

- core: The core objects, methods and functions used for running the rare
  event simulations. This includes objects for defining the system,
  defining a system box, defining simulations etc.

- forcefield: This package define forcefields and how they are calculated.

- tools: This package defines some methods which can be useful for
  setting up simple systems, for example methods for generating lattices.

- inout: This package defines the io for the pyretis program. This includes
  generating output from the analysis and reading input-files etc.

- analysis: This package defines the analysis tools for calculating
  crossing probabilities, rates etc.
"""
from __future__ import absolute_import

__version__ = '0.0.1'
__version_details__ = 'pre-release'
__program_name__ = 'pyretis'

# imports:
from . import core
from . import forcefield
from . import analysis
from . import tools
