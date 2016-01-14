# -*- coding: utf-8 -*-
"""Functions and classes for text based output and input.

This file contains some functions and classes that handle output and input
of 'table-based' output. Typically the data created here will be written
to the screen during the simulation or as a simple column output.

Important classes and functions defined here:

- TxtTable: Class for a table of text with a header and formatted rows.

- txt_save_columns: Writing a simple column-based output using numpy.

- get_predefined_table: Function for creating certain `TxtTable` objects that
  write/formats predefined tables.
"""
import logging
try:  # this will fail in python3
    from itertools import izip_longest as zip_longest
except ImportError:  # for python3
    from itertools import zip_longest as zip_longest
import numpy as np
from pyretis.inout.common import create_backup
logging.getLogger(__name__).addHandler(logging.NullHandler())


__all__ = ['get_predefined_table', 'TxtTable', 'txt_save_columns']

# Define some table which may be useful. These tables
# can be selected using the `get_predefined_tables` function defined below.
_DEFINED_TABLES = {}
_DEFINED_TABLES['energies'] = {'title': 'Energy output',
                               'var': ['step', 'temp', 'vpot',
                                       'ekin', 'etot', 'press'],
                               'headers': ['Step', 'Temp', 'Pot',
                                           'Kin', 'Tot', 'Press'],
                               'width': (10, 12), 'spacing': 2,
                               'row_fmt': ['{:> 10d}'] + 5 * ['{:> 12.6g}']}

_DEFINED_TABLES['path-stats'] = {'title': 'Path ensemble statistics',
                                 'var': ['step', 'ACC', 'BWI',
                                         'BTL', 'FTL', 'BTX', 'FTX'],
                                 'headers': ['Cycle', 'Accepted',
                                             'BWI', 'BTL', 'FTL',
                                             'BTX', 'FTX'],
                                 'width': (10, 12), 'spacing': 2,
                                 'row_fmt': ['{:> 10d}'] + 6 * ['{:> 12d}']}


def get_predefined_table(table):
    """Create predefined `TxtTable` objects.

    This function will set up and return an object like `TxtTable` for some
    predefined tables. The predefined tables are assumed to be defined in
    a dictionary `_DEFINED_TABLES`. Here, objects like `TxtTable` will be
    initiated based on the given settings in `_DEFINED_TABLES`.

    Parameters
    ----------
    table : string
        This should match one of the defined tables in `_DEFINED_TABLES`.

    Returns
    -------
    out : object like `TxtTable` from `pyretis.inout.txtinout`
        This is the text table that can be used for output.
    """
    settings = _DEFINED_TABLES.get(table.lower(), None)
    if settings is None:
        return None
    else:
        if table.lower() == 'path-stats':
            tab = PathTable(settings['var'],
                            width=settings['width'],
                            headers=settings['headers'],
                            spacing=settings['spacing'])
        else:
            tab = TxtTable(settings['var'], width=settings['width'],
                           headers=settings['headers'],
                           spacing=settings['spacing'])
        if 'row_fmt' in settings:  # override the row-format:
            tab.row_fmt = ' ' * settings['spacing']
            tab.row_fmt = tab.row_fmt.join(settings['row_fmt'])
        return tab


def txt_save_columns(outputfile, header, variables, backup=False):
    """Save variables to a text file using `numpy.savetxt`.

    Note that the variables are assumed to be numpy.arrays of equal shape
    and that the output file may also be a gzipped file (this is selected
    by letting the output file name end with '.gz').

    Parameters
    ----------
    outputfile : string
        This is the name of the output file to create.
    header : string
        String that will be written at the beginning of the file.
    variables : tuple of numpy.arrays
        These are the variables that will be save to the text file.
    backup : boolean
        Determines if we should backup old files or not.
    """
    if backup:
        msg = create_backup(outputfile)
        if msg:
            logging.warning(msg)
    nvar = len(variables)
    mat = np.zeros((len(variables[0]), nvar))
    for i, vari in enumerate(variables):
        try:
            mat[:, i] = vari
        except ValueError:
            msg = 'Could not align variables, skipping (writing zeros)'
            logging.warning(msg)
    np.savetxt(outputfile, mat, header=header)


