# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""This module handles the set-up of initial positions and a box.

The initial positions can either be generated on a lattice, or it can
be read from a file.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

create_box
    Create a simulation box from simulation settings.

create_initial_positions
    Get initial positions based on settings. This will either be
    read from a file or generated on a lattice.

create_system
    Set up a system from given settings. This method will probably
    also need to set/get the initial positions and velocities for
    the particles and set up the simulation box.

create_velocities
    Create velocities from settings for a system with particles.

initial_positions_file
    Get initial positions from a file.

initial_positions_lattice
    Get initial positions by generating a lattice.
"""
import logging
import os
import numpy as np
# pyretis imports:
from pyretis.tools import generate_lattice
from pyretis.core.box import Box
from pyretis.core.system import System
from pyretis.core.particles import Particles
from pyretis.core.units import CONVERT
from pyretis.inout.writers.traj import read_xyz_file, read_gromacs_file
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['create_initial_positions', 'create_system', 'create_velocities',
           'create_box', 'initial_positions_file', 'initial_positions_lattice']


PERIODIC_TABLE = {'H': 1.007975, 'He': 4.002602, 'Li': 6.9675,
                  'Be': 9.0121831, 'B': 10.8135, 'C': 12.0106,
                  'N': 14.006855, 'O': 15.9994, 'F': 18.998403163,
                  'Ne': 20.1797, 'Na': 22.98976928, 'Mg': 24.3055,
                  'Al': 26.9815385, 'Si': 28.085, 'P': 30.973761998,
                  'S': 32.0675, 'Cl': 35.4515, 'Ar': 39.948,
                  'K': 39.0983, 'Ca': 40.078, 'Sc': 44.955908,
                  'Ti': 47.867, 'V': 50.9415, 'Cr': 51.9961,
                  'Mn': 54.938044, 'Fe': 55.845, 'Co': 58.933194,
                  'Ni': 58.6934, 'Cu': 63.546, 'Zn': 65.38,
                  'Ga': 69.723, 'Ge': 72.63, 'As': 74.921595,
                  'Se': 78.971, 'Br': 79.904, 'Kr': 83.798,
                  'Rb': 85.4678, 'Sr': 87.62, 'Y': 88.90584,
                  'Zr': 91.224, 'Nb': 92.90637, 'Mo': 95.95,
                  'Ru': 101.07, 'Rh': 102.9055, 'Pd': 106.42,
                  'Ag': 107.8682, 'Cd': 112.414, 'In': 114.818,
                  'Sn': 118.71, 'Sb': 121.76, 'Te': 127.6,
                  'I': 126.90447, 'Xe': 131.293, 'Cs': 132.90545196,
                  'Ba': 137.327, 'La': 138.90547, 'Ce': 140.116,
                  'Pr': 140.90766, 'Nd': 144.242, 'Sm': 150.36,
                  'Eu': 151.964, 'Gd': 157.25, 'Tb': 158.92535,
                  'Dy': 162.5, 'Ho': 164.93033, 'Er': 167.259,
                  'Tm': 168.93422, 'Yb': 173.045, 'Lu': 174.9668,
                  'Hf': 178.49, 'Ta': 180.94788, 'W': 183.84,
                  'Re': 186.207, 'Os': 190.23, 'Ir': 192.217,
                  'Pt': 195.084, 'Au': 196.966569, 'Hg': 200.592,
                  'Tl': 204.3835, 'Pb': 207.2, 'Bi': 208.9804,
                  'Th': 232.0377, 'Pa': 231.03588, 'U': 238.02891}


# Variable that defines some information for reading input files:
# TODO: Move this to the place where the file readers are defined?
READFILE = {'xyz': {'reader': read_xyz_file,
                    'units': {'length': 'A', 'velocity': 'A/fs'}},
            'gro': {'reader': read_gromacs_file,
                    'units': {'length': 'nm', 'velocity': 'nm/ps'}}}


def list_get(input_list, index):
    """Method to get an item from a list that handles out-of bounds errors.

    This method is intended to be used when we are picking items from
    a list and possibly we want a number of items which is larger than
    the number of items in the list. Here, we then just return the last
    element.

    Parameters
    ----------
    input_list : list
        The list to pick from
    index : integer
        The index to pick
    """
    try:
        return input_list[index]
    except IndexError:
        return input_list[-1]


def _guess_particle_mass(particle_no, particle_type, unit):
    """Method that will try to guess a particle mass from it's type.

    Parameters
    ----------
    particle_no : integer
        Just used to identify the particle number
    particle_type : string
        Used to identify the particle
    unit : string
        The system of units. This is used in case we try to get the
        mass from the periodic table where the units are in `g/mol`.
    """
    msg = ['Mass not specified for particle no. {}!'.format(particle_no)]
    msg += ['Will guess from particle type: {}'.format(particle_type)]
    mass = PERIODIC_TABLE.get(particle_type, None)
    if mass is None:
        particle_mass = 1.0
        msg += ['->\nCould not find mass. Assuming' +
                ' {} (internal units)'.format(particle_mass)]
    else:
        msg += ['->\nUsing mass of: {} g/mol'.format(mass)]
        particle_mass = CONVERT['mass']['g/mol', unit] * mass
        msg += ['({} in internal units)'.format(particle_mass)]
    msgtxt = ' '.join(msg)
    logger.warning(msgtxt)
    return particle_mass


def initial_positions_lattice(settings):
    """Method to generate initial positions based on given settings.

    We assume here the input values are given with the correct units
    as dictated by `settings['system']['units']`.

    Parameters
    ----------
    settings : dict
        The input settings for the simulation

    Returns
    -------
    particles : object like `Particles` from `pyretis.core.particles`
        The particles we created.
    size : list of floats
        A size for the region we created. This can be used to create
        a box.
    """
    pos_settings = settings['particles']['position']
    ptype = settings['particles'].get('type', [0])
    pname = settings['particles'].get('name', ['Ar'])
    pmass = settings['particles'].get('mass', {})

    lattice_type = pos_settings['generate'].lower()
    lattice, size = generate_lattice(lattice_type, pos_settings['repeat'],
                                     lcon=pos_settings.get('lcon', None),
                                     density=pos_settings.get('density', None))
    ndim = settings['system'].get('dimensions', None)
    if ndim is None:
        ndim = len(size)
    else:
        if ndim != len(size):
            msg = ['Inconsistent dimensions: settings gives {}D'.format(ndim),
                   'Generated lattice is {}D!'.format(len(size))]
            msgtxt = '\n'.join(msg)
            logger.error(msgtxt)
            raise ValueError(msgtxt)
    particles = Particles(dim=ndim)
    for i, pos in enumerate(lattice):
        particle_type = list_get(ptype, i)
        particle_name = list_get(pname, i)
        # infer mass from the input masses, or try to get it
        # from the periodic table
        try:
            particle_mass = pmass[particle_name]
        except KeyError:
            particle_mass = _guess_particle_mass(i + 1, particle_name,
                                                 settings['system']['units'])
        particles.add_particle(pos, np.zeros_like(pos), np.zeros_like(pos),
                               mass=particle_mass, name=particle_name,
                               ptype=particle_type)
    msg = ['Initiated {} particles on lattice "{}".'.format(particles.npart,
                                                            lattice_type)]
    msg += ['Lattice is {}D.'.format(ndim)]
    msgtxt = '\n'.join(msg)
    logger.info(msgtxt)
    return particles, size


def _get_snapshot_from_file(pos_settings, units):
    """Get a configuration snapshot from a file.

    This snapshot will be used to set up the initial configuration.

    Parameters
    ----------
    pos_settings : dict
        A dict with information on what we should read.
    units : string
        The internal units.

    Returns
    -------
    snapshot : dict
        The snapshot we found in the file. It will at least have the
        keys with the positions ('x', 'y', 'z') and atom name
        'atomnames'. It may have information about velocities
        ('vx', 'vy', 'vz') and the box ('box').
    convert : dict
        Dictionary with conversion factors to internal units.
    """
    filename = pos_settings.get('file', None)
    if filename is None:
        msg = 'No input file given!'
        raise ValueError(msg)

    fmt = pos_settings.get('format', os.path.splitext(filename)[1][1:])
    snaps = []
    convert = None
    if fmt not in READFILE:
        msg = 'Unknown format {} for input file: {}'
        msgtxt = msg.format(fmt, pos_settings)
        logger.error(msgtxt)
        raise ValueError(msgtxt)

    reader = READFILE[fmt]['reader']
    read_units = READFILE[fmt]['units']
    convert = {'length': CONVERT['length'][read_units['length'], units],
               'velocity': CONVERT['velocity'][read_units['velocity'], units]}
    msg = 'Reading "{}" input file.'.format(fmt)
    logger.info(msg)
    snaps = [snap for snap in reader(filename)]

    snapshot = None
    if len(snaps) == 0:
        msg = 'Could not find any configurations in input file: {}'
        raise ValueError(msg.format(filename))
    elif len(snaps) == 1:
        snapshot = snaps[0]
    else:
        msg = ('Found several frames ({}) in input file.'
               ' Will use the last one!')
        msg = msg.format(len(snaps))
        logger.warning(msg)
        snapshot = snaps[-1]
    return snapshot, convert


def initial_positions_file(settings):
    """Method to get initial positions from an input file.

    Parameters
    ----------
    settings : dict
        The input settings for the simulation

    Returns
    -------
    particles : object like `Particles` from `pyretis.core.particles`
        The particles we created.
    size : list of floats
        A size for the region we created. This can be used to create
        a box.
    vel_read : boolean
        True if we read velocities from the input file.
    """
    ndim = settings['system'].get('dimensions', 3)
    pos_settings = settings['particles']['position']
    ptype = settings['particles'].get('type', None)
    pname = settings['particles'].get('name', None)
    pmass = settings['particles'].get('mass', {})
    ptypes = {}  # To automatically set particle types based on name.
    snapshot, convert = _get_snapshot_from_file(pos_settings,
                                                settings['system']['units'])
    vel_read = False
    particles = Particles(dim=ndim)
    for i, atomname in enumerate(snapshot['atomname']):
        pos = []
        vel = []
        for key in ['x', 'y', 'z'][:ndim]:
            pos.append(snapshot[key][i])
            vel_key = 'v{}'.format(key)
            if vel_key in snapshot:
                vel.append(snapshot[vel_key][i])
        pos = np.array(pos) * convert['length']
        if len(vel) != ndim:
            vel = np.zeros_like(pos)
        else:
            vel = np.array(vel) * convert['velocity']
            vel_read = True
        # Get particle type from the atom names or from input list:
        if ptype is None:
            if atomname not in ptypes:
                ptypes[atomname] = len(ptypes)
            particle_type = ptypes[atomname]
        else:
            particle_type = list_get(ptype, i)
        if pname is None:
            particle_name = atomname
        else:
            particle_name = list_get(pname, i)
        # Infer mass from the input masses, or try to get it
        # from the periodic table:
        try:
            particle_mass = pmass[particle_name]
        except KeyError:
            particle_mass = _guess_particle_mass(i + 1, particle_name,
                                                 settings['system']['units'])
        particles.add_particle(pos,
                               vel, np.zeros_like(pos),
                               mass=particle_mass, name=particle_name,
                               ptype=particle_type)
    try:
        size = [lng * convert['length'] for lng in snapshot['box'][:ndim]]
    except KeyError:
        size = None
    if vel_read:
        msg = 'Used velocities found in {}.'.format(pos_settings['file'])
        logger.info(msg)
    return particles, size, vel_read


def create_initial_positions(settings):
    """Set up the initial positions from the given settings.

    The settings can specify the initial positions as a file or
    to be generated on a lattice by pyretis.

    Parameters
    ----------
    settings : dict
        Settings for creating the initial positions.

    Returns
    -------
    out[0] : object like `Particles` from `pyretis.core.particles`.
        The particles we created
    out[1] : list
        The size associated with the particles. Can be used to create a
        box.
    out[2] : boolean
        True if we have read/created velocities different from just
        zeros. This is only True if we have read from a file with
        velocities.
    """
    msg = 'Settings used for initial positions: {}'
    debugtxt = msg.format(settings['particles']['position'])
    logger.debug(debugtxt)
    particles = None
    if 'generate' in settings['particles']['position']:
        particles, size = initial_positions_lattice(settings)
        return particles, size, False
    elif 'file' in settings['particles']['position']:
        # First check if we need to add a path to the file:
        filename = settings['particles']['position']['file']
        if not os.path.isfile(filename) and 'exe-path' in settings:
            filename = os.path.join(settings['exe-path'], filename)
            settings['particles']['position']['file'] = filename
        particles, size, vel = initial_positions_file(settings)
        return particles, size, vel
    else:
        msg = 'Unknown settings for initial positions: {}'
        msgtxt = msg.format(settings['particles']['position'])
        logger.error(msgtxt)
        raise ValueError(msgtxt)


def create_box(settings, size, dim=3):
    """Method that will try to set up a box from settings.

    Parameters
    ----------
    settings : dict
        The dict with the simulation settings
    size : list of floats
        If no box settings are given, we can still create a box,
        inferred from the positions of the particles.
    dim : integer
        Number of dimensions for the box. This is used only as a last
        resort when no information about the box is given.

    Returns
    -------
    box : object like `Box` from `pyretis.core.box` or None
        The box if we managed to create it. Otherwise None.
    """
    msg = 'Box created {}:\n{}'
    if settings.get('box', None) is not None:
        box = Box(**settings['box'])
        msgtxt = msg.format('from settings', box)
        logger.info(msgtxt)
        debugtxt = 'Settings used:\n{}'.format(settings['box'])
        logger.debug(debugtxt)
    else:
        if size is not None:
            box = Box(size=size)
            msgtxt = msg.format('from initial positions', box)
            logger.info(msgtxt)
            msgwarn = 'The box was assumed periodic in all directions.'
            logger.warning(msgwarn)
        else:
            box = Box(periodic=[False]*dim)
            msgtxt = msg.format('without specifications', box)
            logger.info(msgtxt)
            msgwarn = 'The box was assumed *nonperiodic* in all directions.'
            logger.warning(msgwarn)
    return box


def create_velocities(system, settings, vel):
    """Create velocities from settings for a system.

    Parameters
    ----------
    system : object like `pyretis.core.system.System`.
        The system to create velocities for. It's needed since
        we need to know the degrees of freedom.
    settings : dict
        Settings to use for creating the velocities.
    vel : boolean
        If True, we already read velocities. They will now be
        overwritten. We just make some warnings about this.

    Returns
    -------
    out : boolean
        True if we actually generated velocities.
    """
    vel_settings = settings['particles'].get('velocity', {})
    if vel:
        msg = 'Velocities read from file (temperature: {}).'
        msg = msg.format(system.calculate_temperature())
        logger.info(msg)
    if 'generate' in vel_settings:
        if vel:
            msg = 'Will overwrite velocities already set.'
            logger.warning(msg)
        gen_settings = {'distribution': vel_settings['generate']}
        for key in ('seed', 'momentum', 'temperature'):
            try:
                gen_settings[key] = vel_settings[key]
            except KeyError:
                pass
        system.generate_velocities(**gen_settings)
        msg = 'Generated velocities with average temperature: {}'
        msg = msg.format(system.calculate_temperature())
        logger.info(msg)
        msg = 'Settings used for generating velocities: \n{}'
        msg = msg.format(gen_settings)
        logger.debug(msg)
        return True
    elif 'scale' in vel_settings:
        target = vel_settings['scale']
        # just set the velocities to some temperature for now
        # the scaling is done later by calling system.extra_setup()
        gen_settings = {'distribution': 'maxwell',
                        'momentum': system.particles.npart != 1,
                        'temperature': settings['temperature']}
        system.generate_velocities(**gen_settings)
        msg = 'Scaling velocities to total energy {}'.format(target)
        logger.debug(msg)
        system.post_setup.append(('rescale_velocities', (target,)))
        return True
    else:
        return False


def create_system(settings):
    """Method that will set up a system from settings.

    In order to set up the system, there are several things we might
    need to do:

    1. Set the initial positions.

    2. Create/set-up the simulation box.

    3. Set initial velocities.

    Parameters
    ----------
    settings : dict
        The dict with the simulation settings

    Returns
    -------
    system : object like `system` from `pyretis.core.system`
        The system object we create here.
    """
    particles, size, vel = create_initial_positions(settings)
    box = create_box(settings, size, dim=particles.dim)
    system = System(temperature=settings['system']['temperature'],
                    units=settings['system']['units'], box=box)
    system.particles = particles
    # figure out what to do with velocities:
    vel_gen = create_velocities(system, settings, vel)
    if not (vel_gen or vel):
        msg = 'Velocities were not created or read. Just set to zero!'
        logger.warning(msg)
    return system
