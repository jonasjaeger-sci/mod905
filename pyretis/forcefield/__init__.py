# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""Definition of force field classes and potential functions.

In pyretis a force field is just a collection of potential functions
with some parameters. This module defines the force field and the
potential functions that can be used to build up force fields.

Package structure
-----------------

Modules
~~~~~~~

forcefield.py
    Defines the forcefield object (``ForceField``) which can be used
    to represent a generic force field.

potential.py
    Defines the generic potential function object (`PotentialFunction`)
    which is sub-classed in other potential functions.

Sub-packages
~~~~~~~~~~~~

potentials
    Definition of potential functions for force fields.


Important classes defined in this package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ForceField
    A class representing a general force field.

PotentialFunction
    A class representing a general potential function.
"""
from .forcefield import ForceField
from .potential import PotentialFunction
from . import potentials