def create_and_format_row(row, width, header=False, spacing=1, fmt_str=None):
    """Format a row according to the given width(s).

    The specified width can either be a fixed number which will be
    applied to all cells, or it can be an iterable.

    Parameters
    ----------
    row : list
        The data to format.
    width : int or iterable
        This is the width of the cells in the table. If it's given as an
        iterable it will be applied to headers until it's exhausted. In that
        case the last entry will be repeated and used for the remaining items.
    header : boolean, optional
        To tell if we are formatting for a header or not.
        The header will include a '#' to indicate that it's a header.
    spacing : int, optional
        This is the white space for separating columns.
    fmt_str : string, optional
        This is the format to apply, if it's not given, it will be created.

    Returns
    -------
    out[0] : strings
        The format string for the row
    out[1] : string
        This is the formatted row

    Note
    ----
    If the field-width is too large, values will be truncated!
    """
    row_str = []
    # first check if `width` is iterable:
    try:
        for _ in width:
            break
    except TypeError:
        width = [width]
    if fmt_str is None:
        fmt = None
        for (col, wid) in zip_longest(row, width,
                                      fillvalue=width[-1]):
            if header:
                # if this is the header, just assume that all will be strings:
                if fmt is None:  # first item includes a "# " in front.
                    fmt = ['# {{:>{}s}}'.format(wid - 2)]
                else:
                    fmt.append('{{:>{}s}}'.format(wid))
            else:
                # this is not the header, use 'g'
                if fmt is None:
                    fmt = []
                fmt.append('{{:> {}.{}g}}'.format(wid, wid - 6))
                try:
                    fmt[-1].format(col)
                except ValueError:
                    fmt[-1] = '{{:> {}}}'.format(wid)
            rowi = fmt[-1].format(col)
            row_str.append(rowi)
        str_white = ' ' * spacing
        return str_white.join(fmt), str_white.join(row_str)
    else:
        row_str = fmt_str.format(*row)
        return fmt_str, row_str


