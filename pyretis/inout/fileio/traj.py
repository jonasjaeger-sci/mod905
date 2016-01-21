# -*- coding: utf-8 -*-
"""Module for handling the output/input of trajectory data.

This module defines some classes for writing out trajectory data.
Here we define a class for a simple xyz-format and a class for writing
in a gromacs format.

Important classes defined here:

- WriteXYZ: Writing of coordinates to a file in a xyz format.

- WriteGromacs: Writing of a coordinates to a file in a gromacs format.

Important functions defined here:

- read_xyz_file: A function for reading snapshots from a xyz file.

- read_gromacs_file: A function for reading snapshots from a gromacs GRO file.
"""
import logging
import numpy as np
from pyretis.core.units import CONVERT  # unit conversion in trajectory
from pyretis.inout.fileio.fileinout import FileWriter
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


# define formats for the trajectory output:
_GRO_FMT = '{0:5d}{1:5s}{2:5s}{3:5d}{4:8.3f}{5:8.3f}{6:8.3f}\n'
_GRO_VEL_FMT = _GRO_FMT[:-1] + '{7:8.4f}{8:8.4f}{9:8.4f}\n'
_GRO_BOX_FMT = '{0:12.6f} {1:12.6f} {2:12.6f}\n'
_XYZ_FMT = '{0:5s} {1:8.3f} {2:8.3f} {3:8.3f}\n'


__all__ = ['WriteXYZ', 'WriteGromacs', 'read_gromacs_file', 'read_xyz_file']


def create_traj_writer(filename, filefmt, units, oldfile='backup'):
    """Function to create a trajectory writer from settings.

    This function will create a trajectory writer based on settings for
    a format. It will also attach a given `system` so the writer.

    Parameters
    ----------
    filename : string
        Name of file to create
    filefmt : string
        Format of file, 'xyz' for xyz, 'gro' for gromacs.
    oldfile : string
        How to deal with backups of old files with the same name.
    units : string
        This defines the internal units and is used for converting
        to the external units.

    Returns
    -------
    out : object like `WriteXYZ` or `WriteGromacs`.
        The trajectory writer we created here.
    """
    if filefmt == 'xyz':
        return WriteXYZ(filename, units, oldfile=oldfile)
    elif filefmt == 'gro':
        return WriteGromacs(filename, units, oldfile=oldfile)
    else:
        msgtxt = 'Ignored unknown format "{}" for trajectory writer!'
        msgtxt = msgtxt.format(filefmt)
        logger.warning(msgtxt)
        return None


