# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""This module defines io operations for VASP.

Important methods defined here
------------------------------

read_potcar_file
    A method for reading data from the POTCAR file. Here, we are
    only interested in the number of atoms of different elements.

read_poscar_file
    A method for reading a POSCAR file. This method will read the
    positions (and velocities if presents), the scale and the
    cell. This can be used to convert the positions.

get_energy
    Reads energies from a OSZICAR file.

add_velocities
    A method for adding velocities to a POSCAR file.

read_poscar_traj
    A method for reading frames from a POSCAR trajectory.

append_frame_to_traj
    A method for adding frames to a POSCAR trajectory.

poscar_to_xyz
    A method for converting a POSCAR trajectory to a XYZ trajectory.
"""
import logging
import numpy as np
from pyretis.inout.writers.xyzio import format_xyz_data
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


def read_potcar_file(filename):
    """Read atom types from the POTCAR file.

    Parameters
    ----------
    filename : string
        The path to the POTCAR file.

    Returns
    -------
    atoms : list of strings
        The different atom types found in the POTCAR file.
    """
    atoms = []
    with open(filename, 'r') as fileh:
        for lines in fileh:
            if lines.find('TITEL') != -1:
                atom = lines.strip().split('=')[1].split()[1]
                atoms.append(atom)
    return atoms


def read_poscar_file(filename):
    """Read a VASP POSCAR file.

    Parameters
    ----------
    filename : string
        The path to the POSCAR file.

    Returns
    -------
    out[0] : dict
        This dict contains important information from the
        POSCAR file, for instance the cell and scale factor.
    out[0] : numpy.array
        The positions read from the file. Note that these
        positions are *NOT* converted. That is they will
        either have to be multiplied with the scale factor
        or with the scale factor and the cell defined in the file.
    out[1] : numpy.array
        The velocities, if they could be found in the file.
    """
    poscar = {'comment': None, 'scale': None, 'cell': None, 'natom': None,
              'cartesian': False}
    with open(filename, 'r') as fileh:
        poscar['comment'] = fileh.readline().strip()
        poscar['scale'] = float(fileh.readline().strip())
        cell = [[float(i) for i in fileh.readline().split()] for _ in range(3)]
        poscar['cell'] = np.array(cell)
        # Next line is either atoms or number of atoms:
        line = fileh.readline().strip()
        try:
            int(line.split()[0])
        except ValueError:
            line = fileh.readline().strip()
        poscar['natom'] = [int(i) for i in line.split()]
        totatom = sum(poscar['natom'])
        # Next line is either 'selective dynamics' or
        # coordinates...
        line = fileh.readline().lower()
        if line.find('selective dynamics') != -1:
            line = fileh.readline().lower()
        coordinates = line.strip()
        poscar['cartesian'] = (coordinates.startswith('c') or
                               coordinates.startswith('k'))
        xyz = []
        for _ in range(totatom):
            xyz.append([float(i) for i in fileh.readline().split()[:3]])
        fileh.readline()
        vel = []  # skip a line
        for _ in range(totatom):
            vel.append([float(i) for i in fileh.readline().split()[:3]])
        if len(vel) == 0:
            return poscar, np.array(xyz), None
        else:
            return poscar, np.array(xyz), np.array(vel)


def _read_poscar_data(lines):
    """Helper function to interpret POSCAR data.

    This method is meant as a helper method when reading multiple frames
    from a POSCAR trajectory.

    Parameters
    ----------
    filename : string
        The path to the POSCAR file.

    Returns
    -------
    out[0] : dict
        This dict contains important information from the
        POSCAR file, for instance the cell and scale factor.
    out[0] : numpy.array
        The positions read from the file. Note that these
        positions are *NOT* converted. That is they will
        either have to be multiplied with the scale factor
        or with the scale factor and the cell defined in the file.
    out[1] : numpy.array
        The velocities, if they could be found in the file.
    """
    poscar = {'comment': None, 'scale': None, 'cell': None,
              'natom': None, 'cartesian': False}
    # 5 first line are always the same
    poscar['comment'] = lines[0]
    poscar['scale'] = float(lines[1])
    cell = [[float(i) for i in line.split()] for line in lines[2:5]]
    poscar['cell'] = np.array(cell)
    idx = 5
    # Next line is either atoms or number of atoms:
    line = lines[idx]
    idx += 1
    try:
        int(line.split()[0])
    except ValueError:
        line = lines[idx]
        idx += 1
    poscar['natom'] = [int(i) for i in line.split()]
    totatom = sum(poscar['natom'])
    # Next line is either 'selective dynamics' or
    # coordinates...
    line = lines[idx].lower()
    idx += 1
    if line.find('selective dynamics') != -1:
        line = lines[idx].lower()
        idx += 1
    coordinates = line.strip()
    poscar['cartesian'] = (coordinates.startswith('c') or
                           coordinates.startswith('k'))
    xyz = []
    for _ in range(totatom):
        xyz.append([float(i) for i in lines[idx].strip().split()[:3]])
        idx += 1
    if totatom + idx <= len(lines):
        idx += 1  # skip one line
        vel = []
        for _ in range(totatom):
            vel.append([float(i) for i in lines[idx].strip().split()[:3]])
            idx += 1
        return poscar, np.array(xyz), np.array(vel)
    else:
        return poscar, np.array(xyz), None


def get_energy(filename):
    """Reads energies from a OSZICAR file.

    Parameters
    ----------
    filename : string
        The path to the OSZICAR file.

    Returns
    -------
    out[0] : list of floats
        The kinetic energy.
    out[1] : list of floats
        The potential energy.
    """
    ekin = []
    vpot = []
    with open(filename, 'r') as fileh:
        for lines in fileh:
            if lines.find('T=') != -1:
                ekin.append(float(lines.split('EK=')[1].split()[0]))
                vpot.append(float(lines.split('E0=')[1].split()[0]))
    if ekin == float('nan') or vpot == float('nan'):
        raise ValueError('Rar energi!')
    return ekin, vpot


def add_velocities(input_file, output_file, velocities):
    """Add/update velocities to/for a POSCAR file.

    This method will read the input file, write all it's
    contents up to the velocities and then write out the
    specified velocities.

    Parameters
    ----------
    input_file : string
        The input file to strip velocities from.
    output_file : string
        The file to create.
    velocities : numpy.array
        The velocities to add to the file.
    """
    logger.debug('Adding velocities %s -> %s', input_file, output_file)
    with open(output_file, 'w') as outfile, open(input_file, 'r') as infile:
        # First 5 lines are comment, scale + the cell:
        for _ in range(5):
            outfile.write(infile.readline())
        # Next line is either atoms or number of atoms,
        line = infile.readline()
        outfile.write(line)
        try:
            int(line.strip().split()[0])
        except ValueError:
            line = infile.readline()
            outfile.write(line)
        totatom = sum([int(i) for i in line.strip().split()])
        # Next line is either 'selective dynamics' or coordinates
        line = infile.readline()
        outfile.write(line)
        if line.lower().find('selective dynamics') != -1:
            line = infile.readline()
            outfile.write(line)
        for _ in range(totatom):
            outfile.write(infile.readline())
        # Stop reading here and just add velocities:
        for vel in velocities:
            outfile.write('\n{:15.8E} {:15.8E} {:15.8E}'.format(*vel))


def read_poscar_traj(input_file):
    """A method to yield frames from a POSCAR file.

    Parameters
    ----------
    input_file : string
        The file to open and read.

    Yields
    ------
    out : dict
        The frame data.
    """
    buff = []
    frame = 0
    with open(input_file, 'r') as infile:
        for lines in infile:
            if lines.startswith('# Frame:'):
                if len(buff) > 0:
                    # interpret whatever in buff
                    data, xyz, vel = _read_poscar_data(buff)
                    yield frame, data, xyz, vel
                    # reset buff
                    buff = []
                frame = int(lines.split('Frame:')[1])
            else:
                buff.append(lines)
    if len(buff) > 0:
        # interpret last frame:
        data, xyz, vel = _read_poscar_data(buff)
        yield frame, data, xyz, vel


def append_frame_to_traj(input_file, traj_file, frame):
    """Append data from input file to another file

    Parameters
    ----------
    input_file : string
        The file to read.
    traj_file : string
        The file to append to.
    frame : integer
        Just to give a name to the frame.
    """
    with open(traj_file, 'a') as outfile:
        outfile.write('# Frame: {}\n'.format(frame))
        with open(input_file) as infile:
            outfile.write(infile.read())
            outfile.write('\n')


def poscar_to_xyz(traj_file, xyz_file, names=None):
    """Convert a POSCAR trajectory to XYZ format.

    Parameters
    ----------
    traj_file : string
        The input POSCAR trajectory.
    xyz_file : string
        The output XYZ trajectory.
    names : list, optional.
        A list of atom names to use.
    """
    with open(xyz_file, 'w') as outfile:
        for (frame, data, xyz, vel) in read_poscar_traj(traj_file):
            if not data['cartesian']:
                pos = data['scale'] * np.dot(xyz, data['cell'])
            else:
                # Just scale for cartesian
                pos = data['scale'] * xyz
            for line in format_xyz_data(pos, vel=vel,
                                        header='# Frame: {}'.format(frame),
                                        names=names):
                outfile.write('{}\n'.format(line))
