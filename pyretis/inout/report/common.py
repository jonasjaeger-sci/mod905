# -*- coding: utf-8 -*-
"""Some common methods for generating reports.

This module contains some common methods for the genration of reports.
The methods defined here are typically used to format numbers and generate
tables for the reports.

Important functions defined here:

- apply_format: Apply a format string to a given value.

- generate_rst_table: Generate reStructuredText for a table.

- generate_latex_table: Generate latex code for a table.

- latexify_number: Change exponential notation into something nicer for latex.

- mathexify_number: Change exponential notation into something nicer for
  reStructuredText.
"""
from __future__ import absolute_import
import os

__all__ = ['remove_extensions', 'apply_format', 'generate_rst_table',
           'generate_latex_table', 'latexify_number', 'mathexify_number']


def _remove_extension(filename):
    """Remove the extension of a given filename.

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
    """Remove extensions for a list of files.

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


def apply_format(value, fmt):
    """Apply a format string to a given value.

    Here we check the formatting of a float. We are *forcing* a
    *maximum length* on the resulting string. This is to avoid problems
    like: '{:7.2f}'.format(12345.7) which returns '12345.70' with a length
    8 > 7. The indended use of this method is to avoid shuch problems when we
    are formatting numbers for tables. Here it is done by switching to an
    exponential notation. But note however that this will have implications
    for how many decimal places we can show.

    Parameters
    ----------
    value : float
        The float to format.
    fmt : string
        The format to use.

    Note
    ----
    This method converts numbers to have a fixed length. In some cases this
    may reduce the number of significant digits. Remember to also output your
    numbers without this format in case a specific number of significant
    digits is important!
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

    This is a general method to generate a table in reStructuredText.
    The table is specified with a title, headings for the columns and
    the contents of the columns and rows.

    Parameters
    ----------
    table : list of lists
        `table[i][j]` is the contents of column `j` of row `i` of the table.
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
    r"""Generate latex code for a table.

    This method will generate latex code for a table. The table is given with
    a title, headings for the columns and the contents of the table. For latex
    we might wish to make some numbers more pretty by removing exponential
    notation: i.e. ``1.e-10`` can be replaced by ``1.0 \times 10^{-10}``
    (which should render like :math:`1.0 \times 10^{-10}`).

    Parameters
    ----------
    table : list of lists
        `table[i][j]` is the contents of column `j` of row `i` of the table.
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
    r"""Change exponential notation into something nicer for latex.

    This will change exponential notation, e.g ``1.2e-03``, into
    ``1.2 \times 10^{-3}`` for latex output which should be rendered like
    :math:`1.2 \times 10^{-3}`.

    Parameters
    ----------
    str_float : string
        This is the string representation of a float.

    Returns
    -------
    out : string
        A formatted string for latex.
    """
    if 'e' in str_float:
        base, exp = str_float.split('e')
        return r'${0} \times 10^{{{1}}}$'.format(base, int(exp))
    else:
        return r'${}$'.format(str_float)


def mathexify_number(str_float):
    r"""Change exponential notation into something nicer for reStructuredText.

    This will just call `latexify_number` and put it into a math directive for
    reStructuredText.

    Parameters
    ----------
    str_float : string
        This is the string representation of a float.

    Returns
    -------
    out : string
        A math directive for reStructuredText.
    """
    return ':math:`{}`'.format(latexify_number(str_float))
