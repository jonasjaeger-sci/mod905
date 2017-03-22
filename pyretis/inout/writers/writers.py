# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Module for handling input and output of data.

The input and output of data are handled by writers who are responsible
for turning raw data from PyRETIS into an output (in some form).
Note that the writers are not responsible for actually writing the
output to the screen or to files - this is done by an output task.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Writer (:py:class:`.Writer`)
    A generic class for the writers.

CrossWriter (:py:class:`.CrossWriter`)
    A class for writing crossing data from flux simulations.

EnergyWriter (:py:class:`.EnergyWriter`)
    A class for writing energy data.

EnergyPathWriter (:py:class:`.EnergyPathWriter`)
    A class for writing out energy data for paths.

OrderWriter (:py:class:`.OrderWriter`)
    A class for writing out order parameter data.

OrderPathWriter (:py:class:`.OrderPathWriter`)
    A class for writing out order parameter data for paths.

TrajWriter (:py:class:`.TrajWriter`)
    Generic class for writing trajectory output.

PathExtWriter (:py:class:`.PathExtWriter`)
    A class for writing external paths to file.

PathIntWriter (:py:class:`.PathIntWriter`)
    A class for writing internal paths to file.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

adjust_coordinates (:py:func:`.adjust_coordinates`)
    Helper method to add dimensions when writing data in 1D or 2D to an
    output format that requires 3D data.

read_some_lines (:py:func:`.read_some_lines`)
    Open a file and try to read as many lines as possible. This method
    is useful when we are reading possibly unfinished results.
"""
import logging
import os
import numpy as np
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = [
    'CrossWriter',
    'EnergyWriter',
    'EnergyPathWriter',
    'OrderWriter',
    'OrderPathWriter',
    'TrajWriter',
    'PathExtWriter',
    'read_some_lines',
    'adjust_coordinate'
]


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
    new_block = {'comment': [], 'data': []}
    yield_block = False
    read_comment = False
    with open(filename, 'r') as fileh:
        for line in fileh:
            stripline = line.strip()
            if stripline[:nblock] == block_label:
                # this is a comment, then a new block will follow,
                # unless this is a multi-line comment.
                if read_comment:  # part of multiline comment...
                    new_block['comment'].append(stripline)
                else:
                    if yield_block:
                        # Yield the current block
                        yield_block = False  # just for completeness
                        yield new_block
                    new_block = {'comment': [stripline], 'data': []}
                    yield_block = True  # Data has been added
                    ncol = -1
                    read_comment = True
            else:
                read_comment = False
                if line_parser is None:
                    new_block['data'].append(line)  # Note: Full line added
                    yield_block = True  # Data has been added
                else:
                    linedata = line_parser(stripline)
                    newcol = len(linedata)
                    if ncol == -1:  # first item
                        ncol = newcol
                    if newcol == ncol:
                        new_block['data'].append(linedata)
                        yield_block = True  # Data has been added
                    else:
                        # We assume that this is mal-formed data
                        break
    # if the block has not been yielded, yield it
    if yield_block:
        # Yield the current block if any
        yield_block = False  # just for completeness
        yield new_block


class Writer(object):
    """A generic class for writing output from PyRETIS.

    The writer class handles output and input of some data for PyRETIS.

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

        Yields
        ------
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
    # Format for crossing files:
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
    """A class for writing energy data from PyRETIS.

    This class handles writing/reading of energy data.
    The data is written in 7 columns:

    1) Time, i.e. the step number.

    2) Potential energy.

    3) Kinetic energy.

    4) Total energy, should equal the sum of the two previous columns.

    5) Temperature.
    """
    # Format for the energy files:
    ENERGY_FMT = ['{:>10d}'] + 5*['{:>14.6f}']
    ENERGY_TERMS = ('vpot', 'ekin', 'etot', 'temp')
    HEADER = {'labels': ['Time', 'Potential', 'Kinetic', 'Total',
                         'Temperature'],
              'width': [10, 14]}

    def __init__(self):
        """Initialize a `EnergyWriter`."""
        super().__init__('EnergyWriter', header=self.HEADER)

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
            _, col = data.shape
            col_max = min(col, len(self.ENERGY_TERMS) + 1)
            data_dict = {'comment': blocks['comment'],
                         'data': {'time': data[:, 0]}}
            for i in range(col_max-1):
                data_dict['data'][self.ENERGY_TERMS[i]] = data[:, i+1]
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
        for i, key in enumerate(self.ENERGY_TERMS):
            value = energy.get(key, None)
            if value is None:
                towrite.append(self.ENERGY_FMT[i + 1].format(float('nan')))
            else:
                towrite.append(self.ENERGY_FMT[i + 1].format(value))
        return ' '.join(towrite)

    def generate_output(self, step, energy):
        """Yield formatted energy data."""
        yield self.format_data(step, energy)


