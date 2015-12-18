# -*- coding: utf-8 -*-
"""Functions for generating reports.

The reports are useful for displaying results from the analysis.

Important functions defined here:

- generate_report_tis_path: Generate a report for a single TIS simulation.

- generate_report_tis: Generate a report for the over-all results from a
  TIS simulation.
"""
from __future__ import absolute_import
from pyretis.inout.report.markup import (generate_rst_table,
                                         generate_latex_table)
from pyretis.inout.common import apply_format


__all__ = ['generate_report_tis', 'generate_report_tis_path']


def generate_report_tis_path(analysis, output='rst'):
    """Generate a report for a single TIS simulation.

    Parameters
    ----------
    analysis : dict
        This is the output (and some input) for the analysis. The keys are:

        * `tis-fig`: list of corresponding figures (to 'tis')
        * `detect`: locations of the interfaces used for detection
        * `ensemble`: The name of the path ensemble we are reporting results
          for.
        * `interfaces`: list with the interfaces used for this path
          ensemble.
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
    path_ensemble = analysis['ensemble']
    interfaces = analysis['interfaces']
    report = {'ensemble': path_ensemble,
              'figures': {'tis': None},
              'tables': {'interfaces': None,
                         'probability': None,
                         'path': None,
                         'efficiency': None}}
    # Get figures (if any):
    report['figures']['tis'] = analysis.get('tis-fig', None)
    # Create tables
    report['tables']['interfaces'] = _table_interface([path_ensemble],
                                                      [interfaces],
                                                      [analysis['detect']],
                                                      fmt=output)[1]
    report['tables']['probability'] = _table_probability([path_ensemble],
                                                         [analysis],
                                                         fmt=output)[1]
    report['tables']['path'] = _table_path([path_ensemble],
                                           [analysis],
                                           fmt=output)[1]
    report['tables']['efficiency'] = _table_efficiencies([path_ensemble],
                                                         [analysis],
                                                         fmt=output)[1]
    return report


def generate_report_tis(analysis, output='rst'):
    """Generate a report for the over-all results from a TIS simulation.

    Parameters
    ----------
    analysis : dict
        This is the output (and some input!) for the analysis. The keys
        we make use of are:

        * `tis`: list of dicts with the results from analysing the path
          ensembles. `analysis['tis'][i]` contains the analysys results for
          path ensemble no. `i`.
        * `tis-fig`: list of corresponding figures (to 'tis')
        * `matched`: results from the matching of probability
        * `matched-fig`: the figure corresponding to 'matched'
        * `detect`: locations of the interfaces used for detection
        * `ensembles`: list of strings with the names of the path ensembles
          we are reporting results for.
        * `interfaces`: list of lists which give the interfaces for the
          different ensembles.
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
    path_ensembles = analysis['ensembles']
    interfaces = analysis['interfaces']
    report = {'figures': {'tis': None,
                          'tis-matched': None},
              'tables': {'interfaces': None,
                         'probability': None,
                         'path': None,
                         'efficiency': None},
              'numbers': {'pcross': None, 'perr': None, 'simt': None,
                          'teff': None, 'opteff': None}}
    # Get figures:
    report['figures']['tis'] = analysis.get('tis-fig', None)
    report['figures']['tis-matched'] = analysis.get('matched-fig', None)
    # Get numbers:
    fmte = '{0:<16.9e}'
    fmtf = '{0:<16.9f}'
    report['numbers']['pcross'] = fmte.format(analysis['matched']['prob'])
    scaled = analysis['matched']['relerror'] * 100
    if scaled > 1.0:
        report['numbers']['perr'] = fmtf.format(scaled)
    else:
        report['numbers']['perr'] = fmte.format(scaled)
    report['numbers']['simt'] = fmte.format(analysis['matched']['simtime'])
    report['numbers']['teff'] = fmte.format(analysis['matched']['eff'])
    report['numbers']['opteff'] = fmte.format(analysis['matched']['opteff'])
    # Get tables:
    report['tables']['interfaces'] = _table_interface(path_ensembles,
                                                      interfaces,
                                                      analysis['detect'],
                                                      fmt=output)[1]
    report['tables']['probability'] = _table_probability(path_ensembles,
                                                         analysis['tis'],
                                                         fmt=output)[1]
    report['tables']['path'] = _table_path(path_ensembles, analysis['tis'],
                                           fmt=output)[1]
    report['tables']['efficiency'] = _table_efficiencies(path_ensembles,
                                                         analysis['tis'],
                                                         fmt=output)[1]
    return report


def _table_interface(path_ensembles, interfaces, detect, fmt='rst'):
    """Generate the table for the interfaces.

    This table will display the location of the different interfaces.

    Parameters
    ----------
    path_ensembles : list of strings
        These are the path ensembles we have analyzed.
    interfaces : list of lists
        `interfaces[i]` are the interfaces used for `path_ensembles[i]`.
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
    for ensemble, interf, idet in zip(path_ensembles, interfaces, detect):
        row = ['{:^8s}'.format(ensemble)]
        row.append(apply_format(interf[0], '{:^8.4f}'))
        row.append(apply_format(interf[1], '{:^8.4f}'))
        row.append(apply_format(interf[2], '{:^8.4f}'))
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
    table_txt = '\n'.join(table_str)
    return table, table_txt


def _table_probability(path_ensembles, results, fmt='rst'):
    """Generate the table for the probabilities.

    This table will display the crossing probabilities with
    uncertainties.

    Parameters
    ----------
    path_ensembles : list of strings
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
    for ensemble, result in zip(path_ensembles, results):
        row = ['{:^8s}'.format(ensemble)]
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
    table_txt = '\n'.join(table_str)
    return table, table_txt


def _table_path(path_ensembles, results, fmt='rst'):
    """Generate the table for the path lengths.

    This table will display the path lengths and also show the ratio of
    path lengths for all paths and accepted paths.

    Parameters
    ----------
    path_ensembles : list of strings
        These are the path ensembles we have analyzed.
    interfaces : list of lists
        `interfaces[i]` are the interfaces used for `path_ensembles[i]`.
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
    for ensemble, result in zip(path_ensembles, results):
        row = ['{:^8s}'.format(ensemble)]
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
    table_txt = '\n'.join(table_str)
    return table, table_txt


def _table_efficiencies(path_ensembles, results, fmt='rst'):
    """Generate table for efficiencies.

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
    for ensemble, result in zip(path_ensembles, results):
        row = ['{:^8s}'.format(ensemble)]
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
    table_txt = '\n'.join(table_str)
    return table, table_txt
