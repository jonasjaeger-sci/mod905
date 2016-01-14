# -*- coding: utf-8 -*-
"""This package contains functions for generating reports.

The reports will typically summarize the results from different
analysis and present it as a text file, pdf or web-page.

Important functions defined here:

- write_report: A function to write a report to file.

- generate_report: A function for generating reports.


Folders:

- templates: A folder containing templates for generating reports.
"""
from __future__ import absolute_import
from .report import generate_report
from pyretis.inout.common import REPORTFILES


def write_report(report, report_type, ext):
    """Write a generated report to a given file.

    Parameters
    ----------
    report : string
        This is the generated report as a string
    report_type : string
        Identifier for the report we are writing
    ext : string
        Extension for the file to write
    """
    outfile = REPORTFILES[report_type].format(ext)
    with open(outfile, 'wt') as report_fh:
        try:  # will work in python 3
            report_fh.write(report)
        except UnicodeEncodeError:  # for python 2
            report_fh.write(report.encode('utf-8'))
