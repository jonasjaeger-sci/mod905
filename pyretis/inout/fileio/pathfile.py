# -*- coding: utf-8 -*-
"""Functions and classes for input/output of path data.

This module defines classes for writing path data and path ensemble data.

Important classes defined here:

- PathEnsembleFile: Writing/reading of path ensemble data.

"""
import logging
# pyretis imports:
from pyretis.core.path import Path, PathEnsemble  # for PathEnsembleFile
from pyretis.inout.fileio.fileinout import FileIO
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['PathEnsembleFile']


# Define a format used for the path files. Here it's not really needed,
# we are going to assume that these files will be comma separated anyway.
# It is included to be compatible with the previous fortran version.
PATH_FMT = ('{0:>10d} {1:>10d} {2:>10d} {3:1s} {4:1s} {5:1s} {6:>7d} ' +
            '{7:3s} {8:2s} {9:>16.9e} {10:>16.9e} {11:>7d} {12:>7d} ' +
            '{13:>16.9e} {14:>7d} {15:7d}')
# Define a format for position and velocities in the path file:
POSVEL_FMT = ['{:8.3f}', '{:8.3f}', '{:8.3f}']


def _line_to_path_object(line):
    """Convert a text line to a `Path` object.

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
    path_info = {'cycle': int(data[0]),
                 'generated': [str(data[8]), float(data[13]),
                               int(data[14]), int(data[15])],
                 'status': str(data[7]),
                 'length': int(data[6]),
                 'ordermax': (float(data[10]), int(data[12])),
                 'ordermin': (float(data[9]), int(data[11]))}
    start = str(data[3])
    middle = str(data[4])
    end = str(data[5])
    path_info['interface'] = (start, middle, end)
    return path_info


def _path_to_line_data(path, cycle, acc, shoot):
    """Convert path data from a `PathEnsemble` object to a string.

    The string representation is useful from storing path data. This function
    is the "inverse" of the `_line_to_path_data` function.

    Parameters
    ----------
    path : dict
        This is the simplified path description as contained in the
        `PathEnsemble.path` list.
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


class PathEnsembleFile(FileIO):
    """PathEnsembleFile(FileIO) - A class for path ensemble data.

    This class handles writing/reading of path ensemble data to a file.
    It also supports some attributes and functions found in the
    `pyretis.core.path.PathEnsemble` object. This makes it possible to run
    the analysis tool directly using the `PathEnsembleFile` object rather than
    first converting to a `pyretis.core.path.PathEnsemble` and then running
    the analysis. The common functions are `get_paths` and `__str__`.
    The common properties are `ensemble` and `interfaces`
    In the future, this should be made smarter, for instance could path data
    be read in portions, or the full path file could be read if it's small
    enough to fit in the memory. A line-by-line analysis as it is right now
    might not be the most efficient way.

    Attributes
    ----------
    ensemble : str
        This is a string representation of the path ensemble. Typically
        something like '0-', '0+', '1', '2', ..., '001' and so on.
    interfaces : list of ints
        These are the interfaces specified with the values
        for the order parameters: [left, middle, right]
        This variable is used when creating a `PathEnsemble` object
        in `to_path_ensemble`.
    detect : float
        The detect interface to use for analysis.
    """

    def __init__(self, filename, ensemble, interfaces, detect=None, mode='w',
                 oldfile='backup'):
        """Initialize the `PathEnsembleFile` object.

        Parameters
        ----------
        filename : string
            Name of file to read/write.
        ensemble : str
            This is a string representation of the path ensemble. Typically
            something like '0-', '0+', '1', '2', ..., '001' and so on.
        interfaces : list of floats
            These are the interfaces specified with the values
            for the order parameters: [left, middle, right]
        detect : float
            The detect interface to use for analysis.
        mode : string
            Mode can be used to select if we should write to the file
            (if mode is equal to 'w') or read from the file (mode equal
            to 'r'). The default is mode equal to 'w'.
        oldfile : string
            Defines how we handle existing files with the same name as given
            in `filename`. Note that this is only useful when the mode is
            set to 'w'.
        """
        header = {'text': ['Step', 'No. acc', 'No. shoot',
                           'l', 'm', 'r', 'Length', 'Acc', 'Mc',
                           'Min-O', 'Max-O', 'Idx-Min', 'Idx-Max',
                           'O-shoot', 'Idx-sh', 'Idx-shN'],
                  'width': [10, 10, 10, 1, 1, 1, 7, 3, 2, 16, 16, 7, 7,
                            16, 7, 7]}
        super(PathEnsembleFile, self).__init__(filename, 'PathEnsembleFile',
                                               mode=mode, oldfile=oldfile,
                                               header=header)
        self.ensemble = ensemble
        self.interfaces = interfaces
        self.detect = detect

    def to_path_ensemble(self):
        """Read a file and return a `PathEnsemble` object.

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
            logging.critical(msg)
        except Exception as error:
            msg = 'Error: {}'.format(error)
            logging.critical(msg)
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


class PathWriter(object):
    """PathWriter(object) - For writing path information.

    This class handles writing of path information. It combines the
    writers for the order parameter, the energy and the trajectory.

    Attributes
    ----------
    """
    known_files = {'orderp', 'energy', 'traj'}

    def __init__(self, ensemble, file_settings):
        """Initialize the `PathWriter` object.

        Parameters
        ----------
        ensemble : str
            This is a string representation of the path ensemble. Typically
            something like '0-', '0+', '1', '2', ..., '001' and so on.
        file_settings : dict
            This dict contains the settings for each file we want to create.
        oldfile : string
            Defines how we handle existing files with the same name as given
            in `filename`. Note that this is only useful when the mode is
            set to 'w'.
        """
        self.order = file_settings.get('orderp', None)
        self.energy = file_settings.get('energy', None)
        self.traj = file_settings.get('traj', None)
        self.ensemble = ensemble

    def __new__(cls, ensemble, file_settings):
        """Check if at least one file is given in the input.

        Parameters
        ----------
        ensemble : str
            This is a string representation of the path ensemble. Typically
            something like '0-', '0+', '1', '2', ..., '001' and so on.
        file_settings : dict
            This dict contains the settings for each file we want to create.
        oldfile : string
            Defines how we handle existing files with the same name as given
            in `filename`. Note that this is only useful when the mode is
            set to 'w'.

        Returns
        -------
        out : A `PathWriter` object or None
            If at least one file is given with settings, then we create a new
            `PathWriter` object. Otherwise we return None.
        """
        files = any([key in file_settings for key in cls.known_files])
        if files:
            return super(PathWriter, cls).__new__(cls, ensemble,
                                                  file_settings)
        else:
            return None

    def write(self, cycle, path):
        """Write path data to the files.

        Parameters
        ----------
        cycle : integer
            This is the current cycle number.
        path : object like `Path` from `pyretis.core.path`
            This is the path to write to the file.
        """
        msg = 'Path file @ {}... len(path) = {}'.format(cycle, len(path.path))
        logger.warning(msg)
        if self.order is not None:
            pass

    def __str__(self):
        """Return a string with some info about the path file."""
        msg = ['PathWriter for ensemble: {}'.format(self.ensemble)]
        msg += ['\tWriters defined:']
        if self.order is not None:
            msg += ['\t- {}'.format(self.order['writer'])]
        if self.energy is not None:
            msg += ['\t- {}'.format(self.energy['writer'])]
        if self.traj is not None:
            msg += ['\t- {}'.format(self.traj['writer'])]
        return '\n'.join(msg)
