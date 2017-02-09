# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""The sub-package handles input and output for pyretis.

This package is intended for creating various forms of output
from the pyretis program. It include writers for simple text based
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

settings (:py:mod:`pyretis.inout.settings`)
    Handle input and output settings.

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

create_output_tasks (:py:func:`.create_output_tasks`)
    A function to create output tasks for a simulation.

generate_report (:py:func:`.generate_report`)
    A function to generate reports from analysis output(s).
"""
