# -*- coding: utf-8 -*-
"""
This file contain a class to represent a collection of
particles.
"""
import numpy as np

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
    """
    def __init__(self):
        """
        Initialize the Particle list. Here we dictate the the particle list
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

    def empty_list(self):
        """
        This is a method to reset the particle list.
        It will delete all particles in the list.
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

    def add_particle(self, pos, vel, force, mass=1.0,
                     name='?', ptype='?'):
        """
        Adds a particle to the system.

        Parameters
        ----------
        pos : numpy.array, positions of new particle
        vel :  numpy.array, velocities of new particle
        force : numpy.array, forces of new particle.
        mass : float, optional. The mass of the particle
        name : string, optional. The name of the particle.
        ptype : string, optional. The particle type.

        Returns
        -------
        N/A, but increments self.N and updates
        self.particles

        """
        if self.npart == 0:
            self.name = [name]
            self.ptype = [ptype]
            self.pos = pos
            self.vel = vel
            self.force = force
            self.mass = np.array(mass)
            self.imass = np.array(1.0/mass)
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
        properties : list with strings of properties to return
        selection : optional, list with indices to return
            if selection is not given, data for all particles
            are returned.

        Returns
        -------
        A list with the properties in the order they were asked for
        in the properties argument.
        """
        #if selection is None:
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
        a implementation of a smart neighborlist.

        Returns
        -------
        yields the positions and types of the difference pairs.
        """
        for i, posi in enumerate(self.pos[:-1]):
            for j, posj in enumerate(self.pos[i+1:]):
                yield (i, posi, self.ptype[i], i+1+j, posj, self.ptype[j])
