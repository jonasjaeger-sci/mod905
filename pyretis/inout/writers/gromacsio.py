# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Module for handling GROMACS input/output.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

GROWriter (:py:class:`.GROWriter`)
    Writing of a coordinates to a file in a GROMACS format.

PathGROWriter (:py:class:`.PathGROWriter`)
    Writing of trajectories in GROMACS gro-format.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

read_gromacs_file (:py:func:`.read_gromacs_file`)
    A method for reading snapshots from a GROMACS GRO file.

read_gromos96_file (:py:func:`.read_gromos96_file`)
    Read a single configuration GROMACS .g96 file.

write_gromos96_file (:py:func:`.write_gromos96_file`)
    Write configuration in GROMACS g96 format.
"""
import logging
import numpy as np
from pyretis.inout.writers.writers import (TrajWriter, read_some_lines,
                                           adjust_coordinate)
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


# define formats for the trajectory output:
_GRO_FMT = '{0:5d}{1:5s}{2:5s}{3:5d}{4:8.3f}{5:8.3f}{6:8.3f}'
_GRO_VEL_FMT = _GRO_FMT + '{7:8.4f}{8:8.4f}{9:8.4f}'
_GRO_BOX_FMT = '{0:12.6f} {1:12.6f} {2:12.6f}'


__all__ = [
    'GROWriter',
    'PathGROWriter',
    'read_gromacs_file',
    'read_gromos96_file',
    'write_gromos96_file']


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
        pos = adjust_coordinate(pos)  # in case pos is 1D or 2D
        if vel is not None:
            vel = adjust_coordinate(vel)  # in case vel is 1D or 2D
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
            buff.append(_GRO_BOX_FMT.format(222.2, 222.2, 222.2))
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
        system : object like :py:class:`.System`
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
        box : object like :py:class:`.Box`
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
    >>> from pyretis.inout.writers.gromacsio import read_gromacs_file
    >>> for snapshot in read_gromacs_file('traj.gro'):
    ...     print(snapshot['x'][0])
    """
    with open(filename, 'r') as fileh:
        for snapshot in read_gromacs_lines(fileh):
            yield snapshot


def read_gromos96_file(filename):
    """Read a single configuration GROMACS .g96 file.

    Parameters
    ----------
    filename : string
        The file to read.

    Returns
    -------
    rawdata : dict of list of strings
        This is the raw data read from the file grouped into sections.
        Note that this does not include the actual positions and
        velocities as these are returned separately.
    xyz : numpy.array
        The positions.
    vel : numpy.array
        The velocities.
    """
    _len = 15
    _pos = 24
    rawdata = {'TITLE': [], 'POSITION': [], 'VELOCITY': [], 'BOX': []}
    section = None
    with open(filename, 'r') as gromosfile:
        for lines in gromosfile:
            new_section = False
            stripline = lines.strip()
            if stripline == 'END':
                continue
            for key in rawdata:
                if stripline == key:
                    new_section = True
                    section = key
                    break
            if new_section:
                continue
            rawdata[section].append(lines.rstrip())
    txtdata = {}
    xyzdata = {}
    for key in ('POSITION', 'VELOCITY'):
        txtdata[key] = []
        xyzdata[key] = []
        for line in rawdata[key]:
            txt = line[:_pos]
            txtdata[key].append(txt)
            pos = [float(line[i:i+_len]) for i in range(_pos, 4*_len, _len)]
            xyzdata[key].append(pos)
        xyzdata[key] = np.array(xyzdata[key])
    rawdata['POSITION'] = txtdata['POSITION']
    rawdata['VELOCITY'] = txtdata['VELOCITY']
    if len(rawdata['VELOCITY']) == 0:
        # No velicities were found in the input file.
        xyzdata['VELOCITY'] = np.zeros_like(xyzdata['POSITION'])
    return rawdata, xyzdata['POSITION'], xyzdata['VELOCITY']


def write_gromos96_file(filename, raw, xyz, vel):
    """Write configuration in GROMACS g96 format.

    Parameters
    ----------
    filename : string
        The name of the file to create.
    raw : dict of lists of strings
        This contains the raw data read from a .g96 file.
    xyz : numpy.array
        The positions to write.
    vel : numpy.array
        The velocities to write.
    """
    _keys = ('TITLE', 'POSITION', 'VELOCITY', 'BOX')
    _fmt = '{0:}{1:15.9f}{2:15.9f}{3:15.9f}\n'
    with open(filename, 'w') as outfile:
        for key in _keys:
            outfile.write('{}\n'.format(key))
            for i, line in enumerate(raw[key]):
                if key == 'POSITION':
                    outfile.write(_fmt.format(line, *xyz[i]))
                elif key == 'VELOCITY':
                    outfile.write(_fmt.format(line, *vel[i]))
                else:
                    outfile.write('{}\n'.format(line))
            outfile.write('END\n')
