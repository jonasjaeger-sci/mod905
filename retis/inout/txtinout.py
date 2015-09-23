# -*- coding: utf-8 -*-
"""
This file contains methods and objects that handle output/input of
text files.

Objects defined here:

- TxtTable: Table of text with a header and formatted rows.

- FileWriter: Defines a simple object to output to a file.

- PathEnsembleFile: Writing/reading of path ensemble data to a file.

- EnergyFile: Writing/reading of energy data to a file.

- OrderFile: Writing/reading of order parameter data

- CrossFile: Writing/reading of crossing data (i.e. data which can be used
  for calculation of the initial flux).

Important functions:

- txt_save_columns: Writing a simple column-based output using numpy.
"""
import itertools
import os
import warnings
from retis.core.path import Path, PathEnsemble  # for PathEnsembleFile
import numpy as np
from .common import create_backup


__all__ = ['TxtTable', 'PathEnsembleFile', 'EnergyFile', 'OrderFile',
           'CrossFile']

# define a format used for the path files. Here it's not really needed,
# we are going to assume that these files will be comma separated anyway.
# It is included to be compatible with the previous fortran version.
PATH_FMT = ('{0:>10d} {1:>10d} {2:>10d} {3:1s} {4:1s} {5:1s} {6:>7d} ' +
            '{7:3s} {8:2s} {9:>16.9e} {10:>16.9e} {11:>7d} {12:>7d} ' +
            '{13:>16.9e} {14:>7d} {15:7d}')


def txt_save_columns(outputfile, header, *variables):
    """
    This will save the different variables to a text file using
    numpy's savetxt. Note that the variables are assumed to be numpy.arrays of
    equal shape. Note that the outputfile may also be a zipped gz file.

    Parameters
    ----------
    outputfile : string
        This is the name of the output file to create.
    header : string
        String that will be written at the beginning of the file.
    variables : tuple of numpy.arrays
        These are the variables that will be save to the text file
    """
    msg = create_backup(outputfile)
    if msg:
        warnings.warn(msg)
    nvar = len(variables)
    mat = np.zeros((len(variables[0]), nvar))
    for i, vari in enumerate(variables):
        try:
            mat[:, i] = vari
        except ValueError:
            msg = 'Could not align variables, skipping (writing zeros)'
            warnings.warn(msg)
    np.savetxt(outputfile, mat, header=header)


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


def _simple_line_parser(line):
    """
    This is just a simple line parser. It will simply return floats from
    columns from a file. It is here created as a def to avoid assigning
    using a lambda expression (see pep8).

    Parameters
    ----------
    line : string
        This string represents a line that we will parse.

    Returns
    -------
    out : list
        This list contains a float for each item in line.split().
    """
    return [float(col) for col in line.split()]


def _read_some_lines(filename, line_parser=_simple_line_parser):
    """
    This is a helper function, it will open a file and
    try to read as many lines as possible. The argument line_parser
    can be used to define how the file should be read.
    It is able to handle blocks - it will assume that a line starting with
    a '#' will identify a new block

    Parameter
    ---------
    filename : string
        This is the filename to open and read
    line_parser : function, optional
        This is a function which knows how to translate a given line
        to a desired internal format. If not given, a simple float
        will be used.

    Yields
    -------
    data : list
        The data read from the file, arranged in dicts
    """
    ncol = -1  # The number of columns
    new_block = None
    with open(filename, 'r') as fileh:
        for line in fileh:
            stripline = line.strip()
            if stripline[0] == '#':
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


