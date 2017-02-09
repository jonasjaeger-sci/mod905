# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""
#######
pyretis
#######

This file is part of pyretis - a simulation package for rare events.

Copyright (C) 2015  The pyretis team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LILGPLv3ED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


pyretis documentation
---------------------

The documentation for pyretis is available either doc-strings provided
with the code and from `the pyretis homepage <http://www.pyretis.org>`_.

pyretis sub-packages
--------------------

analysis (:py:mod:`pyretis.analysis`)
    Analysis tools for calculating crossing probabilities, rates etc.

core (py:mod:`pyretis.core`)
    Core classes and functions for running the rare event simulations.
    This includes classes defining the system, particles, simulations
    etc.

engines (:py:mod:`pyretis.engines`)
    A package defining engines which can be used to
    evolve the dynamics/solve Newton's equations of motion in time.

forcefield (:py:mod:`pyretis.forcefield`)
    This package define force fields and potentials functions.

inout (:py:mod:`pyretis.inout`)
    This package defines the input output operations for pyretis.
    This includes generating output from the analysis and reading
    input-files etc.

orderparameter (:py:mod:`pyretis.orderparameter`)
    Definition of classes for order parameters. Defines the base class
    for order parameters.

tools (:py:mod:`pyretis.tools`)
    This package defines some functions which can be useful for
    setting up simple systems, for example functions for generating
    lattices.
"""
# pyretis imports:
from .version import VERSION as __version__
from . import info
from . import core
from . import engines
from . import orderparameter
from . import forcefield
from . import tools
from . import analysis
from . import inout
