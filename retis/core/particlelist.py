# -*- coding: utf-8 -*-
"""
This file contain a class to represent a collection of
particles.
"""
import numpy as np

__all__ = ["Particles"]

class Particles(object):
    """
    Particles(object)

    This is a simple particle list. It stores the positions,
    velocities, forces, masses (and inverse masses) and type information
    for a set of particles.
    In general particle lists are intended to define neighbor lists etc.

    Attributes
    ----------
    npart : integer, number of particles
    pos : np.array, positions of the particles
    vel : np.array, velocities of the particles
    force : np.array, forces on the particles
    mass : np.array, masses of the particles
    imass : np.array, inverse masses
    name : list of strings, a name for the particle. Name is intented as
        a short text describing the particle.
    ptype : list of strings, a type for the particle. Particles with identical
        ptype are of the same kind. 

    Parameters
    ----------

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
        self.ptype =  None
        self.index = 0

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

    def kinetic_energy(self):
        """
        This method returns the kinetic energy of the particles in the list.
        
        Returns
        -------
        A numpy array with the same number of dimensions as self.vel.  
        It contains the kinetic energy of the particles.

        Note
        ----
        Consider if this calculation should be moved elsewere.
        It could for instance bee a property that's supposed to
        be calculated. 
        """
        kinetic = 0.5*np.sum(self.vel*self.vel*self.mass, axis=0)
        return kinetic

    def get_kinetic_temperature(self):
        """
        This method returns the kinetic temperature of the 
        particles in the list by making use of self.kinetic_energy()

        Returns
        -------
        temperature : numpy.array with same size as the kinetic energy, it
            contains the temperature in each spatial dimension.
        average_temperature : the temperature averaged over all dimensions.
        
        Note
        ----
        Consider if this calculation should be moved elsewere.
        It could for instance bee a property that's supposed to
        be calculated. 
        """
        temperature = 2.0*self.kinetic_energy()/float(self.npart)
        average_temperature = np.average(temperature)
        return temperature, average_temperature

    def reset_momentum(self):
        """
        This method sets the linear momentum of the particles to zero

        Returns
        -------
        N/A, but modifies self.vel
        """
        mom = np.sum(self.vel*self.mass, axis=0)
        self.vel -= mom/self.mass.sum()

    def pairs(self):
        """
        This is a function to iterate over all pairs of particles.
        For more sophisticated particle lists this is where the 
        speed up can be harvested. The current list will iterate
        over all paris.
     
        
        Returns
        -------
        yields the positions and types of the difference pairs.
        """
        for i, posi in enumerate(self.pos[:-1]):
            for j, posj in enumerate(self.pos[i+1:]):
                yield (i, i+1+j, self.ptype[i], self.ptype[j])