class FileWriter(object):
    """
    FileWriter(object)

    This class defines a simple object to output to a file.
    Actual formatting are handled by derived objects such as the trajectory
    writers and other writers. This object handles creation/opening of the
    file with backup/overwriting etc.

    Attributes
    ----------
    filename : string
        Name of file to write.
    filetype : string
        Identifies the filetype to write - the "format".
    mode : string
        Mode can be used to select if we should write to the file
        (if mode is equal to 'w') or read from the file (mode equal to 'r').
        The default is mode equal to 'w'.
    oldfile : string
        Defines how we handle existing files with the same
        name as given in `filename`. Note that this is only usefull when the
        mode is set to 'w'.
    count : int
        This is just a counter of how many times write has been called.
    fileh : file
        This is the file handle which can be used for writing etc.
    """
    def __init__(self, filename, filetype, mode='w', oldfile='backup',
                 count=0):
        """
        Initiates the file writer object. This will just define and
        set some variables

        Paramters
        ---------
        filename : string
            Name of the file to write.
        filetype : string
            Identifies the filetype to write (i.e. the format).
        mode : string, optional
            This determines if we write (= 'w') or read (='r') the file.
        oldfile : string, optional
            Behavior if the `filename` is an existing file.
        frame : int
            Counts the number of frames written
        """
        self.count = count
        self.filename = filename
        self.filetype = filetype
        self.mode = mode.lower()
        self.fileh = None
        if self.mode == 'w':
            self.fileopen(oldfile=oldfile)

    def fileopen(self, oldfile='bakcup'):
        """
        Method to open a file, to make it ready for reading/writing.
        This function is separated from the __init__ in case some derived
        classes will open the file at a later stage. Default is to run
        open if the mode it set to 'w'.

        Parameters
        ----------
        oldfile : string, optional
            Behavior if the `filename` is an existing file, i.e. it is only
            usfull when self.mode = 'w'

        Returns
        -------
        None, but self.fileh is set to the open file.
        """
        if self.mode == 'r':  # Read data
            try:
                self.fileh = open(self.filename, 'r')
            except IOError as error:
                msg = 'I/O error ({}): {}'.format(error.errno, error.strerror)
                warnings.warn(msg)
        elif self.mode == 'w':  # Write data to file + handle backup:
            try:
                if os.path.isfile(self.filename):
                    msg = 'File exist'
                    if oldfile == 'overwrite':
                        msg += '\nWill overwrite!'
                        self.fileh = open(self.filename, 'w')
                    elif oldfile == 'append':
                        msg += '\nWill append to file!'
                        self.fileh = open(self.filename, 'a')
                    else:
                        msg += create_backup(self.filename)
                        self.fileh = open(self.filename, 'w')
                    warnings.warn(msg)
                else:
                    self.fileh = open(self.filename, 'w')
            except IOError as error:
                msg = 'I/O error ({}): {}'.format(error.errno, error.strerror)
                warnings.warn(msg)
            except Exception as error:
                msg = 'Error: {}'.format(error)
                warnings.warn(msg)
                raise
        else:
            msg = 'Unknown file mode "{}"'.format(self.mode)
            warnings.warn(msg)

        if self.fileh is None:
            msg = 'Could not open file!'
            warnings.warn(msg)
            raise

    def close(self):
        """
        Method to close the file, in case that is explicitly needed.
        """
        if self.fileh is not None and not self.fileh.closed:
            self.fileh.close()

    def get_mode(self):
        """
        Method to return mode of the file.
        """
        try:
            return self.fileh.mode
        except AttributeError:
            return None

    def write_string(self, towrite):
        """
        Method to write a string to the file.

        Parameters
        ----------
        towrite : string
            This is the string to output to the file
        """
        if self.fileh is not None and not self.fileh.closed:
            try:
                self.fileh.write(towrite)
                self.count += 1
                return True
            except IOError as error:
                msg = 'Write I/O error ({}): {}'.format(error.errno,
                                                        error.strerror)
                warnings.warn(msg)
            except Exception as error:
                msg = 'Write error: {}'.format(error)
                warnings.warn(msg)
                raise
        else:
            return False

    def write_line(self, towrite):
        """
        This method is similar to write_string, however, it writes a new-line
        after the given `towrite`.

        Parameters
        ----------
        towrite : string
            This is the string to output to the file
        """
        return self.write_string('{}\n'.format(towrite))

    def __del__(self):
        """
        This method in just to close the file in case the program
        crashes. It is used here as it's not so nice to add a
        with statement to the main script running the simulation.
        """
        if self.fileh is not None and not self.fileh.closed:
            self.fileh.close()


def _line_to_path(line):
    """
    This is a helper function to convert a text line to a Path object.

    Parameters
    ----------
    line : string
        The line of text to convert

    Returns
    -------
    out : object of type Path
    """
    path = Path()
    data = line.split()
    path.ordermin = (float(data[9]), 0)
    path.ordermax = (float(data[10]), -1)
    path.path = [None] * int(data[6])
    path.path[0] = [None, path.ordermin[0]]
    path.path[-1] = [None, path.ordermax[0]]
    path.status = str(data[7])
    path.generated = [str(data[8]), float(data[13]),
                      int(data[14]), int(data[15])]
    return path


