# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Method to re-calculate order parameters for external trajectories.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

recalculate_order (:py:func:`.recalculate_order`)
    Generic method for recalculating order parameters.

recalculate_from_trr (:py:func:`.recalculate_from_trr`)
    Recalculate order parameters using a GROMACS .trr file.

recalculate_from_xyz (:py:func:`.recalculate_from_xyz`)
    Recalculate order parameters using a .xyz file.

recalculate_from_gro (:py:func:`.recalculate_from_gro`)
    Recalculate order parameters using a .gro or .g96 file.
"""
import collections
import logging
import os
import numpy as np
from pyretis.core import System, ParticlesExt
from pyretis.core.box import box_matrix_to_list
from pyretis.inout.common import print_to_screen
from pyretis.inout.writers.gromacsio import (
    read_trr_file,
    read_gromos96_file,
    read_gromacs_gro_file
)
from pyretis.inout.writers.xyzio import read_xyz_file, convert_snapshot
from pyretis.inout.writers import prepare_load
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = [
    'recalculate_from_trr',
    'recalculate_from_xyz',
    'recalculate_from_gro',
    'recalculate_order',
]


def recalculate_from_trr(order_parameter, trr_file, reverse=False,
                         maxidx=None, minidx=None):
    """Re-calculate order parameters from a .trr file.

    Parameters
    ----------
    order_parameter : object like :py:class:`.OrderParameter`
        The order parameter to use.
    trr_file : string
        Path to the trr_file we should read.
    reverse : boolean
        If True, we reverse the velocities.
    maxidx : integer, optional
        This is the maximum frame we will read. Can be used in case
        the .trr file contains extra frames not needed by us.
    minidx : integer, optional
        This is the first frame we will read. Can be used in case we
        want to skip some frames from the .trr file.

    Yields
    ------
    out : list of lists of floats
        The order parameters, calculated per frame.
    """
    system = System(box=None)  # add dummy system
    msg = ('Re-calculate from {}:'.format(os.path.basename(trr_file)) +
           ' Step {}, time {}')
    for i, (header, data) in enumerate(read_trr_file(trr_file)):
        if maxidx is not None and i > maxidx:
            break
        if minidx is not None and i < minidx:
            continue
        print_to_screen(msg.format(header['step'], header['time']))
        if system.particles is None:
            system.particles = ParticlesExt(dim=data['x'].shape[1])
        system.particles.pos = data['x']
        if 'v' in data:
            if reverse:
                system.particles.vel = -1.0 * data['v']
            else:
                system.particles.vel = data['v']
        else:
            logger.warning('No velocities found in .trr file! Set to zero.')
            system.particles.vel = np.zeros_like(data['x'])
        length = box_matrix_to_list(data['box'])
        system.update_box(length)
        order = order_parameter.calculate_all(system)
        yield order


def recalculate_from_xyz(order_parameter, traj_file, reverse=False,
                         maxidx=None, minidx=None):
    """Re-calculate order parameters from a .xyz file.

    Parameters
    ----------
    order_parameter : object like :py:class:`.OrderParameter`
        The order parameter to use.
    traj_file : string
        Path to the trajectory file we should read.
    reverse : boolean
        If True, we reverse the velocities.
    maxidx : integer, optional
        This is the maximum frame we will read. Can be used in case
        the file contains extra frames not needed by us.
    minidx : integer, optional
        This is the first frame we will read. Can be used in case we
        want to skip some frames from the file.

    Yields
    ------
    out : list of lists of floats
        The order parameters as a list.
    """
    system = System(box=None)
    msg = ('Re-calculate from {}:'.format(os.path.basename(traj_file)) +
           ' Step {}')
    for i, snapshot in enumerate(read_xyz_file(traj_file)):
        if maxidx is not None and i > maxidx:
            break
        if minidx is not None and i < minidx:
            continue
        print_to_screen(msg.format(i))
        box, xyz, vel, _ = convert_snapshot(snapshot)
        if reverse:
            vel *= -1
        if system.particles is None:
            system.particles = ParticlesExt(dim=xyz.shape[1])
        system.particles.config = (traj_file, i)
        system.particles.pos = xyz
        system.particles.vel = vel
        system.update_box(box)
        order = order_parameter.calculate_all(system)
        yield order


def recalculate_from_gro(order_parameter, traj_file, ext, reverse=False):
    """Re-calculate order parameters from a .g96/.gro file.

    Here we assume that there is *ONE* frame in the ``traj_file``.

    Parameters
    ----------
    order_parameter : object like :py:class:`.OrderParameter`
        The order parameter to use.
    traj_file : string
        Path to the trajectory file we should read.
    ext : string
        File extension for the ``traj_file``.
    reverse : boolean
        If True, we reverse the velocities.

    Returns
    -------
    out : list of lists of floats
        The order parameters for the current frame.
    """
    system = System(box=None)
    msg = 'Re-calculate from {}:'.format(os.path.basename(traj_file))
    print_to_screen(msg)
    if ext == '.g96':
        _, xyz, vel, box = read_gromos96_file(traj_file)
    elif ext == '.gro':
        _, xyz, vel, box = read_gromacs_gro_file(traj_file)
    else:
        raise ValueError('Unknown format {}'.format(ext))
    if reverse:
        vel *= -1
    if system.particles is None:
        system.particles = ParticlesExt(dim=xyz.shape[1])
    system.particles.config = (traj_file, 0)
    system.particles.pos = xyz
    system.particles.vel = vel
    system.update_box(box)
    return [order_parameter.calculate_all(system)]


def recalculate_order(order_parameter, traj_file, reverse=False,
                      maxidx=None, minidx=None):
    """Re-calculate order parameters.

    Parameters
    ----------
    order_parameter : object like :py:class:`.OrderParameter`
        The order parameter to use.
    traj_file : string
        Path to the trajectory file to recalculate for.
    reverse : boolean
        If True, we assume that we are reading a time-reversed
        trajectory.
    maxidx : integer, optional
        The maximum frame number we will read from ``traj_file``.
    minidx : integer, optional
        The minimum frame number we will read from ``traj_file``
    """

    _, ext = os.path.splitext(traj_file)

    helpers = {'.trr': recalculate_from_trr, '.xyz': recalculate_from_xyz,
               '.g96': recalculate_from_gro, '.gro': recalculate_from_gro}

    if ext in ('.g96', '.gro'):
        all_order = helpers[ext](order_parameter, traj_file, ext,
                                 reverse=reverse)
    else:
        all_order = helpers[ext](order_parameter, traj_file, reverse=reverse,
                                 maxidx=maxidx, minidx=minidx)
    if reverse:
        return reversed(list(all_order))
    return all_order


def get_traj_files(traj_file_name):
    """Read a traj.txt file and get trajectory information."""
    trajfile = prepare_load('pathtrajext', traj_file_name, required=True)
    # Just get the first trajectory:
    traj = next(trajfile)
    files = collections.OrderedDict()
    for snapshot in traj['data']:
        filename = snapshot[1]
        reverse = int(snapshot[-1]) == -1
        if filename not in files:
            files[filename] = {'minidx': None, 'maxidx': None,
                               'reverse': reverse}
        idx = int(snapshot[2])
        minidx = files[filename]['minidx']
        if minidx is None or idx < minidx:
            files[filename]['minidx'] = idx
        maxidx = files[filename]['maxidx']
        if maxidx is None or idx > maxidx:
            files[filename]['maxidx'] = idx
    return files
