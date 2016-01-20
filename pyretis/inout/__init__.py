# -*- coding: utf-8 -*-
"""The sub-package handles input and output for pyretis.

This package is intended for creating various forms of output
from the pyretis program. It include writers for simple text based
output and plotters for creating figures. Figures and the text results
can be combined into reports, which are handled by the report module.

Package structure
~~~~~~~~~~~~~~~~~

Sub-packages:

- analysisio: Handles the input and output needed for analysis.

- fileio: Handles files with output from pyretis which can be used in
  the analysis. It also defines formats for trajectories.

- plotting: Handles plotting. It defines simple things like colors etc.
  for plotting. It also defines functions which can be used for specific
  plotting by the analysis and report tools.

- settings: Handle input and output settings



Modules:

- common.py: Common functions and variables for the input/output. These
  functions are mainly intended for internal use and are not imported here.

- __init__.py: Imports from the other modules.

- txtinout.py: Defines classes and some functions for text-based output. This
  is typically text written to the screen during a simulation.

Important classes and functions:

- CrossFile, EnergyFile, OrderFile: Classes for writing crossing data
  (for initial the flux), energy data and order parameter data.

- PathFile, PathEnembleFile: Classes for writing path and path ensemble data.

- generate_report: A function to generate reports from analysis output(s).

- create_traj_writer: A function to create a trajectory writer from given
  settings.

- create_output_task: A function to create output tasks for a simulation.

- get_predefined_table: A function to get an object which can be used to
  pretty-print tables to the screen/file during a simulation.

- TxtTable: A function to write create text based tables. It is used by
  `get_predefined_table`.
"""
from __future__ import absolute_import
from .txtinout import TxtTable, get_predefined_table
from .fileio import (FileWriter, CrossFile, EnergyFile, OrderFile,
                     PathFile, PathEnsembleFile,
                     create_traj_writer, get_file_object)
from .report import generate_report
from .settings import create_output
