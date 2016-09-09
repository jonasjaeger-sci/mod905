# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""Module for handling the output/input of trajectory data.

This module defines some classes for writing out trajectory data.
Here we define a class for a simple xyz-format and a class for writing
in a gromacs format.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

TrajXYZ
    Writing of coordinates to a file in a xyz format.

TrajGRO
    Writing of a coordinates to a file in a gromacs format.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

read_xyz_file
    A method for reading snapshots from a xyz file.

read_gromacs_file
    A method for reading snapshots from a gromacs GRO file.
"""
import logging
import numpy as np
from pyretis.core.units import CONVERT  # unit conversion in trajectory
from pyretis.inout.writers.writers import Writer
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


# define formats for the trajectory output:
_GRO_FMT = '{0:5d}{1:5s}{2:5s}{3:5d}{4:8.3f}{5:8.3f}{6:8.3f}'
_GRO_VEL_FMT = _GRO_FMT + '{7:8.4f}{8:8.4f}{9:8.4f}'
_GRO_BOX_FMT = '{0:12.6f} {1:12.6f} {2:12.6f}'
_XYZ_FMT = '{0:5s} {1:8.3f} {2:8.3f} {3:8.3f}'
_XYZ_FMTN = '{0:5s} {1:8.3f} {2:8.3f} {3:8.3f}\n'


__all__ = ['TrajXYZ', 'TrajGRO', 'read_gromacs_file', 'read_xyz_file']


def _adjust_coordinate(coord):
    """Method to adjust the dimensionality of coordinates.

    A lot of the different formats expects us to have 3 dimensional
    data. This method just adds dummy dimensions equal to zero.

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


class TrajXYZ(Writer):
    u"""TrajXYZ(Writer) - A class for XYZ files.

    This class handles writing of a system to a file in a simple xyz
    format.

    Attributes
    ----------
    atomnames : list
        These are the atom names used for the output.
    convert_pos : float
        Defines the conversion of positions from internal units to
        Ångström.
    frame : integer
        The number of frames written.
    """
    XYZ_FMT = _XYZ_FMT

    def __init__(self, units):
        """Initialization of the XYZ writer."""
        super(TrajXYZ, self).__init__('TrajXYZ')
        self.atomnames = []
        self.frame = 0  # number of frames written
        try:
            self.convert_pos = CONVERT['length'][units, 'A']
        except KeyError:
            self.convert_pos = 1.0
            msg = ['Could not get conversion for units "{}"'.format(units)]
            msg += ['Positions will be in A']
            msgtxt = '\n'.join(msg)
            logger.warning(msgtxt)

    def xyz_format(self, npart, pos, names=None, header=None):
        """Generate output for a configuration in xyz-format.

        Parameters
        ----------
        npart : integer
            The number of particles.
        pos : numpy.array
            The positions to write.
        names : numpy.array, optional
            Atom names. If atom names are not given, dummy names
            (`X`) will be generated and used.
        header : string, optional
            Header to use for writing the xyz-frame.

        Returns
        -------
        out : list of strings
            The data to be written
        """
        buff = []
        buff.append('{0}'.format(npart))
        if header is None:
            header = 'Trajectory output. Frame: {}'.format(self.frame)
        buff.append('{}'.format(header))
        if names is None:
            if len(self.atomnames) != npart:
                self.atomnames = ['X'] * npart
            names = self.atomnames
        pos = _adjust_coordinate(pos)
        for namei, posi in zip(names, pos):
            out = _XYZ_FMT.format(namei,
                                  posi[0] * self.convert_pos,
                                  posi[1] * self.convert_pos,
                                  posi[2] * self.convert_pos)
            buff.append(out)
        self.frame += 1
        return buff

    def generate_output(self, system, header=None):
        """Write a configuration in xyz-format.

        This is a method for writing a configuration in xyz-format.
        It is similar to `write_frame` and it's meant for convenience:
        atom names will not have to be specified and we are using
        the `system` to access (the positions of) the particles.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`
            The system object with the positions to write
        header : string, optional
            Header to use for writing the xyz-frame.

        Yields
        ------
        out : string
            The lines in the XYZ-snapshot.
        """
        for lines in self.xyz_format(system.particles.npart,
                                     system.particles.pos,
                                     names=system.particles.name,
                                     header=header):
            yield lines

    def load(self, filename):
        """Read snapshots from the trajectory file.

        Here we simply use the `read_xyz_file` method defined below.
        In addition we convert positions to internal units.

        Parameters
        ----------
        filename : string
            The path/filename to open.

        Yields
        ------
        out : dict
            This dict contains the snapshot.
        """
        convert = 1.0 / self.convert_pos
        for snapshot in read_xyz_file(filename):
            snapshot['x'] = np.array(snapshot['x']) * convert
            snapshot['y'] = np.array(snapshot['y']) * convert
            snapshot['z'] = np.array(snapshot['z']) * convert
            yield snapshot


