# -*- coding: utf-8 -*-
"""
This file contains methods that act on a (selection) of particles.
"""
import numpy as np
import warnings

__all__ = ['kinetic_energy', 'kinetic_temperature', 'reset_momentum']


def calculate_linear_momentum(particles, selection=None):
    """
    This function calculate the linear momentum for a collection
    of particles

    Parameters
    ----------
    particles : object of type particlelist.
        List of particles to operate on.
    selection : list of integers, optional
        A list with indices of particles to use in calculation.

    Returns
    -------
    out : numpy.array
        The array contains the linear momentum for each dimension.
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
    particles : object of type particlelist.
        List of particles to operate on.
    selection : list of integers, optional
        A list with indices of particles to use in calculation.

    Returns
    -------
    out : numpy.array
        A numpy array with the same number of dimensions as self.vel.
        It contains the kinetic energy of the particles in the different
        dimensions.
    """
    if selection is None:
        vel, mass = particles.vel, particles.mass
    else:
        vel, mass = particles.vel[selection], particles.mass[selection]
    kinetic = 0.5 * np.sum(vel*vel*mass, axis=0)
    return kinetic


def kinetic_temperature(particles, selection=None,
                        dof=None, kinetic=None):
    """
    This method returns the kinetic temperature of a
    collection of particles.

    Parameters
    ----------
    particles : object of type particlelist.
        List of particles to operate on.
    selection : list of integers, optional
        A list with indices of particles to use in calculation.
    dof : numpy.array, optional
        The degrees of freedom to subtract in each dimension.
    kinetic : numpy.array optional
        The kinetic energy. If the kinetic energy is not given, it
        will be recalculated here.

    Returns
    -------
    out[0] : numpy.array
        Array with same size as the kinetic energy, it
        contains the temperature in each spatial dimension.
    out[1] : float
        The temperature averaged over all dimensions.
    """
    if selection is None:
        vel, mass = particles.vel, particles.mass
    else:
        vel, mass = particles.vel[selection], particles.mass[selection]
    npart = len(mass)
    if kinetic is None:
        kinetic = 0.5 * np.sum(vel*vel*mass, axis=0)
    if dof is None:
        temperature = 2.0 * kinetic / float(npart)
    else:
        if isinstance(dof, list):
            dof = np.array(dof)
        temperature = 2.0 * kinetic/(float(npart)-dof)
    average_temperature = np.average(temperature)
    return temperature, average_temperature


def reset_momentum(particles, selection=None):
    """
    This method sets the linear momentum of a selection
    of particles to zero

    Parameters
    ----------
    particles : object of type particlelist.
        List of particles to operate on.
    selection : list of integers, optional
        A list with indices of particles to use in calculation.

    Returns
    -------
    N/A, but modifies the velocities of the selected particles
    """
    if selection is None:
        vel, mass = particles.vel, particles.mass
    else:
        vel, mass = particles.vel[selection], particles.mass[selection]
    mom = np.sum(vel*mass, axis=0)
    particles.vel[selection] -= (mom/mass.sum())


def evaluate_press(particles, system, temperature=None,
                   dof=None):
    """
    This method evaluates pV

    Parameters
    ----------
    particles : object of type particlelist.
        List of particles to operate on.
    system : object of type system.
        The system, used to obtain kB in correct units and
        number of dimensions.
    temperature : float, optional
        The current temperature of the system. If the temperature is
        not given, it will be calculated here.

    Raises
    ------
    Warning if both temperature and dof is None. This might be perfectly
    fine, but typically, some info about the dof to subtract is needed
    for the temperature calculation. This is perhaps a indication that
    we should rethink how to include dof's to subtract! It could possibly
    be moved to the system.
    """
    if temperature is None and dof is None:
        warnings.warn('Both temperature and dof are not set')
    if temperature is None:
        _, temperature = kinetic_temperature(particles, dof=dof,
                                             kinetic=None)
    dim = float(system.get_dim())
    if dof is None:
        npart = particles.npart
    else:
        npart = (particles.npart * dim - np.sum(dof))/dim
    pressvolume = npart * temperature * system.get_kB() +\
                  (particles.virial/dim)
    press = pressvolume / system.box.calculate_volume()
    return pressvolume, press
