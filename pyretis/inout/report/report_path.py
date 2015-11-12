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
                                         latexify_number,
                                         remove_extensions, generate_report)


__all__ = ['generate_report_tis', 'generate_report_tis_path']


def generate_report_tis_path(path_ensemble, analysis, output='rst',
                             template=None):
    """Generate a report for a single TIS simulation.

    Parameters
    ----------
    analysis : dict
        This is the output (and some input) for the analysis. The keys are:
        'tis' : dict with the results from analysing path ensembles
        'tis-fig' : list of corresponding figures (to 'tis')
        'matched' : results from the matching of probability
        'matched-fig' : the figure corresponding to 'matched'
        'detect' : locations of the interfaces used for detection
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
    # get template and generate:
    output, template, path = get_template(output, 'TIS_PATH',
                                          template=template)
    report = {'version': VERSION,
              'program': PROGRAM_NAME,
              'ensemble': path_ensemble.ensemble,
              'table_int': None,
              'table_prob': None,
              'table_path': None,
              'table_eff': None}
    # get the efficiency results:
    report['table_int'] = _table_interface([path_ensemble],
                                           [analysis['detect']],
                                           fmt=output)[1]
    report['table_prob'] = _table_probability([path_ensemble],
                                              [analysis], fmt=output)[1]
    report['table_path'] = _table_path([path_ensemble],
                                       [analysis], fmt=output)[1]
    report['table_eff'] = _table_efficiencies([path_ensemble],
                                              [analysis], fmt=output)[1]
    if output in ['latex', 'tex']:
        pass
        #for fig in ['figures', 'totalfig']:
        #    report[fig] = remove_extensions(report[fig])
    return generate_report(report, output, template, path)


def generate_report_tis(path_ensembles, analysis, output='rst',
                        template=None):
    """Generate a report for the over-all results from a TIS simulation.

    Parameters
    ----------
    analysis : dict
        This is the output (and some input) for the analysis. The keys are:
        'tis' : dict with the results from analysing path ensembles
        'tis-fig' : list of corresponding figures (to 'tis')
        'matched' : results from the matching of probability
        'matched-fig' : the figure corresponding to 'matched'
        'detect' : locations of the interfaces used for detection
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
    # get template and generate:
    output, template, path = get_template(output, 'TIS', template=template)
    report = {'version': VERSION,
              'program': PROGRAM_NAME,
              'figures': analysis.get('tis-fig', None),
              'totalfig': analysis.get('matched-fig', None),
              'table_int': None, 'table_prob': None,
              'table_path': None, 'table_eff': None,
              'pcross': None, 'perr': None, 'pcross_simt': None,
              'pcross_teff': None, 'pcross_opteff': None}
    # get the efficiency results:
    report['pcross'] = '{0:16.9e}'.format(analysis['matched']['prob'])

    if analysis['matched']['relerror'] > 0.01:
        report['perr'] = '{0:16.9f}'.format(analysis['matched']['relerror'] *
                                            100)
    else:
        report['perr'] = '{0:16.9e}'.format(analysis['matched']['relerror'] *
                                            100)
    report['pcross_simt'] = '{0:16.9e}'.format(analysis['matched']['simtime'])
    report['pcross_teff'] = '{0:16.9e}'.format(analysis['matched']['eff'])
    report['pcross_opteff'] = '{0:16.9e}'.format(analysis['matched']['opteff'])

    _, report['table_int'] = _table_interface(path_ensembles,
                                              analysis['detect'], fmt=output)
    _, report['table_prob'] = _table_probability(path_ensembles,
                                                 analysis['tis'], fmt=output)
    _, report['table_path'] = _table_path(path_ensembles,
                                          analysis['tis'], fmt=output)
    _, report['table_eff'] = _table_efficiencies(path_ensembles,
                                                 analysis['tis'], fmt=output)
    if output in ['latex', 'tex']:
        for fig in ['figures', 'totalfig']:
            report[fig] = remove_extensions(report[fig])
        for key in ['pcross', 'perr', 'pcross_simt', 'pcross_teff',
                    'pcross_opteff']:
            report[key] = latexify_number(report[key])
    return generate_report(report, output, template, path)


