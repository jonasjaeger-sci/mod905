# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Module for handling the output/input of trajectory data.

This module defines some classes for writing out trajectory data.
Here we define a class for a simple xyz-format and a class for writing
in a GROMACS format.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

TrajWriter
    Generic class for writing trajectory output.

XYZWriter
    Writing of coordinates to a file in a xyz format.

PathXYZWriter
    Writing of path data to a file in xyz format.

GROWriter
    Writing of a coordinates to a file in a GROMACS format.

PathGROWriter
    Writing of path data to a file in GROMACS format.

PathExtWriter
    A class for writing external paths to file.


Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

read_xyz_file
    A method for reading snapshots from a xyz file.

read_gromacs_file
    A method for reading snapshots from a GROMACS GRO file.

format_xyz_data
    A method for formatting position/velocity data in to a
    xyz-like format. This can be used by external engines to
    convert to a standard format.
"""
import logging
import os
import numpy as np
from pyretis.core.units import CONVERT  # unit conversion in trajectory
from pyretis.inout.writers.writers import Writer
from pyretis.inout.writers.writers import read_some_lines
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


# define formats for the trajectory output:
_GRO_FMT = '{0:5d}{1:5s}{2:5s}{3:5d}{4:8.3f}{5:8.3f}{6:8.3f}'
_GRO_VEL_FMT = _GRO_FMT + '{7:8.4f}{8:8.4f}{9:8.4f}'
_GRO_BOX_FMT = '{0:12.6f} {1:12.6f} {2:12.6f}'
_XYZ_FMT = '{0:5s} {1:8.3f} {2:8.3f} {3:8.3f}'
_XYZ_BIG_FMT = '{:5s}' + 3*' {:15.9f}'
_XYZ_BIG_VEL_FMT = _XYZ_BIG_FMT + 3*' {:15.9f}'


__all__ = [
    'XYZWriter',
    'PathXYZWriter',
    'GROWriter',
    'PathGROWriter',
    'PathExtWriter',
    'read_gromacs_file',
    'read_xyz_file',
    'format_xyz_data']


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


class TrajWriter(Writer):
    """Generic class for writing system shapshots.

    Attributes
    ----------
    atom_names : list
        These are the atom names used for the output.
    convert_pos : float
        Defines the conversion of positions from internal units.
    covert_vel : float or None
        Defines the conversion of velocities from internal units.
    frame : integer
        The number of frames written.
    """

    def __init__(self, name, write_vel, units, out_units):
        """Initialize the writer.

        Parameters
        ----------
        name : string
            Just a name to identify the writer when printing it.
        write_vel : boolean
            If True, the writer will attempt to output velocities. This may
            or may not be supported by the writer.
        units : string
            The internal units used in the simulation.
        out_units : dict of strings
            The units used in the output from the writer.
        """
        super().__init__(name, header=None)
        self.print_header = False
        self.atom_names = []
        self.frame = 0  # number of frames written
        self.write_vel = write_vel
        pos_unit = out_units['pos']
        vel_unit = out_units.get('vel', None)
        try:
            self.convert_pos = CONVERT['length'][units, pos_unit]
        except KeyError:
            self.convert_pos = 1.0
            msg = 'Could not get conversion "{} -> {}"'.format(units,
                                                               pos_unit)
            logger.info(msg)
            msg = 'Position output will be in units: "{}"'.format(units)
            logger.info(msg)
        if vel_unit is not None:
            try:
                self.convert_vel = CONVERT['velocity'][units, vel_unit]
            except KeyError:
                self.convert_vel = 1.0
                msg = 'Could not get conversion "{} -> {}"'.format(units,
                                                                   vel_unit)
                logger.info(msg)
                msg = 'Position output will be in units: "{}"'.format(units)
                logger.info(msg)

    def format_snapshot(self, step, system):
        """Format the snapshot for output."""
        raise NotImplementedError

    def generate_output(self, step, system):
        """Generate the snapshot output."""
        for lines in self.format_snapshot(step, system):
            yield lines


class XYZWriter(TrajWriter):
    u"""A class for writing XYZ files.

    This class handles writing of a system to a file in a simple xyz
    format.

    Attributes
    ----------
    atom_names : list
        These are the atom names used for the output.
    convert_pos : float
        Defines the conversion of positions from internal units to
        Ångström.
    frame : integer
        The number of frames written.
    """
    out_units = {'pos': 'A', 'vel': None}

    def __init__(self, units):
        """Initialization of the XYZ writer.

        Parameters
        ----------
        units : string
            The system of units used internally for positions and
            velocities.
        """
        super().__init__('XYZWriter', False, units, self.out_units)

    def xyz_format(self, step, npart, pos):
        """Format a single frame using the XYZ format.

        Parameters
        ----------
        step : int
            The current step number.
        npart : int
            The number of particles.
        pos : numpy.array
            The positions for the particles.

        Returns
        -------
        out : list of strings
            The XYZ formatted snapshot.
        """
        buff = []
        buff.append('{0}'.format(npart))
        buff.append('Snapshot, step: {}'.format(step))
        if len(self.atom_names) != npart:
            self.atom_names = ['X'] * npart
        pos = _adjust_coordinate(pos)
        for namei, posi in zip(self.atom_names, pos):
            out = _XYZ_FMT.format(namei,
                                  posi[0] * self.convert_pos,
                                  posi[1] * self.convert_pos,
                                  posi[2] * self.convert_pos)
            buff.append(out)
        self.frame += 1
        return buff

    def format_snapshot(self, step, system):
        """Format the given snapshot.

        Parameters
        ----------
        step : int
            The current simulation step.
        system : object like `System` from `pyretis.core.system`
            The system object with the positions to write

        Returns
        -------
        out : list of strings
            The formatted snapshot
        """
        if len(self.atom_names) != system.particles.npart:
            self.atom_names = system.particles.name
        return self.xyz_format(step, system.particles.npart,
                               system.particles.pos)

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


class PathXYZWriter(XYZWriter):
    """A class for writing trajectories to XYZ files."""

    def generate_output(self, step, path):
        yield '# Cycle: {}, status: {}'.format(step, path.status)
        for i, phasepoint in enumerate(path.trajectory()):
            npart = len(phasepoint['pos'])
            for line in self.xyz_format(i, npart, phasepoint['pos']):
                yield line


class GROWriter(TrajWriter):
    """A class for writing GROMACS GRO files.

    This class handles writing of a system to a file using the GROMACS
    format. The GROMACS format is described in the GROMACS manual [#]_.

    Attributes
    ----------
    atom_names : list
        These are the atom names used for the output.
    residue_names : list
        These are the residue names used for the output.
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
    out_units = {'pos': 'nm', 'vel': 'nm/ps'}

    def __init__(self, units, write_vel):
        """Initiate the GROMACS writer.

        Parameters
        ----------
        units : string
            The internal units used in the simulation.
        write_vel : boolean
            If True, we will also output velocities
        names : list of strings, optional
            Names for labeling atoms.
        """
        super().__init__('GROWriter', write_vel, units, self.out_units)
        self.residue_names = self.atom_names

    def gro_format(self, step, npart, pos, vel, box_lengths):
        """Apply the GROMACS format to a snapshot.

        Parameters
        ----------
        step : int
            The current simulation step.
        npart : int
            The number of particles in the snapshot.
        pos : numpy.array
            The positions of the particles.
        vel : numpy.array or None
            The velocities of the particles.
        box : list of floats.
            The simulation box lengths.

        Returns
        -------
        out : list of strings
            The formatted snapshot.
        """
        buff = ['Snapshot, step: {}'.format(step)]
        buff.append('{}'.format(npart))
        pos = _adjust_coordinate(pos)  # in case pos is 1D or 2D
        if vel is not None:
            vel = _adjust_coordinate(vel)  # in case vel is 1D or 2D
        if len(self.atom_names) != npart:
            self.atom_names = ['X'] * npart
        if len(self.residue_names) != npart:
            self.residue_names = ['X'] * npart
        for i in range(npart):
            residuenr = i + 1
            atomnr = i + 1
            if vel is None:
                buff.append(_GRO_FMT.format(residuenr, self.residue_names[i],
                                            self.atom_names[i], atomnr,
                                            pos[i][0] * self.convert_pos,
                                            pos[i][1] * self.convert_pos,
                                            pos[i][2] * self.convert_pos))
            else:
                buff.append(_GRO_VEL_FMT.format(residuenr,
                                                self.residue_names[i],
                                                self.atom_names[i],
                                                atomnr,
                                                pos[i][0] * self.convert_pos,
                                                pos[i][1] * self.convert_pos,
                                                pos[i][2] * self.convert_pos,
                                                vel[i][0] * self.convert_vel,
                                                vel[i][1] * self.convert_vel,
                                                vel[i][2] * self.convert_vel))
        if box_lengths is None:
            buff.append(_GRO_BOX_FMT.format(123.0, 123.0, 123.0))
        else:
            buff.append(_GRO_BOX_FMT.format(*box_lengths))
        self.frame += 1
        return buff

    def format_snapshot(self, step, system):
        """Format a snapshot in GROMACS format.

        This is a method for writing a configuration in GRO-format.

        Parameters
        ----------
        step : int
            The current step number.
        system : object like `System` from `pyretis.core.system`
            The system object with the positions to write

        Returns
        -------
        out : list of strings
            The lines in the GRO-snapshot.
        """
        if len(self.atom_names) != system.particles.npart:
            self.atom_names = system.particles.name
            self.residue_names = self.atom_names
        vel = None if not self.write_vel else system.particles.vel
        box = self.box_lengths(system.box)
        return self.gro_format(step, system.particles.npart,
                               system.particles.pos, vel, box)

    def box_lengths(self, box):
        """Obtain the box lengths from a object.

        Parameters
        ----------
        box : object like `pyretis.core.Box`
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


class PathGROWriter(GROWriter):
    """A class for writing trajectories to GRO files."""

    def generate_output(self, step, path):
        yield '# Cycle: {}, status: {}'.format(step, path.status)
        for i, phasepoint in enumerate(path.trajectory()):
            vel = None if not self.write_vel else phasepoint['vel']
            pos = phasepoint['pos']
            npart = len(pos)
            box = None
            for line in self.gro_format(i, npart, pos, vel, box):
                yield line

    def load(self, filename):
        """Load a trajectory GRO file."""
        convert_pos = 1.0 / self.convert_pos
        convert_vel = 1.0 / self.convert_vel
        for block in read_some_lines(filename, line_parser=None):
            traj = []
            for snapshot in read_gromacs_lines(block['data']):
                new_snap = {'pos': None, 'vel': None}

                for key in ('x', 'y', 'z'):
                    new_snap[key] = np.array(snapshot[key]) * convert_pos
                for key in ('vx', 'vy', 'vz'):
                    if key in snapshot:
                        new_snap[key] = np.array(snapshot[key]) * convert_vel
                traj.append(new_snap)
            out = {'comment': block['comment'], 'data': traj}
            yield out


class PathExtWriter(Writer):
    """A class for writing external trajectories.

    Attributes
    ----------
    print_header : boolean
        Determines if we should print the header on the first step.
    """

    def __init__(self):
        """Initialization of the PathExtWriter writer.

        Parameters
        ----------
        units : string
            The system of units used internally for positions and
            velocities.
        """
        header = {'labels': ['Step', 'Filename', 'index', 'vel'],
                  'width': [10, 20, 10, 5], 'spacing': 2}

        super().__init__('PathExtWriter', header=header)
        self.print_header = False

    def generate_output(self, step, path):
        yield '# Cycle: {}, status: {}'.format(step, path.status)
        yield self.header
        for i, phasepoint in enumerate(path.trajectory()):
            filename, idx = phasepoint['pos']
            filename_short = os.path.basename(filename)
            if idx is None:
                idx = 0
            vel = -1 if phasepoint['vel'] else 1
            yield '{:>10}  {:>20s}  {:>10}  {:5}'.format(i, filename_short,
                                                         idx, vel)

    @staticmethod
    def line_parser(line):
        """A simple parser for reading path data.

        Parameters
        ----------
        line : string
            The line to parse.

        Returns
        -------
        out : list
            The columns of data.
        """
        return [col for col in line.split()]


def read_gromacs_lines(lines):
    """A method for reading GROMACS GRO data.

    This method will read a GROMACS file and yield the different
    snapshots found in the file.

    Parameters
    ----------
    lines : iterable
        Some lines of text data representing a GROMACS GRO file.

    Yields
    ------
    out : dict
        This dict contains the snapshot.
    """
    lines_to_read = 0
    snapshot = {}
    read_natoms = False
    gro = (5, 5, 5, 5, 8, 8, 8, 8, 8, 8)
    gro_keys = ('residunr', 'residuname', 'atomname', 'atomnr',
                'x', 'y', 'z', 'vx', 'vy', 'vz')
    gro_type = (int, str, str, int, float, float, float, float, float, float)
    for line in lines:
        if read_natoms:
            read_natoms = False
            lines_to_read = int(line.strip()) + 1
            continue  # just skip to next line
        if lines_to_read == 0:  # new shapshot
            if len(snapshot) > 0:
                yield snapshot
            snapshot = {'header': line.strip()}
            read_natoms = True
        elif lines_to_read == 1:  # read box
            snapshot['box'] = [float(boxl) for boxl in line.strip().split()]
            lines_to_read -= 1
        else:  # read atoms
            lines_to_read -= 1
            current = 0
            for i, key, gtype in zip(gro, gro_keys, gro_type):
                val = line[current:current+i].strip()
                if len(val) == 0:
                    # This typically happens if we try to read velocities
                    # and they are not present in the file.
                    break
                value = gtype(val)
                current += i
                try:
                    snapshot[key].append(value)
                except KeyError:
                    snapshot[key] = [value]
    if len(snapshot) > 1:
        yield snapshot


def read_gromacs_file(filename):
    """A method for reading GROMACS GRO files.

    This method will read a GROMACS file and yield the different
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
    with open(filename, 'r') as fileh:
        for snapshot in read_gromacs_lines(fileh):
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


def format_xyz_data(pos, vel=None, names=None, header=None, fmt=None):
    """Format xyz data for outputting.

    Parameters
    ----------
    pos : numpy.array
       The positions to write.
    vel : numpy.array, optional
       The velocities to write.
    names : list, optional
        The atom names.
    header : string, optional
        Header to use for writing the xyz-file.
    fmt : string
        A format to use for the writing

    Yields
    ------
    out : string
        The formatted lines.
    """
    npart = len(pos)
    pos = _adjust_coordinate(pos)

    if fmt is None:
        fmt = _XYZ_BIG_FMT if vel is None else _XYZ_BIG_VEL_FMT

    if vel is not None:
        vel = _adjust_coordinate(vel)
    yield '{}'.format(npart)

    if header is None:
        yield 'pyretis xyz writer'
    else:
        yield '{}'.format(header)

    if names is None:
        logger.warning('No atom name given. Using "X"')

    for i in range(npart):
        if names is None:
            namei = 'X'
        else:
            namei = names[i]
        if vel is None:
            yield fmt.format(namei, *pos[i, :])
        else:
            yield fmt.format(namei, *pos[i, :], *vel[i, :])
