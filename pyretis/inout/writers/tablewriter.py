# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""A module defining a generic writer for tables.

The tables are defined with a set of variables (`keys`) and some rules
for formatting. The table writer is similar to the other writer but can
be made more generic and is more suited for creating output that will be
displayed on screen.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

TxtTable
    A class for generating table output.

PathTable
    A class for table-like output from path simulations.

ThermoTable
    A class for thermodynamic output, useful for output from
    MD-simulations.
"""
import logging
# pyretis imports:
from pyretis.inout.writers.writers import Writer

logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['TxtTable', 'PathTable', 'ThermoTable']


# Tables can be defined and created as follows:
# tabl = {'title': 'Energy output',
#         'var': ['step', 'temp', 'vpot',
#                 'ekin', 'etot', 'press'],
#         'format': {'labels': ['Step', 'Temp', 'Pot',
#                              'Kin', 'Tot', 'Press'],
#                    'width': (10, 12),
#                    'spacing': 2,
#                    'row_fmt': ['{:> 10d}', '{:> 12.6g}']}}
# table = TxtTable(tabl['var'], tabl['title'], **tabl['format'])


def _fill_list(the_list, length, fillvalue=None):
    """Method to fill a list to a specified length.

    Parameters
    ----------
    the_list : list
        The list to fill.
    length : int
        The required length.
    fillvalue : optional
        The value to insert. If None is given the last item in the list
        is repeated.
    """
    if fillvalue is None:
        fillvalue = the_list[-1]
    while len(the_list) < length:
        the_list.append(fillvalue)


class TxtTable(Writer):
    """TxtTable(Writer) - A class for generating table output.

    This class handles writing/reading of output data to a table-like
    format.

    Attributes
    ----------
    variables : list of strings
        These are the variables we will use in the table.
    fmt : string
        The format to apply to the columns.
    row_fmt : list of strings
        A list of strings used for formatting, used to construct `fmt`.
    title : string
        A title for the table.
    """
    def __init__(self, variables, title, **kwargs):
        """Initialize the `TxtTable` object.

        Parameters
        ----------
        variables : list of strings
            These are the variables we will use in the table. If the
            header is not specified, then we will create one using
            these variables.
        title : string
            A title for the table.
        kwargs : dict
            Additional settings for the writer. This may contain:

            * width : list of ints
                The (maximum) width of the columns. If the number of
                items in this list is smaller than the number of
                variables, we simply repeat the last width for the
                number of times we need.
            * labels : list of strings
                Table headers to use for the columns.
            * spacing : integer
                The separation between columns. Default value is 1.
            * row_fmt : list of strings
                The format to apply to the columns. If the number of
                items in this list is smaller than the number of
                variables, we simply repeat the last width for the
                number of times we need.
        """
        spacing = kwargs.get('spacing', 1)
        header = {'spacing': spacing,
                  'labels': kwargs.get('labels', [var for var in variables])}
        width = kwargs.get('width', None)
        if width is None:
            header['width'] = [12 for _ in variables]
        else:
            header['width'] = [i for i in width]

        _fill_list(header['width'], len(header['labels']))

        super(TxtTable, self).__init__('TxtTable', header=header)
        self.title = title
        self.variables = variables
        row_fmt = kwargs.get('row_fmt', None)
        if row_fmt is None:
            self.row_fmt = []
            for wid in header['width']:
                if wid - 6 <= 0:
                    self.row_fmt.append('{{:> {}}}'.format(wid))
                else:
                    self.row_fmt.append('{{:> {}.{}g}}'.format(wid, wid - 6))
        else:
            self.row_fmt = row_fmt
        _fill_list(self.row_fmt, len(self.variables))
        str_white = ' ' * spacing
        self.fmt = str_white.join(self.row_fmt)

    def generate_output(self, step, row):
        """Generate output from a dictionary using the requested variables.

        Parameters
        ----------
        step : int
            This is the current step number or a cycle number in a
            simulation.
        row : dict
            A dictionary that hopefully contains the variables we want
            to output.

        Yields
        ------
        out : string
            A line with the formatted output.
        """
        var = []
        for i in self.variables:
            if i == 'step':
                var.append(step)
            else:
                var.append(row.get(i, float('nan')))
        txt = self.fmt.format(*var)
        yield txt

    def __str__(self):
        """Return a string with some info about the TxtTable."""
        msg = ['TxtTable: "{}"'.format(self.title)]
        msg += ['\t* Variables: {}'.format(self.variables)]
        msg += ['\t* Format: {}'.format(self.fmt)]
        return '\n'.join(msg)


class PathTable(TxtTable):
    """PathTable(object) - Special table for path ensembles.

    This object will return a table of text with a header and with
    formatted rows for a path ensemble. The table rows will contain
    data from the `PathEnsemble.nstats` variable. This table is just
    meant as output to the screen during a path ensemble simulation.

    Attributes
    ----------
    Identical to the `TxtTable` object.
    """
    def __init__(self):
        """Initiate parent."""
        title = 'Path Ensemble Statistics'
        var = ['step', 'ACC', 'BWI',
               'BTL', 'FTL', 'BTX', 'FTX']
        table_format = {'labels': ['Cycle', 'Accepted', 'BWI', 'BTL', 'FTL',
                                   'BTX', 'FTX'],
                        'width': (10, 12),
                        'spacing': 2,
                        'row_fmt': ['{:> 10d}', '{:> 12d}']}
        super(PathTable, self).__init__(var, title, **table_format)

    def generate_output(self, step, path_ensemble):
        """Generate the output for the PathTable.

        Here we overload the `generate_output` method in `TxtTable`
        in order to write path ensemble statistics to (presumably)
        the screen.

        Parameters
        ----------
        step : int
            This is the current step number or a cycle number in a
            simulation.
        path_ensemble : object like `pyretis.core.path.PathEnsemble`
            This is the path ensemble to output for.

        Yield
        -----
        out : string
            This string is the formatted row.
        """
        row = {}
        for key in self.variables:
            if key == 'step':
                value = step
            else:
                value = path_ensemble.nstats.get(key, 0)
            row[key] = value
        var = [row.get(i, float('nan')) for i in self.variables]
        yield self.fmt.format(*var)


class ThermoTable(TxtTable):
    """Class ThermoTable(TxtTable) - Special table for energy output.

    This object will return a table of text with a header and with
    formatted rows for energy output. Typical use is in MD simulation
    where we want to display energies at different steps in the
    simulations.

    Attributes
    ----------
    Identical to the `TxtTable` object.
    """
    def __init__(self):
        """Initiate parent."""
        title = 'Energy Output'
        var = ['step', 'temp', 'vpot', 'ekin', 'etot', 'press']
        table_format = {'labels': ['Step', 'Temp', 'Pot',
                                   'Kin', 'Tot', 'Press'],
                        'width': (10, 12),
                        'spacing': 2,
                        'row_fmt': ['{:> 10d}', '{:> 12.6g}']}
        super(ThermoTable, self).__init__(var, title, **table_format)
