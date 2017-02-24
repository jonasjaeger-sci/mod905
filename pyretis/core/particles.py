# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""This file contain a class to represent a collection of particles.

The class for particles is in reality a simplistic particle list which
stores positions, velocities, masses etc. and is used for representing
the particles in the simulations.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Particles (:py:class:`.Particles`)
    Class for a list of particles.

ParticlesExt (:py:class:`.ParticlesExt`)
    Class for an external particle list.
"""
import logging
import numpy as np
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['Particles', 'ParticlesExt']


class Particles(object):
    """Base class for a collection of particles.

    This is a simple particle list. It stores the positions,
    velocities, forces, masses (and inverse masses) and type information
    for a set of particles. In general the particle lists are intended
    to define neighbor lists etc. This class will just define an
    all-pairs list.

    Attributes
    ----------
    npart : integer
        Number of particles.
    pos : numpy.array
        Positions of the particles.
    vel : numpy.array
        Velocities of the particles.
    force : numpy.array
        Forces on the particles.
    mass : numpy.array
        Masses of the particles.
    imass : numpy.array
        Inverse masses, `1.0 / self.mass`.
    name : list of strings
        A name for the particle. This may be used as short text
        describing the particle.
    ptype : numpy.array of integers
        A type for the particle. Particles with identical `ptype` are
        of the same kind.
    dim : int
        This variable is the dimensionality of the particle list. This
        should be derived from the box. For some functions it is
        convenient to be able to access the dimensionality directly
        from the particle list. It is therefore set as an attribute
        here.
    vpot : float
        The potential energy of the particles.
    ekin : float
        The kinetic energy of the particles.
    """

    def __init__(self, dim=1):
        """Initialize the Particle list.

        Here we just create an empty particle list.
        """
        self.npart = 0
        self.pos = None
        self.vel = None
        self.vpot = None
        self.ekin = None
        self.force = None
        self.mass = None
        self.imass = None
        self.name = []
        self.ptype = None
        self.virial = np.zeros((dim, dim))
        self.dim = dim

    def empty_list(self):
        """Reset the particle list.

        This will delete all particles in the list and set other
        variables to `None`.

        Note
        ----
        This is almost `self.__init__` repeated. The reason for this is
        simply that we want to define all attributes in `self.__init__`
        and not get any 'surprise attributes' defined elsewhere.
        Also note that the dimensionality (`self.dim`) is not changed
        in this method.
        """
        self.npart = 0
        self.pos = None
        self.vpot = None
        self.ekin = None
        self.vel = None
        self.force = None
        self.mass = None
        self.imass = None
        self.name = []
        self.ptype = None
        self.virial = np.zeros_like(self.virial)

    def get_particle_state(self):
        """Return a copy of the current phase point.

        The phase point includes `self.pos` and `self.vel`. In addition
        it returns the accompanying forces from `self.force`.

        Returns
        -------
        out : dict
            Dictionary with the positions, velocity and forces.
        """
        return {'pos': np.copy(self.pos), 'vel': np.copy(self.vel),
                'vpot': self.vpot, 'ekin': self.ekin,
                'force': np.copy(self.force)}

    def set_pos(self, pos):
        """Set the positions for the particles.

        This will copy the input positions.

        Parameters
        ----------
        pos : tuple of (string, int)
            The positions to set.
        """
        self.pos = np.copy(pos)

    def get_pos(self):
        """Return (a copy of) positions."""
        return np.copy(self.pos)

    def set_vel(self, vel):
        """Set the velocities for the particles.

        This will copy the input velocities.

        Parameters
        ----------
        vel : tuple of (string, int)
            The velocities to set.
        """
        self.vel = np.copy(vel)

    def get_vel(self):
        """Return (a copy of) the velocities."""
        return np.copy(self.vel)

    def set_force(self, force):
        """Set the forces for the particles.

        This will copy the input forces.

        Parameters
        ----------
        vel : tuple of (string, int)
            The velocities to set.
        """
        self.force = np.copy(force)

    def set_particle_state(self, phasepoint):
        """Set the position, velocities (and forces) for the particles.

        The function is included here for convenience - it can be used
        together with `self.get_particle_state()` for easy change of the
        particle state.

        Parameters
        ----------
        phasepoint : dict
            This dict contains the phase point we wish to set.
            It contains the positions in the key `'pos'` and the
            velocities in the key `'vel'`. It may optionally include
            the forces in the key `'forces'`.

        Returns
        -------
        out : None
            Returns `None` and updates `self.pos`, `self.vel`
            and `self.force` (if given).
        """
        self.set_pos(phasepoint['pos'])
        self.set_vel(phasepoint['vel'])
        self.set_force(phasepoint.get('force', None))
        self.ekin = phasepoint['ekin']
        self.vpot = phasepoint['vpot']

    def add_particle(self, pos, vel, force, mass=1.0,
                     name='?', ptype=0):
        """Add a particle to the system.

        Parameters
        ----------
        pos : numpy.array
            Positions of new particle.
        vel :  numpy.array
            Velocities of new particle.
        force : numpy.array
            Forces on the new particle.
        mass : float, optional
            The mass of the particle.
        name : string, optional
            The name of the particle.
        ptype : integer, optional
            The particle type.

        Returns
        -------
        out : None
            This method does not return anything, but increments
            `self.npart` and updates `self.particles`.
        """
        if self.npart == 0:
            self.name = [name]
            self.ptype = np.array(ptype, dtype=np.int16)
            self.pos = np.zeros((1, self.dim))
            self.pos[0] = pos
            self.vel = np.zeros((1, self.dim))
            self.vel[0] = vel
            self.force = np.zeros((1, self.dim))
            self.force[0] = force
            self.mass = np.zeros((1, 1))  # column matrix
            self.mass[0] = mass
            self.imass = 1.0 / self.mass
        else:
            self.name.append(name)
            self.ptype = np.append(self.ptype, ptype)
            self.pos = np.vstack([self.pos, pos])
            self.vel = np.vstack([self.vel, vel])
            self.force = np.vstack([self.force, force])
            self.mass = np.vstack([self.mass, mass])
            self.imass = np.vstack([self.imass, 1.0/mass])
        self.npart += 1

    def get_selection(self, properties, selection=None):
        """Return selected properties for a selection of particles.

        Parameters
        ----------
        properties : list of strings
            The strings represent the properties to return.
        selection : optional, list with indexes to return
            If selection is not given, data for all particles
            are returned.

        Returns
        -------
        A list with the properties in the order they were asked for
        in the properties argument.
        """
        # if selection is None:
        #    selection = range(self.npart)
        sel_prop = []
        for prop in properties:
            if hasattr(self, prop):
                var = getattr(self, prop)
                if isinstance(var, list):
                    if selection is None:
                        sel_prop.append(var)
                    else:
                        sel_prop.append([var[i] for i in selection])
                else:
                    if selection is None:
                        sel_prop.append(var)
                    else:
                        sel_prop.append(var[selection])
        return sel_prop

    def __iter__(self):
        """Iterate over the particles.

        This function will yield the properties of the different
        particles.

        Returns
        -------
        yields the information in `self.pos`, `self.vel`, ... etc.
        """
        for i, pos in enumerate(self.pos):
            part = {'pos': pos, 'vel': self.vel[i], 'force': self.force[i],
                    'mass': self.mass[i], 'imass': self.imass[i],
                    'name': self.name[i], 'type': self.ptype[i]}
            yield part

    def pairs(self):
        """Iterate over all pairs of particles.

        For more sophisticated particle lists this can/should be an
        implementation of a 'smart' neighbor list.

        Returns
        -------
        yields the positions and types of the difference pairs.
        """
        for i, itype in enumerate(self.ptype[:-1]):
            for j, jtype in enumerate(self.ptype[i+1:]):
                yield (i, i+1+j, itype, jtype)

    def __str__(self):
        """Print out basic info about the particle list."""
        msg = ['Particles: {}'.format(self.npart)]
        msg += ['Types: {}'.format(np.unique(self.ptype))]
        msg += ['Names: {}'.format(set(self.name))]
        return '\n'.join(msg)


class ParticlesExt(Particles):
    """Particles, when positions and velocities are stored in files.

    This represents a particle list for the case where the positions
    and velocities might be stored in files.

    Attributes
    ----------
    config : tuple of (string, int)
        The location of the file with positions and the index
        for locating a frame.
    vel_rev : boolean
        True if velocities should be reversed or not before using
        the phase point.
    """

    def __init__(self, dim=1):
        """Initialize the Particle list.

        Here we just create an empty particle list.
        """
        super().__init__(dim=dim)
        self.config = (None, None)
        self.vel_rev = None

    def set_pos(self, pos):
        """Set the positions for the particles.

        This will copy the input positions.

        Parameters
        ----------
        pos : tuple of (string, int)
            The positions to set.
        """
        self.config = (pos[0], pos[1])

    def get_pos(self):
        """Just return the positions of the particles."""
        return self.config

    def set_vel(self, vel):
        """Set the velocities for the particles.

        This will copy the input velocities.

        Parameters
        ----------
        vel : tuple of (string, int)
            The velocities to set.
        """
        self.vel_rev = vel

    def get_particle_state(self):
        """Return a copy of the current phase point.

        The phase point includes `self.pos` and `self.vel`. In addition
        it returns the accompanying forces from `self.force`.

        Returns
        -------
        out : dict
            Dictionary with the positions, velocity and forces.
        """
        return {'pos': self.config, 'vel': self.vel_rev, 'vpot': self.vpot,
                'ekin': self.ekin}

    def set_particle_state(self, phasepoint):
        """Update the state of particles to the given phase point.

        The function is included here for convenience - it can be used
        together with `self.get_particle_state()` for easy change of the
        particle state.

        Parameters
        ----------
        phasepoint : dict
            This dict contains the phase point we wish to set.
            It contains the positions in the key `'pos'` and the
            velocities in the key `'vel'`.

        Returns
        -------
        out : None
            Returns `None` and updates `self.pos`, `self.vel`
        """
        self.set_pos(phasepoint['pos'])
        self.set_vel(phasepoint['vel'])
        self.ekin = phasepoint['ekin']
        self.vpot = phasepoint['vpot']


def get_particle_type(engine_type):
    """Method to return the path ensemble class to work with an engine.

    Parameters
    ----------
    engine_type : string
        The type of particles we are requesting.
    """
    particle_map = {'internal': Particles,
                    'external': ParticlesExt}
    try:
        return particle_map[engine_type]
    except KeyError:
        msg = 'Unknown particle type "{}" requested.'.format(engine_type)
        logger.critical(msg)
        raise ValueError(msg)
