# -*- coding: utf-8 -*-
"""Module for handling crossing files.

This file contains functions for handling the input and output of crossing
data. This is typically needed for the simulation of type 'MDFlux' where
the goal is to obtain the initial flux. This initial flux can then be used
to obtain a crossing rate when combined with the crossing probability.

Important classes defined here:

- CrossFile: Writing/reading of crossing data.
"""
import logging
# pyretis imports
from pyretis.inout.fileio.fileinout import FileWriter, read_some_lines
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['CrossFile']


# format for crossing files:
CROSS_FMT = '{:>10d} {:>4d} {:>3s}'


class CrossFile(FileWriter):
    """CrossFile(FileWriter) - A class for crossing data.

    This class handles writing/reading of crossing data. The format for the
    crossing file is in three columns:

    1) First column is the step number (an integer).

    2) Second column is the interface number (an integer). These are
       numbered from 1 (_NOT_ from 0).

    3) The direction we are moving in - `+` for the positive direction or
       `-` for the negative direction. Internally this is converted to an
       integer (`+1` or `-1`)
    """

    def __init__(self, filename, mode='w', oldfile='backup'):
        """Initialize the `CrossFile` class.

        Parameters
        ----------
        filename : string
            Name of file to read/write.
        mode : string
            Mode can be used to select if we should write to the file
            (if mode is equal to `'w'`) or read from the file (mode equal
            to `'r'`). The default is mode equal to `'w'`.
        oldfile : string
            Defines how we handle existing files with the same name as given
            in `filename`. Note that this is only useful when the mode is
            set to `'w'`.
        """
        header = {'text': ['Step', 'Int', 'Dir'],
                  'width': [10, 4, 3]}
        super(CrossFile, self).__init__(filename, 'crossingfile',
                                        mode=mode, oldfile=oldfile,
                                        header=header)

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
        """
        linessplit = line.strip().split()
        try:
            step, inter = int(linessplit[0]), int(linessplit[1])
            direction = -1 if linessplit[2] == '-' else 1
            return step, inter, direction
        except IndexError:
            return None

    def load(self):
        """Load entire blocks from the cross file into memory.

        In the future, a more intelligent way of handling files like this
        may be in order, but for now the entire file is read as it's very
        convenient for the subsequent analysis.

        Returns
        -------
        data : list of tuples of int
            This is the data contained in the file. The columns are the
            step number, interface number and direction.
        """
        for blocks in read_some_lines(self.filename,
                                      line_parser=self.line_parser):
            data_dict = {'comment': blocks['comment'],
                         'data': blocks['data']}
            yield data_dict

    def write(self, step, cross):
        """Write the cross data to a file.

        It will just write a space separated file without fancy formatting.

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

        See Also
        --------
        `check_crossing` in `pyretis.core.path` for definition of the tuples
        in `cross`.

        Note
        ----
        We add 1 to the interface number here. This is for compatibility with
        the old Fortran code where the interfaces are numbered 1, 2, ...
        rather than 0, 1, ... .
        """
        retval = []
        msgtxt = 'Writing crossing file at step: {}'.format(step)
        logger.debug(msgtxt)
        for cro in cross:
            towrite = CROSS_FMT.format(cro[0], cro[1] + 1, cro[2])
            retval.append(self.write_line(towrite))
        return retval
