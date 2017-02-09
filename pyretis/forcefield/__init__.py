# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Definition of force field classes and potential functions.

In pyretis a force field is just a collection of potential functions
with some parameters. This module defines the force field and the
potential functions that can be used to build up force fields.

Package structure
-----------------

Modules
~~~~~~~

forcefield.py (:py:mod:`pyretis.forcefield.forcefield`)
    Defines the force field class (:py:class:`.ForceField`) which can
    be used to represent a generic force field.

potential.py (:py:mod:`pyretis.forcefield.potential`)
    Defines the generic potential function class
    (:py:class:`.PotentialFunction`) which is sub-classed in other
    potential functions.

Sub-packages
~~~~~~~~~~~~

potentials (:py:mod:`pyretis.forcefield.potentials`)
    Definition of potential functions for force fields.


Important classes defined in this package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ForceField (:py:class:`.ForceField`)
    A class representing a general force field.

PotentialFunction (:py:class:`.PotentialFunction`)
    A class representing a general potential function.
"""
from .forcefield import ForceField
from .potential import PotentialFunction
from . import potentials
