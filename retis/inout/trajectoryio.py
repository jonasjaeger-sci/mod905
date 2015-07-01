# -*- coding: utf-8 -*-
"""
This file contains methods/classes for io operations
on trajectories.
"""
from __future__ import absolute_import
from retis.core.units import CONVERT
from .inout import create_backup
import numpy as np
import itertools
import os
import warnings

__all__ = ['WriteXYZ', 'WriteGromacs']


def _adjust_coordinate(coord):
    """
    Method to adjust the dimensionality. A lot of the different
    formats expects us to have 3 dimensional data. This methods just
    adds dummy dimensions equal to zero

    Parameters
    ----------
    coord : numpy.array
        The real coordinates

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


class TrajectoryWriter(object):
    """
    TrajectoryWriter(object)

    This class defines a simple object to output a trajectory.
    The actual writing of the trajectory should be specified in the
    appropriate class for the format.

    Attributes
    ----------
    filename : string
        Name of file to write.
    filetype : string
        Identifies the filetype to write - the "format".
    frame : int
        Counter for the number of frames written.
    atomnames : list of strings
        Variables that stores atomnames in case
        these are not specified when writing frames.
    oldfile : string
        Defines how we handle existing files with the same
        name as given in filename.
    """
    def __init__(self, filename, filetype, oldfile, frame=0):
        """
        Initiates the trajectory writer object.

        Paramters
        ---------
        filename : string
            Name of the file to write.
        filetype : string
            Identifies the filetype to write (i.e. the format).
        oldfile : string
            Behavior if the filename is an existing file.
        frame : int
            Counts the number of frames written
        """
        self.frame = frame
        self.filename = filename
        self.filetype = filetype
        self.atomnames = []
        try:
            if os.path.isfile(self.filename):
                msg = 'File exist'
                if oldfile == 'overwrite':
                    msg += '\nWill overwrite!'
                    self.trajfile = open(self.filename, 'w')
                elif oldfile == 'append':
                    msg += '\nWill append to file!'
                    self.trajfile = open(self.filename, 'a')
                else:
                    msg += create_backup(self.filename)
                    self.trajfile = open(self.filename, 'w')
                warnings.warn(msg)
            else:
                self.trajfile = open(self.filename, 'w')
        except IOError as error:
            msg = 'I/O error ({}): {}'.format(error.errno, error.strerror)
            warnings.warn(msg)
        except Exception as error:
            msg = 'Error: {}'.format(error)
            warnings.warn(msg)
            raise

    def _generate_atom_names(self, npart, name='X'):
        """
        This method will generate atom names is case they
        are not given

        Parameters
        ----------
        npart : int
            Number of particles currently present
        name : string
            Atom name to use, default is X.
        """
        if len(self.atomnames) != npart:
            self.atomnames = [name] * npart

    def close(self):
        """
        Method to close the file, in case that is explicitly needed.
        """
        if not self.trajfile.closed:
            self.trajfile.close()

    def __del__(self):
        """
        This method in just to close the file in case the program
        crashes. It is used here as it's not so nice to add as
        with statement to the main script running the simulation.
        """
        if not self.trajfile.closed:
            self.trajfile.close()


class WriteXYZ(TrajectoryWriter):
    """
    WriteXYZ(TrajectoryWriter)
    This class handles writing of a system to a file in a simple xyz format.

    Attributes
    ----------
    Same as for TrajectoryWriter and in addition:
    convert : dict of floats
        Defines the conversion of positions from internal units to Å.
    """
    def __init__(self, filename, oldfile='backup', frame=0, units='lj'):
        filetype = 'xyz'
        self.convert = {'pos': CONVERT['length'][units, 'Å']}
        super(WriteXYZ, self).__init__(filename, filetype, oldfile,
                                       frame=frame)

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
        status = False
        try:
            npart = len(pos)
            self.trajfile.write('{0}\n'.format(npart))
            if header is None:
                header = 'Output from retis, frame no. {}'.format(self.frame)
            self.trajfile.write(header)
            if names is None:
                self._generate_atom_names(npart)
                names = self.atomnames
            pos = _adjust_coordinate(pos)
            for namei, posi in zip(names, pos):
                posc = posi * self.convert['pos']
                self.trajfile.write('\n{} {} {} {}'.format(namei, *posc))
            self.frame += 1
            status = True
        except IOError as error:
            msg = 'XYZ write I/O error ({}): {}'.format(error.errno,
                                                        error.strerror)
            warnings.warn(msg)
        except ValueError as error:
            msg = 'XYZ write value error: {}'.format(error)
            warnings.warn(msg)
        except Exception as error:
            msg = 'XYZ write error: {}'.format(error)
            warnings.warn(msg)
            raise
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


class WriteGromacs(TrajectoryWriter):
    """
    WriteGromacs(TrajectoryWriter)
    This class handles writing of a system to a file in a simple xyz format.

    Attributes
    ----------
    Same as for TrajectoryWriter and in addition the following:
    box : object of type box as defined in box.py
        The simulation box, used for box-lengths.
    gro_fmt : string
        The gromacs file format.
    gro_vmt_vel : string
        gromacs file format that also accepts velocities.
    convert : dict of floats
        Defines the conversion of positions from internal units to nm
        and nm/ps.
    """
    def __init__(self, filename, box, oldfile='backup', frame=0, units='lj'):
        filetype = 'gromacs'
        self.box = box
        self.convert = {'pos': CONVERT['length'][units, 'nm'],
                        'vel': CONVERT['velocity'][units, 'nm/ps']}
        super(WriteGromacs, self).__init__(filename, filetype, oldfile,
                                           frame=frame)
        self.gro_fmt = '{0:5d}{1:5s}{2:5s}{3:5d}{4:8.3f}{5:8.3f}{6:8.3f}\n'
        self.gro_fmt_vel = self.gro_fmt[:-1] + '{7:8.3f}{8:8.3f}{9:8.3f}\n'

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
        status = False
        try:
            npart = len(pos)
            if atomname is None:
                self._generate_atom_names(npart)
                atomname = self.atomnames
            if residuename is None:  # just reuse atomnames
                residuename = atomname
            if header is None:
                header = 'Output from retis, frame no. {}\n'.format(self.frame)

            self.trajfile.write(header)
            self.trajfile.write('{0}\n'.format(npart))

            pos = _adjust_coordinate(pos)  # in case pos is 1D or 2D
            if not vel is None:
                vel = _adjust_coordinate(vel)

            for i, posi in enumerate(pos):
                posc = posi * self.convert['pos']
                residuenr = i + 1 if residuenum is None else residuenum[i]
                atomnr = i + 1 if atomnum is None else atomnum[i]
                if vel is None:
                    newline = self.gro_fmt.format(residuenr, residuename[i],
                                                  atomname[i], atomnr, *posc)
                else:
                    velc = vel[i] * self.convert['vel']
                    newline = self.gro_fmt_vel.format(residuenr,
                                                      residuename[i],
                                                      atomname[i],
                                                      atomnr,
                                                      *itertools.chain(posc,
                                                                       velc))
                self.trajfile.write(newline)
            self.trajfile.write('{0} {1} {2}\n'.format(*self._box_lengths()))
            status = True
            self.frame += 1
        except IOError as error:
            msg = 'Gro write I/O error ({}): {}'.format(error.errno,
                                                        error.strerror)
            warnings.warn(msg)
        except ValueError as error:
            msg = 'Gro write value error: {}'.format(error)
            warnings.warn(msg)
        except Exception as error:
            msg = 'Gro write error: {}'.format(error)
            warnings.warn(msg)
            raise
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
