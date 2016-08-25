# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""Package defining classes for pair potentials.

This package defines different pair potentials for use with internal
calculation in pyretis.

Package structure
-----------------

Modules
~~~~~~~

lennardjones.py
    Potential functions for Lennard-Jones interactions.

wca.py
    Potential functions for WCA-type interactions.

Important classes defined in this package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PairLennardJonesCut
    A class defining a Lennard-Jones potential.

PairLennardJonesCutnp
    A class defining a Lennard-Jones potential using numpy for the
    evaluation.

DoubleWellWCA
    This class defines a n-dimensional Double Well potential for a
    pair of particles.
"""
from .lennardjones import PairLennardJonesCut, PairLennardJonesCutnp
from .wca import DoubleWellWCA
from .pairpotential import generate_pair_interactions