def _line_to_path_data(line):
    """
    This is a helper function to convert a text line to simplified
    representation of a path. This can be used to parse a file with path data.

    Parameters
    ----------
    line : string
        The line of text to convert.

    Returns
    -------
    out : dict
        This dict contains the path information.
    """
    data = [col.strip() for col in line.split()]
    path_info = {}
    path_info['generated'] = [str(data[8]), float(data[13]),
                              int(data[14]), int(data[15])]
    path_info['status'] = str(data[7])
    path_info['length'] = int(data[6])
    path_info['ordermax'] = (float(data[10]), int(data[12]))
    path_info['ordermin'] = (float(data[9]), int(data[11]))
    start = str(data[3])
    middle = str(data[4])
    end = str(data[5])
    path_info['interface'] = (start, middle, end)
    return path_info


def _path_to_line_data(path, cycle, acc, shoot):
    """
    This is a helper function to convert path data from a PathEnsemble object
    to a simple string which can be used for storing path data. This function
    is the "inverse" of the ``_line_to_path_data`` function.

    Parameters
    ----------
    path : dict
        This is the simplified path description as contained in the
        PathEnsemble.path list.
    cycle : integer
        This is the current cycle number.
    acc : integer
        This is a counter for the number of accepted paths.
    shoot : integer
        This is a counter for the number of shooting moved.

    Returns
    -------
    out : string
        A simple string, column separated, with the path information.
    """
    interface_list = []
    for val in path['interface']:
        if val is None:
            interface_list.append('*')
        else:
            interface_list.append(val)
    out = PATH_FMT.format(cycle, acc, shoot,
                          interface_list[0],
                          interface_list[1],
                          interface_list[2],
                          path['length'],
                          path['status'],
                          path['generated'][0],
                          path['ordermin'][0],
                          path['ordermax'][0],
                          path['ordermin'][1],
                          path['ordermax'][1],
                          path['generated'][1],
                          path['generated'][2],
                          path['generated'][3])
    return out


