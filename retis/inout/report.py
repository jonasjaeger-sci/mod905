# -*- coding: utf-8 -*-
"""
This file contains methods that will generate reports for displaying
the results from the pytismol program.
"""
from __future__ import absolute_import
from retis import __version__ as VERSION
import warnings
# for converting rst to html and/or latex:
import docutils.core
from docutils.writers.html4css1 import Writer as HTMLWriter
from docutils.writers.html4css1 import HTMLTranslator
import os
# for using templates
#from jinja2 import Environment, FileSystemLoader
import jinja2

__all__ = ['generate_report']

# the types the program know how to generate:
_TEMPLATES = {'rst': 'report_template.rst',
              'html': 'report_template.rst',  # html is done via rst,
              'latex': 'report_template.tex',
              'tex': 'report_template.tex'}


def _rst_to_html(rst):
    """
    This will convert a reStrcuturedText string to simple html.

    Parameters
    ----------
    rst : string
        The string to convert.

    Returns
    -------
    out : string
        A html document corresponding to the input reStructuredText.
    """
    htmlwriter = HTMLWriter()
    htmlwriter.translator_class = HTMLTranslator
    html = docutils.core.publish_string(rst, writer=htmlwriter)
    return html


def _remove_extension(filename):
    """
    This method will remove the extension of a given filename

    Parameters
    ----------
    filename : string
        The filename to check

    Returns
    -------
    out : string
        The filename with the extension removed
    """
    try:
        return os.path.splitext(filename)[0]
    except IndexError:
        return filename


def generate_report(path_ensembles, analysis, output='rst', template=None):
    """
    This will generate the report for the results.

    Parameters
    ----------
    analysis : dict
        This is the output (and some input) for the analysis. The keys are:
        'tis' : dict with the results from analysing path ensembles
        'tis-fig' : list of correponding figures (to 'tis')
        'matched' : results from the matchin of probability
        'matched-fig' : the figure corresponding to 'matched'
        'detect' : locations of the interfaces used for detection
    output : string, optional
        This is the desired output format. It must match one of the
        formats defined in _TEMPLATES. Default is reStructuredText.
    template : string, optional
        This is the template file to use. The default is given
        by _TEMPLATES[output].

    Returns
    -------
    out : string
        The generated report in the desired format.
    """
    if not output in _TEMPLATES:
        warnings.warn('Unknown output {} will use rst'.format(output))
        output = 'rst'
    if template is None or not os.path.isfile(template):
        # Use default template, this is located in the templates dir:
        path = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(path, 'templates')
        template = _TEMPLATES[output]
    else:
        # user specified full path to template:
        path = os.path.dirname(template)
        template = os.path.basename(template)

    env = jinja2.Environment(block_start_string='@{%',
                             block_end_string='%}@',
                             variable_start_string='@{{',
                             variable_end_string='}}@',
                             loader=jinja2.FileSystemLoader(path))

    report = {'version': VERSION, 'figures': analysis['tis-fig'],
              'totalfig': analysis['matched-fig'], 'table_int': None, 'table_prob': None,
              'table_path': None, 'table_eff': None, 'pcross': None,
              'perr': None, 'pcross_simt': None, 'pcross_teff': None,
              'pcross_opteff':None}
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
        # remove extensions of figures:
        report['figures'] = []
        for fig in analysis['tis-fig']:
            report['figures'].append({key: _remove_extension(fig[key]) for key in fig})
        report['totalfig'] = [_remove_extension(fig) for fig in report['totalfig']]
        report['pcross'] = _latexify_number(report['pcross'])
        report['perr'] = _latexify_number(report['perr'])
    #pylint: disable=maybe-no-member
    render = env.get_template(template).render(report)
    #pylint: enable=maybe-no-member
    if output == 'html':
        return _rst_to_html(render)
    else:
        return render


def _apply_format(value, fmt):
    """
    This method is to check the formatting of a float. Here we are
    going to force a maximum length on the resulting string.
    This is to avoid problems like: '{:7.2f}'.format(12345.7) which
    returns '12345.70' with a length 8 > 7. Here it is done by simply
    switching to an exponential notation, but note however that this
    will have implications for how many decimal places we can show.

    Parameters
    ----------
    value : float
        The float to format
    fmt : string
        The format to use.
    """
    maxlen = fmt.split(':')[1].split('.')[0]
    align = ''
    if not maxlen[0].isalnum():
        align = maxlen[0]
        maxlen = maxlen[1:]
    maxlen = int(maxlen)
    str_fmt = fmt.format(value)
    if len(str_fmt) > maxlen:  # switch to exponential:
        if value < 0:
            deci = maxlen - 7
        else:
            deci = maxlen - 6
        new_fmt = '{{:{0}{1}.{2}e}}'.format(align, maxlen, deci)
        return new_fmt.format(value)
    else:
        return str_fmt


