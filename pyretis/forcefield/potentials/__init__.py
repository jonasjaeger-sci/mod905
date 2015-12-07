# -*- coding: utf-8 -*-
"""A collection of potential functions.

This package defines some potential functions. These potential functions
can be used to create force fields.


Package structure
~~~~~~~~~~~~~~~~~

Modules:

- potential.py: Defines the generic potential function object
  (`PotentialFunction`) which is sub-classed in other potential functions.

- potentials.py: This module defines some simple potential functions.

Sub-packages:

- pairpotentials: This package defines different pair interactions,
  for instance the Lennard-Jones 6-12 simple cut potential.

Important classes defined in this module:

- PotentialFunction: A class representing a general potential function.
"""
from .potential import PotentialFunction
from .potentials import DoubleWell, RectangularWell
from .pairpotentials import (PairLennardJonesCut, PairLennardJonesCutnp,
                             PairWCAnp, DoubleWellWCA)
