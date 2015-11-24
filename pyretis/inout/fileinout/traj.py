# -*- coding: utf-8 -*-
"""Module for handling the output/input of trajectory data.

This module defines some classes for writing out trajectory data.
Here we define a class for a simple xyz-format and a class for writing
in a gromacs format.

Important classes defined here:

- WriteXYZ: Writing of coordinates to a file in a xyz format.

- WriteGromacs: Writing of a coordinates to a file in a gromacs format.
"""
import numpy as np
from pyretis.core.units import CONVERT  # unit conversion in trajectory
from pyretis.inout.fileinout.fileinout import FileWriter

# define formats for the trajectory output:
_GRO_FMT = '{0:5d}{1:5s}{2:5s}{3:5d}{4:8.3f}{5:8.3f}{6:8.3f}\n'
_GRO_VEL_FMT = _GRO_FMT[:-1] + '{7:8.3f}{8:8.3f}{9:8.3f}\n'
_GRO_BOX_FMT = '{0:12.6f} {1:12.6f} {2:12.6f}\n'
_XYZ_FMT = '{0:5s} {1:8.3f} {2:8.3f} {3:8.3f}\n'


__all__ = ['WriteXYZ', 'WriteGromacs']


def create_traj_writer(filename, filefmt, oldfile, system):
    """Method to create a trajectory writer from settings.

    This method will create a trajectory writer based on settings for
    a format. It will also attach a given `system` so the writer.

    Parameters
    ----------
    filename : string
        Name of file to create
    filefmt : string
        Format of file, 'xyz' for xyz, 'gro' for gromacs.
    oldfile : string
        How to deal with backups of old files with the same name.
    system : object like `System` from `pyretis.core.system`
        This object is included since information about the units (and
        possibly the box) is needed.
    """
    if filefmt == 'xyz':
        trajwriter = WriteXYZ(filename,
                              system,
                              oldfile=oldfile)
    elif filefmt == 'gro':
        trajwriter = WriteGromacs(filename,
                                  system,
                                  oldfile=oldfile)
    else:
        trajwriter = None
    return trajwriter


def _adjust_coordinate(coord):
    """Method to adjust the dimensionality of coordinates.

    A lot of the different formats expects us to have 3 dimensional data.
    This methods just adds dummy dimensions equal to zero.

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
    Same as for `FileWriter` and in addition:
    convert : dict of floats
        Defines the conversion of positions from internal units to Ångström.
    atomnames : list
        These are the atom names used for the output.
    """

    def __init__(self, filename, system, oldfile='backup'):
        """Initialization of the XYZ writer."""
        super(WriteXYZ, self).__init__(filename, 'xyz', mode='w',
                                       oldfile=oldfile)
        self.atomnames = []
        self.frame = 0  # number of frames written
        self.system = system
        self.convert = {'pos': CONVERT['length'][system.units, 'A']}

    def write_frame(self, pos, names=None, header=None):
        """Write a configuration in xyz-format.

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
            header = 'Trajectory ouput. Frame: {}'.format(self.frame)
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

    def write(self, system=None, header=None):
        """Write a configuration in xyz-format.

        This is a method for writing a configuration in xyz-format. It is
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
        if system is None:
            system = self.system
        return self.write_frame(system.particles.pos,
                                names=system.particles.name, header=header)


class WriteGromacs(FileWriter):
    """WriteGromacs(FileWriter) - A class for GRO files.

    This class handles writing of a system to a file using the gromacs format.
    The gromacs format is described in the gromacs manual [GRO]_.

    Attributes
    ----------
    Same as for FileWriter and in addition the following:
    box : object like `Box` from `pyretis.core.box`
        The simulation box, used for box-lengths.
    convert : dict of floats
        Defines the conversion of positions from internal units to nm
        and nm/ps.

    References
    ----------

    .. [GRO] http://manual.gromacs.org/current/online/gro.html
    """

    def __init__(self, filename, system, oldfile='backup'):
        """Initiate the gromacs writer."""
        super(WriteGromacs, self).__init__(filename, 'gromacs', mode='w',
                                           oldfile=oldfile)
        self.atomnames = []
        self.box = system.box
        self.system = system
        self.frame = 0  # number of frames written
        self.convert = {'pos': CONVERT['length'][system.units, 'nm'],
                        'vel': CONVERT['velocity'][system.units, 'nm/ps']}

    def write_frame(self, pos, vel=None, residuenum=None, residuename=None,
                    atomname=None, atomnum=None, header=None):
        """Write a configuration in gromacs format.

        This will write a specific frame with given positions to the file.
        Velocities can also be written if given.

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
            header = 'Trajectory ouput. Frame: {}'.format(self.frame)

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
        status = self.write_string(_GRO_BOX_FMT.format(*self._box_lengths()))
        self.frame += 1
        return status

    def write(self, system=None, header=None, write_vel=False):
        """Write a configuration in gromacs format.

        This is a method for writing a configuration in gro-format. It is
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
        if system is None:
            system = self.system
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
        """Obtain the box lengths from the box object."""
        missing = 3 - self.box.dim
        if missing > 0:
            boxlength = np.ones(3)
            for i, length in enumerate(self.box.length):
                boxlength[i] = length * self.convert['pos']
            return boxlength
        else:
            return self.box.length * self.convert['pos']