class EnergyPathWriter(EnergyWriter):
    """A class for writing out energy data for paths."""
    ENERGY_TERMS = ('vpot', 'ekin')
    HEADER = {'labels': ['Time', 'Potential', 'Kinetic'],
              'width': [10, 14]}

    def __init__(self):
        """Initialize."""
        super().__init__()
        self.print_header = False

    def generate_output(self, step, path, status):
        """Format the order parameter data from a path.

        Parameters
        ----------
        step : int
            The cycle number we are creating output for.
        path : object like :py:class:`.PathBase`
            The path we are creating output for.

        Yields
        ------
        out : string
            The strings to be written.
        """
        yield '# Cycle: {}, status: {}'.format(step, status)
        yield self.header
        for i, phasepoint in enumerate(path.trajectory()):
            yield self.format_data(i, phasepoint)


class OrderWriter(Writer):
    """A class for writing out order parameter data.

    This class handles writing/reading of order parameter data.
    The format for the order file is column-based and the columns are:

    1) Time.

    2) Main order parameter.

    3) Collective variable 1

    4) Collective variable 2

    5) ...
    """
    # Format for order files, note that we don't know how many parameters
    # we need to write yet.
    ORDER_FMT = ['{:>10d}', '{:>12.6f}']

    def __init__(self):
        """Initialize a `OrderWriter`."""
        header = {'labels': ['Time', 'Orderp'], 'width': [10, 12]}
        super().__init__('OrderWriter', header=header)

    def load(self, filename):
        """Load entire order parameter blocks into memory.

        In the future, a more intelligent way of handling files like
        this may be in order, but for now the entire file is read as
        it's very convenient for the subsequent analysis. In case
        blocks are found in the file, they will be yielded, this is
        just to reduce the memory usage.
        The format is:
        `time` `orderp0` orderp1` `orderp2` ...
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
            data_dict = {'comment': blocks['comment'],
                         'data': np.array(blocks['data'])}
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

    def generate_output(self, step, path, status):
        """Format the order parameter data from a path.

        Parameters
        ----------
        step : int
            The cycle number we are creating output for.
        path : object like :py:class:`.PathBase`
            The path we are creating output for.

        Yields
        ------
        out : string
            The strings to be written.
        """
        yield '# Cycle: {}, status: {}'.format(step, status)
        yield self.header
        for i, phasepoint in enumerate(path.trajectory()):
            yield self.format_data(i, phasepoint['order'])


def adjust_coordinate(coord):
    """Method to adjust the dimensionality of coordinates.

    This is a helper method for trajectory writers.

    A lot of the different formats expects us to have 3 dimensional
    data. This method just adds dummy dimensions equal to zero.

    Parameters
    ----------
    coord : numpy.array
        The real coordinates.

    Returns
    -------
    out : numpy.array
        The "zero-padded" coordinates.
    """
    if len(coord.shape) == 1:
        npart, dim = len(coord), 1
    else:
        npart, dim = coord.shape
    if dim == 3:
        return coord
    else:
        adjusted = np.zeros((npart, 3))
        try:
            for i in range(dim):
                adjusted[:, i] = coord[:, i]
        except IndexError:
            if dim == 1:
                adjusted[:, 0] = coord
        return adjusted


def read_txt_snapshots(filename, data_keys=None):
    """A method for reading snapshots from a text file.

    Parameters
    ----------
    filename : string
        The file to read from.
    data_keys : tuple of strings.
        This tuple determines the data we are to read. It can
        be of type ``('atomname', 'x', 'y', 'z', ...)``.

    Yields
    ------
    out : dict
        A dictionary with the snapshot.
    """
    lines_to_read = 0
    snapshot = None
    if data_keys is None:
        data_keys = ('atomname', 'x', 'y', 'z', 'vx', 'vy', 'vz')
    read_header = False
    with open(filename, 'r') as fileh:
        for lines in fileh:
            if read_header:
                snapshot = {'header': lines.strip()}
                read_header = False
                continue
            if lines_to_read == 0:  # new shapshot
                if snapshot is not None:
                    yield snapshot
                lines_to_read = int(lines.strip())
                read_header = True
                snapshot = None
            else:
                lines_to_read -= 1
                data = lines.strip().split()
                for i, (val, key) in enumerate(zip(data, data_keys)):
                    if i == 0:
                        value = val.strip()
                    else:
                        value = float(val)
                    try:
                        snapshot[key].append(value)
                    except KeyError:
                        snapshot[key] = [value]
    if snapshot is not None:
        yield snapshot


class TrajWriter(Writer):
    """Generic class for writing system shapshots.

    Attributes
    ----------
    frame : integer
        The number of frames written.
    write_vel : boolean
        If True, we will also write velocities
    fmt : string
        Format to use for position output.
    fmt_vel : string
        Format to use for position and velocity output.
    """
    data_keys = ('atomname', 'x', 'y', 'z', 'vx', 'vy', 'vz')
    _FMT_FULL = '{} {} {} {}'
    _FMT_FULL_VEL = '{} {} {} {} {} {} {}'
    _FMT = '{:5s} {:15.9f} {:15.9f} {:15.9f}'
    _FMT_VEL = '{:5s} {:15.9f} {:15.9f} {:15.9f} {:15.9f} {:15.9f} {:15.9f}'

    def __init__(self, write_vel, fmt=None):
        """Initialize the writer.

        Parameters
        ----------
        name : string
            Just a name to identify the writer when printing it.
        write_vel : boolean
            If True, the writer will attempt to output velocities. This may
            or may not be supported by the writer.
        """
        super().__init__('TrajWriter', header=None)
        self.print_header = False
        self.frame = 0  # number of frames written
        self.write_vel = write_vel
        if fmt is 'full':
            self.fmt = self._FMT_FULL
            self.fmt_vel = self._FMT_FULL_VEL
        else:
            self.fmt = self._FMT
            self.fmt_vel = self._FMT_VEL

    def generate_output(self, step, system):
        """Generate the snapshot output."""
        for lines in self.format_snapshot(step, system):
            yield lines

    def _format_without_vel(self, particles):
        """Format positions of particles for output.

        Parameters
        ----------
        particles : object like :py:class:`.Particles`
            The particles we will write information about.

        Yields
        ------
        out : string
            The formatted output, to be written.
        """
        pos = adjust_coordinate(particles.pos)
        for namei, posi in zip(particles.name, pos):
            yield self.fmt.format(namei, *posi)

    def _format_with_vel(self, particles):
        """Format positions of particles for output.

        Parameters
        ----------
        particles : object like :py:class:`.Particles`
            The particles we will write information about.

        Yields
        ------
        out : string
            The formatted output, to be written.
        """
        pos = adjust_coordinate(particles.pos)
        vel = adjust_coordinate(particles.vel)
        for namei, posi, veli in zip(particles.name, pos, vel):
            yield self.fmt_vel.format(namei, *posi, *veli)

    def format_snapshot(self, step, system):
        """Format the given snapshot.

        Parameters
        ----------
        step : int
            The current simulation step.
        system : object like :py:class:`.System`
            The system object with the positions to write

        Returns
        -------
        out : list of strings
            The formatted snapshot
        """
        npart = system.particles.npart
        buff = ['{}'.format(npart)]
        buff.append('Snapshot, step: {}'.format(step))
        if self.write_vel:
            formatter = self._format_with_vel
        else:
            formatter = self._format_without_vel
        for lines in formatter(system.particles):
            buff += [lines]
        return buff

    def load(self, filename):
        """Read snapshots from the trajectory file.

        Parameters
        ----------
        filename : string
            The path/filename to open.

        Yields
        ------
        out : dict
            This dict contains the snapshot.
        """
        for snapshot in read_txt_snapshots(filename,
                                           data_keys=self.data_keys):
            yield snapshot


class PathExtWriter(Writer):
    """A class for writing external trajectories.

    Attributes
    ----------
    print_header : boolean
        Determines if we should print the header on the first step.
    """

    def __init__(self):
        """Initialization of the PathExtWriter writer.

        Parameters
        ----------
        units : string
            The system of units used internally for positions and
            velocities.
        """
        header = {'labels': ['Step', 'Filename', 'index', 'vel'],
                  'width': [10, 20, 10, 5], 'spacing': 2}

        super().__init__('PathExtWriter', header=header)
        self.print_header = False

    def generate_output(self, step, path, status):
        yield '# Cycle: {}, status: {}'.format(step, status)
        yield self.header
        for i, phasepoint in enumerate(path.trajectory()):
            filename, idx = phasepoint['pos']
            filename_short = os.path.basename(filename)
            if idx is None:
                idx = 0
            vel = -1 if phasepoint['vel'] else 1
            yield '{:>10}  {:>20s}  {:>10}  {:>5}'.format(i, filename_short,
                                                          idx, vel)

    @staticmethod
    def line_parser(line):
        """A simple parser for reading path data.

        Parameters
        ----------
        line : string
            The line to parse.

        Returns
        -------
        out : list
            The columns of data.
        """
        return [col for col in line.split()]


class PathIntWriter(Writer):

    """A class for writing internal trajectories.

    Attributes
    ----------
    print_header : boolean
        Determines if we should print the header on the first step.
    """

    def __init__(self):
        """Initialization of the PathIntWriter writer.

        Parameters
        ----------
        units : string
            The system of units used internally for positions and
            velocities.
        """
        super().__init__('PathIntWriter', header=None)
        self.print_header = False
        self.fmt = None

    def generate_output(self, step, path, status):
        yield '# Cycle: {}, status: {}'.format(step, status)
        for i, phasepoint in enumerate(path.trajectory()):
            yield 'Snapshot: {}'.format(i)
            pos = phasepoint['pos']
            vel = phasepoint['vel']
            for posj, velj in zip(pos, vel):
                if self.fmt is None:
                    self.fmt = ('{} ' * (len(posj) + len(velj))).strip()
                yield self.fmt.format(*posj, *velj)

    @staticmethod
    def read_snapshots(data):
        """Read snapshots from data from a file.

        Parameters
        ----------
        data : strings
            The data to read
        """
        snapshots = []
        pos, vel = [], []
        dim = None
        for lines in data:
            if lines.startswith('Snapshot'):
                if len(pos) > 0:
                    snapshots.append({'pos': np.array(pos),
                                      'vel': np.array(vel)})
                    pos, vel = [], []
            else:
                raw = [float(col) for col in lines.split()]
                if dim is None:
                    dim = len(raw) // 2
                    if dim > 3 or dim < 1:
                        raise ValueError('Malformed trajectory data!')
                pos.append(raw[:dim])
                vel.append(raw[dim:])
        if len(pos) > 0:
            snapshots.append({'pos': np.array(pos),
                              'vel': np.array(vel)})
        return snapshots

    def load(self, filename):
        """Load entire snapshots into memory.

        Parameters
        ----------
        filename : string
            The path/file name of the file we want to open.

        Yields
        ------
        data : list of tuples of int
            This is the data contained in the file. The columns are the
            step number, interface number and direction.
        """
        for blocks in read_some_lines(filename, line_parser=None):
            data_dict = {'comment': blocks['comment'],
                         'data': self.read_snapshots(blocks['data'])}
            yield data_dict
