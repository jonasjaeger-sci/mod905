# -*- coding: utf-8 -*-
"""
This file contains methods and objects that handle output/input of
path data files.

Objects defined here:

- PathEnsembleFile: Writing/reading of path ensemble data to a file.
"""
import warnings
from retis.core.path import Path, PathEnsemble  # for PathEnsembleFile
from .txtinout import FileWriter


__all__ = ['PathEnsembleFile']

# define a format used for the path files. Here it's not really needed,
# we are going to assume that these files will be comma separated anyway.
# It is included to be compatible with the previous fortran version.
PATH_FMT = ('{0:>10d} {1:>10d} {2:>10d} {3:1s} {4:1s} {5:1s} {6:>7d} ' +
            '{7:3s} {8:2s} {9:>16.9e} {10:>16.9e} {11:>7d} {12:>7d} ' +
            '{13:>16.9e} {14:>7d} {15:7d}')


def _line_to_path_object(line):
    """
    This is a helper function to convert a text line to a Path object.

    Parameters
    ----------
    line : string
        The line of text to convert

    Returns
    -------
    out : object of type Path

    Note
    ----
    TODO: This function is considered for deletion - is it going to be
    usefull or are we always going to create path data from a file. It might
    be usefull in the future for restart files.
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
        This variable is used when creating a ``PathEnsemble`` object
        in ``to_path_ensemble``.
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
