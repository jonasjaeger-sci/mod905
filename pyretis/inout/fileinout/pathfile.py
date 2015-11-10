# -*- coding: utf-8 -*-
"""Methods and classes for input/output of path data.

This module defines classes for writing and storein path data and
path ensemble data.

Important classes
-----------------

- PathEnsembleFile: Writing/reading of path ensemble data.

- PathFile: Writing/reading of path data
"""
import warnings
try:  # this will fail in python3
    from itertools import izip_longest as zip_longest
except ImportError:  # for python3
    from itertools import zip_longest as zip_longest
# pyretis imports:
from pyretis.core.path import Path, PathEnsemble  # for PathEnsembleFile
from pyretis.inout.txtinout import create_and_format_row
from pyretis.inout.fileinout.fileinout import FileWriter, read_some_lines
from pyretis.inout.fileinout.orderfile import ORDER_FMT


__all__ = ['PathFile', 'PathEnsembleFile']


# define a format used for the path files. Here it's not really needed,
# we are going to assume that these files will be comma separated anyway.
# It is included to be compatible with the previous fortran version.
PATH_FMT = ('{0:>10d} {1:>10d} {2:>10d} {3:1s} {4:1s} {5:1s} {6:>7d} ' +
            '{7:3s} {8:2s} {9:>16.9e} {10:>16.9e} {11:>7d} {12:>7d} ' +
            '{13:>16.9e} {14:>7d} {15:7d}')
# define a format for position and velocities in the path file:
POSVEL_FMT = ['{:8.3f}', '{:8.3f}', '{:8.3f}']


