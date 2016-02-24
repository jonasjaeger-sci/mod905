# -*- coding: utf-8 -*-
"""This package defines the core pyretis tools.

The core tools are intended to set up simulations and run them.

Package structure
-----------------

Sub-packages:

- simulation: This module defines the Simulation class which is used for
  setting up generic simulations. It also defines classes for more
  specialized simulations for instance the `SimulationNVE` for running
  NVE molecular dynamics simulations.

Modules:

- __init__.py: Import core functions from the other modules.

- box.py: This module defines the simulation box class.

- integrators.py: This module defines integrators which can be used to
  evolve the dynamics/solve Newton's equations of motion.

- montecarlo.py: This module defines functions for performing
  Monte Carlo moves.

- orderparameter.py: This module define the order parameter class.

- particlefunctions.py: This module defines several functions that
  operate on (a selection of) particles, for instance calculation of the
  kinetic temperature.

- particles.py: This module define the particles class which is used to
  represent a collection of particles.

- path.py: This module defines functions and classes for paths.

- pathensemble.py: This module defines the class for a collection of
  paths (i.e. a path ensemble).

- properties.py: This module defines a class for a generic property.

- random_gen.py: This module define a class for generating random
  numbers.

- retis.py: Module defining the replica exchange transition interface
  sampling.

- system.py: This module define the system class which connects
  different parts (for instance box, forcefield and particles) into a
  single structure.

- tis.py: This module contains functions used in the transition
  interface sampling algorithm.

- units.py: This module defines conversion between units.

Important classes and functions:

- Box: A class which defines the simulation box. This box will also
  handle the periodic boundaries.

- System: A class which defines the system we are working with. This
  class contain a lot of information and is used to group the
  information into a structure which the simulations will make use of.
  Typically the system will contain a reference to a Box, a list of
  particles and also a force field.

- Particles: A class defining a list of  particles. This will contain
  the positions, velocities and forces for the particles.

- Path: A class representing a path. The path contains snapshots with
  some additional information (energies and order parameters).

- PathEnsemble: A class representing a collection of paths. The path
  ensemble will not store the full trajectories of path, only a
  simplified representation of the paths.

- RandomGenerator: A class for generating random numbers.

- OrderParameter: A general class for order parameters. Prototype for
  all other order parameters.

- Simulation: A sub-package defining the simulations. There is also a
  class named `Simulation` which defines a generic simulation.
"""
from __future__ import absolute_import
from . import simulation
from .system import System
from .box import Box
from .particles import Particles
from .path import Path
from .pathensemble import PathEnsemble
from .random_gen import RandomGenerator
from .orderparameter import (OrderParameter, OrderParameterPosition,
                             OrderParameterParse)
