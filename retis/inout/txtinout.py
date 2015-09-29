# -*- coding: utf-8 -*-
"""
This file contains methods and objects that handle output/input of
text files.

Objects defined here:

- TxtTable: Table of text with a header and formatted rows.

- FileWriter: Defines a simple object to output to a file.

- OrderFile: Writing/reading of order parameter data

Important functions:

- txt_save_columns: Writing a simple column-based output using numpy.
"""
import itertools
import os
import warnings
import numpy as np
from .common import create_backup


__all__ = ['TxtTable', 'OrderFile']

# format for order files, here as a tuple since we don't know how many
# parameters we will write:
ORDER_FMT = ['{:>10d}', '{:>12.6f}']


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


def read_some_lines(filename, line_parser=_simple_line_parser):
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
                 count=0, header=None):
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
        header : dict, optional
            This determines if we should create a header for the file. For some
            text files this can help for the readability.
        """
        self.count = count
        self.filename = filename
        self.filetype = filetype
        self.mode = mode.lower()
        self.fileh = None
        if self.mode == 'w':
            self.fileopen(oldfile=oldfile)
        if header is not None:
            _, self.header = _create_and_format_row(header['text'],
                                                    header['width'],
                                                    header=True,
                                                    spacing=1,
                                                    fmt_str=None)
        else:
            self.header = None

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
                    msg = 'File {} exist'.format(self.filename)
                    if oldfile == 'overwrite':
                        msg = '{}: Will overwrite!'.format(msg)
                        self.fileh = open(self.filename, 'w')
                    elif oldfile == 'append':
                        msg = '{}: Will append to file'.format(msg)
                        self.fileh = open(self.filename, 'a')
                    else:
                        msg_back = create_backup(self.filename)
                        msg = '{}: {}'.format(msg, msg_back)
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
        header = {'text': ['Time', 'Orderp', 'Orderv'],
                  'width': [10, 12]}
        super(OrderFile, self).__init__(filename, 'orderparameter',
                                        mode=mode, oldfile=oldfile,
                                        header=header)

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
        read_some_lines
        """
        for blocks in read_some_lines(self.filename):
            data = np.array(blocks['data'])
            _, col = data.shape
            data_dict = {'comment': blocks['comment']}
            data_dict['data'] = []
            for i in range(col):
                data_dict['data'].append(data[:, i])
            yield data_dict

    def write(self, step, orderdata):
        """
        This will write the order parameter data to the file.

        Parameters
        ----------
        step : int
            This is the current step number.
        orderdata : list of floats
            This is the raw order parameter data.

        Returns
        -------
        out : boolean
            True if line could be written, False otherwise.
        """
        towrite = [ORDER_FMT[0].format(step)]
        for orderp in orderdata:
            towrite.append(ORDER_FMT[1].format(orderp))
        towrite = ' '.join(towrite)
        return self.write_line(towrite)

    def __str__(self):
        """
        Return a string with some info about this object
        """
        msg = 'Order parameter file: {} (mode: {})'.format(self.filename,
                                                           self.mode)
        return msg
