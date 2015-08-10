# -*- coding: utf-8 -*-
"""This file contains methods that handle output/input of text"""
import itertools
import os
import warnings
from retis.core.units import CONVERT  # unit conversion in trajectory
from retis.core.path import Path, PathEnsemble  # for PathEnsembleFile
import numpy as np
from .common import create_backup

# define formats for the trajectory output:
_GRO_FMT = '{0:5d}{1:5s}{2:5s}{3:5d}{4:8.3f}{5:8.3f}{6:8.3f}\n'
_GRO_VEL_FMT = _GRO_FMT[:-1] + '{7:8.3f}{8:8.3f}{9:8.3f}\n'
_GRO_BOX_FMT = '{0:12.6f} {1:12.6f} {2:12.6f}\n'
_XYZ_FMT = '{0:5s} {1:8.3f} {2:8.3f} {3:8.3f}\n'


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
                 count=0):
        """
        Initiates the file writer object.

        Paramters
        ---------
        filename : string
            Name of the file to write.
        filetype : string
            Identifies the filetype to write (i.e. the format).
        oldfile : string
            Behavior if the `filename` is an existing file.
        frame : int
            Counts the number of frames written
        """
        self.count = count
        self.filename = filename
        self.filetype = filetype
        self.mode = mode.lower()
        self.fileh = None
        if self.mode == 'r':  # Read data
            try:
                self.fileh = open(self.filename, 'r')
            except IOError as error:
                msg = 'I/O error ({}): {}'.format(error.errno, error.strerror)
                warnings.warn(msg)
        elif self.mode == 'w':  # Write data to file + handle backup:
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


def _adjust_coordinate(coord):
    """
    Method to adjust the dimensionality. A lot of the different
    formats expects us to have 3 dimensional data. This methods just
    adds dummy dimensions equal to zero

    Parameters
    ----------
    coord : numpy.array
        The real coordinates.

    Returns
    -------
    out : numpy.array
        The "zero-padded" coordinates.
    """
    if len(coord.shape) == 1:
        npart, dim = len(coord), 1
    else:
        npart, dim = coord.shape
    if dim == 3:
        return coord
    else:
        adjusted = np.zeros((npart, 3))
        for i in range(dim):
            adjusted[:, i] = coord[:, i]
        return adjusted


class WriteXYZ(FileWriter):
    """
    WriteXYZ(TrajectoryWriter)
    This class handles writing of a system to a file in a simple xyz format.

    Attributes
    ----------
    Same as for FileWriter and in addition:
    convert : dict of floats
        Defines the conversion of positions from internal units to Å.
    atomnames : list
        These are the atomnames used for the output.
    """
    def __init__(self, filename, oldfile='backup', units='lj'):
        self.convert = {'pos': CONVERT['length'][units, 'Å']}
        self.atomnames = []
        self.frame = 0  # number of frames written
        super(WriteXYZ, self).__init__(filename, 'xyz', mode='w',
                                       oldfile=oldfile)

    def write_frame(self, pos, names=None, header=None):
        """
        This is a method for writing a configuration in
        xyz-format.

        Parameters
        ----------
        pos : numpy.array
            The positions to write.
        names : numpy.array, optional
            The atom names. If the atom names are not the generated ones
            will be used ("X").
        header : string, optional
            Header to use for writing the xyz-frame.
        """
        npart = len(pos)
        self.write_string('{0}\n'.format(npart))
        if header is None:
            header = 'pytismol ouput. Frame: {}'.format(self.frame)
        self.write_string('{}\n'.format(header))
        if names is None:
            if len(self.atomnames) != npart:
                self.atomnames = ['X'] * npart
            names = self.atomnames
        pos = _adjust_coordinate(pos)
        for namei, posi in zip(names, pos):
            out = _XYZ_FMT.format(namei,
                                  posi[0] * self.convert['pos'],
                                  posi[1] * self.convert['pos'],
                                  posi[2] * self.convert['pos'])
            #out = _format(_XYZ_FMT, namei, posi[0]*self.convert['pos'],
            #              posi[1]*self.convert['pos'],
            #              posi[2]*self.convert['pos'])
            #out.append('\n')
            #status = self.write_string('  '.join(out))
            status = self.write_string(out)
            if not status:
                return status
        self.frame += 1
        return status

    def write_system(self, system, header=None):
        """
        This is a method for writing a configuration in
        xyz-format. It is similar to `write_frame` and it's
        meant for convenience: atoms names will not have to be specified.

        Parameters
        ----------
        system : object of type retis.core.System
            The system object with the positions to write
        header : string, optional
            Header to use for writing the xyz-frame.
        """
        return self.write_frame(system.particles.pos,
                                names=system.particles.name, header=header)

    def __call__(self, system, header=None):
        """
        This is a method for writing a configuration in
        xyz-format. This method will just call write_system and is
        included here for convenience.

        Parameters
        ----------
        system : object of type retis.core.System
            The system object with the positions to write
        header : string, optional
            Header to use for writing the xyz-frame.
        """
        return self.write_system(system, header=header)


