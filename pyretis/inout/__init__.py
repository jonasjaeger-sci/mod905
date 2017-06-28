# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""The sub-package handles input and output for PyRETIS.

This package is intended for creating various forms of output
from the PyRETIS program. It include writers for simple text based
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

settings.py (:py:mod:`pyretis.inout.settings`)
    A module which handles the reading/writing of settings.

restart.py (:py:mod:`pyretis.inout.restart`)
    A module which handles restart reading/writing.

Sub-packages
~~~~~~~~~~~~

analysisio (:py:mod:`pyretis.inout.analysisio`)
    Handles the input and output needed for analysis.

plotting (:py:mod:`pyretis.inout.plotting`)
    Handles plotting. It defines simple things like colors etc.
    for plotting. It also defines functions which can be used for
    specific plotting by the analysis and report tools.

report (:py:mod:`pyretis.inout.report`)
    Generate reports with results from simulations.

setup (:py:mod:`pyretis.inout.setup`)
    Handles set-up of simulations etc. from user settings.

writers (:py:mod:`pyretis.inout.writers`)
    Handle formatting and presentation of text based output.

Important classes defined in this package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

CrossWriter (:py:class:`.CrossWriter`)
    A class for writing crossing data.

EnergyWriter (:py:class:`.EnergyWriter`)
    A class for writing energy data.

EnergyPathWriter (:py:class:`.EnergyPathWriter`)
    A class for writing out energy data for paths.

OrderWriter (:py:class:`.OrderWriter`)
    A class for writing order parameter data.

OrderPathWriter (:py:class:`.OrderPathWriter`)
    A class for writing out order parameter data for paths.

TrajWriter (:py:class:`.TrajWriter`)
    Generic class for writing trajectory output.

PathExtWriter (:py:class:`.PathExtWriter`)
    A class for writing external paths to file.

PathEnsembleWriter (:py:class:`.PathEnsembleWriter`)
    Class for writing path ensemble data.

TxtTable (:py:class:`.TxtTable`)
    Class for writing/create text based tables.

Important methods defined in this package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

create_engine (:py:func:`.create_engine`)
    Create an engine from input settings.

create_force_field (:py:func:`.create_force_field`)
    Create a force field from input settings.

create_orderparameter (:py:func:`.create_orderparameter`)
    Create an order parameter from input settings.

create_output_tasks (:py:func:`.create_output_tasks`)
    Create output tasks from input settings.

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
