# -*- coding: utf-8 -*-
"""
This file contains methods that will generate reports for displaying
the results from the pytismol program.
"""
from __future__ import absolute_import
from retis import __version__ as VERSION


__all__ = ['rst_generate_report']


def _rst_table_interface(path_ensembles, detect):
    """
    This will generate an table in reStrcuturedText which displays the
    different interfaces and their location. Used by the report generation.

    Parameters
    ----------
    path_ensembles : list of objects of type PathEnsemble
        These are the path ensembles we have analysed.
    detect : list of floats
        These are the detect interfaces used in the analysis.

    Returns
    -------
    out : string
        The table as a string in reStructuredText format.
    """
    hline = ['+----------+----------+----------+----------+----------+']
    header = ['+------------------------------------------------------+',
              '|Interfaces                                            |',
              '+----------+----------+----------+----------+----------+',
              '| Ensemble |   Left   |  Middle  |  Right   |  Detect  |']
    rows = []
    fmt = '| {0:^8s} | {1:^8.4f} | {2:^8.4f} | {3:^8.4f} | {4:^8.4f} |'
    for path_e, idet in zip(path_ensembles, detect):
        rows.append(fmt.format(path_e.ensemble,
                               path_e.interfaces[0],
                               path_e.interfaces[1],
                               path_e.interfaces[2],
                               idet))
        rows.extend(hline)
    table = header + hline + rows
    table = '\n'.join(table)
    return table


def _rst_table_probabilities(path_ensembles, results):
    """
    This will generate an table in reStrcuturedText which displays the
    obtained probabilities for the different path ensembles. This is used by
    the report generation.

    Parameters
    ----------
    path_ensembles : list of objects of type PathEnsemble
        These are the path ensembles we have analysed.
    results : list of dicts
        The dictionaries are the results obtained from the analysis.

    Returns
    -------
    out : string
        The table as a string in reStructuredText format.
    """
    hline = ['+----------+------------+------------+----------------+']
    header = ['+-----------------------------------------------------+',
              '|Probabilities                                        |',
              '+----------+------------+------------+----------------+',
              '| Ensemble |   Pcross   |   Error    | Rel. error (%) |']
    rows = []
    fmt = '| {0:^8s} | {1:^10.6f} | {2:^10.6f} |   {3:^10.6f}   |'
    for path_e, result in zip(path_ensembles, results):
        rows.append(fmt.format(path_e.ensemble,
                               result['prun'][-1],
                               result['blockerror'][2],
                               result['blockerror'][4]*100.))
        rows.extend(hline)
    table = header + hline + rows
    table = '\n'.join(table)
    return table


def _rst_table_path_lengths(path_ensembles, results):
    """
    This will generate an table in reStrcuturedText which displays the
    obtained path-lengths for the different path ensembles. This is used by
    the report generation.

    Parameters
    ----------
    path_ensembles : list of objects of type PathEnsemble
        These are the path ensembles we have analysed.
    results : list of dicts
        The dictionaries are the results obtained from the analysis.

    Returns
    -------
    out : string
        The table as a string in reStructuredText format.
    """
    hline = ['+----------+------------+------------+----------------+']
    header = ['+-----------------------------------------------------+',
              '|Path lengths                                         |',
              '+----------+------------+------------+----------------+',
              '| Ensemble |  Accepted  |    All     |  All/Accepted  |']
    rows = []
    fmt = '| {0:^8s} | {1:^10.5f} | {2:^10.5f} |   {3:^10.5f}   |'

    for path_e, result in zip(path_ensembles, results):
        hist1 = result['pathlength'][0]
        hist2 = result['pathlength'][1]
        rows.append(fmt.format(path_e.ensemble,
                               hist1[2][0],
                               hist2[2][0],
                               hist2[2][0]/hist1[2][0]))
        rows.extend(hline)
    table = header + hline + rows
    table = '\n'.join(table)
    return table


def _rst_figure_3_row(figure_files, selection):
    """
    This is a rather specific method which will place three figures in a row.
    This is done by setting the width equal to 30%. This method is used
    by ``_rst_figures``.

    Parameters
    ----------
    figure_files : list of dicts.
        These are the figures we will use.
    selection : list of strings
        This will select which images to use, for instance
        selection = ['pcross', 'prun', 'blockerror']
    """
    image_fmt = '.. image:: {0}\n   :width: 30%'
    image_text = []
    for fig in figure_files:
        for sel in selection:
            image_text.append(image_fmt.format(fig[sel]))
        image_text.append('')
    image_text.pop()  # just remove last one for aesthetics...
    return '\n'.join(image_text)


def _rst_figures(figure_files, total_figure):
    """
    This method will generate the image-rows with the results.
    It will simply put 3 images in each row with a width equal to 30%.

    Parameters
    ----------
    figure_files : list of dicts.
        These are the figures we will use.
    total_figure : string
        This is the figure with the total probability plot.
    """
    image_text = ['.. _prob-figures-output:\n',
                  'Probability figures', 19*('-'), '']
    sel = ['pcross', 'prun', 'blockerror']
    image_text.append(_rst_figure_3_row(figure_files, sel))
    image_prob = '\n'.join(image_text)

    image_text = ['.. _len-shoot-figures-output:\n',
                  'Length and shoots figures', 25*('-'), '']
    sel = ['pathlength', 'shoots', 'shoots-scaled']
    image_text.append(_rst_figure_3_row(figure_files, sel))
    image_shoots = '\n'.join(image_text)

    image_total = ['.. _total-probability-figure:',
                   '', 'Total probability', 17*('-'), '',
                   '.. image:: {}'.format(total_figure),
                   '   :width: 50%', '   :align: center']
    image_total = '\n'.join(image_total)
    return image_prob, image_shoots, image_total


def rst_generate_report(path_ensembles, results, figure_files, total_figure,
                        detect):
    """
    This method will generate the report in reStructuredText format.

    Parameters
    ----------
    path_ensembles : list of objects of type PathEnsemble
        These are the path ensembles we have analysed.
    figure_files : list of strings.
        These are the figures we will use.
    total_figure : string
        This is the figure with the total probability plot.
    results : list of dicts
        The dictionaries are the results obtained from the analysis.
    detect : list of floats
        These are the detect interfaces used in the analysis.

    Returns
    -------
    out : list
        This list are the text lines of the report.
    """
    # generate image code:
    images_prob, images_shoot, image_total = _rst_figures(figure_files,
                                                          total_figure)
    # generate tables:
    table_int = _rst_table_interface(path_ensembles, detect)
    table_pro = _rst_table_probabilities(path_ensembles, results)
    table_len = _rst_table_path_lengths(path_ensembles, results)
    tables = ['.. _tis-results:', '', 'Numerical TIS results', 21*('='), '',
              table_int, '', table_pro, '', table_len]
    tables = '\n'.join(tables)
    # generate output list:
    report = []
    report.append(19*('#'))
    report.append('pytismol - analysis')
    report.append(19*('#'))
    report.append('')
    report.append('Report generated by pytismol version {}'.format(VERSION))
    report.append('')
    report.append('.. _figure-results:')
    report.append('')
    report.append('Result figures')
    report.append('==============')
    report.append('')
    report.append('The following figures were generated by the')
    report.append('analysis program:')
    report.append('')
    report.append(images_prob)
    report.append('')
    report.append(images_shoot)
    report.append('')
    report.append(image_total)
    report.append('')
    report.append(tables)
    return report
