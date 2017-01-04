# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Module for handling input and output of data.

The input and output of data are handled by writers who are responsible
for turning raw data from pyretis into an output (in some form).
Note that the writers are not responsible for actually writing the
output to the screen or to files - this is done by an output task.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Writer
    A generic class for the writers.

CrossWriter
    A class for writing crossing data from flux simulations.

OrderWriter
    A class for writing out order parameter data.
"""
import logging
import numpy as np
# pyretis imports
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['CrossWriter', 'EnergyWriter', 'OrderWriter']


def _make_header(labels, width, spacing=1):
    """This method will format a table header with the given labels.

    Parameters
    ----------
    labels : list of strings
        The strings to use for the table header.
    width : list of ints
        The widths to use for the table.
    spacing : int
        The spacing between columns in the table

    Returns
    -------
    out : string
        A header for the table.
    """
    heading = []
    for i, col in enumerate(labels):
        try:
            wid = width[i]
        except IndexError:
            wid = width[-1]
        if i == 0:
            fmt = '# {{:>{}s}}'.format(wid - 2)
        else:
            fmt = '{{:>{}s}}'.format(wid)
        heading.append(fmt.format(col))
    str_white = ' ' * spacing
    return str_white.join(heading)


def _simple_line_parser(line):
    """A simple line parser. Returns floats from columns in a file.

    Parameters
    ----------
    line : string
        This string represents a line that we will parse.

    Returns
    -------
    out : list
        This list contains a float for each item in `line.split()`.
    """
    return [float(col) for col in line.split()]


def read_some_lines(filename, line_parser=_simple_line_parser,
                    block_label='#'):
    """Open a file and try to read as many lines as possible.

    This method will read a file using the given `line_parser`.
    If the given `line_parser` fails at a line in the file,
    `read_some_lines` will stop here. Further, this method
    will read data in blocks and yield a block when a new
    block is found. A special string (`block_label`) is assumed to
    identify the start of blocks.

    Parameters
    ----------
    filename : string
        This is the name/path of the file to open and read.
    line_parser : function, optional
        This is a function which knows how to translate a given line
        to a desired internal format. If not given, a simple float
        will be used.
    block_label : string
        This string is used to identify blocks.

    Yields
    ------
    data : list
        The data read from the file, arranged in dicts
    """
    nblock = len(block_label)
    ncol = -1  # The number of columns
    new_block = None
    with open(filename, 'r') as fileh:
        for line in fileh:
            stripline = line.strip()
            if stripline[:nblock] == block_label:
                # this is a comment = a new block follows
                # store the current block:
                if new_block is not None:
                    yield new_block
                new_block = {'comment': stripline, 'data': []}
                ncol = -1
            else:
                linedata = line_parser(stripline)
                newcol = len(linedata)
                if ncol == -1:  # first item
                    ncol = newcol
                    if new_block is None:
                        new_block = {'comment': None, 'data': []}
                if newcol == ncol:
                    new_block['data'].append(linedata)
                else:
                    break
    if new_block is not None:
        yield new_block


class Writer(object):
    """A generic class for writing output from pyretis.

    The writer class handles output and input of some data for pyretis.

    Attributes
    ----------
    file_type : string
        A string which identifies the file type which the writer can
        support.
    header : string
        A header (or table heading) that gives information about the
        output data.
    print_header : boolean
        Determines if we are to print the header or not on the first
        use of `generate_output`. Note that the behavior can be
        overridden in child classes so that the print_header is
        ignored.
    """

    def __init__(self, file_type, header=None):
        """Initiate the Writer.

        Paramters
        ---------
        file_type : string
            A string which identifies the output type of this writer.
        header : string
            The header for the output data
        """
        self.file_type = file_type
        self._header = None
        self.print_header = True
        if header is not None:
            if 'width' in header:
                self._header = _make_header(header['labels'],
                                            header['width'],
                                            spacing=header.get('spacing', 1))
            else:
                self._header = header.get('text', None)
        else:
            self.print_header = False

    @property
    def header(self):
        """Define the header as a property."""
        return self._header

    @header.setter
    def header(self, value):
        """Set the header"""
        self._header = value

    @staticmethod
    def line_parser(line):
        """A simple line parser. Returns floats from columns in a file.

        Parameters
        ----------
        line : string
            This string represents a line that we will parse.

        Returns
        -------
        out : list
            This list contains a float for each item in `line.split()`.
        """
        return [float(col) for col in line.split()]

    def load(self, filename):
        """Load entire blocks from the file into memory.

        In the future, a more intelligent way of handling files like
        this may be in order, but for now the entire file is read as
        it's very convenient for the subsequent analysis.

        Parameters
        ----------
        filename : string
            The path/file name of the file we want to open.

        Returns
        -------
        data : list of tuples of int
            This is the data contained in the file. The columns are the
            step number, interface number and direction.

        Note
        ----
        The main reason for not making this a class method
        (as `line_parser`) is that certain writers may need to convert
        the output to internal units from some specified units.
        The specified units may also change between instances of
        these classes.
        """
        for blocks in read_some_lines(filename, line_parser=self.line_parser):
            data_dict = {'comment': blocks['comment'],
                         'data': blocks['data']}
            yield data_dict

    def generate_output(self, step, data):
        """Use the writer to generate output."""
        raise NotImplementedError

    def __str__(self):
        """Return basic info about the writer."""
        return 'Writer: {}'.format(self.file_type)


class CrossWriter(Writer):
    """A class for writing crossing data from flux simulations.

    This class handles writing/reading of crossing data. The format for
    the crossing file is three columns:

    1) First column is the step number (an integer).

    2) Second column is the interface number (an integer). These are
       numbered from 1 (_NOT_ from 0).

    3) The direction we are moving in - `+` for the positive direction
       or `-` for the negative direction. Internally this is converted
       to an integer (`+1` or `-1`).
    """
    # format for crossing files:
    CROSS_FMT = '{:>10d} {:>4d} {:>3s}'

    def __init__(self):
        """Initialize a `CrossWriter`."""
        header = {'labels': ['Step', 'Int', 'Dir'], 'width': [10, 4, 3]}
        super().__init__('CrossWriter', header=header)

    @staticmethod
    def line_parser(line):
        """Define a simple parser for reading the file.

        It is used in the `self.load()` to parse the input file.

        Parameters
        ----------
        line : string
            A line to parse.

        Returns
        -------
        out : tuple of ints
            out is (step number, interface number and direction).

        Note
        ----
        The interface will be subtracted '1' in the analysis.
        This is just for backwards compatibility with the old Fortran
        code.
        """
        linessplit = line.strip().split()
        try:
            step, inter = int(linessplit[0]), int(linessplit[1])
            direction = -1 if linessplit[2] == '-' else 1
            return step, inter, direction
        except IndexError:
            return None

    def generate_output(self, step, cross):
        """Generate output data to be written to a file or screen.

        It will just write a space separated file without fancy
        formatting.

        Parameters
        ----------
        step : int
            This is the current step number. It is only used here for
            debugging and can possibly be removed. However, it's useful
            to have here since this gives a common write interface for
            all writers.
        cross : list of tuples
            The tuples are crossing with interfaces (if any) on the form
            `(timestep, interface, direction)` where the direction
            is '-' or '+'.

        Yields
        ------
        out : string
            The line(s) to be written.

        See Also
        --------
        `check_crossing` in `pyretis.core.path` calculates the tuple
        `cross` which is used in this routine.

        Note
        ----
        We add 1 to the interface number here. This is for
        compatibility with the old Fortran code where the interfaces
        are numbered 1, 2, ... rather than 0, 1, ... .
        """
        msgtxt = 'Generating crossing data at step: {}'.format(step)
        logger.debug(msgtxt)
        for cro in cross:
            yield self.CROSS_FMT.format(cro[0], cro[1] + 1, cro[2])


class EnergyWriter(Writer):
    """A class for writing energy data from pyretis.

    This class handles writing/reading of energy data.
    The data is written in 7 columns:

    1) Time, i.e. the step number.

    2) Potential energy.

    3) Kinetic energy.

    4) Total energy, should equal the sum of the two previous columns.

    5) Temperature.
    """
    # format for the energy files, here also as a tuple since this makes
    # convenient for outputting in a specific order:
    ENERGY_FMT = ['{:>10d}'] + 5*['{:>12.6f}']

    def __init__(self):
        """Initialize a `EnergyWriter`."""
        header = {'labels': ['Time', 'Potential', 'Kinetic', 'Total',
                             'Temperature'],
                  'width': [10, 12]}
        super().__init__('EnergyWriter', header=header)

    def load(self, filename):
        """Load entire energy blocks into memory.

        In the future, a more intelligent way of handling
        files like this may be in order, but for now the entire file is
        read as it's very convenient for the subsequent analysis.

        Parameters
        ----------
        filename : string
            The path/file name of the file we want to open.

        Yields
        ------
        data_dict : dict
            This is the energy data read from the file, stored in
            a dict. This is for convenience, so that each energy term
            can be accessed by `data_dict['data'][key]`.

        See Also
        --------
        `read_some_lines`.
        """
        for blocks in read_some_lines(filename, line_parser=self.line_parser):
            data = np.array(blocks['data'])
            data_dict = {'comment': blocks['comment'],
                         'data': {'time': data[:, 0],
                                  'vpot': data[:, 1],
                                  'ekin': data[:, 2],
                                  'etot': data[:, 3],
                                  'temp': data[:, 4]}}
            yield data_dict

    def format_data(self, step, energy):
        """Format a line of data.

        Parameters
        ----------
        step : int
            This is the current step number.
        energy : dict
            This is the energy data stored as a dictionary.

        Returns
        -------
        out : string
            A formatted line of data.
        """
        towrite = [self.ENERGY_FMT[0].format(step)]
        for i, key in enumerate(['vpot', 'ekin', 'etot', 'temp']):
            value = energy.get(key, 0.0)
            towrite.append(self.ENERGY_FMT[i + 1].format(value))
        return ' '.join(towrite)

    def generate_output(self, step, energy):
        """Yield formatted energy data."""
        yield self.format_data(step, energy)


class EnergyPathWriter(EnergyWriter):
    """A class for writing out energy data for paths."""

    def __init__(self):
        """Initialize."""
        super().__init__()
        self.print_header = False

    def generate_output(self, step, path):
        """Format the order parameter data from a path.

        Parameters
        ----------
        step : int
            The cycle number we are creating output for.
        path : object like :py:class:`pyretis.core.path.PathBase`
            The path we are creating output for.

        Yields
        ------
        out : string
            The strings to be written.
        """
        yield '# Cycle: {}, status: {}'.format(step, path.status)
        yield self.header
        for i, phasepoint in enumerate(path.trajectory()):
            yield self.format_data(i, phasepoint)


class OrderWriter(Writer):
    """A class for writing out order parameter data.

    This class handles writing/reading of order parameter data.
    The format for the order file is column-based and the columns are:

    1) Time.

    2) Main order parameter.

    3) Velocity for main order parameter.

    4) Second order parameter.

    5) Velocity for second order parameter ``A``.

    6) ...

    And so on, that is, columns 2, 4, 6, ... are order parameters, while
    columns 3, 5, 7, ... are the corresponding velocities. The first
    column is always just the time (or step number).
    """
    # format for order files, note that we don't know how many parameters
    # we need to write yet.
    ORDER_FMT = ['{:>10d}', '{:>12.6f}']

    def __init__(self):
        """Initialize a `OrderWriter`."""
        header = {'labels': ['Time', 'Orderp', 'Orderv'], 'width': [10, 12]}
        super().__init__('OrderWriter', header=header)

    def load(self, filename):
        """Load entire order parameter blocks into memory.

        In the future, a more intelligent way of handling files like
        this may be in order, but for now the entire file is read as
        it's very convenient for the subsequent analysis. In case
        blocks are found in the file, they will be yielded, this is
        just to reduce the memory usage.
        The format is:
        `time` `orderp0` `orderv0` `orderp1` `orderp2` ...,
        where the actual meaning of `orderp1` `orderp2` and the
        following order parameters are left to be defined by the user.

        Parameters
        ----------
        filename : string
            The path/file name of the file we want to open.

        Yields
        ------
        data_dict : dict
            The data read from the order parameter file.

        See Also
        --------
        `read_some_lines`.
        """
        for blocks in read_some_lines(filename, line_parser=self.line_parser):
            data = np.array(blocks['data'])
            _, col = data.shape
            data_dict = {'comment': blocks['comment'], 'data': []}
            for i in range(col):
                data_dict['data'].append(data[:, i])
            yield data_dict

    def format_data(self, step, orderdata):
        """Format order parameter data.

        Parameters
        ----------
        step : int
            This is the current step number.
        orderdata : list of floats
            This is the raw order parameter data.

        Yields
        ------
        out : string
            The strings to be written.
        """
        towrite = [self.ORDER_FMT[0].format(step)]
        for orderp in orderdata:
            towrite.append(self.ORDER_FMT[1].format(orderp))
        out = ' '.join(towrite)
        return out

    def generate_output(self, step, orderdata):
        """Yield formatted order parameter data."""
        yield self.format_data(step, orderdata)


class OrderPathWriter(OrderWriter):
    """A class for writing out order parameter data for paths."""

    def __init__(self):
        """Initialize."""
        super().__init__()
        self.print_header = False

    def generate_output(self, step, path):
        """Format the order parameter data from a path.

        Parameters
        ----------
        step : int
            The cycle number we are creating output for.
        path : object like :py:class:`pyretis.core.path.PathBase`
            The path we are creating output for.

        Yields
        ------
        out : string
            The strings to be written.
        """
        yield '# Cycle: {}, status: {}'.format(step, path.status)
        yield self.header
        for i, phasepoint in enumerate(path.trajectory()):
            yield self.format_data(i, phasepoint['order'])
