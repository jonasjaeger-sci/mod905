# -*- coding: utf-8 -*-
"""Classes for pair potentials.

This package defines different pair potentials for use with internal
calculation in pyretis.

Package structure
=================

Modules
-------

- __init__.py: Imports the different pair potential functions.

- lennardjones.py: Defines potential functions for Lennard-Jones
  interactions.

- wca.py: Defines potential functions for the WCA interaction.

Important classes and functions
-------------------------------

- PairLennardJonesCut: A class defining a Lennard-Jones potential

- PairWCAnp: A class defining a WCA potential. The 'np' in the name
  reflects that this class is using numpy for calculations.
"""
from .lennardjones import PairLennardJonesCut, PairLennardJonesCutnp
from .wca import PairWCAnp, DoubleWellWCA
