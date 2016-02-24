# -*- coding: utf-8 -*-
"""A collection of potential functions.

This package defines some potential functions. These potential functions
can be used to create force fields.


Package structure
~~~~~~~~~~~~~~~~~

Modules:

- potentials.py: This module defines some simple potential functions.

Sub-packages:

- pairpotentials: This package defines different pair interactions,
  for instance the Lennard-Jones 6-12 simple cut potential.

Important classes defined in this module:

- DoubleWell: A double well potential

- RectangularWell: A rectangular well potential -- useful as a
  bias potential.

- PairLennardJonesCut/PairLennardJonesCutnp: The Lennard-Jones
  potential.

- DoubleWellWCA: A n-dimensional Double Well potential.
"""
from .potentials import DoubleWell, RectangularWell
from .pairpotentials import (PairLennardJonesCut, PairLennardJonesCutnp,
                             DoubleWellWCA)
