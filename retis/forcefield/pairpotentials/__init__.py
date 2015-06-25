# -*- coding: utf-8 -*-
"""
This sub-package defines different pair potentials.

Package structure
=================

Modules:

- __init__.py: Imports the different pair potential functions.

- pairlennardjones.py: Defines potential functions for Lennard-Jones
  interactions.

- pairwca.py: Defines potential functions for the WCA interaction.
"""
from .pairlennardjones import PairLennardJonesCut, PairLennardJonesCutnp
from .pairwca import PairWCAnp, DoubleWellWCA