class PathFile(FileWriter):
    """PathFile(FileWriter) - A writer for paths.

    This class handles writing/reading of path data.

    Attributes
    ----------
    Same as for the FileWriter object. In addition
    block_label : string
        This label is used to identify new blocks of data
    block_head : string
        This is a header written for each new block. It can be used to
        identify different blocks.
    header_order : string
        Header used for the order parameter.
    header_energy
        Header used for the energy data.
    """

    def __init__(self, filename, mode='w', oldfile='backup'):
        """Initialize the PathFile object.

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
        super(PathFile, self).__init__(filename, 'pathfile',
                                       mode=mode, oldfile=oldfile,
                                       header=None)
        header = {'text': ['Time', 'Orderp', 'Orderv'],
                  'width': [10, 12]}
        self.header_order = create_and_format_row(header['text'],
                                                  header['width'],
                                                  header=True,
                                                  spacing=1,
                                                  fmt_str=None)
        header = {'text': ['Time', 'Potential', 'Kinetic',
                           'Total', 'Hamiltonian',
                           'Temperature', 'External'],
                  'width': [10, 12]}
        self.header_energy = create_and_format_row(header['text'],
                                                   header['width'],
                                                   header=True,
                                                   spacing=1,
                                                   fmt_str=None)
        self.block_label = '#>'
        self.block_head = ' '.join([self.block_label,
                                    'Cycle: {}, Path status: {}, Length: {}'])

    @staticmethod
    def line_parser(line):
        """Define a simple parser for reading the path file.

        It is used in `self.load()` to parse the input file.

        Parameters
        ----------
        line : string
            A line to parse

        Returns
        -------
        out : list of strings
            Here it will just strip and split the given line.
        """
        return line.strip().split()

    def load(self):
        """Load a path file into the memory.

        The paths are assumed to be organized into blocks defined
        by `self.block_label`. This method will yield blocks successively.

        Yields
        ------
        data_dict : dict
            Data read from the order parameter file.

        See Also
        --------
        read_some_lines
        """
        for blocks in read_some_lines(self.filename,
                                      line_parser=self.line_parser,
                                      block_label=self.block_label):
            data_dict = {'comment': blocks['comment'],
                         'data': blocks['data']}
            yield data_dict

    def write(self, step, path):
        """Write a path to the file.

        Parameters
        ----------
        step : int
            This is the current step number.
        path : object like `Path` from `pyretis.core.path`
            The path to write to the file.

        Returns
        -------
        out : boolean
            True if line could be written, False otherwise.
        """
        block_head = self.block_head.format(step, path.status, len(path.path))
        self.write_line(block_head)
        for i, (pos, vel, orderp, energy) in enumerate(path.path):
            self.write_line('# Frame: {}'.format(i))
            order_write = (['# Order:'] +
                           [ORDER_FMT[1].format(val) for val in orderp])
            self.write_line(' '.join(order_write))
            self.write_line('# Energy: {}'.format(energy))
            self.write_line('# Trajectory in INTERNAL UNITS')
            traj = []
            for fmt, posi in zip_longest(POSVEL_FMT, pos, fillvalue=0.0):
                traj.append(fmt.format(posi))
            for fmt, veli in zip_longest(POSVEL_FMT, vel, fillvalue=0.0):
                traj.append(fmt.format(veli))
            self.write_line(''.join(traj))
        return None

    def __str__(self):
        """Return a string with some info about the path file."""
        msg = 'Path file: {} (mode: {})'.format(self.filename, self.mode)
        return msg


def _line_to_path_object(line):
    """Convert a text line to a Path object.

    Parameters
    ----------
    line : string
        The line of text to convert.

    Returns
    -------
    out : object like `Path` from `pyretis.core.path`
        The path created from the given input text.

    Note
    ----
    TODO: This function is considered for deletion - is it going to be
    useful or are we always going to create path data (rather than Path
    objects) when we read files? It might be useful in the future for restart
    files.
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
    """Convert a text line to simplified representation of a path.

    This is used to parse a file with path data. It will not create real
    `pyretis.core.path.Path` objects but only a dict with information about
    this path. This dict can be used to build up a path ensemble.

    Parameters
    ----------
    line : string
        The line of text to convert.

    Returns
    -------
    out : dict
        This dict contains the path information.
    """
    if line.find('#') != -1:
        linec = line.split('#')[0].strip()
    else:
        linec = line.strip()
    data = [col.strip() for col in linec.split()]
    if len(data) < 16:  # valid data should have 15 columns!
        return None
    path_info = {}
    path_info['cycle'] = int(data[0])
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
    """Convert path data from a PathEnsemble object to a string.

    The string representation is useful from storing path data. This function
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
    """PathEnsembleFile(FileWriter).

    This class handles writing/reading of path ensemble data to a file.
    It also supports some attributes and functions found in the
    `pyretis.core.path.PathEnsemble` object. This makes it possible to run
    the analysis tool directly using the PathEnsembleFile object rather than
    first converting to a `pyretis.core.path.PathEnsemble` and then running
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
        This variable is used when creating a ``PathEnsemble`` object
        in ``to_path_ensemble``.
    """

    def __init__(self, filename, ensemble, interfaces, mode='w',
                 oldfile='backup'):
        """Initialize the PathEnsembleFile object.

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
        header = {'text': ['Step', 'No. acc', 'No. shoot',
                           'l', 'm', 'r', 'Length', 'Acc', 'Mc',
                           'Min-O', 'Max-O', 'Idx-Min', 'Idx-Max',
                           'O-shoot', 'Idx-sh', 'Idx-shN'],
                  'width': [10, 10, 10, 1, 1, 1, 7, 3, 2, 16, 16, 7, 7,
                            16, 7, 7]}
        super(PathEnsembleFile, self).__init__(filename, 'pathensemble',
                                               mode=mode, oldfile=oldfile,
                                               header=header)
        self.ensemble = ensemble
        self.interfaces = interfaces

    def to_path_ensemble(self):
        """Read a file and return a path ensemble object.

        This will read an entire file and return a path ensemble object.
        Note that this might not be the fastest way of using the path ensemble
        file and that this can require a lot of memory. For analysis
        purposes, this object also supports a on-line analysis.

        Returns
        -------
        out : object like `PathEnsemble` from `pyretis.core.path`
            The path ensemble read from the file.
        """
        path_ensemble = PathEnsemble(self.ensemble, self.interfaces)
        for path in self.get_paths():
            path_ensemble.add_path_data(path, path.status)
        return path_ensemble

    def get_paths(self):
        """Yield the different paths stored in the file.

        The lines are read on-the-fly, converted and yielded one-by-one.
        Note that the file will be opened here, i.e. it will assumed that
        it's not open in `self.fileh`.

        Yields
        ------
        out : object like `Path` from `pyretis.core.path`
            The current path in the file.
        """
        try:
            with open(self.filename, 'r') as fileh:
                for line in fileh:
                    path_data = _line_to_path_data(line)
                    if path_data is not None:
                        yield path_data
        except IOError as error:
            msg = 'I/O error ({}): {}'.format(error.errno, error.strerror)
            warnings.warn(msg)
        except Exception as error:
            msg = 'Error: {}'.format(error)
            warnings.warn(msg)
            raise

    def write(self, cycle, path_ensemble, path=None):
        """Write a given path from a path ensemble to the file.

        If the path is not explicitly given, the latest path from the path
        ensemble will be written.

        Parameters
        ----------
        cycle : integer
            This is the current cycle number.
        path_ensemble : object like `PathEnsemble` from `pyretis.core.path`
            We will write the path defined by PathEnsemble.paths[-1]
        path : object like `Path` from `pyretis.core.path`
            This is the path to write to the file.
        """
        if path is None:
            path_dict = path_ensemble.paths[-1]
        else:
            path_dict = path.get_path_data(path.status,
                                           path_ensemble.interfaces)
        towrite = _path_to_line_data(path_dict,
                                     cycle,
                                     path_ensemble.nstats['ACC'],
                                     path_ensemble.nstats['nshoot'])
        return self.write_line(towrite)

    def __str__(self):
        """Return a string with some info about the path ensemble file."""
        msg = ['Path (file) ensemble : {}'.format(self.ensemble)]
        msg += ['\tFile name: {}'.format(self.filename)]
        msg += ['\tFile mode: {}'.format(self.mode)]
        return '\n'.join(msg)
