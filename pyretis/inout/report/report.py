# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""General functions for generating reports.

This module contains some general functions for report generation. These
functions are used by the specific report generators to format the
reports.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

get_template
    Returns the template for a specific output format and report type.

render_report
    Render a report using a template and jinja2.

generate_report
    Generate a specific report from analysis output.
"""
from __future__ import absolute_import
import datetime
import logging
import os
# for converting rst to html and/or latex:
import docutils.core
from docutils.writers.html4css1 import Writer as HTMLWriter
from docutils.writers.html4css1 import HTMLTranslator
# for using templates
import jinja2
# pyretis imports:
from pyretis import __version__ as VERSION
from pyretis import __program_name__ as PROGRAM_NAME
from pyretis.inout.report.markup import latexify_number
from pyretis.inout.report.report_md import generate_report_mdflux
from pyretis.inout.report.report_path import (generate_report_retis,
                                              generate_report_retis0,
                                              generate_report_tis,
                                              generate_report_tis_path)
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['get_template', 'render_report', 'generate_report']


_DATE_FMT = '%d.%m.%Y %H:%M:%S'
# File names for pre-defined templates.
# - html is done via rst (i.e. there is no html template)
# - htm is assumed to be equal to html
# - tex is assumed to be equal to latex
_TEMPLATES = {'rst': 'report_{}.rst',
              'html': 'report_{}.rst',
              'htm': 'report_{}.rst',
              'latex': 'report_{}.tex',
              'tex': 'report_{}.tex',
              'txt': 'report_{}.txt'}

_TEMPLATE_NAMES = {'md-flux': 'mdflux',
                   'retis': 'retis',
                   'retis0': 'retis0',
                   'tis': 'tis',
                   'tis-single': 'tis_single'}

_REPORT_MAP = {'md-flux': generate_report_mdflux,
               'retis': generate_report_retis,
               'retis0': generate_report_retis0,
               'tis': generate_report_tis,
               'tis-single': generate_report_tis_path}
# Table for file extensions:
_EXT = {'rst': 'rst',
        'html': 'html',
        'htm': 'htm',  # in case some people prefer it
        'latex': 'tex',
        'tex': 'tex',
        'txt': 'txt'}


def _rst_to_html(rst):
    """Convert a reStrcuturedText string to simple HTML.

    Parameters
    ----------
    rst : string
        The string to convert.

    Returns
    -------
    out : string
        A HTML document corresponding to the input reStructuredText.
    """
    htmlwriter = HTMLWriter()
    htmlwriter.translator_class = HTMLTranslator
    override = {'output_encoding': 'unicode'}
    # custom css can be added by: 'stylesheet_path': '/path/to/style.css'
    html = docutils.core.publish_string(rst, writer=htmlwriter,
                                        settings_overrides=override)
    return html


def get_template(output, report_type, template=None):
    """Return the template to use for a specified output format.

    The output is one of the defined output types, for instance 'rst'
    for restrucutred text or 'latex' for latex. Different report types
    will have different templates and the report types must also be
    specified here.

    Parameters
    ----------
    output : string
        This string selects the output format for the template, i.e.,
        rst, html, latex, tex.
    template : string, optional
        The full path to the template to use. If not given/found, the
        defaults in _TEMPLATES will be used.
    report_type : string
        This is the type of report we are doing, e.g. TIS or MD.

    Returns
    -------
    out[1] : string
        File name of template to use.
    out[2] : string
        Path to the template to use.
    """
    if template is None or not os.path.isfile(template):
        # Use default template, this is located in the templates dir:
        path = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(path, 'templates')
        ltype = report_type.lower()
        template = _TEMPLATES[output].format(_TEMPLATE_NAMES[ltype])
        path_to_template = os.path.join(path, template)
        if not os.path.isfile(path_to_template):
            msg = 'Could not locate template "{}"!'.format(path_to_template)
            raise ValueError(msg)
    else:
        # user specified full path to template:
        path = os.path.dirname(template)
        template = os.path.basename(template)
    return template, path


def render_report(report, output, template, path):
    """This will render a report using a template and jinja2.

    The report is given as a dictionary which is used to fill in a
    template with jinja2. The template is given as string
    (a file name) with a path to the template. The output can also be
    specified here and this is only use to convert to HTML if that is
    the desired output.

    Parameters
    ----------
    report : dict
        This dict contains the data to be reported. It is assumed that
        this dict matches the specified template.
    output : string
        This is the desired output format. Here it's used only for
        generating HTML as this is done via rst.
    template : string
        This is the template to use (the file name).
    path :  string
        This is the template file to use (it's path).

    Returns
    -------
    out[0] : string
        The generated report in the desired format.
    out[1] : string
        The file extension (i.e. file type) for the generated report.

    Note
    ----
    The parameters `template` and `path` are typically obtained by a
    call to `get_template`.
    """
    env = jinja2.Environment(block_start_string='@{%',
                             block_end_string='%}@',
                             variable_start_string='@{{',
                             variable_end_string='}}@',
                             loader=jinja2.FileSystemLoader(path))
    # pylint: disable=maybe-no-member
    render = env.get_template(template).render(report)
    # pylint: enable=maybe-no-member
    if output == 'html':
        return _rst_to_html(render), _EXT[output]
    else:
        return render, _EXT[output]


def generate_report(report_type, analysis_results, output, template=None):
    """Generate a report of a given type with the given analysis results.

    Parameters
    ----------
    report_type : string
        Selects the kind of report we want.
    analysis_results : dict
        The results from running the analysis.
    output : string
        Output format for the report.
    template : string, optional
        The full path to the template to use. If not given/found, the
        defaults in _TEMPLATES will be used. This is handled by
        `get_template`.

    Returns
    -------
    out[0] : string
        This is the generated report in the desired format
    out[1] : string
        This is an extension which can be used when writing the report
        to a file.
    """
    report = {'version': VERSION,
              'program': PROGRAM_NAME,
              'date': datetime.datetime.now().strftime(_DATE_FMT),
              'figures': [], 'tables': [], 'numbers': []}
    try:
        generator = _REPORT_MAP[report_type]
    except KeyError:
        return None, None
    # Check if the output is a valid format
    if output not in _TEMPLATES:
        msg = 'Format {} not defined for {} report. Defaulting to rst'
        msg = msg.format(output, report_type)
        logger.warning(msg)
        output = 'rst'
    template, path = get_template(output, report_type, template=template)
    generated = generator(analysis_results, output=output)
    report.update(generated)
    # Remove white-space from numbers:
    for key in report['numbers']:
        report['numbers'][key] = report['numbers'][key].strip()
    if output in ('latex', 'tex', 'html', 'htm'):
        # Latexify numbers:
        for key in report['numbers']:
            report['numbers'][key] = latexify_number(report['numbers'][key])
    return render_report(report, output, template, path)
