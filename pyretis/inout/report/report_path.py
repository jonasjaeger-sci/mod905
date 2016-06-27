# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""Functions for generating reports.

The reports are useful for displaying results from the analysis.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

generate_report_tis
    Generate a report for the over-all results from a TIS simulation.

generate_report_tis_path
    Generate a report for a single TIS simulation.

generate_report_retis
    Generate a report for the over-all results from a RETIS simulation.
"""
from __future__ import absolute_import
import logging
from pyretis.inout.report.markup import (generate_rst_table,
                                         generate_latex_table)
from pyretis.inout.common import apply_format
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['generate_report_tis', 'generate_report_tis_path',
           'generate_report_retis']


def format_number(number, minf, maxf, fmtf='{0:<16.9f}', fmte='{0:<16.9e}'):
    """Method to format a number based on it's size.

    Parameters
    ----------
    number : float
        The number to format.
    minf : float
        If the number is smaller than `minf` then apply the
        format with scientific notation.
    maxf : float
        If the number is greater than `maxf` then apply the
        format with scientific notation.
    fmtf : string
        Format to use for floats.
    fmte : string
        Format to use for scientific notation.

    Returns
    -------
    out : string
        The formatted number."""
    if minf <= number <= maxf:
        return fmtf.format(number)
    else:
        return fmte.format(number)


def generate_report_tis_path(analysis, output='rst'):
    """Generate a report for a single TIS simulation.

    Parameters
    ----------
    analysis : dict
        This is the output from the analysis.
    output : string, optional
        This is the desired output format. It must match one of the
        formats defined in `.report._TEMPLATES`. Default is 'rst'
        (reStructuredText).

    Returns
    -------
    out[0] : string
        The generated report in the desired format.
    out[1] : string
        The file extension (i.e. file type) for the generated report.
    """
    result = analysis['pathensemble']
    report = {'ensemble': result['out']['ensemble'],
              'figures': {},
              'tables': {'interfaces': None,
                         'probability': None,
                         'path': None,
                         'efficiency': None}}
    # Get figures (if any):
    report['figures'] = _get_path_figures(result['figures'])
    # Create tables
    results = [result]
    tables = report['tables']
    tables['interfaces'] = _table_interface(results, fmt=output)[1]
    tables['probability'] = _table_probability(results, fmt=output)[1]
    tables['path'] = _table_path(results, fmt=output)[1]
    tables['efficiency'] = _table_efficiencies(results, fmt=output)[1]
    return report


def generate_report_tis(analysis, output='rst'):
    """Generate a report for the over-all results from a TIS simulation.

    Parameters
    ----------
    analysis : dict
        This is the output from the analysis.
    output : string, optional
        This is the desired output format. It must match one of the
        formats defined in `.report._TEMPLATES`. Default is 'rst'
        (reStructuredText).

    Returns
    -------
    out[0] : string
        The generated report in the desired format.
    out[1] : string
        The file extension (i.e. file type) for the generated report.
    """
    report = {'figures': {'tis': [],
                          'matched': None},
              'tables': {'interfaces': None,
                         'probability': None,
                         'path': None,
                         'efficiency': None},
              'numbers': {'pcross': None, 'perr': None, 'simt': None,
                          'teff': None, 'opteff': None}}
    results = analysis['pathensemble']
    figures = report['figures']
    # Add figures:
    for result in results:
        figures['tis'].append(_get_path_figures(result['figures']))
    # Get matched result:
    matched_fig = analysis['matched']['figures']
    matched_out = analysis['matched']['out']
    figures['matched'] = matched_fig.get('matched-probability', None)
    figures['total'] = matched_fig.get('total-probability', None)
    # Get numbers:
    report['numbers']['pcross'] = format_number(matched_out['prob'], 0.1, 1)
    report['numbers']['perr'] = format_number(matched_out['relerror'] * 100,
                                              0.1, 100)
    report['numbers']['simt'] = format_number(matched_out['simtime'],
                                              0.1, 100)
    report['numbers']['teff'] = format_number(matched_out['eff'], 0.1, 100)
    report['numbers']['opteff'] = format_number(matched_out['opteff'], 0.1,
                                                100)
    # Get tables:
    tables = report['tables']
    tables['interfaces'] = _table_interface(results, fmt=output)[1]
    tables['probability'] = _table_probability(results, fmt=output)[1]
    tables['path'] = _table_path(results, fmt=output)[1]
    tables['efficiency'] = _table_efficiencies(results, fmt=output)[1]
    return report


def generate_report_retis(analysis, output='rst'):
    """Generate a report for the over-all results from a RETIS simulation.

    Parameters
    ----------
    analysis : dict
        This is the output from the analysis.
    output : string, optional
        This is the desired output format. It must match one of the
        formats defined in `.report._TEMPLATES`. Default is 'rst'
        (reStructuredText).

    Returns
    -------
    out[0] : string
        The generated report in the desired format.
    out[1] : string
        The file extension (i.e. file type) for the generated report.
    """
    report = {'figures': {'tis': [],
                          'matched': None},
              'tables': {'interfaces': None,
                         'interfaces0': None,
                         'path0': None,
                         'probability': None,
                         'path': None,
                         'efficiency': None},
              'numbers': {'pcross': None, 'perr': None, 'simt': None,
                          'teff': None, 'opteff': None, 'flux': None,
                          'fluxc': None, 'flux-err': None, 'fluxc-err': None},
              'text': {'flux-unit': None, 'fluxc-unit': None}}
    results = analysis['pathensemble']
    result0 = analysis['pathensemble0']
    figures = report['figures']
    # Add figures:
    for result in results:
        figures['tis'].append(_get_path_figures(result['figures']))
    figures['path0'] = _get_path_figures(result0['figures'])
    # Get matched result:
    matched_fig = analysis['matched']['figures']
    matched_out = analysis['matched']['out']
    figures['matched'] = matched_fig.get('matched-probability', None)
    figures['total'] = matched_fig.get('total-probability', None)
    # Get numbers:
    report['numbers']['pcross'] = format_number(matched_out['prob'], 0.1, 1)
    report['numbers']['perr'] = format_number(matched_out['relerror'] * 100,
                                              0.1, 100)
    report['numbers']['flux'] = format_number(analysis['flux']['value'],
                                              0.1, 100)
    report['numbers']['flux-err'] = format_number(analysis['flux']['error'],
                                                  0.1, 100)
    report['text']['flux-unit'] = analysis['flux']['unit']
    report['numbers']['fluxc'] = format_number(analysis['fluxc']['value'],
                                               0.1, 100)
    report['numbers']['fluxc-err'] = format_number(analysis['fluxc']['error'],
                                                   0.1, 100)
    report['text']['fluxc-unit'] = analysis['fluxc']['unit']
    report['numbers']['simt'] = format_number(matched_out['simtime'],
                                              0.1, 100)
    report['numbers']['teff'] = format_number(matched_out['eff'], 0.1, 100)
    report['numbers']['opteff'] = format_number(matched_out['opteff'], 0.1,
                                                100)
    # Get tables:
    tables = report['tables']
    tables['interfaces0'] = _table_interface0([result0], fmt=output)[1]
    tables['path0'] = _table_path([result0], fmt=output)[1]
    tables['interfaces'] = _table_interface(results, fmt=output)[1]
    tables['probability'] = _table_probability(results, fmt=output)[1]
    tables['path'] = _table_path(results, fmt=output)[1]
    tables['efficiency'] = _table_efficiencies(results, fmt=output)[1]
    return report


def generate_report_retis0(analysis, output='txt'):
    """Generate a report for [0^-] in a RETIS simulation.

    This method is primary intended for displaying results on the
    screen during the analysis.

    Parameters
    ----------
    analysis : dict
        This is the output from the analysis.
    output : string, optional
        This is the desired output format. It must match one of the
        formats defined in `.report._TEMPLATES`. Default is 'rst'
        (reStructuredText).

    Returns
    -------
    out[0] : string
        The generated report in the desired format.
    out[1] : string
        The file extension (i.e. file type) for the generated report.
    """
    if output != 'txt':
        msg = ('Report for [0^-] is only indended as "txt"'
               '\nOutput format "{}" ignored'.format(output))
        logger.warning(msg)
        output = 'txt'
    result = analysis['pathensemble']
    report = {'ensemble': result['out']['ensemble']}
    # Create tables
    report['tables'] = {'interfaces0': _table_interface0([result],
                                                         fmt=output)[1],
                        'path0': _table_path([result], fmt=output)[1]}
    return report


def _table_interface(results, fmt='rst'):
    """Generate the table for the interfaces.

    This table will display the location of the different interfaces.

    Parameters
    ----------
    results : list of dicts
        These are the results from the analysis.
    fmt : string, optional
        Determines if we create reStructuredText ('rst') or
        latex ('tex').

    Returns
    -------
    out[0] : list of strings
        These are the rows of the table.
    out[1] : string
        This is a string in the desired format which represents
        the table.
    """
    table = []
    for result in results:
        row = ['{:^8s}'.format(result['out']['ensemble'])]
        interf = result['out']['interfaces']
        row.append(apply_format(interf[0], '{:^8.4f}'))
        row.append(apply_format(interf[1], '{:^8.4f}'))
        row.append(apply_format(interf[2], '{:^8.4f}'))
        detect = result['out']['detect']
        if detect is None:
            row.append('')
        else:
            row.append(apply_format(detect, '{:^8.4f}'))
        table.append(row)
    if fmt in ['tex', 'latex']:
        table_str = generate_latex_table(table, 'Interfaces',
                                         ['Ensemble', 'Left', 'Middle',
                                          'Right', 'Detect'],
                                         fixnum={0, 1, 2, 3, 4})
    else:
        table_str = generate_rst_table(table, 'Interfaces',
                                       ['Ensemble', 'Left', 'Middle',
                                        'Right', 'Detect'])
    table_txt = '\n'.join(table_str)
    return table, table_txt


def _table_interface0(results, fmt='rst'):
    """Generate the table for the [0^-] ensemble.

    This table will display the location of the different interfaces.

    Parameters
    ----------
    results : list of dicts
        These are the results from the analysis.
    fmt : string, optional
        Determines if we create reStructuredText ('rst') or
        latex ('tex').

    Returns
    -------
    out[0] : list of strings
        These are the rows of the table.
    out[1] : string
        This is a string in the desired format which represents
        the table.
    """
    table = []
    for result in results:
        row = ['{:^8s}'.format(result['out']['ensemble'])]
        interf = result['out']['interfaces']
        row.append(apply_format(interf[0], '{:^8.4f}'))
        row.append(apply_format(interf[1], '{:^8.4f}'))
        row.append(apply_format(interf[2], '{:^8.4f}'))
        table.append(row)
    if fmt in ['tex', 'latex']:
        table_str = generate_latex_table(table, 'Interfaces',
                                         ['Ensemble', 'Left', 'Middle',
                                          'Right'],
                                         fixnum={0, 1, 2, 3})
    else:
        table_str = generate_rst_table(table, 'Interfaces',
                                       ['Ensemble', 'Left', 'Middle',
                                        'Right'])
    table_txt = '\n'.join(table_str)
    return table, table_txt


def _table_probability(results, fmt='rst'):
    """Generate the table for the probabilities.

    This table will display the crossing probabilities with
    uncertainties.

    Parameters
    ----------
    results : list of dicts
        The dictionaries are the results obtained from the analysis.
    fmt : string, optional
        Determines if we create reStructuredText ('rst') or
        latex ('tex').

    Returns
    -------
    out[0] : list of strings
        These are the rows of the table.
    out[1] : string
        This is a string in reStructuredText format which represents
        the table.
    """
    table = []
    for result in results:
        row = ['{:^8s}'.format(result['out']['ensemble'])]
        row.append(apply_format(result['out']['prun'][-1], '{:^10.6f}'))
        row.append(apply_format(result['out']['blockerror'][2], '{:^10.6f}'))
        row.append(apply_format(result['out']['blockerror'][4] * 100,
                                '{:^10.6f}'))
        table.append(row)
    if fmt in ['tex', 'latex']:
        table_str = generate_latex_table(table, r'Probabilities',
                                         [r'Ensemble', r'$P_\text{cross}$',
                                          r'Error', r'Rel. error (\%)'],
                                         fixnum={0, 1, 2, 3})
    else:
        table_str = generate_rst_table(table, r'Probabilities',
                                       [r'Ensemble', r'Pcross', r'Error',
                                        r'Rel. error (%)'])
    table_txt = '\n'.join(table_str)
    return table, table_txt


def _table_path(results, fmt='rst'):
    """Generate the table for the path lengths.

    This table will display the path lengths and also show the ratio of
    path lengths for all paths and accepted paths.

    Parameters
    ----------
    results : list of dicts
        The dictionaries are the results obtained from the analysis.
    fmt : string, optional
        Determines if we create reStructuredText ('rst') or
        latex ('tex').

    Returns
    -------
    out[0] : list of strings
        These are the rows of the table.
    out[1] : string
        This is a string in reStructuredText format which represents
        the table.
    """
    table = []
    for result in results:
        row = ['{:^8s}'.format(result['out']['ensemble'])]
        hist1 = result['out']['pathlength'][0]
        hist2 = result['out']['pathlength'][1]
        row.append(apply_format(hist1[2][0], '{:^10.6f}'))
        row.append(apply_format(hist2[2][0], '{:^10.6f}'))
        row.append(apply_format(hist2[2][0] / hist1[2][0], '{:^10.6f}'))
        table.append(row)
    if fmt in ['tex', 'latex']:
        table_str = generate_latex_table(table, 'Path lengths',
                                         ['Ensemble', 'Accepted', 'All',
                                          'All/Accepted'],
                                         fixnum={0, 1, 2, 3})
    else:
        table_str = generate_rst_table(table, 'Path lengths',
                                       ['Ensemble', 'Accepted', 'All',
                                        'All/Accepted'])
    table_txt = '\n'.join(table_str)
    return table, table_txt


def _table_efficiencies(results, fmt='rst'):
    """Generate table for efficiencies.

    This table will display results for the efficiencies, acceptance
    ratios and correlation.

    Parameters
    ----------
    results : list of dicts
        The dictionaries are the results obtained from the analysis.
    fmt : string, optional
        Determines if we create reStructuredText ('rst') or
        latex ('tex').

    Returns
    -------
    out[0] : list of strings
        These are the rows of the table.
    out[1] : string
        This is a string in reStructuredText format which represents
        the table.
    """
    table = []
    for result in results:
        row = ['{:^8s}'.format(result['out']['ensemble'])]
        row.append(apply_format(result['out']['tis-cycles'], '{:^10.0f}'))
        row.append(apply_format(result['out']['efficiency'][1], '{:^10.6f}'))
        row.append(apply_format(result['out']['efficiency'][0], '{:^10.6f}'))
        row.append(apply_format(result['out']['blockerror'][6], '{:^10.6f}'))
        row.append(apply_format(result['out']['efficiency'][2], '{:^10.6f}'))
        table.append(row)
    if fmt in ['tex', 'latex']:
        table_str = generate_latex_table(table, 'Efficiency',
                                         ['Ensemble', 'TIS cycles',
                                          'Tot sim.', 'Acceptance ratio',
                                          'Correlation', 'Efficiency'],
                                         fixnum={0, 1, 2, 3, 4, 5})
    else:
        table_str = generate_rst_table(table, 'Efficiency',
                                       ['Ensemble', 'TIS cycles', 'Tot sim.',
                                        'Acceptance ratio', 'Correlation',
                                        'Efficiency'])
    table_txt = '\n'.join(table_str)
    return table, table_txt


def _get_path_figures(figures):
    """Return path figures from a dict of figures.

    This method extracts figures from results and make them avaiable
    to the report.

    Paramters
    ---------
    figures : dict
        The figures generated by the analysis.

    Returns
    -------
    path_figures : dict
        A dict which can be used in the report.
    """
    path_figures = {}
    for fig in set(('pcross', 'prun', 'perror', 'lpath',
                    'shoots', 'shoots_scaled')):
        for key in figures:
            if key.endswith(fig):
                path_figures[fig] = figures[key]
    return path_figures
