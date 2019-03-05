# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""The sub-package handles input and output for PyRETIS.

This package is intended for creating various forms of output
from the PyRETIS program. It includes writers for simple text-based
output and plotters for creating figures. Figures and the text results
can be combined into reports, which are handled by the report module.

Package structure
~~~~~~~~~~~~~~~~~

Modules
~~~~~~~

__init__.py
    Imports from the other modules.

common.py (:py:mod:`pyretis.inout.common`)
    Common functions and variables for the input/output. These
    functions are mainly intended for internal use and are not imported
    here.

fileio.py (:py:mod:`pyretis.inout.fileio`)
    A module which defines a generic file class for PyRETIS output files.

settings.py (:py:mod:`pyretis.inout.settings`)
    A module which handles the reading/writing of settings.

restart.py (:py:mod:`pyretis.inout.restart`)
    A module which handles restart reading/writing.

Sub-packages
~~~~~~~~~~~~

analysisio (:py:mod:`pyretis.inout.analysisio`)
    Handles the input and output needed for analysis.

formats (:py:mod:`pyretis.inout.formats`)
    Handles the input and output of different data formats. This
    includes the configurations and the internal data formats.

plotting (:py:mod:`pyretis.inout.plotting`)
    Handles the plotting needed by the analysis by defining plotting
    tools, methods and styles.

report (:py:mod:`pyretis.inout.report`)
    Generate reports with results from simulations.

setup (:py:mod:`pyretis.inout.setup`)
    Handles set-up of simulations etc. from user settings.


Important classes defined in this package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Important methods defined in this package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

create_engine (:py:func:`.create_engine`)
    Create an engine from input settings.

create_force_field (:py:func:`.create_force_field`)
    Create a force field from input settings.

create_orderparameter (:py:func:`.create_orderparameter`)
    Create an order parameter from input settings.

create_simulation (:py:func:`.create_simulation`)
    Create a simulation from input settings.

create_system (:py:func:`.create_system`)
    Create a system from input settings.

generate_report (:py:func:`.generate_report`)
    A function to generate reports from analysis output(s).

parse_settings_file (:py:func:`.parse_settings_file`)
    Method for parsing settings from a given input file.

write_settings_file (:py:func:`.write_settings_file`)
    Method for writing settings from a simulation to a given file.

write_restart_file (:py:func:`.write_restart_file`)
    Method for writing restart information.
"""
from pyretis.inout.screen import print_to_screen
