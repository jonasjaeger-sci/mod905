# -*- coding: utf-8 -*-
"""This file contains methods input/output for the analysis.

The methods defined here will typically run the analysis on the
given input and write outputs, typically this will be plots and simple
text files.

Important functions defined here:

- run_md_flux_analysis: Method to run the MD flux analysis on a set
  of files. It will plot the results and generate a MD-flux report.
"""
from __future__ import absolute_import
from .analysisio import run_md_flux_analysis, analyse_file
