# -*- coding: utf-8 -*-
"""
This file contains methods that act on a (selection) of particles.
"""
import numpy as np
#import warnings

__all__ = ['calculate_kinetic_energy', 'calculate_kinetic_temperature',
           'reset_momentum', 'calculate_kinetic_energy_tensor',
           'calculate_scalar_pressure', 'calculate_pressure_tensor',
           'calculate_linear_momentum', 'atomic_kinetic_energy_tensor']


def calculate_linear_momentum(system, selection=None):
    """
    This function calculate the linear momentum for a collection
    of particles

    Parameters
    ----------
    system : object of type System from retis.core.system
        This object is assumed to contain the particle list to calculate
        the linear momentum for.
    selection : list of integers, optional
        A list with indices of particles to use in calculation.

    Returns
    -------
    out : numpy.array
        The array contains the linear momentum for each dimension.
    """
    particles = system.particles
    if selection is None:
        vel, mass = particles.vel, particles.mass
    else:
        vel, mass = particles.vel[selection], particles.mass[selection]
    return np.sum(vel*mass, axis=0)


def calculate_kinetic_energy_tensor(system, selection=None):
    """
    This function returns the kinetic energy as a tensor
    for a selection of particles. The tensor is formed as the
    outer product of the velocities.

    Parameters
    ----------
    system : object of type System from retis.core.system
        This object is assumed to contain the particle list to calculate
        the linear momentum for.
    selection : list of integers, optional
        A list with indices of particles to use in calculation.

    Returns
    -------
    out : numpy.array
        A numpy array with dimesionality equal to (dim, dim) where dim
        is the number of dimensions used in the velocities. This tensor
        should be symmetric and it's trace should be identical to the
        output from the ``dim`` times the averaged output of the
        ``kinetic_energy`` method defined below
    """
    particles = system.particles
    if selection is None:
        vel, mass = particles.vel, particles.mass
    else:
        vel, mass = particles.vel[selection], particles.mass[selection]
    mom = vel*mass
    if len(mass) == 1:
        kin = 0.5*np.outer(mom, vel)
    else:
        kin = 0.5*np.einsum('ij,ik->jk', mom, vel)
    return kin


def atomic_kinetic_energy_tensor(system, selection=None):
    """
    This function returns the kinetic energy tensor for
    each atom in a selection of particles.

    Parameters
    ----------
    system : object of type System from retis.core.system
        This object is assumed to contain the particle list to calculate
        the linear momentum for.
    selection : list of integers, optional
        A list with indices of particles to use in calculation.

    Returns
    -------
    out[] : numpy.array
        A numpy array with dimesionality equal to (len(selection), dim, dim)
        where dim is the number of dimensions used in the velocities.
        out[i] contains the kinetic energy tensor formed by the outer product
        of mol[selection][i] and vel[selection][i].
        The sum of the tensor should equal the output from
        ``calculate_kinetic_energy_tensor``
    """
    particles = system.particles
    if selection is None:
        vel, mass = particles.vel, particles.mass
    else:
        vel, mass = particles.vel[selection], particles.mass[selection]
    mom = vel*mass
    if len(mass) == 1:
        kin = 0.5*np.outer(mom, vel)
    else:
        kin = 0.5*np.einsum('ij,ik->ijk', mom, vel)
    return kin


def calculate_kinetic_energy(system, selection=None, kin_tensor=None):
    """
    This function returns the kinetic energy of a collection of
    particles.

    Parameters
    ----------
    system : object of type System from retis.core.system
        This object is assumed to contain the particle list to calculate
        the linear momentum for.
    selection : list of integers, optional
        A list with indices of particles to use in calculation.
    kin_tensor : numpy.array
        If kinetic_tensor is not given, the kinetic energy tensor will be
        calculated.

    Returns
    -------
    out[0] : float
        The scalar kinetic energy.
    out[1] : numpy.array
        The kinetic energy tensor.
    """
    if kin_tensor is None:
        kin_tensor = calculate_kinetic_energy_tensor(system,
                                                     selection=selection)
    return kin_tensor.trace(), kin_tensor


