# -*- coding: utf-8 -*-
"""
This file contains methods that will generate reports for displaying
the results from the analysis.
"""
from __future__ import absolute_import
from retis import __version__ as VERSION
from retis import __program_name__ as PROGRAM_NAME
import warnings
# for converting rst to html and/or latex:
import docutils.core
from docutils.writers.html4css1 import Writer as HTMLWriter
from docutils.writers.html4css1 import HTMLTranslator
import os
# for using templates
import jinja2


__all__ = ['generate_report_tis', 'generate_report_md']


# filename for known templates:
_TEMPLATES = {'rst': 'report_template_{}.rst',
              'html': 'report_template_{}.rst',  # html is done via rst,
              'latex': 'report_template_{}.tex',
              'tex': 'report_template_{}.tex',
              'txt': 'report_template_{}.txt'}
# look-up table for file extensions
_EXT = {'rst': 'rst',
        'html': 'html',
        'latex': 'tex',
        'tex': 'tex',
        'txt': 'txt'}


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


def _remove_extensions(list_of_files):
    """
    This will strip out extensions for all the files in a given iterable.
    Here, the iterable might be a simple list which contains dictionaries or
    it can be a dictionary. How we to the loop will depend on this.

    Parameters
    ----------
    list_of_files : list or dict, iterable
        This is the list for which we will try to remove extensions

    Returns
    -------
    newlist : list or dict
        A copy of list_of_files, where the extensions has been removed.

    Note
    ----
    If, for some reason, list_of_files is a list and the items are just
    integers, the TypeError will not be raised. This is pretty unlikely and
    we therefor do not check for this.
    """
    # we assume that list_of_files is a simple dict
    try:
        newlist = {}
        for key in list_of_files:
            newlist[key] = _remove_extension(list_of_files[key])
        return newlist
    except TypeError:
        newlist = []
        for fig in list_of_files:
            newfig = {key: _remove_extension(fig[key]) for key in fig}
            newlist.append(newfig)
        return newlist


def _get_template(output, report_type, template=None):
    """
    This method will return the template to use for a specified
    output format.

    Parameters
    ----------
    output : string
        This string selects the output format for the template, i.e.,
        rst, html, latex, tex.
    template : string, optional
        The full path to the template to use. If not given/found, the defaults
        in default_template will be used.
    report_type : string
        This is the type of report we are doing, e.g. TIS or MD.

    Returns
    -------
    out[0] : string
        File name of template to use.
    out[1] : string
        Path to the template to use.
    """
    if output not in _TEMPLATES:
        msg = 'Format {} not defined for {} report: Will use rst'
        warnings.warn(msg.format(output, report_type))
        output = 'rst'
    if template is None or not os.path.isfile(template):
        # Use default template, this is located in the templates dir:
        path = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(path, 'templates')
        template = _TEMPLATES[output].format(report_type.lower())
    else:
        # user specified full path to template:
        path = os.path.dirname(template)
        template = os.path.basename(template)
    return output, template, path


def _generate_report(report, output, template, path):
    """
    This method will do the actual generation of the report.

    Parameters
    ----------
    report : dict
        This dict contains the data to be reported. It is assumed that
        this dict matches the specified template.
    output : string
        This is the desired output format. Here it's used only for generating
        html as this is done via rst.
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


def generate_report_tis(path_ensembles, analysis, output='rst',
                        template=None):
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
    output, template, path = _get_template(output, 'TIS', template=template)
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
            report[fig] = _remove_extensions(report[fig])
        for key in ['pcross', 'perr', 'pcross_simt', 'pcross_teff',
                    'pcross_opteff']:
            report[key] = _latexify_number(report[key])
    return _generate_report(report, output, template, path)


def generate_report_md(analysis, output='rst', template=None):
    """
    This will generate the report for the results.

    Parameters
    ----------
    analysis : dict
        This is the output from the analysis. The keys are:
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
    output, template, path = _get_template(output, 'MD', template=template)
    report = {'version': VERSION,
              'program': PROGRAM_NAME,
              'flux_figures': analysis.get('flux_figures', None),
              'energy_figures': analysis.get('energy_figures', None),
              'order_figures': analysis.get('order_figures', None)}
    # generate some tables:
    _, report['table_md_flux'] = _table_md_flux(analysis['flux'], fmt=output)
    _, report['table_md_cycles'] = _table_md_flux_cycles(analysis['flux'],
                                                         fmt=output)
    _, report['table_md_efficiency'] = _table_md_efficiency(analysis['flux'],
                                                            fmt=output)
    # check if we need some additional latexification:
    if output in ['latex', 'tex']:
        for fig in ['flux_figures', 'energy_figures', 'order_figures']:
            report[fig] = _remove_extensions(report[fig])
    return _generate_report(report, output, template, path)


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