def _table_interface(path_ensembles, detect, fmt='rst'):
    """
    Generate the table for the interfaces.

    This table will display the location of the different
    interfaces.

    Parameters
    ----------
    path_ensembles : list of objects like `pyretis.core.path.PathEnsemble`.
        These are the path ensembles we have analyzed.
    detect : list of floats
        These are the detect interfaces used in the analysis.
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
    table = []
    for path_e, idet in zip(path_ensembles, detect):
        row = ['{:^8s}'.format(path_e.ensemble)]
        row.append(apply_format(path_e.interfaces[0], '{:^8.4f}'))
        row.append(apply_format(path_e.interfaces[1], '{:^8.4f}'))
        row.append(apply_format(path_e.interfaces[2], '{:^8.4f}'))
        row.append(apply_format(idet, '{:^8.4f}'))
        table.append(row)
    if fmt in ['tex', 'latex']:
        table_str = generate_latex_table(table, 'Interfaces',
                                         ['Ensemble', 'Left', 'Middle',
                                          'Right', 'Detect'],
                                         fixnum=set([1, 2, 3, 4]))
    else:
        table_str = generate_rst_table(table, 'Interfaces',
                                       ['Ensemble', 'Left', 'Middle',
                                        'Right', 'Detect'])
    table_str = '\n'.join(table_str)
    return table, table_str


def _table_probability(path_ensembles, results, fmt='rst'):
    """
    Generate the table for the probabilities.

    This table will display the crossing probabilities with
    uncertainties.

    Parameters
    ----------
    path_ensembles : list of objects like `pyretis.core.pathP.athEnsemble`.
        These are the path ensembles we have analyzed.
    results : list of dicts
        The dictionaries are the results obtained from the analysis.
    fmt : string, optional
        Determines if we create reStructuredText ('rst') or latex ('tex').

    Returns
    -------
    out[0] : list of strings
        These are the rows of the table.
    out[1] : string
        This is a string in reStrucutredText format which represents
        the table.
    """
    table = []
    for path_e, result in zip(path_ensembles, results):
        row = ['{:^8s}'.format(path_e.ensemble)]
        row.append(apply_format(result['prun'][-1], '{:^10.6f}'))
        row.append(apply_format(result['blockerror'][2], '{:^10.6f}'))
        row.append(apply_format(result['blockerror'][4] * 100, '{:^10.6f}'))
        table.append(row)
    if fmt in ['tex', 'latex']:
        table_str = generate_latex_table(table, r'Probabilities',
                                         [r'Ensemble', r'$P_\text{cross}$',
                                          r'Error', r'Rel. error (\%)'],
                                         fixnum=set([1, 2, 3]))
    else:
        table_str = generate_rst_table(table, r'Probabilities',
                                       [r'Ensemble', r'Pcross', r'Error',
                                        r'Rel. error (%)'])
    table_str = '\n'.join(table_str)
    return table, table_str


def _table_path(path_ensembles, results, fmt='rst'):
    """
    Generate the table for the path lengths.

    This table will display the path lengths and also show the ratio of
    path lengths for all paths and accepted paths.

    Parameters
    ----------
    path_ensembles : list of objects like `pyretis.core.path.PathEnsemble`.
        These are the path ensembles we have analyzed.
    results : list of dicts
        The dictionaries are the results obtained from the analysis.
    fmt : string, optional
        Determines if we create reStructuredText ('rst') or latex ('tex').

    Returns
    -------
    out[0] : list of strings
        These are the rows of the table.
    out[1] : string
        This is a string in reStrucutredText format which represents
        the table.
    """
    table = []
    for path_e, result in zip(path_ensembles, results):
        row = ['{:^8s}'.format(path_e.ensemble)]
        hist1 = result['pathlength'][0]
        hist2 = result['pathlength'][1]
        row.append(apply_format(hist1[2][0], '{:^10.6f}'))
        row.append(apply_format(hist2[2][0], '{:^10.6f}'))
        row.append(apply_format(hist2[2][0] / hist1[2][0], '{:^10.6f}'))
        table.append(row)
    if fmt in ['tex', 'latex']:
        table_str = generate_latex_table(table, 'Path lengths',
                                         ['Ensemble', 'Accepted', 'All',
                                          'All/Accepted'],
                                         fixnum=set([1, 2, 3]))
    else:
        table_str = generate_rst_table(table, 'Path lengths',
                                       ['Ensemble', 'Accepted', 'All',
                                        'All/Accepted'])
    table_str = '\n'.join(table_str)
    return table, table_str


def _table_efficiencies(path_ensembles, results, fmt='rst'):
    """
    Generate table for efficiencies.

    This table will display results for the efficiencies, acceptance
    ratios and correlation.

    Parameters
    ----------
    path_ensembles : list of objects like `pyretis.core.path.PathEnsemble`.
        These are the path ensembles we have analyzed.
    results : list of dicts
        The dictionaries are the results obtained from the analysis.
    fmt : string, optional
        Determines if we create reStructuredText ('rst') or latex ('tex').

    Returns
    -------
    out[0] : list of strings
        These are the rows of the table.
    out[1] : string
        This is a string in reStrucutredText format which represents
        the table.
    """
    table = []
    for path_e, result in zip(path_ensembles, results):
        row = ['{:^8s}'.format(path_e.ensemble)]
        row.append(apply_format(result['tis-cycles'], '{:^10.0f}'))
        row.append(apply_format(result['efficiency'][1], '{:^10.6f}'))
        row.append(apply_format(result['efficiency'][0], '{:^10.6f}'))
        row.append(apply_format(result['blockerror'][6], '{:^10.6f}'))
        row.append(apply_format(result['efficiency'][2], '{:^10.6f}'))
        table.append(row)
    if fmt in ['tex', 'latex']:
        table_str = generate_latex_table(table, 'Efficiency',
                                         ['Ensemble', 'TIS cycles',
                                          'Tot sim.', 'Acceptance ratio',
                                          'Correlation', 'Efficiency'],
                                         fixnum=set([1, 2, 3, 4, 5]))
    else:
        table_str = generate_rst_table(table, 'Efficiency',
                                       ['Ensemble', 'TIS cycles', 'Tot sim.',
                                        'Acceptance ratio', 'Correlation',
                                        'Efficiency'])
    table_str = '\n'.join(table_str)
    return table, table_str
