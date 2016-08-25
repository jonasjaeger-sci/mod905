# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""This package contains functions for input/output for the analysis.

The functions defined here will typically run the analysis on the
given input and write outputs, typically this will be plots and simple
text files.

Package structure
-----------------

Modules
~~~~~~~

analysisio.py
    Methods that will output results from the analysis functions.
    The methods defined here can also be used to run an analysis on
    output files from pyretis.

analysistxt.py
    Methods and classes for text based output from the analysis.

__init__.py
    This file, handles imports for pyretis.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

analyse_file
    Method to analyse a file.

run_analysis_files
    Method to analyse simulation data in output files. This is a
    post-processing step.
"""
from __future__ import absolute_import
from .analysisio import analyse_file, run_analysis_files
