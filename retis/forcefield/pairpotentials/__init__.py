# -*- coding: utf-8 -*-
"""
This sub-package defines different pair potentials.

Package structure
=================

Modules:

- __init__.py: Imports the different pair potential functions.

- lennardjones.py: Defines potential functions for Lennard-Jones
  interactions.

- wca.py: Defines potential functions for the WCA interaction.
"""
from .lennardjones import PairLennardJonesCut, PairLennardJonesCutnp
from .wca import PairWCAnp, DoubleWellWCA
