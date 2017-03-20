# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Module for handling the output/input of trajectory data.

This module defines some classes for writing out and reading snapshots
and trajectories in a XYZ-like format. By XYZ-like we here mean
that we also include velocities as part of the file.

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
from pyretis.inout.writers.writers import (adjust_coordinate,
                                           read_txt_snapshots)
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


# define formats for the trajectory output:
_XYZ_FMT = '{0:5s} {1:8.3f} {2:8.3f} {3:8.3f}'
_XYZ_BIG_FMT = '{:5s}' + 3*' {:15.9f}'
_XYZ_BIG_VEL_FMT = _XYZ_BIG_FMT + 3*' {:15.9f}'


__all__ = ['read_xyz_file', 'format_xyz_data']


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
    The positions will **NOT** be converted to a specified set of units.
    """
    xyz_keys = ('atomname', 'x', 'y', 'z', 'vx', 'vy', 'vz')
    for snapshot in read_txt_snapshots(filename, data_keys=xyz_keys):
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
        yield 'PyRETIS XYZ writer'
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