class TrajGRO(Writer):
    """TrajGRO(Writer) - A class for gromacs GRO files.

    This class handles writing of a system to a file using the gromacs
    format. The gromacs format is described in the GROMACS manual [#]_.

    Attributes
    ----------
    atomnames : list
        These are the atom names used for the output.
    convert_pos : float
        Defines the conversion of positions from internal units to `nm`.
    convert_vel : float
        Defines the conversion of velocities from internal units to
        `nm/ps`.
    frame : integer
        The number of frames written.
    write_vel : boolean
        Determines if we should write the velocity in addition to the
        positions.

    References
    ----------

    .. [#] The GROMACS manual,
       http://manual.gromacs.org/current/online/gro.html
    """
    heading = 'Trajectory output. Frame: {}'

    def __init__(self, units, write_vel):
        """Initiate the gromacs writer."""
        super(TrajGRO, self).__init__('TrajGRO', header=None)
        self.atomnames = []
        self.frame = 0  # number of frames written
        self.write_vel = write_vel
        try:
            self.convert_pos = CONVERT['length'][units, 'nm']
            self.convert_vel = CONVERT['velocity'][units, 'nm/ps']
        except KeyError:
            self.convert_pos = 1.0
            self.convert_vel = 1.0
            msg = ['Could not get conversion for units "{}"'.format(units)]
            msg += ['Positions will be in nm, velocity in nm/ps']
            msgtxt = '\n'.join(msg)
            logger.warning(msgtxt)

    def gro_format(self, npart, pos, vel, box, **kwargs):
        """Format positions, box and velocities according to the GRO format.

        This method will generate a list of strings which is the GRO
        format representation of a configuration. Note that velicities
        do not have to be written (i.e. `vel = None`).

        Parameters
        ----------
        npart : integer
            The number of particles.
        pos : numpy.array
            The positions to write.
        vel : numpy.array or None
            Velocities to write. If `None`, velocities are not written.
        box : object like `Box` from `pyretis.core.box`
            The simulation box, used for box-lengths.
        kwargs : dict,
            Additional arguments for the GRO file. This may include:

            * residuenum : list of ints, optional
              Residue numbers, may be used to group molecules etc.
            * residuename : list of strings
              The residue names.
            * atomname : list of strings, optional.
              The atom names.
            * atomnum : list of ints, optional.
              The atomnumbers.
            * header : string, optional.
              Header to include in the output file.

        Returns
        -------
        out : list of strings
            The strings which is the GRO representation of the given
            configuration.
        """
        atomname = kwargs.get('atomname', ['X'] * npart)
        residuename = kwargs.get('residuename', atomname)
        residuenum = kwargs.get('residuenum', None)
        atomnum = kwargs.get('atomnum', None)
        header = kwargs.get('header', self.heading.format(self.frame))

        buff = ['{}'.format(header)]
        buff.append('{}'.format(npart))

        pos = _adjust_coordinate(pos)  # in case pos is 1D or 2D
        if vel is not None:
            vel = _adjust_coordinate(vel)  # in case vel is 1D or 2D

        for i in range(npart):
            residuenr = i + 1 if residuenum is None else residuenum[i]
            atomnr = i + 1 if atomnum is None else atomnum[i]
            if vel is None:
                buff.append(_GRO_FMT.format(residuenr, residuename[i],
                                            atomname[i], atomnr,
                                            pos[i][0] * self.convert_pos,
                                            pos[i][1] * self.convert_pos,
                                            pos[i][2] * self.convert_pos))
            else:
                buff.append(_GRO_VEL_FMT.format(residuenr, residuename[i],
                                                atomname[i], atomnr,
                                                pos[i][0] * self.convert_pos,
                                                pos[i][1] * self.convert_pos,
                                                pos[i][2] * self.convert_pos,
                                                vel[i][0] * self.convert_vel,
                                                vel[i][1] * self.convert_vel,
                                                vel[i][2] * self.convert_vel))
        buff.append(_GRO_BOX_FMT.format(*self.box_lengths(box)))
        self.frame += 1
        return buff

    def generate_output(self, system, header=None):
        """Write a configuration in gromacs format.

        This is a method for writing a configuration in GRO-format.
        It is similar to `write_frame` and it's meant for convenience:
        atom names will not have to be specified and we are using a
        `system` object to access the positions and velocities.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`
            The system object with the positions to write
        header : string, optional
            Header to use for writing the frame.

        Yields
        ------
        out : string
            The lines in the XYZ-snapshot.
        """
        velocity = None if not self.write_vel else system.particles.vel
        for lines in self.gro_format(system.particles.npart,
                                     system.particles.pos,
                                     velocity,
                                     system.box,
                                     atomname=system.particles.name,
                                     header=header):
            yield lines

    def box_lengths(self, box):
        """Obtain the box lengths from a object.

        Parameters
        ----------
        box : object like `pyretis.core.Box`.
            This is the simulation box.

        Returns
        -------
        out : list of floats
            The box lengths in the different dimensions.
        """
        missing = 3 - box.dim
        if missing > 0:
            boxlength = np.ones(3)
            for i, length in enumerate(box.length):
                boxlength[i] = length * self.convert_pos
            return boxlength
        else:
            return box.length * self.convert_pos

    def load(self, filename):
        """Read snapshots from the trajectory file.

        Here we simply use the `read_gromacs_file` method defined below.
        In addition we convert positions/velocities to internal units.

        Parameters
        ----------
        filename : string
            The path/filename to open.

        Yields
        ------
        out : dict
            This dict contains the snapshot.
        """
        convert_pos = 1.0 / self.convert_pos
        convert_vel = 1.0 / self.convert_vel
        for snapshot in read_gromacs_file(filename):
            snapshot['x'] = np.array(snapshot['x']) * convert_pos
            snapshot['y'] = np.array(snapshot['y']) * convert_pos
            snapshot['z'] = np.array(snapshot['z']) * convert_pos
            snapshot['box'] = [boxl * convert_pos for boxl in snapshot['box']]
            for key in ('vx', 'vy', 'vz'):
                if key in snapshot:
                    snapshot[key] = np.array(snapshot[key]) * convert_vel
            yield snapshot


def read_gromacs_file(filename):
    """A method for reading gromacs GRO files.

    This method will read a gromacs file and yield the different
    snapshots found in the file.

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
    >>> from pyretis.inout.writers.traj import read_gromacs_file
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
    """A method for reading files in xyz format.

    This method will read a xyz file and yield the different snapshots
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
    >>> from pyretis.inout.writers.traj import read_xyz_file
    >>> for snapshot in read_xyz_file('traj.xyz'):
    ...     print(snapshot['x'][0])

    Note
    ----
    The positions will not be converted to a specified set of units.
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

    This is just a simple method to write a single xyz
    configuration to a file. It will NOT convert positions and assumes
    that these are given in correct units. This method is intended as a
    lightweight alternative to `TrajXYZ`.

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
                logger.warning('No atom name given. Using "X"')
                out = _XYZ_FMTN.format('X', posi[0], posi[1], posi[2])
                fileh.write(out)
        else:
            for namei, posi in zip(names, pos):
                out = _XYZ_FMTN.format(namei, posi[0], posi[1], posi[2])
                fileh.write(out)
