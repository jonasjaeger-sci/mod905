# -*- coding: utf-8 -*-
"""
This library handles the input and output for pyretis.

This package is intended for creating various forms of output
from the pyretis program. It include writers for simple text based
output and plotters for creating figures. Figures and the text results
can be combined into reports, which can be templated.

Package structure
=================

Sub-packages
------------

- fileinout: handles the input and output of files used as input for the
  analysis. It also defines formats for trajectories.

- plotting: handles plotting. It defines simple things like colors etc. 
  for plotting. It also defines functions which can be used for specific
  plotting by the analysis and report tools.

Modules
-------

- analysisio.py: This is a module to output the analysis of (RE)TIS
  simulation.

- common.py: This module contains some common functions. These functions
  are mainly intended for internal use and are not currently imported
  here.

- __init__.py: Imports from the other modules and define some convenience
  functions for creating trajectory writers and text tables.

- report.py: Module for creating reports based on analysis. This module
  is responsible for creating the final output from the analysis of (RE)TIS
  simulations

- simulationinout.py: Module for handling input and output from simulation
  results.

- txtinout.py: Defines objects and some methods for text-based output.
  It defines the TxtTable object (table-like-format) intended to be
  written to the screen during a simulation or to a file.

Important classes and functions
-------------------------------

- CrossFile, EnergyFile, OrderFile: Classes for writing crossing data
  (for initial the flux), energy data and order parameter data.

- PathEnembleFile: A writer of path ensemble data.

- generate_report: A function to generate reports from analysis output(s).

- create_traj_writer: A function to create a trajectory writer from given
  settings.

- create_output_task: A function to create output tasks for a simulation.

- get_predefined_table: A function to get an object which can be used to
  pretty-print tables to the screen/file during a simulation.

- TxtTable: A function to write text tables.

Folders
-------

- templates: This folder contains templates for the report.
"""
from .txtinout import TxtTable, get_predefined_table
from .fileinout import (FileWriter, CrossFile, EnergyFile, OrderFile,
                        PathEnsembleFile, create_traj_writer)
from .report import generate_report_md, generate_report_tis
from .simulationinout import create_output, store_settings_as_py
