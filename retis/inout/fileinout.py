# -*- coding: utf-8 -*-
"""
This file contains methods and objects that handle output/input of
crossing data.

Objects defined here:

- CrossFile: Writing/reading of crossing data (i.e. data which can be used
  for calculation of the initial flux).

- EnergyFile: Writing/reading of energy data to a file.

- OrderFile: Writing/reading of order parameter data

- PathEnsembleFile: Writing/reading of path ensemble data to a file.
"""
import numpy as np
import warnings
try:  # this will fail in python3
    from itertools import izip_longest as zip_longest
except ImportError:  # for python3
    from itertools import zip_longest as zip_longest
# local imports
from retis.inout.txtinout import FileWriter
from retis.inout.txtinout import read_some_lines, create_and_format_row
from retis.core.path import Path, PathEnsemble  # for PathEnsembleFile


__all__ = ['CrossFile', 'EnergyFile', 'OrderFile', 'PathEnsembleFile']


# format for crossing files:
CROSS_FMT = '{:>10d} {:>4d} {:>3s}'
# format for the energy files, here also as a tuple since this makes
# convenient for outputting in a specific order:
ENERGY_FMT = ['{:>10d}'] + 6*['{:>12.6f}']
# format for order files, here as a tuple since we don't know how many
# parameters we will write:
ORDER_FMT = ['{:>10d}', '{:>12.6f}']
# define a format used for the path files. Here it's not really needed,
# we are going to assume that these files will be comma separated anyway.
# It is included to be compatible with the previous fortran version.
PATH_FMT = ('{0:>10d} {1:>10d} {2:>10d} {3:1s} {4:1s} {5:1s} {6:>7d} ' +
            '{7:3s} {8:2s} {9:>16.9e} {10:>16.9e} {11:>7d} {12:>7d} ' +
            '{13:>16.9e} {14:>7d} {15:7d}')
# define a format for position and velocities in the path file:
POSVEL_FMT = ['{:8.3f}', '{:8.3f}', '{:8.3f}']


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
        This method will attempt to load entire blocks from the cross file
        into memory.
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
        header = {'text': ['Time', 'Potential', 'Kinetic', 'Total',
                           'Hamiltonian', 'Temperature', 'External'],
                  'width': [10, 12]}
        super(EnergyFile, self).__init__(filename, 'energyfile',
                                         mode=mode,
                                         oldfile=oldfile,
                                         header=header)

    def load(self):
        """
        This method will attempt to load entire energy blocks into memory.
        (Quote of the day: 'memory is cheap, function calls are expensive'.)
        In the future, a more intelligent way of handling files like this
        may be in order, but for now the entire file is read as it's very
        convenient for the subsequent analysis.

        Yields
        -------
        data_dict : dict
            This is the energy data read from the file, stored in
            a dict. This is for convenience, so that each energy term
            can be accessed by data[key]

        See Also
        --------
        read_some_lines
        """
        for blocks in read_some_lines(self.filename):
            data = np.array(blocks['data'])
            data_dict = {'comment': blocks['comment'],
                         'data': {'time': data[:, 0],
                                  'vpot': data[:, 1],
                                  'ekin': data[:, 2],
                                  'etot': data[:, 3],
                                  'ham': data[:, 4],
                                  'temp': data[:, 5],
                                  'ext': data[:, 6]}}
            yield data_dict

    def write(self, step, energy):
        """
        This function will write the energy data to the file.

        Parameters
        ----------
        step : int
            This is the current step number.
        energy : dict
            This is the energy data stored as a dictionary.

        Returns
        -------
        out : boolean
            True if line could be written, False otherwise.
        """
        towrite = [ENERGY_FMT[0].format(step)]
        for i, key in enumerate(['vpot', 'ekin', 'etot', 'ham',
                                 'temp', 'ext']):
            value = energy.get(key, 0.0)
            towrite.append(ENERGY_FMT[i + 1].format(value))
        towrite = ' '.join(towrite)
        return self.write_line(towrite)

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
        header = {'text': ['Time', 'Orderp', 'Orderv'],
                  'width': [10, 12]}
        super(OrderFile, self).__init__(filename, 'orderparameter',
                                        mode=mode, oldfile=oldfile,
                                        header=header)

    def load(self):
        """
        This method will attempt to load the entire order parameter blocks
        into memory.
        In the future, a more intelligent way of handling files like this
        may be in order, but for now the entire file is read as it's very
        convenient for the subsequent analysis. In case blocks are found in
        the file, they will be yielded, this is just to reduce the memory
        usage.
        The format is `time` `orderp0` `orderv0` `orderp1` `orderp2` ...,
        where the actual meaning of `orderp1` `orderp2` and the following
        order parameters are left to be defined by the user.

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


class PathFile(FileWriter):
    """
    PathFile(FileWriter)

    This class handles writing/reading of path data.

    Attributes
    ----------
    Same as for the FileWriter object.
    """
    def __init__(self, filename, mode='w', oldfile='backup'):
        """
        Initialize the PathFile object

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
        return line.strip().split()

    def load(self):
        """
        This method will attempt to load a path into the memory. The paths
        are assumed to be organized into blocks defined by self.block_label.
        This method will yield blocks successively.

        Yields
        -------
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
        """
        This will write a path to the file.

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
        """
        Return a string with some info about this object
        """
        msg = 'Order parameter file: {} (mode: {})'.format(self.filename,
                                                           self.mode)
        return msg


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
    if line.find('#') != -1:
        linec = line.split('#')[0].strip()
    else:
        linec = line.strip()
    data = [col.strip() for col in linec.split()]
    if len(data) < 16:  # valid data should have 15 columns!
        return None
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
        """
        This method will write a given path from a path ensemble to the file.
        If the path is not explicitly given, the latest path from the path
        ensemble will be written.

        Parameters
        ----------
        cycle : integer
            This is the current cycle number.
        path_ensemble : object of type PathEnsemble
            We will write the path defined by PathEnsemble.paths[-1]
        path : object of type Path
            This is the path to write to the file.
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
