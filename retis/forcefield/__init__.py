# -*- coding: utf-8 -*-
"""
This module defines the force field and the potential functions that can
be used to build up force fields.

Package structure
=================

Modules:

- __init__.py: Imports __all__ from the modules.

- forcefield.py: Defines the forcefield object (`ForceField`) which can be
  used to represent a generic force field.

- potential.py: Defines the generic potential function object
  (`PotentialFunction`) which is subclassed in other potential functions.

- potentials.py: This module defines some simple potential functions.

- pairpotentials.py: This package defines different pair interactions,
  for instance the Lennard-Jones 6-12 simple cut potential.
"""

from .forcefield import ForceField
from .potential import PotentialFunction
from retis.forcefield import potentials
from retis.forcefield import pairpotentials
