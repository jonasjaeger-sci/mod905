# -*- coding: utf-8 -*-
"""
Methods and objects that handle the output/input of trajectory data.

Objects defined here:

- WriteXYZ: Writing of coordinates to a file in a xyz format.

- WriteGromacs: Writing of a coordinates to a file in a gromacs format.
"""
import numpy as np
from retis.core.units import CONVERT  # unit conversion in trajectory
from retis.inout.txtinout import FileWriter

# define formats for the trajectory output:
_GRO_FMT = '{0:5d}{1:5s}{2:5s}{3:5d}{4:8.3f}{5:8.3f}{6:8.3f}\n'
_GRO_VEL_FMT = _GRO_FMT[:-1] + '{7:8.3f}{8:8.3f}{9:8.3f}\n'
_GRO_BOX_FMT = '{0:12.6f} {1:12.6f} {2:12.6f}\n'
_XYZ_FMT = '{0:5s} {1:8.3f} {2:8.3f} {3:8.3f}\n'


__all__ = ['WriteXYZ', 'WriteGromacs']


def _adjust_coordinate(coord):
    """
    Method to adjust the dimensionality of coordinates.

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
    u"""
    WriteXYZ(FileWriter).

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
        """Initialization of the XYZ writer."""
        self.convert = {'pos': CONVERT['length'][units, 'Å']}
        self.atomnames = []
        self.frame = 0  # number of frames written
        super(WriteXYZ, self).__init__(filename, 'xyz', mode='w',
                                       oldfile=oldfile)

    def write_frame(self, pos, names=None, header=None):
        """
        Write a configuration in xyz-format.

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

    def write(self, system, header=None):
        """
        Write a configuration in xyz-format.

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
        Write the configuration in xyz-format.

        This is a method for writing a configuration in
        xyz-format. This method will just call write and is
        included here for convenience.

        Parameters
        ----------
        system : object of type retis.core.System
            The system object with the positions to write
        header : string, optional
            Header to use for writing the xyz-frame.
        """
        return self.write(system, header=header)


class WriteGromacs(FileWriter):
    """
    WriteGromacs(FileWriter).

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
        """Initiate the gromacs writer."""
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
        Write a configuration in gromacs format.

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

    def write(self, system, header=None, write_vel=False):
        """
        Write a configuration in gromacs format.

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
        Write a gromacs configuration.

        This is a method for writing a configuration in gro-format.
        This method will just call write and is
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
        return self.write(system, header=header, write_vel=write_vel)

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