class WriteGromacs(FileWriter):
    """
    WriteGromacs(FileWriter)
    This class handles writing of a system to a file in a simple xyz format.

    Attributes
    ----------
    Same as for FileWriter and in addition the following:
    box : object of type box as defined in box.py
        The simulation box, used for box-lengths.
    convert : dict of floats
        Defines the conversion of positions from internal units to nm
        and nm/ps.
    """
    def __init__(self, filename, box, oldfile='backup', units='lj'):
        self.atomnames = []
        self.box = box
        self.frame = 0  # number of frames written
        self.convert = {'pos': CONVERT['length'][units, 'nm'],
                        'vel': CONVERT['velocity'][units, 'nm/ps']}
        super(WriteGromacs, self).__init__(filename, 'gromacs', mode='w',
                                           oldfile=oldfile)

    def write_frame(self, pos, vel=None, residuenum=None, residuename=None,
                    atomname=None, atomnum=None, header=None):
        """
        This is a method for writing a configuration frame in
        gromacs-format.

        Parameters
        ----------
        pos : numpy.array
            The positions to write.
        vel : numpy.array, optional
            Velocities to write.
        residuenum : list of ints, optional
            Residue numbers, may be used to group molecules etc.
        residuename : list of strings
            The residue names.
        atomname : list of strings, optional.
            The atom names.
        atomnum : list of ints, optional.
            The atomnumbers.
        header : string, optional.
            Header to include in the output file.

        Note
        ----
        In short, the format is:
        residuenum, residuename, atomname, atomnum, x, y, z, vx, vy, vz
        """
        npart = len(pos)
        if atomname is None:
            if len(self.atomnames) != npart:
                self.atomnames = ['X'] * npart
            atomname = self.atomnames
        if residuename is None:  # just reuse atomnames
            residuename = atomname
        if header is None:
            header = 'pytismol ouput. Frame: {}'.format(self.frame)

        self.write_string('{}\n'.format(header))
        self.write_string('{}\n'.format(npart))

        pos = _adjust_coordinate(pos)  # in case pos is 1D or 2D
        if not vel is None:
            vel = _adjust_coordinate(vel)  # in case vel is 1D or 2D

        for i, posi in enumerate(pos):
            residuenr = i + 1 if residuenum is None else residuenum[i]
            atomnr = i + 1 if atomnum is None else atomnum[i]
            if vel is None:
                out = _GRO_FMT.format(residuenr, residuename[i],
                                      atomname[i], atomnr,
                                      posi[0] * self.convert['pos'],
                                      posi[1] * self.convert['pos'],
                                      posi[2] * self.convert['pos'])
                #out = _format(_GRO_FMT, residuenr, residuename[i],
                #              atomname[i], atomnr,
                #              posi[0] * self.convert['pos'],
                #              posi[1] * self.convert['pos'],
                #              posi[2] * self.convert['pos'])
            else:
                out = _GRO_VEL_FMT.format(residuenr, residuename[i],
                                          atomname[i], atomnr,
                                          posi[0] * self.convert['pos'],
                                          posi[1] * self.convert['pos'],
                                          posi[2] * self.convert['pos'],
                                          vel[i][0] * self.convert['vel'],
                                          vel[i][1] * self.convert['vel'],
                                          vel[i][2] * self.convert['vel'])
                #out = _format(_GRO_VEL_FMT, residuenr, residuename[i],
                #              atomname[i], atomnr,
                #              posi[0] * self.convert['pos'],
                #              posi[1] * self.convert['pos'],
                #              posi[2] * self.convert['pos'],
                #              vel[i][0] * self.convert['vel'],
                #              vel[i][1] * self.convert['vel'],
                #              vel[i][2] * self.convert['vel'])
            status = self.write_string(out)
            #aout.append('\n')
            #status = self.write_string(''.join(out))
            if not status:
                return status
        # Write box, note that we update the box-lengths here since
        # it may change during the simulation.
        #out = _format(_GRO_BOX_FMT, *self._box_lengths())
        #out.append('\n')
        #status = self.write_string(' '.join(out))
        status = self.write_string(_GRO_BOX_FMT.format(*self._box_lengths()))
        self.frame += 1
        return status

    def write_system(self, system, header=None, write_vel=False):
        """
        This is a method for writing a configuration in
        gro-format. It is similar to `write_frame` and it's
        meant for convenience: atoms names will not have to be specified.

        Parameters
        ----------
        system : object of type retis.core.System
            The system object with the positions to write
        header : string, optional
            Header to use for writing the xyz-frame.
        write_vel : boolean, optional
            If true, velocities will be written
        """
        if not write_vel:
            return self.write_frame(system.particles.pos,
                                    atomname=system.particles.name,
                                    header=header)
        else:
            return self.write_frame(system.particles.pos,
                                    vel=system.particles.vel,
                                    atomname=system.particles.name,
                                    header=header)

    def __call__(self, system, header=None, write_vel=False):
        """
        This is a method for writing a configuration in gro-format.
        This method will just call write_system and is
        included here for convenience.

        Parameters
        ----------
        system : object of type retis.core.System
            The system object with the positions to write
        header : string, optional
            Header to use for writing the xyz-frame.
        write_vel : boolean, optional
            If true, velocities will be written
        """
        return self.write_system(system, header=header, write_vel=write_vel)

    def _box_lengths(self):
        """
        This is a helper method to obtain the box lengths from the
        box object
        """
        missing = 3 - self.box.dim
        if missing > 0:
            boxlength = np.ones(3)
            for i, length in enumerate(self.box.length):
                boxlength[i] = length * self.convert['pos']
            return boxlength
        else:
            return self.box.length * self.convert['pos']


