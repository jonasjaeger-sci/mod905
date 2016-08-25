# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""
#######
pyretis
#######

This file is part of pyretis - a simulation package for rare events.

Pyretis is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Pyretis is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with pyretis.  If not, see `<http://www.gnu.org/licenses/>`_.


pyretis documentation
---------------------

The documentation for pyretis is avaiable either docstrings provided
with the code and from `the pyretis homepage <http://www.pyretis.org>`_.

pyretis sub-packages
--------------------

analysis
    Analysis tools for calculating crossing probabilities, rates etc.
core
    Core classes and functions for running the rare event simulations.
    This includes classes defining the system, particles, simulations
    etc.
forcefield
    This package define force fields and potentials functions.
inout
    This package defines the input output operations for pyretis.
    This includes generating output from the analysis and reading
    input-files etc.
tools
    This package defines some functions which can be useful for
    setting up simple systems, for example functions for generating
    lattices.
"""
from __future__ import absolute_import
# pyretis imports:
from . import core
from . import forcefield
from . import analysis
from . import tools
from .version import version as __version__
__program_name__ = 'pyretis'
__url__ = 'http://www.pyretis.org'
__git_url__ = 'https://gitlab.com/andersle/pyretis'
__cite__ = """
[1] A. A., B. B and C. C., Journal Name, 42, pp. 101--102
    doi: doi/number/here
[2] A. A. and B. B, Journal Name, 43, pp. 101-102
    doi: doi/number/here
"""
