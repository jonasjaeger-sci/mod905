# -*- coding: utf-8 -*-
"""
This package defines the core pyretis tools.

The core tools are intended to set up simulations and run
them. This module is not intended to handle output or analysis.

Package structure
=================

Modules:

- __init__.py: Import core functions from the other modules.

- box.py: This module defines the simulation box object.

- integrators.py: This module defines integrators which can be used to
  evolve the dynamics/solve Newton's equations of motion.

- montecarlo.py: This module defines methods for performing Monte Carlo moves.

- orderparameter.py: This module define the order parameter object.

- particlefunctions.py: This module defines several methods/functions that
  operate on (a selection of) particles, for instance calculation of the
  kinetic temperature.

- particles.py: This module define the particles object which is used to
  represent a collection of particles.

- path.py: This module defines objects and methods for paths. It defines
  the object for a path and a collection of paths (i.e. a path ensemble).

- properties.py: This module define an object for a generic property.

- random_gen.py: This module define an object for generating random numbers.

- simulation.py: This module defines the Simulation object which is used for
  setting up generic simulations. It also defines objects for more
  specialized simulations for instance the SimulationNVE for running NVE
  molecular dynamics simulations.

- system.py: This module define a system object which connects different
  parts (for instance box, forcefield and particles) into a single object.

- tis.py: This module contains method used in the transition interface
  sampling algorithm.

- units.py: This module defines conversion between units.

Important classes/functions
---------------------------

- Box: A class which defines the simulation box. This box will also
  handle the periodic boundaries.

- System: A class which defines the system we are working with. This
  class contain a lot of information and is used to group the information
  into a structure which the simulations will make use of. Typically the
  system will contain a reference to a Box, a list of particles and also
  a force field.

- Particles: A class defining a list of  particles. This will contain the
  positions, velocities and forces for the particles.

- Path: A class representing a path. The path contains shapshots with some
  additional information (energies and order parameters).

- PathEnsemble: A class representing a collection of paths. The path ensemble
  will not store the full trajectories of path, only a simplified
  representation of the paths.

- RandomGenerator: A class for generating random numbers.

- OrderParameter: A general class for order parameters. Prototype for all
  other order parameters.

- Simulation: A sub-packages (and a class) defining the simulations.
"""
from . import simulation
from .system import System
# from .properties import Property
# from .montecarlo import *
from .box import Box
from .particles import Particles
from .path import Path, PathEnsemble
from .random_gen import RandomGenerator
from .orderparameter import (OrderParameter, OrderParameterPosition,
                             OrderParameterParse)
# from .tis import *