def _table_interface(path_ensembles, detect, fmt='rst'):
    """
    This will generate the table for the interfaces.

    Parameters
    ----------
    path_ensembles : list of objects of type PathEnsemble
        These are the path ensembles we have analysed.
    detect : list of floats
        These are the detect interfaces used in the analysis.
    fmt : string, optional
        Determines if we create reStructuredText ('rst') or latex ('tex').

    Returns
    -------
    out[0] : list of strings
        These are the rows of the table
    out[1] : string
        This is a string in the desired format which represents
        the table.
    """
    # table for interfaces:
    table = []
    for path_e, idet in zip(path_ensembles, detect):
        row = ['{:^8s}'.format(path_e.ensemble)]
        row.append(_apply_format(path_e.interfaces[0], '{:^8.4f}'))
        row.append(_apply_format(path_e.interfaces[1], '{:^8.4f}'))
        row.append(_apply_format(path_e.interfaces[2], '{:^8.4f}'))
        row.append(_apply_format(idet, '{:^8.4f}'))
        table.append(row)
    if fmt in ['tex', 'latex']:
        table_str = _generate_latex_table(table, 'Interfaces',
                                          ['Ensemble', 'Left', 'Middle',
                                           'Right', 'Detect'],
                                          fixnum=set([1, 2, 3, 4]))
    else:
        table_str = _generate_rst_table(table, 'Interfaces',
                                        ['Ensemble', 'Left', 'Middle',
                                         'Right', 'Detect'])
    table_str = '\n'.join(table_str)
    return table, table_str


def _table_probability(path_ensembles, results, fmt='rst'):
    """
    This will generate the table for the probabilities.

    Parameters
    ----------
    path_ensembles : list of objects of type PathEnsemble
        These are the path ensembles we have analysed.
    results : list of dicts
        The dictionaries are the results obtained from the analysis.
    fmt : string, optional
        Determines if we create reStructuredText ('rst') or latex ('tex').

    Returns
    -------
    out[0] : list of strings
        These are the rows of the table
    out[1] : string
        This is a string in reStrucutredText format which represents
        the table.
    """
    # table for probabilities:
    table = []
    for path_e, result in zip(path_ensembles, results):
        row = ['{:^8s}'.format(path_e.ensemble)]
        row.append(_apply_format(result['prun'][-1], '{:^10.6f}'))
        row.append(_apply_format(result['blockerror'][2], '{:^10.6f}'))
        row.append(_apply_format(result['blockerror'][4] * 100, '{:^10.6f}'))
        table.append(row)
    if fmt in ['tex', 'latex']:
        table_str = _generate_latex_table(table, r'Probabilities',
                                          [r'Ensemble', r'$P_\text{cross}$',
                                           r'Error', r'Rel. error (\%)'],
                                          fixnum=set([1, 2, 3]))
    else:
        table_str = _generate_rst_table(table, r'Probabilities',
                                        [r'Ensemble', r'Pcross', r'Error',
                                         r'Rel. error (%)'])
    table_str = '\n'.join(table_str)
    return table, table_str


def _table_path(path_ensembles, results, fmt='rst'):
    """
    This will generate the table for the probabilities.

    Parameters
    ----------
    path_ensembles : list of objects of type PathEnsemble
        These are the path ensembles we have analysed.
    results : list of dicts
        The dictionaries are the results obtained from the analysis.
    fmt : string, optional
        Determines if we create reStructuredText ('rst') or latex ('tex').

    Returns
    -------
    out[0] : list of strings
        These are the rows of the table
    out[1] : string
        This is a string in reStrucutredText format which represents
        the table.
    """
    table = []
    for path_e, result in zip(path_ensembles, results):
        row = ['{:^8s}'.format(path_e.ensemble)]
        hist1 = result['pathlength'][0]
        hist2 = result['pathlength'][1]
        row.append(_apply_format(hist1[2][0], '{:^10.6f}'))
        row.append(_apply_format(hist2[2][0], '{:^10.6f}'))
        row.append(_apply_format(hist2[2][0] / hist1[2][0], '{:^10.6f}'))
        table.append(row)
    if fmt in ['tex', 'latex']:
        table_str = _generate_latex_table(table, 'Path lengths',
                                          ['Ensemble', 'Accepted', 'All',
                                           'All/Accepted'],
                                          fixnum=set([1, 2, 3]))
    else:
        table_str = _generate_rst_table(table, 'Path lengths',
                                        ['Ensemble', 'Accepted', 'All',
                                         'All/Accepted'])
    table_str = '\n'.join(table_str)
    return table, table_str

