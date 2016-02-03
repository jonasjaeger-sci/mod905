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

- plotting: Handles plotting. It defines simple things like colors etc.
  for plotting. It also defines functions which can be used for specific
  plotting by the analysis and report tools.

- settings: Handle input and output settings

- writers: Handle formatting and presentation of text based output.

Modules:

- common.py: Common functions and variables for the input/output. These
  functions are mainly intended for internal use and are not imported here.

- __init__.py: Imports from the other modules.

- txtinout.py: Defines functions for text-based output.

Important classes and functions:

- CrossWriter, EnergyWriter, OrderWriter: Classes for writing crossing data
  (for initial the flux), energy data and order parameter data.

- PathEnsembleWriter: Class for writing path ensemble data.

- generate_report: A function to generate reports from analysis output(s).

- create_output_task: A function to create output tasks for a simulation.

- TxtTable: A function to write create text based tables.
"""
from __future__ import absolute_import
from .report import generate_report
from .settings import create_output
