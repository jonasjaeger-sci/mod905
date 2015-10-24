# -*- coding: utf-8 -*-
"""Definition of force field classes and potential functions.

In pyretis a force field is just a collection of potential functions
with some parameters. This module defines the force field and the
potential functions that can be used to build up force fields.

Package structure
=================

Modules
-------

- __init__.py: Imports from the modules.

- forcefield.py: Defines the forcefield object (`ForceField`) which can be
  used to represent a generic force field.

- potential.py: Defines the generic potential function object
  (`PotentialFunction`) which is subclassed in other potential functions.

- potentials.py: This module defines some simple potential functions.

- pairpotentials.py: This package defines different pair interactions,
  for instance the Lennard-Jones 6-12 simple cut potential.

Important classes and functions
-------------------------------

- ForceField: A class representing a general force field.

- PotentialFunction: A class representing a general potential function.
"""
from .forcefield import ForceField
from .potential import PotentialFunction
from retis.forcefield import potentials
from retis.forcefield import pairpotentials
