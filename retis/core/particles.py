# -*- coding: utf-8 -*-
"""This file contain a class to represent a collection of particles."""
import numpy as np
import warnings


__all__ = ['Particles']


class Particles(object):
    """
    Particles(object)

    This is a simple particle list. It stores the positions,
    velocities, forces, masses (and inverse masses) and type information
    for a set of particles.
    In general particle lists are intended to define neighbor lists etc.

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
    imass : np.array
        Inverse masses, 1.0/self.mass.
    name : list of strings
        A name for the particle. This may be used as short text
        describing the particle.
    ptype : list of strings
        A type for the particle. Particles with identical ptype are of the
        same kind.
    dim : int
        This variable is the dimensionality of the particle list. This
        should be derived from the box. For some functions it is convenient
        to be able to access the dimensionality directly from the particle
        list. It is therefore set as an attribute here.
    """
    def __init__(self, dim=1):
        """
        Initialize the Particle list. Here we dictate that the particle list
        is created with zero particles.
        """
        self.npart = 0
        self.pos = None
        self.vel = None
        self.force = None
        self.mass = None
        self.imass = None
        self.name = None
        self.ptype = None
        self.virial = None
        self.dim = dim

    def empty_list(self):
        """
        This is a method to reset the particle list.
        It will delete all particles in the list.
        Note, this is almost __init__ repeated. The reason for __init__ to be
        repeated is simply that we want to define all attributes in __init__
        and not get any surprise attributes elsewhere.
        """
        self.npart = 0
        self.pos = None
        self.vel = None
        self.force = None
        self.mass = None
        self.imass = None
        self.name = None
        self.ptype = None
        self.virial = None

    def get_dim(self):
        """
        Function to get the dimensionality, it simply returns self.dim

        Returns
        -------
        out : int
            The dimensionality
        """
        return self.dim
#    def get_dim(self):
#        """
#        Function to get the dimensionality, based on self.pos, self.vel
#        and self.force
#
#        Returns
#        -------
#        out : int
#            The dimensionality
#        """
#        if self.npart == 0:
#            dims = [0]
#        elif self.npart == 1:
#            dims = [len(i) for i in (self.pos, self.vel, self.force)]
#        else:
#            dims = [len(i) for i in (self.pos[0], self.vel[0], self.force[0])]
#        if len(set(dims)) != 1:
#            msg = 'Inconsistent dimensions in position, velocity and force!'
#            warnings.warn(msg)
#        return dims[0]

    def get_phase_point(self):
        """
        This function returns a copy of the current phase point, that is
        self.pos and self.vel. In addition in returns the accompanying forces.

        Returns
        -------
        out : dict
            Dictionary with the positions, velocity and forces.
        """
        retval = {'pos': np.copy(self.pos),
                  'vel': np.copy(self.vel),
                  'force': np.copy(self.force)}
        return retval

    def set_phase_point(self, phasepoint):
        """
        This function sets the position, velocities (and forces) and
        included here for convenience - it can be used together with
        ``get_phase_point()`` for easy change of the particle state.

        Returns
        -------
        N/A but updates self.pos, self.vel and self.force
        """
        self.pos = np.copy(phasepoint['pos'])
        self.vel = np.copy(phasepoint['vel'])
        try:
            self.force = np.copy(phasepoint['force'])
        except KeyError:
            msg = 'Setting particle pos & vel without setting forces'
            warnings.warn(msg)

    def add_particle(self, pos, vel, force, mass=1.0,
                     name='?', ptype='?'):
        """
        Adds a particle to the system.

        Parameters
        ----------
        pos : numpy.array
            Positions of new particle.
        vel :  numpy.array
            Velocities of new particle.
        force : numpy.array
            Forces on the new particle.
        mass : float, optional.
            The mass of the particle.
        name : string, optional.
            The name of the particle.
        ptype : string, optional.
            The particle type.

        Returns
        -------
        N/A, but increments self.N and updates self.particles.
        """
        if self.npart == 0:
            self.name = [name]
            self.ptype = [ptype]
            self.pos = pos
            self.vel = vel
            self.force = force
            self.mass = np.array([mass])
            self.imass = np.array([1.0/mass])
        else:
            self.name.append(name)
            self.ptype.append(ptype)
            self.pos = np.vstack([self.pos, pos])
            self.vel = np.vstack([self.vel, vel])
            self.force = np.vstack([self.force, force])
            self.mass = np.vstack([self.mass, mass])
            self.imass = np.vstack([self.imass, 1.0/mass])
        self.npart += 1

    def get_selection(self, properties, selection=None):
        """
        This is a helper method to return properties
        for a selection of particles.

        Parameters
        ----------
        properties : list of strings
            The strings represent the properties to return.
        selection : optional, list with indices to return
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
        """
        This is to iterate over the particles.
        This function will yield the properties of the different
        particles.

        Returns
        -------
        yields the information in self.pos, self.vel, ... etc.
        """
        for i, pos in enumerate(self.pos):
            part = {'pos': pos, 'vel': self.vel[i], 'force': self.force[i],
                    'mass': self.mass[i], 'imass': self.imass[i],
                    'name': self.name[i], 'type': self.ptype[i]}
            yield part

    def pairs(self):
        """
        This is a function to iterate over all pairs of particles.
        For more sophisticated particle lists this can be
        a implementation of a smart neighbor list.

        Returns
        -------
        yields the positions and types of the difference pairs.
        """
        for i, itype in enumerate(self.ptype[:-1]):
            for j, jtype in enumerate(self.ptype[i+1:]):
                yield (i, i+1+j, itype, jtype)
