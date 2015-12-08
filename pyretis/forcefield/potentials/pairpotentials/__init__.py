# -*- coding: utf-8 -*-
"""Package defining classes for pair potentials.

This package defines different pair potentials for use with internal
calculation in pyretis.

Package structure
~~~~~~~~~~~~~~~~~

Modules:

- lennardjones.py: Potential functions for Lennard-Jones interactions.

- wca.py: Potential functions for WCA-type interactions.

Important classes and functions defined here:

- PairLennardJonesCut: A class defining a Lennard-Jones potential

- DoubleWellWCA: This class defines a n-dimensional Double Well potential for
  a pair of particles.
"""
from .lennardjones import PairLennardJonesCut, PairLennardJonesCutnp
from .wca import DoubleWellWCA
