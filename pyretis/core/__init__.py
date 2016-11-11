# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""This package defines the core pyretis tools.

The core tools are intended to set up simulations and run them.

Package structure
-----------------

Modules
~~~~~~~

__init__.py
    Import core functions from the other modules.

box.py (:py:mod:`pyretis.core.box`)
    Definition of the simulation box class.

integrators.py (:py:mod:`pyretis.core.integrators`)
    This module defines integrators which can be used to
    evolve the dynamics/solve Newton's equations of motion.

montecarlo.py (:py:mod:`pyretis.core.montecarlo`)
    This module defines functions for performing Monte Carlo moves.

orderparameter.py (:py:mod:`pyretis.core.orderparameter`)
    Definition of classes for order parameters.

particlefunctions.py (:py:mod:`pyretis.core.particlefunctions`)
    Functions that operate on (a selection of) particles, for instance
    calculation of the kinetic temperature, pressure, momentum etc.

particles.py (:py:mod:`pyretis.core.particles`)
    Definition of the particle class which is used to represent
    a collection of particles.

path.py (:py:mod:`pyretis.core.path`)
    This module defines functions and classes for paths.

pathensemble.py (:py:mod:`pyretis.core.pathensemble`)
    Definition of a class for a collection of paths (i.e. a path
    ensemble).

properties.py (:py:mod:`pyretis.core.properties`)
    This module defines a class for a generic property.

random_gen.py (:py:mod:`pyretis.core.random_gen`)
    This module define a class for generating random numbers.

retis.py (:py:mod:`pyretis.core.retis`)
    Module defining method for performing replica exchange transition
    interface sampling.

system.py (:py:mod:`pyretis.core.system`)
    This module define the system class which connects different
    parts (for instance box, forcefield and particles) into a single
    structure.

tis.py (:py:mod:`pyretis.core.tis`)
    This module contains methods used in the transition
    interface sampling algorithm.

units.py (:py:mod:`pyretis.core.units`)
    This module defines conversion between units.

Sub-packages
~~~~~~~~~~~~

simulation
    Package defining the `Simulation` class which is used for
    setting up generic simulations. It also contains classes for
    more specialized simulations (NVE, TIS, etc.).

Important classes defined in this package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Box (:py:class:`pyretis.core.box.Box`)
    A class which defines the simulation box. This box will also
    handle the periodic boundaries.

System (:py:class:`pyretis.core.system.System`)
    A class which defines the system we are working with. This
    class contain a lot of information and is used to group the
    information into a structure which the simulations will make use
    of. Typically the system will contain a reference to a box,
    a list of particles and also a force field.

Particles (:py:class:`pyretis.core.particles.Particles`)
    A class defining a list of particles. This will contain the
    positions, velocities and forces for the particles.

Path (:py:class:`pyretis.core.path.Path`)
    A class representing a path. The path contains snapshots with
    some additional information (energies and order parameters).

PathEnsemble (:py:class:`pyretis.core.pathensemble.PathEnsemble`)
    A class representing a collection of paths. The path ensemble
    will not store the full trajectories of path, only a simplified
    representation of the paths.

RandomGenerator (:py:class:`pyretis.core.random_gen.RandomGenerator`)
    A class for generating random numbers.

OrderParameter (:py:class:`pyretis.core.orderparameter.OrderParameter`)
    A general class for order parameters. Prototype for all other
    order parameters.

Simulation (:py:mod:`pyretis.core.simulation`)
    A sub-package defining the simulations. There is also a
    class named ``Simulation`` which defines a generic simulation.
"""
from __future__ import absolute_import
from . import simulation
from .system import System
from .box import Box
from .particles import Particles
from .path import Path
from .pathensemble import PathEnsemble
from .random_gen import RandomGenerator
from .orderparameter import OrderParameter, OrderParameterPosition
