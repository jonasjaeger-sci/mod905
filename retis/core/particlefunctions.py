# -*- coding: utf-8 -*-
"""
This file contains methods that act on a (selection) of particles.
"""
import numpy as np

__all__ = ['kinetic_energy', 'kinetic_temperature', 'reset_momentum']

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

