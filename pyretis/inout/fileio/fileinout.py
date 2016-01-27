# -*- coding: utf-8 -*-
"""Module defining the base classes for file writers.

The base objects defines how file should be opened, if we are to write
headers to the file, if we should overwrite or backup old files etc.

Important classes and functions defined here:

- read_some_lines: A function that can be used to read data from a file. It
  will try to read as many lines as possible with a given parser for lines.
  It will yield blocks of data.

- FileWriter: A generic file writer class.
"""
import os
import logging
# local imports
from pyretis.inout.common import create_backup
from pyretis.inout.txtinout import create_and_format_row
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['FileWriter']


def _simple_line_parser(line):
    """A simple line parser. Returns floats from columns in a file.

    This function will return floats from columns from a file. It is here
    created as function to avoid a lambda expression in `read_some_lines`
    defined below.

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

    This function will read a file using the given `line_parser`.
    If the given `line_parser` fails at a line in the file, `read_some_lines`
    will stop here.

    This function will read data in blocks and yield a block when a new block
    is found. A special string (`block_label`) is assumed to identify the
    start of blocks.

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


class FileWriter(object):
    """FileWriter(object) - A generic file writer class.

    This class defines a simple object to output to a file.
    Actual formatting are handled by derived objects such as the trajectory
    writers and other writers. This object handles creation/opening of the
    file with backup/overwriting etc.

    Attributes
    ----------
    filename : string
        Name of file to write.
    filetype : string
        Identifies the file type to write - the "format".
    mode : string
        Mode can be used to select if we should write to the file
        (if mode is equal to 'w') or read from the file (mode equal to 'r').
        The default is mode equal to 'w'.
    oldfile : string
        Defines how we handle existing files with the same
        name as given in `filename`. Note that this is only useful when the
        mode is set to 'w'.
    count : int
        This is just a counter of how many times write has been called.
    fileh : file
        This is the file handle which can be used for writing etc.
    header : string
        A header (comment) for the first line of the file.
    """

    def __init__(self, filename, filetype, mode='w', oldfile='backup',
                 count=0, header=None):
        """Initiate the file writer object.

        Parameters
        ----------
        filename : string
            Name of the file to write.
        filetype : string
            Identifies the file type to write (i.e. the format).
        mode : string, optional
            This determines if we write (`'w'`) or read (`'r'`) the file.
        oldfile : string, optional
            Behavior if `filename` is an existing file.
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
        self.header = None
        if header is not None:
            if 'width' in header:
                _, self.header = create_and_format_row(header['text'],
                                                       header['width'],
                                                       header=True,
                                                       spacing=1,
                                                       fmt_str=None)
            else:
                self.header = header['text']
        if self.mode == 'w':
            self.fileopen(oldfile=oldfile)
            if oldfile != 'append' and self.header is not None:
                self.write_line(self.header)

    def fileopen(self, oldfile='backup'):
        """Open a file and make it ready for reading/writing.

        Function to open a file, to make it ready for reading/writing.
        This function is separated from `self.__init__` in case some derived
        classes will open the file at a later stage. Default is to run
        open if the mode it set to 'w'.

        Parameters
        ----------
        oldfile : string, optional
            Behavior if the `filename` is an existing file, i.e. it is only
            useful when self.mode = 'w'

        Returns
        -------
        None, but `self.fileh` is set to the open file.
        """
        if self.mode == 'r':  # Read data
            try:
                self.fileh = open(self.filename, 'r')
            except IOError as error:
                msgtxt = 'I/O error ({}): {}'.format(error.errno,
                                                     error.strerror)
                logger.warning(msgtxt)
        elif self.mode == 'w':  # Write data to file + handle backup:
            try:
                if os.path.isfile(self.filename):
                    msg = ['File "{}" exist'.format(self.filename)]
                    if oldfile == 'overwrite':
                        msg += ['Will overwrite!']
                        self.fileh = open(self.filename, 'w')
                    elif oldfile == 'append':
                        msg += ['Will append to file']
                        self.fileh = open(self.filename, 'a')
                    else:
                        msg_back = create_backup(self.filename)
                        msg += [msg_back]
                        self.fileh = open(self.filename, 'w')
                    msgtxt = ': '.join(msg)
                    logger.warning(msgtxt)
                else:
                    self.fileh = open(self.filename, 'w')
            except IOError as error:
                msg = 'I/O error ({}): {}'.format(error.errno, error.strerror)
                logger.critical(msg)
            except Exception as error:
                msg = 'Error: {}'.format(error)
                logger.critical(msg)
                raise
        else:
            msg = 'Unknown file mode "{}"'.format(self.mode)
            logger.warning(msg)

        if self.fileh is None:
            msg = 'Could not open file!'
            logger.warning(msg)
            raise SystemExit(msg)

    def close(self):
        """Close the file, in case that is explicitly needed."""
        if self.fileh is not None and not self.fileh.closed:
            self.fileh.close()

    def get_mode(self):
        """Return mode of the file."""
        try:
            return self.fileh.mode
        except AttributeError:
            return None

    def _write_string(self, towrite):
        """Write a string to the file.

        Parameters
        ----------
        towrite : string
            The string to output to the file.

        Returns
        -------
        out : boolean
            True if we managed to write, False otherwise.
        """
        if towrite is None:
            return False
        if self.fileh is not None and not self.fileh.closed:
            try:
                self.fileh.write(towrite)
                self.count += 1
                return True
            except IOError as error:
                msg = 'Write I/O error ({}): {}'.format(error.errno,
                                                        error.strerror)
                logger.critical(msg)
            except Exception as error:
                msg = 'Write error: {}'.format(error)
                logger.critical(msg)
                raise
        else:
            return False

    def write_line(self, towrite):
        """Write a line with a newline at the end.

        This function will call `write_string` adding a new-line to the given
        string.

        Parameters
        ----------
        towrite : string
            The string to output to the file
        """
        return self._write_string('{}\n'.format(towrite))

    def __del__(self):
        """Close a file in case the object is deleted.

        This function will just close the file in case the program
        crashes or exits in some other way. It is used here as it's not so
        nice to add a with statement to the main script running the
        simulation.
        """
        if self.fileh is not None and not self.fileh.closed:
            self.fileh.close()

    def __str__(self):
        """Return basic info."""
        msg = '{} (file: "{}", mode: "{}")'.format(self.filetype,
                                                   self.filename,
                                                   self.get_mode())
        return msg
