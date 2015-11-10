# -*- coding: utf-8 -*-
"""This sub-package handle the input and output of pyretis files.

These files will store results/outputs from the simulation and
can be used to analyze a simulation.

Package structure
=================

Modules
-------

- crossfile.py: Module for handling crossing data.

- energyfile.py: Module for handling energy data.

- fileinout.py: Module for handling generic writing of data.

- orderfile.py: Module for handling order parameter data.

- pathfile.py: Module for handling path data and path-ensemble data.

- traj.py: Module for handling writing of trajectory data.


Important classes and functions
-------------------------------

- create_traj_writer: A function to create a trajectory writer from given
  settings.

- FileWriter: A generic file writer class.

- CrossWriter: A writer of crossing data.

- EnergyFile: A writer of energy data

- OrderFile: A writer of order parameter data.

- PathFile: A writer for path data.

- PathEnembleFile : A writer of path ensemble data.
"""
from .traj import create_traj_writer
from .fileinout import FileWriter
from .crossfile import CrossFile
from .energyfile import EnergyFile
from .orderfile import OrderFile
from .pathfile import PathFile, PathEnsembleFile