class PathEnsembleFile(FileWriter):
    """
    PathEnsembleFile(FileWriter)

    This class handles writing/reading of path ensemble data to a file.
    It also supports some attributes and functions found in the
    ``retis.core.path.PathEnsemble`` object. This makes it possible to run
    the analysis tool directly using the PathEnsembleFile object rather than
    first converting to a ``retis.core.path.PathEnsemble`` and then running
    the analysis. The common methods are ``get_paths`` and ``__str__``.
    The common properties are `ensemble` and `interfaces`
    In the future, this should be made smarter, for instance could path data
    be read in portions, or the full path file could be read if it's small
    enough to fit in the memory. A line-by-line analysis as it is righ now
    might not be the most efficient way...

    Attributes
    ----------
    Same as for the FileWriter object, in addition:
    ensemble : str
        This is a string representation of the path ensemble. Typically
        something like '0-', '0+', '1', '2', ..., '001' and so on.
    interfaces : list of ints
        These are the interfaces specified with the values
        for the order parameters: [left, middle, right]
    """
    def __init__(self, filename, ensemble, interfaces, mode='w',
                 oldfile='backup'):
        """
        Initialize the PathEnsembleFile object

        Parameters
        ----------
        filename : string
            Name of file to read/write.
        ensemble : str
            This is a string representation of the path ensemble. Typically
            something like '0-', '0+', '1', '2', ..., '001' and so on.
        interfaces : list of ints
            These are the interfaces specified with the values
            for the order parameters: [left, middle, right]
        mode : string
            Mode can be used to select if we should write to the file
            (if mode is equal to 'w') or read from the file (mode equal
            to 'r'). The default is mode equal to 'w'.
        oldfile : string
            Defines how we handle existing files with the same name as given
            in `filename`. Note that this is only usefull when the mode is
            set to 'w'.
        """
        super(PathEnsembleFile, self).__init__(filename, 'pathensemble',
                                               mode=mode,
                                               oldfile=oldfile)
        self.ensemble = ensemble
        self.interfaces = interfaces

    def to_path_ensemble(self):
        """
        This will read an entire file and return a path ensemble object.
        Note that this might not be the fastes way of using the path ensemble
        file and that this can require a lot of memory. For analysis
        purposes, this object also supports a on-line analysis

        Returns
        -------
        out : object of type PathEnsemble
            The path ensemble read from the file.
        """
        path_ensemble = PathEnsemble(self.ensemble, self.interfaces)
        for path in self.get_paths():
            path_ensemble.add_path_data(path, path.status)
        return path_ensemble

    def get_paths(self):
        """
        This will yield the different paths stored in the file. The lines
        are read on-the-fly, converted and yielded one-by-one.
        Note that the file will be opened here, i.e. it will assumed that
        it's not open in self.fileh

        Yields
        ------
        out : object of type Path, the current path in the file
        """
        try:
            with open(self.filename, 'r') as fileh:
                for line in fileh:
                    yield _line_to_path_data(line)
        except IOError as error:
            msg = 'I/O error ({}): {}'.format(error.errno, error.strerror)
            warnings.warn(msg)
        except Exception as error:
            msg = 'Error: {}'.format(error)
            warnings.warn(msg)
            raise

    def write(self, path_ensemble, cycle=0, path=None):
        """
        This method will write a given path from a path ensemble to the file.
        If the path is not explicitly given, the latest path from the path
        ensemble will be written.

        Parameters
        ----------
        path_ensemble : object of type PathEnsemble
            We will write the path defined by PathEnsemble.paths[-1]
        path : object of type Path
            This is the path to write to the file.
        cycle : integer
            This is the current cycle number. Default is zero.
        """
        if path is None:
            path_dict = path_ensemble.paths[-1]
        else:
            path_dict = path.get_path_data(path.status,
                                           path_ensemble.interfaces)
        towrite = _path_to_line_data(path_dict,
                                     cycle,
                                     path_ensemble.nacc,
                                     path_ensemble.nshoot)
        return self.write_line(towrite)

    def __str__(self):
        """
        Return a string with some info about this object
        """
        msg = ['Path (file) ensemble : {}'.format(self.ensemble)]
        msg += ['\tFile name: {}'.format(self.filename)]
        msg += ['\tFile mode: {}'.format(self.mode)]
        return '\n'.join(msg)


class EnergyFile(FileWriter):
    """
    EnergyFile(FileWriter)

    This class handles writing/reading of energy data.

    Attributes
    ----------
    Same as for the FileWriter object.
    """
    def __init__(self, filename, mode='w', oldfile='backup'):
        """
        Initialize the EnergyFile object

        Parameters
        ----------
        filename : string
            Name of file to read/write.
        mode : string
            Mode can be used to select if we should write to the file
            (if mode is equal to 'w') or read from the file (mode equal
            to 'r'). The default is mode equal to 'w'.
        oldfile : string
            Defines how we handle existing files with the same name as given
            in `filename`. Note that this is only usefull when the mode is
            set to 'w'.
        """
        super(EnergyFile, self).__init__(filename, 'energyfile',
                                         mode=mode,
                                         oldfile=oldfile)

    def load(self):
        """
        This method will attempt to load the entire energy file into memory.
        (Quote of the day: 'memory is cheap, function calls are expensive'.)
        In the future, a more intelligent way of handling files like this
        may be in order, but for now the entire file is read as it's very
        convenient for the subsequent analysis. In case blocks are found in
        the file, they will be yielded, this is just to reduce the memory
        usage.

        Yields
        -------
        data_dict : dict
            This is the energy data read from the file, stored in
            a dict. This is for convenience, so that each energy term
            can be accessed by data[key]

        See Also
        --------
        _read_some_lines
        """
        for blocks in _read_some_lines(self.filename):
            data = np.array(blocks['data'])
            data_dict = {'comment': blocks['comment'],
                         'data': {'time': data[:, 0],
                                  'pot': data[:, 1],
                                  'kin': data[:, 2],
                                  'tot': data[:, 3],
                                  'ham': data[:, 4],
                                  'temp': data[:, 5],
                                  'ext': data[:, 6]}}
            yield data_dict

    def __str__(self):
        """
        Return a string with some info about this object
        """
        msg = 'Energy file: {} (mode: {})'.format(self.filename, self.mode)
        return msg


