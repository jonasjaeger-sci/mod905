# -*- coding: utf-8 -*-
"""
This file contains methods and objects that handle output/input of
crossing data.

Objects defined here:

- CrossFile: Writing/reading of crossing data (i.e. data which can be used
  for calculation of the initial flux).
"""
from .txtinout import FileWriter, read_some_lines

__all__ = ['CrossFile']

# format for crossing files:
CROSS_FMT = '{:>10d} {:>4d} {:>3s}'


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
        header = {'text': ['Step', 'Int', 'Dir'],
                  'width': [10, 4, 3]}
        super(CrossFile, self).__init__(filename, 'crossingfile',
                                        mode=mode, oldfile=oldfile,
                                        header=header)

    @staticmethod
    def line_parser(line):
        """
        This function defines a simple parser for reading the file.
        It is used in the self.load() to parse the input file

        Parameters
        ----------
        line : string
            A line to parse

        Returns
        -------
        out : tuple of ints
            out is (step number, interface number and direction).
        """
        linessplit = line.strip().split()
        try:
            step, inter = int(linessplit[0]), int(linessplit[1])
            direction = -1 if linessplit[2] == '-' else 1
            return (step, inter, direction)
        except IndexError:
            return None

    def load(self):
        """
        This method will attempt to load the entire energy file into memory.
        (Quote of the day: 'memory is cheap, function calls are expensive'.)
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

        Note
        ----
        We add 1 to the interface number here. This is for compatibility with
        the old fortran code where the interfaces are numbered 1,2,... rather
        than 0,1,... .
        """
        retval = []
        for cro in cross:
            towrite = CROSS_FMT.format(cro[0], cro[1] + 1, cro[2])
            retval.append(self.write_line(towrite))
        return retval

    def __str__(self):
        """
        Return a string with some info about this object
        """
        msg = 'Crossing file: {} (mode: {})'.format(self.filename,
                                                    self.mode)
        return msg