def _table_md_efficiency(results, fmt='rst'):
    """
    This will generate the table for the MD-flux results for efficiencies
    and correlations.

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
        These are the rows of the table
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
        row.append(_apply_format(pmd, '{:^10.6f}'))
        row.append(_apply_format(prel, '{:^10.6f}'))
        row.append(_apply_format(teff, '{:^10.6f}'))
        row.append(_apply_format(corr, '{:^10.6f}'))
        table.append(row)

    if fmt in ['tex', 'latex']:
        table_str = _generate_latex_table(table, 'Efficiency',
                                          ['Interface',
                                           r'$p_\text{MD}$',
                                           r'$\frac{1-p}{p}$',
                                           'Efficiency time', 'Correlation'],
                                          fixnum=set([1, 2, 3, 4]))
    elif fmt in ['txt']:
        table_str = _generate_rst_table(table, 'Efficiency',
                                        ['Interface',
                                         'p_MD',
                                         '(1-p_MD)/p_MD',
                                         'Efficiency time', 'Correlation'])
    else:
        table_str = _generate_rst_table(table, 'Efficiency',
                                        ['Interface',
                                         r':math:`p_\text{MD}`',
                                         r':math:`\frac{1-p}{p}`',
                                         'Efficiency time', 'Correlation'])
    table_str = '\n'.join(table_str)
    return table, table_str


def _table_md_flux_cycles(results, fmt='rst'):
    """
    This will generate the table for the MD-flux results for cycle numbers.
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
        These are the rows of the table
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
        table_str = _generate_latex_table(table, 'Cycles spent in state',
                                          ['State', 'Cycles'],
                                          fixnum=set([2]))
    else:
        table_str = _generate_rst_table(table, 'Cycles spent in state',
                                        ['State', 'Cycles'])
    table_str = '\n'.join(table_str)
    return table, table_str


def _table_md_flux(results, fmt='rst'):
    """
    This will generate the table for the MD-flux results.

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
        These are the rows of the table
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
        row.append(_apply_format(idet, '{:^8.4f}'))
        row.append(_apply_format(flux, '{:^10.6f}'))
        row.append(_apply_format(error, '{:^10.6f}'))
        row.append(_apply_format(relerror, '{:^10.6f}'))
        row.append('{:^8d}'.format(results['ncross'][i]))
        row.append('{:^8d}'.format(results['neffcross'][i]))
        row.append(_apply_format(results['neffc/nc'][i], '{:^10.6f}'))
        row.append(_apply_format(results['cross_time'][i], '{:^10.6f}'))
        table.append(row)
    if fmt in ['tex', 'latex']:
        table_str = _generate_latex_table(table, 'Flux for interfaces',
                                          ['Int.', 'Position', 'Flux / units',
                                           'Error', 'Rel. error', 'Ncross',
                                           'Neffcross', 'Neffcross/Ncross',
                                           'Steps per cross'],
                                          fixnum=set([2, 3, 4, 5, 6, 7, 8]))
    else:
        table_str = _generate_rst_table(table, 'Flux for interfaces',
                                        ['Int.', 'Position', 'Flux / units',
                                         'Error', 'Rel. error', 'Ncross',
                                         'Neffcross', 'Neffcross/Ncross',
                                         'Steps per cross'])
    table_str = '\n'.join(table_str)
    return table, table_str


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
        row.append(_apply_format(result['tis-cycles'], '{:^10.0f}'))
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
    str_table = [r'\renewcommand{\arraystretch}{1.25}',
                 r'\noindent', r'\begin{minipage}{\textwidth}', r'\centering',
                 r'\textbf{' + title + r'} \\', r'\medskip'
                 r'\begin{tabular}{' + len(headings) * ('| c ') + '|}']
    str_table.append(r'\hline')
    str_table.append(' & '.join(headings) + r'\\ \hline')
    for row in table:
        if fixnum:
            rowl = [_latexify_number(col) if i in fixnum else col for i, col
                    in enumerate(row)]
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
