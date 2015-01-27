# -*- coding: utf-8 -*-
"""
This file contains methods that act on a (selection) of particles.
"""
import numpy as np

__all__ = ["kinetic_energy", "kinetic_temperature", "reset_momentum"]

def calculate_linear_momentum(particles, selection=None):
    """
    This function calculate the linear momentum for a collection
    of particles
    Parameters
    ----------
    particles : object with a list of particles
    selection : optional, list with indices of particles to use
    
    Returns
    -------
    numpy.array with the momentum in each dimension
    """
    if selection is None:
        vel, mass = particles.vel, particles.mass
    else:
        vel, mass = particles.vel[selection], particles.mass[selection]
    return np.sum(vel*mass, axis=0)

def kinetic_energy(particles, selection=None):
    """
    This function returns the kinetic energy of a collection of 
    particles.
    
    Parameters
    ----------
    particles : object with a list of particles
    selection : optional, list with indices of particles to use

    Returns
    -------
    A numpy array with the same number of dimensions as self.vel.  
    It contains the kinetic energy of the particles in the different
    dimensions

    """
    if selection is None:
        vel, mass = particles.vel, particles.mass
    else:
        vel, mass = particles.vel[selection], particles.mass[selection]
    kinetic = 0.5*np.sum(vel*vel*mass, axis=0)
    return kinetic

def kinetic_temperature(particles, selection=None, 
                        dof=None, kinetic=None):
    """
    This method returns the kinetic temperature of a
    collection of particles.

    Parameters
    ----------
    particles : object with a list of particles
    selection : optional, list with indices of particles to use
    dof : optional, numpy.array containing the degrees of freedom
        to subtract in each dimension.
    kinetic : optional, the kinetic energy. It the kinetic energy
        is not given, it is recalculated here.


    Returns
    -------
    temperature : numpy.array with same size as the kinetic energy, it
        contains the temperature in each spatial dimension.
    average_temperature : the temperature averaged over all dimensions.
    
    """
    if selection is None:
        vel, mass = particles.vel, particles.mass
    else:
        vel, mass = particles.vel[selection], particles.mass[selection]
    npart = len(mass)
    if kinetic is None:
        kinetic = 0.5*np.sum(vel*vel*mass, axis=0)
    if dof is None:
        temperature = 2.0*kinetic/float(npart)
    else:
        if type(dof) == type([]):
            dof = np.array(dof)
        temperature = 2.0*kinetic/(float(npart)-dof)
    average_temperature = np.average(temperature)
    return temperature, average_temperature

def reset_momentum(particles, selection=None):
    """
    This method sets the linear momentum of a selection
    of particles to zero
    
    Parameters
    ----------
    particles : object with a list of particles
    selection : optional, list with indices of particles to use

    Returns
    -------
    N/A, but modifies the velocities of the selected particles
    """
    if selection is None:
        vel, mass = particles.vel, particles.mass
    else:
        vel, mass = particles.vel[selection], particles.mass[selection]
    mom = np.sum(vel*mass, axis=0)
    particles.vel[selection] -= mom/mass.sum()

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
        self.empty_list()

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
        self.ptype =  None

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
                if type(var) == type([]):
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
                yield (i, i+1+j, self.ptype[i], self.ptype[j])



