# -*- coding: utf-8 -*-
"""This file contains methods for generating reports.

The reports will typically summarize the results from different
analysis and present it as a text file, pdf or web-page.

Important functions
-------------------

"""
from __future__ import absolute_import
import warnings
from pyretis import __version__ as VERSION
from pyretis import __program_name__ as PROGRAM_NAME
from .report import (get_template, render_report, _TEMPLATES,
                     remove_extensions, latexify_number)
from .report_md import generate_report_mdflux
from .report_path import generate_report_tis


def generate_report(report_type, analysis, output, template=None):
    """Generate a report of a given type with the given analysis results.

    Parameters
    ----------
    report_type : string
        Selects the kind of report we want.
    analysis : dict
        The results from running the analysis.
    output : string
        Output format for the report.
    """
    report = {'version': VERSION,
              'program': PROGRAM_NAME}
    # Check if the output is a valid format
    if output not in _TEMPLATES:
        msg = 'Format {} not defined for {} report. Defaulting to rst'
        warnings.warn(msg.format(output, report_type))
        output = 'rst'
    template, path = get_template(output, report_type, template=template)
    if report_type == 'mdflux':
        report.update(generate_report_mdflux(analysis, output))
    # Remove file extensions for figures and latexify numbers:
    if output in ('latex', 'tex'):
        for fig in report['figures']:
            report['figures'][fig] = remove_extensions(report['figures'][fig])
        for key in report['numbers']:
            report['numbers'][key] = latexify_number(report['numbers'][key])
    return render_report(report, output, template, path)