def _table_efficiencies(path_ensembles, results, fmt='rst'):
    """
    This will generate the table for the probabilities.

    Parameters
    ----------
    path_ensembles : list of objects of type PathEnsemble
        These are the path ensembles we have analysed.
    results : list of dicts
        The dictionaries are the results obtained from the analysis.
    fmt : string, optional
        Determines if we create reStructuredText ('rst') or latex ('tex').

    Returns
    -------
    out[0] : list of strings
        These are the rows of the table
    out[1] : string
        This is a string in reStrucutredText format which represents
        the table.
    """
    # table for efficiency:
    table = []
    for path_e, result in zip(path_ensembles, results):
        row = ['{:^8s}'.format(path_e.ensemble)]
        row.append(_apply_format(path_e.npath, '{:^10.0f}'))
        row.append(_apply_format(result['efficiency'][1], '{:^10.6f}'))
        row.append(_apply_format(result['efficiency'][0], '{:^10.6f}'))
        row.append(_apply_format(result['blockerror'][6], '{:^10.6f}'))
        row.append(_apply_format(result['efficiency'][2], '{:^10.6f}'))
        table.append(row)
    if fmt in ['tex', 'latex']:
        table_str = _generate_latex_table(table, 'Efficiency',
                                          ['Ensemble', 'TIS cycles',
                                           'Tot sim.', 'Acceptance ratio',
                                           'Correlation', 'Efficiency'],
                                          fixnum=set([1, 2, 3, 4, 5]))
    else:
        table_str = _generate_rst_table(table, 'Efficiency',
                                        ['Ensemble', 'TIS cycles', 'Tot sim.',
                                         'Acceptance ratio', 'Correlation',
                                         'Efficiency'])
    table_str = '\n'.join(table_str)
    return table, table_str

def _generate_rst_table(table, title, headings):
    """
    This method will generate the reStructuredText for a table.

    Parameters
    ----------
    table : list of lists
        table[i][j] is the string contents of column j of table i of the table.
    title : string
        The header/title for the table
    headings : list of strings
        These are the headings for each table column.
    """
    # for each column, we need to figure out how wide it should be
    # 1) Check headings
    col_len = [len(col) + 2 for col in headings]
    # 2) Check if some of the columns are wider
    for row in table:
        for i, col in enumerate(row):
            if len(col) >= col_len[i] - 2:
                col_len[i] = len(col) + 2  # add some extra space

    width = len(col_len) + sum(col_len) - 1
    topline = '+' + width * ('-') + '+'
    # create the header
    str_header = '|{{0:<{0}s}}|'.format(width)
    str_header = str_header.format(title)
    # make format for header:
    head_fmt = ['{{0:^{0}s}}'.format(col) for col in col_len]
    # create first row, which is the header on columns:
    row_line = [fmt.format(col) for fmt, col in zip(head_fmt, headings)]
    row_line = [''] + row_line + ['']
    row_line = '|'.join(row_line)
    # also set-up the horizontal line:
    hline = [''] + [col * ('-') for col in col_len] + ['']
    hline = '+'.join(hline)
    # generate table
    str_table = [topline, str_header, hline, row_line, hline]
    for row in table:
        row_line = [fmt.format(col) for fmt, col in zip(head_fmt, row)]
        row_line = [''] + row_line + ['']
        row_line = '|'.join(row_line)
        str_table.extend([row_line, hline])
    return str_table

def _generate_latex_table(table, title, headings, fixnum=None):
    """
    This method will generate the latex code for a table.

    Parameters
    ----------
    table : list of lists
        table[i][j] is the string contents of column j of table i of the table.
    title : string
        The header/title for the table
    headings : list of strings
        These are the headings for each table column.
    fixnum : list/set of integers
        These integers identifies the columns where ``_latexify_number`` is
        to be applied.
    """
    #for col in headings
    str_table = [r'\renewcommand{\arraystretch}{1.25}',
                 r'\noindent', r'\begin{minipage}{\textwidth}', r'\centering',
                 r'\textbf{' + title + r'} \\', r'\medskip'
                 r'\begin{tabular}{' + len(headings)*('| c ')  + '|}']
    str_table.append(r'\hline')
    str_table.append(' & '.join(headings) + r'\\ \hline')
    for row in table:
        if fixnum:
            rowl = [_latexify_number(col) if i in fixnum else col for i, col in enumerate(row)]
            str_table.append(' & '.join(rowl) + r'\\')
        else:
            str_table.append(' & '.join(row) + r'\\')
    str_table.append(r'\hline')
    str_table.append(r'\end{tabular}')
    str_table.append(r'\bigskip')
    str_table.append(r'\end{minipage}')
    return str_table

def _latexify_number(str_float):
    r"""
    This will change exponential notation, e.g 1.2e-03, into
    1.2 \times 10^{-3} for latex output.

    Parameters
    ----------
    str_float : string
        This is the string representation of a float

    """
    if 'e' in str_float:
        base, exp = str_float.split('e')
        return r'${0} \times 10^{{{1}}}$'.format(base, int(exp))
    else:
        return r'${}$'.format(str_float)