def _line_to_path(line):
    """
    This is a helper function to convert a text line to a Path object.

    Parameters
    ----------
    line : string
        The line of text to convert

    Returns
    -------
    out : object of type Path
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

    Attributes
    ----------
    Same as for the FileWriter object, in addition:
    ensemble : str
        This is a string representation of the path ensemble. Typically
        something like '0-', '0+', '1', '2', ..., '001' and so on.
    interfaces : list of ints
        These are the interfaces specified with the values
        for the order parameters: [left, middle, right]
    """
    def __init__(self, filename, ensemble, interfaces, mode='w',
                 oldfile='backup'):
        """
        Initialize the PathEnsembleFile object

        Parameters
        ----------
        filename : string
            Name of file to write.
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
        super(PathEnsembleFile, self).__init__(filename, 'pathensemble',
                                               mode=mode,
                                               oldfile=oldfile)
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

        Yields
        ------
        out : object of type Path, the current path in the file
        """
        try:
            self.fileh.seek(0)  # just to make sure we rewind
            for lines in self.fileh:
                new_path = _line_to_path_data(lines)
                yield new_path
        except IOError as error:
            msg = 'I/O error ({}): {}'.format(error.errno, error.strerror)
            warnings.warn(msg)
        except Exception as error:
            msg = 'Error: {}'.format(error)
            warnings.warn(msg)
            raise

    def __str__(self):
        """
        Return a string with some info about this object
        """
        msg = ['Path (file) ensemble : {}'.format(self.ensemble)]
        msg += ['\tFile name: {}'.format(self.filename)]
        msg += ['\tFile mode: {}'.format(self.mode)]
        return '\n'.join(msg)