class TxtTable(object):
    """TxtTable(object) - Represent a table of text.

    This object will return a table of text with a header and
    with formatted rows. The typical use is when we want to output results
    in a table given a dictionary which contains the result. The `TxtTable`
    can then be used to only pick out a subset of the items we want to output.

    Attributes
    ----------
    variables : list of strings
        This is used to choose the variables to write out
    headers : list of strings
        These can be used as headers for the table. If they are
        not given, the strings in variables will be used.
    headers : string
        This is the formatted header for the table.
    width : int or iterable
        This defines the maximum width of one cell.
    spacing : int
        This defines the white space between columns.
        A spacing less than 0 will be interpreted as a 0.
    row_fmt : string
        This is a format string which can be used to format the rows of the
        table.
    """

    def __init__(self, variables, width=12, headers=None, spacing=1):
        """Initialize the table.

        Parameters
        ----------
        variables : list of strings
            This is the variables to output to the table.
        width : int or iterable, optional
            This defines the maximum width of one cell.
        headers : list of strings, optional
            These can be used as headers for the table. If they are
            not given, the strings in variables will be used.
        spacing : int, optional
            This is the white space to include between columns.
        """
        self.width = width
        self.variables = variables
        self.spacing = spacing  # zeros are correctly handled by get_header
        self.headers, header = self.make_header(headers=headers)
        self._header = header
        self.row_fmt = None

    @property
    def header(self):
        """Define the header as a property."""
        return self._header

    @header.setter
    def header(self, header_list=None):
        """Handle the setting of the header.

        Here, we call `self.make_header` to handle this.

        Parameters
        ----------
        header_list : list of strings, optional
            These can be used as headers for the table. If they are
            not given, the strings in variables will be used.
        """
        header = self.make_header(headers=header_list)[1]
        self._header = header

    def make_header(self, headers=None):
        """Create and return the header.

        Parameters
        ----------
        headers : list of strings, optional
            These can be used as headers for the table. If they are
            not given, the strings in variables will be used.

        Returns
        -------
        out[0] : list of strings
            The created headers.
        out[1] : string
            The header as a formatted string. Can directly be used for writing.
        """
        if headers is None:
            new_headers = [var for var in self.variables]
        else:
            new_headers = [var for var in headers]
        _, header = create_and_format_row(new_headers, width=self.width,
                                          header=True, spacing=self.spacing)
        return new_headers, header

    def format_row(self, row_dict, header=False):
        """Return a formatted string representation of a row.

        This function will format a 'row'. The row is given as a dictionary and
        we pick out values based on the variables defined in `self.variables`.

        Parameters
        ----------
        row_dict : dict
            This is the row values (columns) to write. Variables will be
            selected according to `self.variables`. This is just to enforce
            a specific ordering.
        header : boolean, optional
            If this is true, we are creating the header.
        """
        row = [row_dict.get(var, None) for var in self.variables]
        row_fmt, str_row = create_and_format_row(row,
                                                 width=self.width,
                                                 header=header,
                                                 spacing=self.spacing,
                                                 fmt_str=self.row_fmt)
        if self.row_fmt is None:  # store the row format for re-usage
            self.row_fmt = row_fmt
        return str_row

    def write(self, step, row, first_step=False):
        """Function which mimics the `write` function of a `FileWriter`.

        This function is intended to wrap the `self.get_row()` function so
        that we can use `self.write()` defined here in a similar way to the
        `FileWriter.write` function.

        Parameters
        ----------
        step : int
            This is the current step number or a cycle number in a simulation.
        row : dict
            These are the row values (columns) to write.
        first_step : boolean
            If first step is True, we will also write the header for the
            table.

        Returns
        -------
        out : string
            This string is the formatted row.
        """
        if 'step' in self.variables and 'step' not in row:
            row['step'] = step
        if first_step:
            return '\n'.join([self._header] + [self.format_row(row)])
        else:
            return self.format_row(row)

    def __call__(self, step, row, first_step=False):
        """Function to make `self.write` callable.

        Parameters
        ----------
        step : int
            This is the current step number or a cycle number in a simulation.
        row : dict
            These are the row values (columns) to write.
        first_step : boolean
            If first step is True, we will also write the header for the
            table.
        """
        return self.write(step, row, first_step=first_step)


class PathTable(TxtTable):
    """PathTable(object) - Special table for path ensembles.

    This object will return a table of text with a header and with formatted
    rows for a path ensemble. The table rows will contain data from the
    `PathEnsemble.nstats` variable. This table is just meant as output to the
    screen during a path ensemble simulation.

    Attributes
    ----------
    Identical to the `TxtTable` object.
    """
    def __init__(self, variables, width=12, headers=None, spacing=1):
        """Initiate parent."""
        super(PathTable, self).__init__(variables, width=width,
                                        headers=headers, spacing=spacing)

    def write(self, step, path_ensemble, first_step=False):
        """Function which mimics the `write` function of a `FileWriter`.

        This function is intended to wrap the `self.get_row()` function so
        that we can use `self.write()` defined here in a similar way to the
        `FileWriter.write` function. Here we overload the `write`function
        defined in `TxtTable` so that we can write path ensemble statistics to
        the screen.

        Parameters
        ----------
        step : int
            This is the current step number or a cycle number in a simulation.
        path_ensemble : object like `pyretis.core.path.PathEnsemble`
            This is the path ensemble to output for.
        first_step : boolean
            If first step is True, we will also write the header for the
            table.

        Returns
        -------
        out : string
            This string is the formatted row.
        """
        row_dict = {}
        for key in self.variables:
            if key == 'step':
                value = step
            else:
                value = path_ensemble.nstats.get(key, 0)
            row_dict[key] = value
        if first_step:
            return '\n'.join([self._header] + [self.format_row(row_dict)])
        else:
            return self.format_row(row_dict)