def calculate_kinetic_temperature(system, selection=None,
                                  kin_tensor=None):
    """
    This method returns the kinetic temperature of a
    collection of particles.

    Parameters
    ----------
    system : object of type System from retis.core.system
        This object is assumed to contain the particle list to calculate
        the linear momentum for.
    selection : list of integers, optional
        A list with indices of particles to use in calculation.
    kin_tensor : numpy.array optional
        The kinetic energy tensor. If the kinetic energy tensor is not
        given, it will be recalculated here.

    Returns
    -------
    out[0] : numpy.array
        Array with same size as the kinetic energy, it
        contains the temperature in each spatial dimension.
    out[1] : float
        The temperature averaged over all dimensions.
    """
    particles = system.particles
    if selection is None:
        vel, mass = particles.vel, particles.mass
    else:
        vel, mass = particles.vel[selection], particles.mass[selection]
    
    npart = len(mass)
    if npart == 1:
        ndof = npart * np.ones(vel.shape)
    else:
        ndof = npart * np.ones(vel[0].shape)

    if kin_tensor is None:
        kin_tensor = calculate_kinetic_energy_tensor(system,
                                                     selection=selection)
    dof = system.temperature['dof']
    if not dof is None:
        ndof = ndof - dof
    temperature = 2.0 * kin_tensor.diagonal() / ndof
    return temperature, np.average(temperature), kin_tensor


def reset_momentum(system, selection=None, dim=None):
    """
    This method sets the linear momentum of a selection
    of particles to zero

    Parameters
    ----------
    system : object of type system.
        System is assumed to contain a object in system.particles of type
        particlelist which defines the particles to operate on.
    selection : list of integers, optional
        A list with indices of particles to use in calculation.
    dim : list
        If dim is None, ``reset_momentum'' will be applied to
        all dimensions. Otherwise it will only be applied to the
        dimensions where dim is True.
    Returns
    -------
    N/A, but modifies the velocities of the selected particles
    """
    particles = system.particles
    if selection is None:
        vel, mass = particles.vel, particles.mass
    else:
        vel, mass = particles.vel[selection], particles.mass[selection]
    mom = np.sum(vel*mass, axis=0)
    if not dim is None:
        for i, reset in enumerate(dim):
            if not reset:
                mom[i] = 0
    particles.vel[selection] -= (mom/mass.sum())


def calculate_pressure_from_temp(system, temperature):
    """
    This method evaluates the scalar pressure using the temperature
    and the degrees of freedom.

    Parameters
    ----------
    system : object of type system.
        The system, used to obtain kB in correct units and
        number of dimensions.
    temperature : float
        The current kinetic temperature of the system. This temperature
        is calculated by ``calculate_kientic_temperature``
    """
    dim = float(system.get_dim())
    particles = system.particles
    dof = system.temperature['dof']
    if dof is None:
        ndof = particles.npart
    else:
        ndof = (particles.npart * dim - np.sum(dof))/dim
    pressvolume = ndof * temperature * system.get_boltzmann() +\
                  (particles.virial.trace()/dim)
    press = pressvolume / system.box.calculate_volume()
    return pressvolume, press


def calculate_scalar_pressure(system, press_tensor=None, kin_tensor=None):
    """
    This method evaluates the scalar pressure using the pressure tensor.

    Parameters
    ----------
    system : object of type system.
        Contains the particle list to use for the computation.
    press_tensor : numpy.array
        If press_tensor is not given, the pressure tensor will be
        calculated.
    kin_tensor : numpy.array
        If kinetic_tensor is not given, the kinetic energy tensor will be
        calculated.
    """
    if press_tensor is None:
        press_tensor = calculate_pressure_tensor(system,
                                                 kin_tensor=kin_tensor)
    return press_tensor.trace()/float(system.box.dim)


def calculate_pressure_tensor(system, kin_tensor=None):
    """
    This method evaluates the pressure tensor.

    Parameters
    ----------
    system : object of type system.
        The system, used to obtain the volume and the particle list.
    kin_tensor : numpy.array
        If kinetic_tensor is not given, the kinetic energy tensor will be
        calculated.

    Returns
    -------
    out : numpy.array
        The symmetric pressure tensor, dimensions (dim, dim), where
        dim = system.box.dim are the number of dimensions considere.
    """
    if kin_tensor is None:
        kin_tensor = calculate_kinetic_energy_tensor(system, selection=None)
    virial = system.particles.virial
    pressure = (virial + kin_tensor*2.0)/system.box.calculate_volume()
    return pressure