class OrderFile(FileWriter):
    """
    OrderFile(FileWriter)

    This class handles writing/reading of order parameter data.

    Attributes
    ----------
    Same as for the FileWriter object.
    """
    def __init__(self, filename, mode='w', oldfile='backup'):
        """
        Initialize the OrderFile object

        Parameters
        ----------
        filename : string
            Name of file to read/write.
        mode : string
            Mode can be used to select if we should write to the file
            (if mode is equal to 'w') or read from the file (mode equal
            to 'r'). The default is mode equal to 'w'.
        oldfile : string
            Defines how we handle existing files with the same name as given
            in `filename`. Note that this is only usefull when the mode is
            set to 'w'.
        """
        super(OrderFile, self).__init__(filename, 'orderparameter',
                                        mode=mode, oldfile=oldfile)

    def load(self):
        """
        This method will attempt to load the entire energy file into memory.
        (Quote of the day: 'memory is cheap, function calls are expensive'.)
        In the future, a more intelligent way of handling files like this
        may be in order, but for now the entire file is read as it's very
        convenient for the subsequent analysis. In case blocks are found in
        the file, they will be yielded, this is just to reduce the memory
        usage.
        The format is `time` `orderp0` `orderv0` `orderp1` `orderv1` etc...

        Yields
        -------
        data_dict : dict
            Data read from the order parameter file.

        See Also
        --------
        _read_some_lines
        """
        for blocks in _read_some_lines(self.filename):
            data = np.array(blocks['data'])
            _, col = data.shape
            data_dict = {'comment': blocks['comment']}
            data_dict['data'] = []
            for i in range(col):
                data_dict['data'].append(data[:, i])
            yield data_dict

    def __str__(self):
        """
        Return a string with some info about this object
        """
        msg = 'Order parameter file: {} (mode: {})'.format(self.filename,
                                                           self.mode)
        return msg


class CrossFile(FileWriter):
    """
    CrossFile(FileWriter)

    This class handles writing/reading of crossing data.

    Attributes
    ----------
    Same as for the FileWriter object.
    """
    def __init__(self, filename, mode='w', oldfile='backup'):
        """
        Initialize the CrossFile object

        Parameters
        ----------
        filename : string
            Name of file to read/write.
        mode : string
            Mode can be used to select if we should write to the file
            (if mode is equal to 'w') or read from the file (mode equal
            to 'r'). The default is mode equal to 'w'.
        oldfile : string
            Defines how we handle existing files with the same name as given
            in `filename`. Note that this is only usefull when the mode is
            set to 'w'.
        """
        super(CrossFile, self).__init__(filename, 'crossingfile',
                                        mode=mode, oldfile=oldfile)

    def load(self):
        """
        This method will attempt to load the entire energy file into memory.
        (Quote of the day: 'memory is cheap, function calls are expensive'.)
        In the future, a more intelligent way of handling files like this
        may be in order, but for now the entire file is read as it's very
        convenient for the subsequent analysis.

        Yields
        -------
        data_dict : dict
            Data read from the order parameter file.

        """
        with open(self.filename, 'r') as fileh:
            for lines in fileh:
                linessplit = lines.strip().split()
                try:
                    step, inter = int(linessplit[0]), int(linessplit[1])
                    direction = -1 if linessplit[2] == '-' else '+'
                    yield (step, inter, direction)
                except IndexError:
                    pass

    def write(self, cross):
        """
        This method will write the cross data to a file. It will just write a
        space separated file without fancy formatting.

        Parameters
        ----------
        cross : list of tuples
            The tuples are crossing with interfaces (if any). The typles
            contain (timestep, interface, direction), where the direction
            is '-' or '+'.

        See Also
        --------
        ``check_crossing`` in retis.core.path for definition of the tuples in
        cross.
        """
        retval = []
        for cro in cross:
            towrite = '{} {} {}'.format(cro[0], cro[1], cro[2])
            retval.append(self.write_line(towrite))
        return retval

    def __str__(self):
        """
        Return a string with some info about this object
        """
        msg = 'Crossing file: {} (mode: {})'.format(self.filename,
                                                    self.mode)
        return msg
