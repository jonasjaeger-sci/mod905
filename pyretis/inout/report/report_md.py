# -*- coding: utf-8 -*-
"""Methods for generating reports.

The reports are useful for displaying results from the analysis.
"""
from __future__ import absolute_import
from pyretis import __version__ as VERSION
from pyretis import __program_name__ as PROGRAM_NAME
from pyretis.inout.report.report import (generate_rst_table,
                                         generate_latex_table,
                                         apply_format, get_template,
                                         remove_extensions, generate_report)


__all__ = ['generate_report_mdflux']


def generate_report_mdflux(analysis, output='rst', template=None):
    """Generate a report for a MD flux simulation.

    Parameters
    ----------
    analysis : dict
        This is the output from the analysis.
    output : string, optional
        This is the desired output format. It must match one of the
        formats defined in _TEMPLATES.
        Default is reStructuredText = 'rst'.
    template : string, optional
        This is the template file to use. The default is given
        by _TEMPLATES[output].

    Returns
    -------
    out[0] : string
        The generated report in the desired format.
    out[1] : string
        The file extension (i.e. file type) for the generated report.
    """
    output, template, path = get_template(output, 'MD', template=template)
    report = {'version': VERSION,
              'program': PROGRAM_NAME,
              'flux_figures': analysis.get('cross_figures', None),
              'energy_figures': analysis.get('energy_figures', None),
              'order_figures': analysis.get('order_figures', None)}
    # generate some tables:
    _, report['table_md_flux'] = _table_md_flux(analysis['cross'], fmt=output)
    _, report['table_md_cycles'] = _table_md_flux_cycles(analysis['cross'],
                                                         fmt=output)
    _, report['table_md_efficiency'] = _table_md_efficiency(analysis['cross'],
                                                            fmt=output)
    # check if we need some additional latexification:
    if output in ['latex', 'tex']:
        for fig in ['flux_figures', 'energy_figures', 'order_figures']:
            report[fig] = remove_extensions(report[fig])
    return generate_report(report, output, template, path)


def _table_md_efficiency(results, fmt='rst'):
    """
    Generate a table with  MD-flux results for efficiencies and correlations.

    Parameters
    ----------
    results : dict
        These are the results obtained in the ``analyse_flux`` method in
        the analysis package.
    fmt : string, optional
        Determines if we create reStructuredText ('rst') or latex ('tex').

    Returns
    -------
    out[0] : list of strings
        These are the rows of the table.
    out[1] : string
        This is a string in the desired format which represents
        the table.
    """
    # table for interfaces:
    table = []
    for i, _ in enumerate(results['interfaces']):
        pmd = results['pMD'][i]
        teff = results['teffMD'][i]
        corr = results['corrMD'][i]
        prel = results['1-p'][i]
        row = ['{:^10d}'.format(i + 1)]
        row.append(apply_format(pmd, '{:^10.6f}'))
        row.append(apply_format(prel, '{:^10.6f}'))
        row.append(apply_format(teff, '{:^10.6f}'))
        row.append(apply_format(corr, '{:^10.6f}'))
        table.append(row)

    if fmt in ['tex', 'latex']:
        table_str = generate_latex_table(table, 'Efficiency',
                                         ['Interface',
                                          r'$p_\text{MD}$',
                                          r'$\frac{1-p}{p}$',
                                          'Efficiency time', 'Correlation'],
                                         fixnum=set([1, 2, 3, 4]))
    elif fmt in ['txt']:
        table_str = generate_rst_table(table, 'Efficiency',
                                       ['Interface',
                                        'p_MD',
                                        '(1-p_MD)/p_MD',
                                        'Efficiency time', 'Correlation'])
    else:
        table_str = generate_rst_table(table, 'Efficiency',
                                       ['Interface',
                                        r':math:`p_\text{MD}`',
                                        r':math:`\frac{1-p}{p}`',
                                        'Efficiency time', 'Correlation'])
    table_str = '\n'.join(table_str)
    return table, table_str


def _table_md_flux_cycles(results, fmt='rst'):
    """
    Generate the table for the MD-flux results for cycle numbers.

    The table will display the number of steps in state A, state B,
    overall state A and B and total number of MD cycles.

    Parameters
    ----------
    results : dict
        These are the results obtained in the ``analyse_flux`` method in
        the analysis package.
    fmt : string, optional
        Determines if we create reStructuredText ('rst') or latex ('tex').

    Returns
    -------
    out[0] : list of strings
        These are the rows of the table.
    out[1] : string
        This is a string in the desired format which represents
        the table.
    """
    # table for interfaces:
    table = []
    table.append(['A', '{:8d}'.format(results['times']['A'])])
    table.append(['B', '{:8d}'.format(results['times']['B'])])
    table.append(['overall A', '{:8d}'.format(results['times']['OA'])])
    table.append(['overall B', '{:8d}'.format(results['times']['OB'])])
    table.append(['Total cycles', '{:8d}'.format(results['totalcycle'])])
    if fmt in ['tex', 'latex']:
        table_str = generate_latex_table(table, 'Cycles spent in state',
                                         ['State', 'Cycles'],
                                         fixnum=set([2]))
    else:
        table_str = generate_rst_table(table, 'Cycles spent in state',
                                       ['State', 'Cycles'])
    table_str = '\n'.join(table_str)
    return table, table_str


def _table_md_flux(results, fmt='rst'):
    """
    Generate the table for the MD-flux results.

    Parameters
    ----------
    results : dict
        These are the results obtained in the ``analyse_flux`` method in
        the analysis package.
    fmt : string, optional
        Determines if we create reStructuredText ('rst') or latex ('tex').

    Returns
    -------
    out[0] : list of strings
        These are the rows of the table.
    out[1] : string
        This is a string in the desired format which represents
        the table.
    """
    # table for interfaces:
    table = []
    for i, idet in enumerate(results['interfaces']):
        flux = results['runflux'][i][-1]
        error = results['errflux'][i][2]
        relerror = results['errflux'][i][4]
        row = ['{:^4d}'.format(i + 1)]
        row.append(apply_format(idet, '{:^8.4f}'))
        row.append(apply_format(flux, '{:^10.6f}'))
        row.append(apply_format(error, '{:^10.6f}'))
        row.append(apply_format(relerror, '{:^10.6f}'))
        row.append('{:^8d}'.format(results['ncross'][i]))
        row.append('{:^8d}'.format(results['neffcross'][i]))
        row.append(apply_format(results['neffc/nc'][i], '{:^10.6f}'))
        row.append(apply_format(results['cross_time'][i], '{:^10.6f}'))
        table.append(row)
    if fmt in ['tex', 'latex']:
        table_str = generate_latex_table(table, 'Flux for interfaces',
                                         ['Int.', 'Position', 'Flux / units',
                                          'Error', 'Rel. error', 'Ncross',
                                          'Neffcross', 'Neffcross/Ncross',
                                          'Steps per cross'],
                                         fixnum=set([2, 3, 4, 5, 6, 7, 8]))
    else:
        table_str = generate_rst_table(table, 'Flux for interfaces',
                                       ['Int.', 'Position', 'Flux / units',
                                        'Error', 'Rel. error', 'Ncross',
                                        'Neffcross', 'Neffcross/Ncross',
                                        'Steps per cross'])
    table_str = '\n'.join(table_str)
    return table, table_str