def _adjust_coordinate(coord):
    """Function to adjust the dimensionality of coordinates.

    A lot of the different formats expects us to have 3 dimensional data.
    This function just adds dummy dimensions equal to zero.

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
        try:
            for i in range(dim):
                adjusted[:, i] = coord[:, i]
        except IndexError:
            if dim == 1:
                adjusted[:, 0] = coord
        return adjusted


class WriteXYZ(FileWriter):
    u"""WriteXYZ(FileWriter) - A class for XYZ files.

    This class handles writing of a system to a file in a simple xyz format.

    Attributes
    ----------
    atomnames : list
        These are the atom names used for the output.
    convert : dict of floats
        Defines the conversion of positions from internal units to Ångström.
    frame : integer
        The number of frames written.
    """

    def __init__(self, filename, units, oldfile='backup'):
        """Initialization of the XYZ writer."""
        super(WriteXYZ, self).__init__(filename, 'xyz', mode='w',
                                       oldfile=oldfile)
        self.atomnames = []
        self.frame = 0  # number of frames written
        self.convert = {'pos': CONVERT['length'][units, 'A']}

    def write_frame(self, pos, names=None, header=None):
        """Write a configuration in xyz-format.

        Parameters
        ----------
        pos : numpy.array
            The positions to write.
        names : numpy.array, optional
            Atom names. If atom names are not given, dummy names
            (`X`) will be generated and used.
        header : string, optional
            Header to use for writing the xyz-frame.

        Returns
        -------
        status : boolean
            True if we managed to write to the file, False otherwise.
        """
        status = False
        npart = len(pos)
        self.write_string('{0}\n'.format(npart))
        if header is None:
            header = 'Trajectory output. Frame: {}'.format(self.frame)
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
            status = self.write_string(out)
            if not status:
                return status
        self.frame += 1
        return status

    def write(self, system, header=None):
        """Write a configuration in xyz-format.

        This is a function for writing a configuration in xyz-format. It is
        similar to `write_frame` and it's meant for convenience: atom names
        will not have to be specified and we are using the `system` to access
        (the positions of) the particles.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`
            The system object with the positions to write
        header : string, optional
            Header to use for writing the xyz-frame.
        """
        return self.write_frame(system.particles.pos,
                                names=system.particles.name, header=header)


class WriteGromacs(FileWriter):
    """WriteGromacs(FileWriter) - A class for GRO files.

    This class handles writing of a system to a file using the gromacs format.
    The gromacs format is described in the gromacs manual [#]_.

    Attributes
    ----------
    atomnames : list
        These are the atom names used for the output.
    convert : dict of floats
        Defines the conversion of positions from internal units to `nm` and
        velocities from internal units to `nm/ps`.
    frame : integer
        The number of frames written.

    References
    ----------

    .. [#] The GROMACS manual,
       http://manual.gromacs.org/current/online/gro.html
    """

    def __init__(self, filename, units, oldfile='backup'):
        """Initiate the gromacs writer."""
        super(WriteGromacs, self).__init__(filename, 'gromacs', mode='w',
                                           oldfile=oldfile)
        self.atomnames = []
        self.frame = 0  # number of frames written
        self.convert = {'pos': CONVERT['length'][units, 'nm'],
                        'vel': CONVERT['velocity'][units, 'nm/ps']}

    def write_frame(self, pos, box, vel=None, residuenum=None,
                    residuename=None, atomname=None, atomnum=None,
                    header=None):
        """Write a configuration in gromacs format.

        This will write a specific frame with given positions to the file.
        Velocities can also be written if given.

        Parameters
        ----------
        pos : numpy.array
            The positions to write.
        box : object like `Box` from `pyretis.core.box`
            The simulation box, used for box-lengths.
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
        ``residuenum, residuename, atomname, atomnum, x, y, z, vx, vy, vz``.
        """
        npart = len(pos)
        if atomname is None:
            if len(self.atomnames) != npart:
                self.atomnames = ['X'] * npart
            atomname = self.atomnames
        if residuename is None:  # just reuse atomnames
            residuename = atomname
        if header is None:
            header = 'Trajectory output. Frame: {}'.format(self.frame)

        self.write_string('{}\n'.format(header))
        self.write_string('{}\n'.format(npart))

        pos = _adjust_coordinate(pos)  # in case pos is 1D or 2D
        if vel is not None:
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
            else:
                out = _GRO_VEL_FMT.format(residuenr, residuename[i],
                                          atomname[i], atomnr,
                                          posi[0] * self.convert['pos'],
                                          posi[1] * self.convert['pos'],
                                          posi[2] * self.convert['pos'],
                                          vel[i][0] * self.convert['vel'],
                                          vel[i][1] * self.convert['vel'],
                                          vel[i][2] * self.convert['vel'])
            status = self.write_string(out)
            if not status:
                return status
        # Write box, note that we update the box-lengths here since
        # it may change during the simulation.
        status = self.write_string(_GRO_BOX_FMT.format(*self.box_lengths(box)))
        self.frame += 1
        return status

    def write(self, system, header=None, write_vel=False):
        """Write a configuration in gromacs format.

        This is a function for writing a configuration in GRO-format. It is
        similar to `write_frame` and it's meant for convenience: atom names
        will not have to be specified and we are using a `system` to access
        the positions and velocities.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`
            The system object with the positions to write
        header : string, optional
            Header to use for writing the frame.
        write_vel : boolean, optional
            If true, velocities will be written
        """
        velocity = None if not write_vel else system.particles.vel
        return self.write_frame(system.particles.pos,
                                system.box,
                                vel=velocity,
                                atomname=system.particles.name,
                                header=header)

    def box_lengths(self, box):
        """Obtain the box lengths from a object."""
        missing = 3 - box.dim
        if missing > 0:
            boxlength = np.ones(3)
            for i, length in enumerate(box.length):
                boxlength[i] = length * self.convert['pos']
            return boxlength
        else:
            return box.length * self.convert['pos']


def read_gromacs_file(filename):
    """A function for reading gromacs GRO files.

    This function will read a gromacs file and yield the different snapshots
    found in the file.

    Parameters
    ----------
    filename : string
        The file to open.

    Yields
    ------
    out : dict
        This dict contains the snapshot.

    Examples
    --------
    >>> from pyretis.inout.fileio.traj import read_gromacs_file
    >>> for snapshot in read_gromacs_file('traj.gro'):
    ...     print(snapshot['x'][0])
    """
    lines_to_read = 0
    snapshot = {}
    read_natoms = False
    gro = (5, 5, 5, 5, 8, 8, 8, 8, 8, 8)
    gro_keys = ('residunr', 'residuname', 'atomname', 'atomnr',
                'x', 'y', 'z', 'vx', 'vy', 'vz')
    gro_type = (0, 1, 1, 0, 2, 2, 2, 2, 2, 2)
    with open(filename, 'r') as fileh:
        for lines in fileh:
            if read_natoms:
                read_natoms = False
                lines_to_read = int(lines.strip()) + 1
                continue  # just skip to next line
            if lines_to_read == 0:  # new shapshot
                if len(snapshot) > 0:
                    yield snapshot
                snapshot = {'header': lines.strip()}
                read_natoms = True
            elif lines_to_read == 1:  # read box
                snapshot['box'] = [float(length) for length in
                                   lines.strip().split()]
                lines_to_read -= 1
            else:  # read atoms
                lines_to_read -= 1
                current = 0
                for i, key, gtype in zip(gro, gro_keys, gro_type):
                    val = lines[current:current+i].strip()
                    if len(val) == 0:
                        # This typically happens if we try to read velocities
                        # and they are not present in the file.
                        break
                    if gtype == 0:
                        val = int(val)
                    elif gtype == 2:
                        val = float(val)
                    current += i
                    try:
                        snapshot[key].append(val)
                    except KeyError:
                        snapshot[key] = [val]
    if len(snapshot) > 1:
        yield snapshot


def read_xyz_file(filename):
    """A function for reading files in xyz format.

    This function will read a xyz file and yield the different snapshots
    found in the file.

    Parameters
    ----------
    filename : string
        The file to open.

    Yields
    ------
    out : dict
        This dict contains the snapshot.

    Examples
    --------
    >>> from pyretis.inout.fileio.traj import read_xyz_file
    >>> for snapshot in read_xyz_file('traj.xyz'):
    ...     print(snapshot['x'][0])
    """
    lines_to_read = 0
    snapshot = None
    xyz_keys = ('atomname', 'x', 'y', 'z')
    read_header = False
    with open(filename, 'r') as fileh:
        for lines in fileh:
            if read_header:
                snapshot = {'header': lines.strip()}
                read_header = False
                continue
            if lines_to_read == 0:  # new shapshot
                if snapshot is not None:
                    yield snapshot
                lines_to_read = int(lines.strip())
                read_header = True
                snapshot = None
            else:
                lines_to_read -= 1
                data = lines.strip().split()
                for i, (val, key) in enumerate(zip(data, xyz_keys)):
                    if i != 0:
                        val = float(val)
                    try:
                        snapshot[key].append(val)
                    except KeyError:
                        snapshot[key] = [val]
    if snapshot is not None:
        yield snapshot


def write_xyz_file(filename, pos, names=None, header=None):
    """Write a single configuration in xyz-format.

    This is just a simple function to write a single xyz
    configuration to a file. It will NOT convert positions and assumes
    that these are given in correct units.

    Parameters
    ----------
    filename : string
        The file to create.
    pos : numpy.array or list-like.
       The positions to write.
    names : list, optional
        The atom names.
    header : string, optional
        Header to use for writing the xyz-file.
    """
    npart = len(pos)
    pos = _adjust_coordinate(pos)
    with open(filename, 'w') as fileh:
        fileh.write('{}\n'.format(npart))
        if header is None:
            fileh.write('pyretis xyz writer\n')
        else:
            fileh.write('{}\n'.format(header))
        if names is None:
            for posi in pos:
                logging.warning('No atom name given. Using "X"')
                out = _XYZ_FMT.format('X', posi[0], posi[1], posi[2])
                fileh.write(out)
        else:
            for namei, posi in zip(names, pos):
                out = _XYZ_FMT.format(namei, posi[0], posi[1], posi[2])
                fileh.write(out)
