# -*- coding: utf-8 -*-
"""This file contains methods that handle output/input of text"""
import itertools


_DEFINED_TABLES = {'energies': {'title': 'Energy output',
                                'var': ['stepno', 'temp', 'vpot',
                                        'ekin', 'etot', 'press'],
                                'headers': ['Step', 'Temp', 'Pot',
                                            'Kin', 'Tot', 'Press'],
                                'width': (10, 12), 'spacing': 2}}


def get_predefined_table(table):
    """
    This method will just set up and return some predefined tables which
    are used often. It simply initiate TxtTable with some predefined
    settings.

    Parameters
    ----------
    table : string
        This should match one of the defined tables in _DEFINED_TABLES

    Returns
    -------
    out : object of type TxtTable
    """
    settings = _DEFINED_TABLES.get(table.lower(), None)
    if settings is None:
        return None
    else:
        tab = TxtTable(settings['var'], width=settings['width'],
                       headers=settings['headers'],
                       spacing=settings['spacing'])
        return tab


def _create_and_format_row(row, width, header=False, spacing=1, fmt_str=None):
    """
    This will create the header format given the width.
    The specified width can either be a fixed number which will be
    applied to all cells, or it can be an iterable.

    Parameters
    ----------
    row : list
        The data to format.
    width : int or iterable
        This is the width of the cells in the table. If it's given as an
        iterable it will be applied to headers untill it's exhausted. In that
        case the last entry will be repeated.
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
    If the field-width is too large, the value will be truncated here!
    """
    row_str = []
    # first check if width is iterable:
    try:
        for _ in width:
            break
    except TypeError:
        width = [width]
    if fmt_str is None:
        fmt = None
        for (col, wid) in itertools.izip_longest(row, width,
                                                 fillvalue=width[-1]):
            if header:
                # if this is the header, just assume that all will be strings:
                if fmt is None:
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
        str_white = (' ') * spacing
        return str_white.join(fmt), str_white.join(row_str)
    else:
        row_str = fmt_str.format(*row)
        return fmt_str, row_str


class TxtTable(object):
    """
    TxtTable(object)

    This object will return a table of text with a header and
    with formatted rows.

    Attributes
    ----------
    variables : list of strings
        This is used to choose the variables to write out
    headers : list of strings
        These can be used as headers for the table. If they are
        not given, the strings in variables will be used.
    header : string
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
        """
        Initialize the table. Here we can specify default formats for
        floats and for integers.

        Parameters
        ----------
        variables : list of strings
            This is the variables to output to the table.
        headers : list of strings, optional
            These can be used as headers for the table. If they are
            not given, the strings in variables will be used.
        width : int or iterable
            This defines the maximum width of one cell.
        """
        self.width = width
        self.variables = variables
        self.spacing = spacing  # zeros are correctly handled by get_header
        self.headers, self.header = self.make_header(headers=headers)
        self.row_fmt = None

    def make_header(self, headers=None):
        """
        This is just a function to return the header. It will also
        create it if needed.

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
            The header as a string.
        """
        if headers is None:
            new_headers = [var.title() for var in self.variables]
        else:
            new_headers = [var.title() for var in headers]
        _, header = _create_and_format_row(new_headers, width=self.width,
                                           header=True, spacing=self.spacing)
        return new_headers, header

    def get_header(self):
        """Function to just return the current header."""
        return self.header

    def write(self, row_dict, header=False):
        """
        This method will write a row.

        Parameters
        ----------
        row_dict : dict
            This is the row values (columns) to write. Variables will
            be selected accordint to self.variables. This is just so that
            we can enforce a ordering.
        header : boolean, optional
            If this is true, we are creating the header.
        """
        row = [row_dict.get(var, None) for var in self.variables]
        row_fmt, str_row = _create_and_format_row(row,
                                                  width=self.width,
                                                  header=header,
                                                  spacing=self.spacing,
                                                  fmt_str=self.row_fmt)
        if self.row_fmt is None:  # store the row format for re-usage
            self.row_fmt = row_fmt
        return str_row

    def __call__(self, row, header=False):
        """
        This method is just for convenience. It will just
        call self.write with the parameters.

        Parameters
        ----------
        row : list
            This is the row values (columns) to write.
        header : boolean, optional
            If this is true, we are creating the header.
        """
        return self.write(row, header=header)
