# -*- coding: utf-8 -*-
"""
This file contains common methods and functions for the input/output.
"""
from __future__ import absolute_import
import os
import warnings

__all__ = ['create_backup', 'FileWriter']


def create_backup(outputfile):
    """
    This method will check if the given filename exist and if it
    does, it will move that file to a new filename such that the given
    one can be used without overwriting.

    Parameters
    ----------
    outputfile : string
        This is the name of the file we wish to create

    Returns
    -------
    out : string
        This string is None if no backup is made, otherwise it will just
        say what file was moved (and to where).

    Note
    ----
    No warning is issued here. This is just in case the msg returned here
    will be part of some more elaborate message.
    """
    filename = '{}'.format(outputfile)
    fileid = 0
    msg = None
    while os.path.isfile(filename) or os.path.isdir(filename):
        filename = '{}_{}'.format(outputfile, fileid)
        fileid += 1
    if fileid > 0:
        msg = '\nBackup existing file {} to {}'.format(outputfile, filename)
        os.rename(outputfile, filename)
    return msg


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
    oldfile : string
        Defines how we handle existing files with the same
        name as given in filename.
    count : int
        This is just a counter of how many times write has been called.
    fileh : file
        This is the file handle which can be used for writing etc.
    """
    def __init__(self, filename, filetype, oldfile, count=0):
        """
        Initiates the file writer object.

        Paramters
        ---------
        filename : string
            Name of the file to write.
        filetype : string
            Identifies the filetype to write (i.e. the format).
        oldfile : string
            Behavior if the filename is an existing file.
        frame : int
            Counts the number of frames written
        """
        self.count = count
        self.filename = filename
        self.filetype = filetype
        self.fileh = None
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
        if self.fileh is None:
            msg = 'Could not open file!'
            warnings.warn(msg)
            raise

    def close(self):
        """
        Method to close the file, in case that is explicitly needed.
        """
        if not self.fileh.closed:
            self.fileh.close()

    def get_mode(self):
        """
        Method to return mode of the file.
        """
        return self.fileh.mode

    def write_string(self, towrite):
        """
        Method to write a string to the file.

        Parameters
        ----------
        towrite : string
            This is the string to output to the file
        """
        if not self.fileh.closed:
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
        This method is similar to write_string, however, it write a new
        line after the given `towrite`.
        
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
        if not self.fileh.closed:
            self.fileh.close()
