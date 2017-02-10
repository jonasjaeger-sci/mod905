# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Module for handling the output/input of trajectory data.

This module defines some classes for writing out and reading
trajectory data in a XYZ-like format. By XYZ-like we here mean
that we also include velocities as part of the file.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

XYZWriter (:py:class:`.XYZWriter`)
    Writing of coordinates to a file in a XYZ format.

PathXYZWriter (:py:class:`.PathXYZWriter`)
    Writing of path data to a file in XYZ format.


Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

read_xyz_file (:py:func:`.read_xyz_file`)
    A method for reading snapshots from a XYZ file.

format_xyz_data (:py:func:`.format_xyz_data`)
    A method for formatting position/velocity data in to a
    XYZ-like format. This can be used by external engines to
    convert to a standard format.

write_xyz_file (:py:func:`.write_xyz_file`)
    Just a convenience method for writing to a new file.
"""
import logging
import numpy as np
from pyretis.inout.writers.writers import TrajWriter, adjust_coordinate
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


# define formats for the trajectory output:
_XYZ_FMT = '{0:5s} {1:8.3f} {2:8.3f} {3:8.3f}'
_XYZ_BIG_FMT = '{:5s}' + 3*' {:15.9f}'
_XYZ_BIG_VEL_FMT = _XYZ_BIG_FMT + 3*' {:15.9f}'


__all__ = [
    'XYZWriter',
    'PathXYZWriter',
    'read_xyz_file',
    'format_xyz_data']


class XYZWriter(TrajWriter):
    u"""A class for writing XYZ files.

    This class handles writing of a system to a file in a simple XYZ
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
        pos = adjust_coordinate(pos)
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
        system : object like :py:class:`.System`
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


def read_xyz_file(filename):
    """A method for reading files in XYZ format.

    This method will read a XYZ file and yield the different snapshots
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
    >>> from pyretis.inout.writers.xyzio import read_xyz_file
    >>> for snapshot in read_xyz_file('traj.xyz'):
    ...     print(snapshot['x'][0])

    Note
    ----
    The positions will not be converted to a specified set of units.
    """
    lines_to_read = 0
    snapshot = None
    xyz_keys = ('atomname', 'x', 'y', 'z', 'vx', 'vy', 'vz')
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
                    if i == 0:
                        value = val.strip()
                    else:
                        value = float(val)
                    try:
                        snapshot[key].append(value)
                    except KeyError:
                        snapshot[key] = [value]
    if snapshot is not None:
        yield snapshot


def format_xyz_data(pos, vel=None, names=None, header=None, fmt=None):
    """Format XYZ data for outputting.

    Parameters
    ----------
    pos : numpy.array
       The positions to write.
    vel : numpy.array, optional
       The velocities to write.
    names : list, optional
        The atom names.
    header : string, optional
        Header to use for writing the XYZ-file.
    fmt : string
        A format to use for the writing

    Yields
    ------
    out : string
        The formatted lines.
    """
    npart = len(pos)
    pos = adjust_coordinate(pos)

    if fmt is None:
        fmt = _XYZ_BIG_FMT if vel is None else _XYZ_BIG_VEL_FMT

    if vel is not None:
        vel = adjust_coordinate(vel)
    yield '{}'.format(npart)

    if header is None:
        yield 'pyretis XYZ writer'
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


def write_xyz_file(filename, pos, vel=None, names=None, header=None):
    """Create a new XYZ file with the given file name.

    Parameters
    ----------
    filename : string
        The file to create.
    pos : numpy.array
       The positions to write.
    vel : numpy.array, optional
       The velocities to write.
    names : list, optional
        The atom names.
    header : string, optional
        Header to use for writing the XYZ-file.

    Note
    ----
    We will here just overwrite if the file already exist.

    Examples
    --------
    >>> import numpy as np
    >>> from pyretis.inout.writers.xyzio import write_xyz_file
    >>> xyz = 10 * np.random.rand(10, 3)
    >>> write_xyz_file('conf.xyz', xyz)
    >>> vel = 10 * np.random.rand(10, 3)
    >>> write_xyz_file('confv.xyz', xyz, vel)
    """
    with open(filename, 'w') as output_file:
        for line in format_xyz_data(pos, vel=vel, names=names,
                                    header=header):
            output_file.write('{}\n'.format(line))
