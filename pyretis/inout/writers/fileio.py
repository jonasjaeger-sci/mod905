# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""Module defining the base classes for file writers.

This module defines a class that is useful for writing data
to the disk. The typical usage in pyretis is to write the output from
a `Writer` to a file.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

FileIO
    A generic class for handling output to files.
"""
import os
import logging
from pyretis.inout.common import create_backup
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())

__all__ = ['FileIO']


class FileIO(object):
    """FileIO(object) - A generic file writer class.

    This class defines a simple object for writing to files.
    Formatting etc. is handled by objects like `Writers` from
    `pyretis.inout.writers.writers`, The `FileIO` class handle the
    creation/opening of the file with backup/overwriting etc.

    Attributes
    ----------
    filename : string
        Name (path) of the file to open.
    oldfile : string
        Determines if we should backup, overwrite or append if a file
        exist with the given `filename`.
    fileh : object like `file` (`io.IOBase`).
        The file handle we are using.
    """
    OLDFILE = ('append', 'overwrite', 'backup')

    def __init__(self, filename, oldfile='backup', header=None):
        """Just a simple initialize of the file object.

        Parameters
        ----------
        filename : string
            This is the name of the file we want to open.
        oldfile : string, optional
            The is used to control how we do backup.
        header = string, optional
            This is a header we write to the file as the first line.
            Typically this gives some meta information about the
            contents in the file.
        """
        self.filename = filename
        self.fileh = None
        self.open_file(oldfile.lower())
        if header is not None:
            self.write(header)

    def open_file(self, oldfile):
        """Open the file for writing.

        Parameters
        ----------
        oldfile : string
            This determines how we deal with already existing files.
            If they should be backed up, overwritten or appended to.
        """
        status = False
        if oldfile not in self.OLDFILE:
            msg = ['Unknown setting "{}" for "oldfile"'.format(oldfile)]
            msg += ['Should be one of: {}'.format(self.OLDFILE)]
            msgtxt = '\n'.join(msg)
            logger.warning(msgtxt)
            return status
        try:
            if os.path.isfile(self.filename):
                msg = ['File "{}" exist'.format(self.filename)]
                if oldfile == 'overwrite':
                    msg += ['Will overwrite!']
                    self.fileh = open(self.filename, 'w')
                    status = True
                elif oldfile == 'append':
                    msg += ['Will append to file']
                    self.fileh = open(self.filename, 'a')
                    status = True
                else:
                    msg_back = create_backup(self.filename)
                    msg += [msg_back]
                    self.fileh = open(self.filename, 'w')
                    status = True
                msgtxt = ': '.join(msg)
                logger.warning(msgtxt)
            else:
                self.fileh = open(self.filename, 'w')
                status = True
        except (OSError, IOError) as error:
            msg = ['File "{}" could not be opened!'.format(self.filename)]
            msg += ['I/O error ({}): {}'.format(error.errno, error.strerror)]
            msgtxt = '\n'.join(msg)
            logger.critical(msgtxt)
            status = False
        except TypeError as error:  # for cases when self.filename is None
            msg = ['File "{}" could not be opened!'.format(self.filename)]
            msg += ['TypeError: {}'.format(error)]
            msgtxt = '\n'.join(msg)
            logger.critical(msgtxt)
            status = False
        return status

    def write(self, towrite, end='\n'):
        """Write a string to the file.

        Parameters
        ----------
        towrite : string
            The string to output to the file.
        end : string
            Appended to `towrite` when writing, can be used to print a
            new line after the input `towrite`.

        Returns
        -------
        out : boolean
            True if we managed to write, False otherwise.
        """
        if towrite is None:
            return False
        if self.fileh is not None and not self.fileh.closed:
            status = False
            try:
                if end is not None:
                    self.fileh.write('{}{}'.format(towrite, end))
                    status = True
                else:
                    self.fileh.write(towrite)
                    status = True
            except (OSError, IOError) as error:
                msg = 'Write I/O error ({}): {}'.format(error.errno,
                                                        error.strerror)
                logger.critical(msg)
            return status
        else:
            if self.fileh is not None and self.fileh.closed:
                logger.warning('Ignored writing to closed file.')
            if self.fileh is None:
                logger.warning('File handle is empty.')
            return False

    def close(self):
        """Close the file, in case that is explicitly needed."""
        if self.fileh is not None and not self.fileh.closed:
            self.fileh.close()

    def __del__(self):
        """Close a file in case the object is deleted.

        This method will just close the file in case the program
        crashes or exits in some other way. It is used here as it's not
        so nice to add a with statement to the main script running the
        simulation.
        """
        if self.fileh is not None and not self.fileh.closed:
            self.fileh.close()

    def __str__(self):
        """Return basic info."""
        msg = ['FileIO (file: "{}")'.format(self.filename)]
        if self.fileh is not None and not self.fileh.closed:
            msg += ['\t* File is open']
            msg += ['\t* Mode: {}'.format(self.fileh.mode)]
        return '\n'.join(msg)
