# -*- coding: utf-8 -*-
"""Methods for generating reports.

The reports are useful for displaying results from the analysis.
"""
from __future__ import absolute_import
#from pyretis import __version__ as VERSION
#from pyretis import __program_name__ as PROGRAM_NAME
import warnings
# for converting rst to html and/or latex:
import docutils.core
from docutils.writers.html4css1 import Writer as HTMLWriter
from docutils.writers.html4css1 import HTMLTranslator
import os
# for using templates
import jinja2


__all__ = ['generate_rst_table']


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
    Convert a reStrcuturedText string to simple HTML.

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
    html = docutils.core.publish_string(rst, writer=htmlwriter,
                                        settings_overrides=override)
    return html


def _remove_extension(filename):
    """
    Remove the extension of a given filename.

    Parameters
    ----------
    filename : string
        The filename to check.

    Returns
    -------
    out : string
        The filename with the extension removed.
    """
    try:
        return os.path.splitext(filename)[0]
    except IndexError:
        return filename


def remove_extensions(list_of_files):
    """
    Remove extensions for a list of files.

    This will strip out extensions for all the files in a given iterable.
    Here, the iterable might be a simple list which contains dictionaries or
    it can be a dictionary. How we to the loop will depend on this.

    Parameters
    ----------
    list_of_files : list or dict, iterable
        This is the list for which we will try to remove extensions.

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


def get_template(output, report_type, template=None):
    """
    Return the template to use for a specified output format.

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


def generate_report(report, output, template, path):
    """
    Do the actual generation of a report.

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


def apply_format(value, fmt):
    """
    Apply format string to a given value.

    This method is to check the formatting of a float. Here we are
    going to force a maximum length on the resulting string.
    This is to avoid problems like: '{:7.2f}'.format(12345.7) which
    returns '12345.70' with a length 8 > 7. Here it is done by simply
    switching to an exponential notation, but note however that this
    will have implications for how many decimal places we can show.

    Parameters
    ----------
    value : float
        The float to format.
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


def generate_rst_table(table, title, headings):
    """Generate reStructuredText for a table.

    Parameters
    ----------
    table : list of lists
        table[i][j] is the string contents of column j of table i of the table.
    title : string
        The header/title for the table.
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


def generate_latex_table(table, title, headings, fixnum=None):
    """Generate latex code for a table.

    Parameters
    ----------
    table : list of lists
        table[i][j] is the string contents of column j of table i of the table.
    title : string
        The header/title for the table.
    headings : list of strings
        These are the headings for each table column.
    fixnum : list/set of integers
        These integers identifies the columns where `latexify_number` is
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
            rowl = [latexify_number(col) if i in fixnum else col for i, col
                    in enumerate(row)]
            str_table.append(' & '.join(rowl) + r'\\')
        else:
            str_table.append(' & '.join(row) + r'\\')
    str_table.append(r'\hline')
    str_table.append(r'\end{tabular}')
    str_table.append(r'\bigskip')
    str_table.append(r'\end{minipage}')
    return str_table


def latexify_number(str_float):
    r"""
    Change exponential notation into something nicer for latex.

    This will change exponential notation, e.g ``1.2e-03``, into
    ``1.2 \times 10^{-3}`` for latex output.

    Parameters
    ----------
    str_float : string
        This is the string representation of a float.
    """
    if 'e' in str_float:
        base, exp = str_float.split('e')
        return r'${0} \times 10^{{{1}}}$'.format(base, int(exp))
    else:
        return r'${}$'.format(str_float)
