# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""This package contains methods for generating reports.

The reports will typically summarize the results from different
analysis and present it as a text file, pdf or web-page.

Package structure
-----------------

Modules
~~~~~~~

__init__.py
    This file, handles imports for pyretis and defines a method for
    writing a report to a file.

markup.py
    This module defines some methods for generating simple tables and
    formatting numbers for rst and latex.

report_md.py
    This module defines the molecular dynamics reports. Specifically
    it defines the report that is made based on results from a MD Flux
    simulations.

report_path.py
    This module defines the reports for path simulations like TIS and
    RETIS.

report.py
    General methods for generating reports.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

write_report
    Method for writing a report to file.

generate_report
    Method for generating reports.


Folders
~~~~~~~

templates
    A folder containing templates for generating reports.
"""
from __future__ import absolute_import
from .report import generate_report
from pyretis.inout.common import name_file, REPORTFILES


def write_report(report_txt, report_type, ext, path=None):
    """Write a generated report to a given file.

    Parameters
    ----------
    report_txt : string
        This is the generated report as a string
    report_type : string
        Identifier for the report we are writing
    ext : string
        Extension for the file to write
    path : string
        A directory to use for saving the report to.

    Returns
    -------
    out : string
        The name of the file written.
    """
    outfile = name_file(REPORTFILES[report_type], ext, path=path)
    with open(outfile, 'wt') as report_fh:
        try:  # will work in python 3
            report_fh.write(report_txt)
        except UnicodeEncodeError:  # for python 2
            report_fh.write(report_txt.encode('utf-8'))
    return outfile
