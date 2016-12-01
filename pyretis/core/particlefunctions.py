# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""This file contains functions that act on (a selection of) particles.

These functions are intended for calculating particle properties as the
kinetic temperature, pressure etc.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

atomic_kinetic_energy_tensor
    Return the kinetic energy tensor for each atom in a selection
    of particles.

calculate_kinetic_energy
    Return the kinetic energy of a collection of particles.

calculate_kinetic_energy_tensor
    Return the kinetic energy tensor for a selection of particles.

calculate_kinetic_temperature
    Return the kinetic temperature of a collection of particles.

calculate_linear_momentum
    Calculates the linear momentum of a collection of particles.

calculate_pressure_from_temp
    Return the scalar pressure using the temperature and the virial.

calculate_pressure_tensor
    Return the pressure tensor, obtained from the virial and the kinetic
    energy tensor.

calculate_scalar_pressure
    Return the scalar pressure (from the trace of the pressure tensor).

calculate_thermo
    Calculate and return several "thermodynamic" properties as the
    potential, kinetic and total energies per particle, the temperature,
    the pressure and the momentum.

calculate_thermo_path
    Calculate and return some thermodynamic properties. This method
    is similar to the `calculate_thermo`, however it is simpler and
    calculates fewer quantities.

reset_momentum
    Set linear momentum (for a selection of particles) to zero.
"""
import numpy as np


__all__ = ['atomic_kinetic_energy_tensor',
           'calculate_kinetic_energy',
           'calculate_kinetic_energy_tensor',
           'calculate_kinetic_temperature',
           'calculate_linear_momentum',
           'calculate_pressure_from_temp',
           'calculate_pressure_tensor',
           'calculate_scalar_pressure',
           'calculate_thermo',
           'calculate_thermo_path',
           'reset_momentum']


def atomic_kinetic_energy_tensor(particles, selection=None):
    """Return kinetic energy tensors for a particle selection.

    Parameters
    ----------
    particles : object like `Particles` from `pyretis.core.particles`
        This object represent the particles.
    selection : list of integers, optional
        A list with indexes of particles to use in calculation.

    Returns
    -------
    kin : numpy.array
        A numpy array with dimensionality equal to
        (`len(selection)`, `dim`, `dim`) where `dim` is the number of
        dimensions used in the velocities. `kin[i]` contains the kinetic
        energy tensor formed by the outer product of `mol[selection][i]`
        and `vel[selection][i]`. The sum of the tensor should equal the
        output from `calculate_kinetic_energy_tensor`.
    """
    if selection is None:
        vel, mass = particles.vel, particles.mass
    else:
        vel, mass = particles.vel[selection], particles.mass[selection]
    mom = vel*mass
    if len(mass) == 1:  # in general: selection != particles.npart
        kin = 0.5*np.outer(mom, vel)
    else:
        kin = 0.5*np.einsum('ij,ik->ijk', mom, vel)
    return kin


def calculate_kinetic_energy(particles, selection=None, kin_tensor=None):
    """Return the kinetic energy of a collection of particles.

    Parameters
    ----------
    particles : object like `Particles` from `pyretis.core.particles`
        This object represent the particles.
    selection : list of integers, optional
        A list with indexes of particles to use in calculation.
    kin_tensor : numpy.array
        If kinetic_tensor is not given, the kinetic energy tensor will
        be calculated.

    Returns
    -------
    out[0] : float
        The scalar kinetic energy.
    out[1] : numpy.array
        The kinetic energy tensor.
    """
    if kin_tensor is None:
        kin_tensor = calculate_kinetic_energy_tensor(particles,
                                                     selection=selection)
    return kin_tensor.trace(), kin_tensor


def calculate_kinetic_energy_tensor(particles, selection=None):
    """Return the kinetic energy tensor for a selection of particles.

    The tensor is formed as the outer product of the velocities.

    Parameters
    ----------
    particles : object like `Particles` from `pyretis.core.particles`
        This object represent the particles.
    selection : list of integers, optional
        A list with indexes of particles to use in calculation.

    Returns
    -------
    out : numpy.array
        A numpy array with dimensionality equal to (dim, dim) where dim
        is the number of dimensions used in the velocities. This tensor
        should be symmetric and it's trace should be identical to the
        output from the `dim` times the averaged output of the
        `kinetic_energy` function defined below.
    """
    if selection is None:
        vel, mass = particles.vel, particles.mass
    else:
        vel, mass = particles.vel[selection], particles.mass[selection]
    mom = vel*mass
    if len(mass) == 1:  # in general: selection != particles.npart
        kin = 0.5*np.outer(mom, vel)
    else:
        kin = 0.5*np.einsum('ij,ik->jk', mom, vel)
    return kin


def calculate_kinetic_temperature(particles, boltzmann, dof=None,
                                  selection=None,
                                  kin_tensor=None):
    """Return the kinetic temperature of a collection of particles.

    Parameters
    ----------
    particles : object like `Particles` from `pyretis.core.particles`
        This object represent the particles.
    boltzmann : float
        This is the Boltzmann factor/constant in correct units.
    dof : list of floats, optional
        dof is the degrees of freedom to subtract. It's shape should
        be equal to the number of dimensions.
    selection : list of integers, optional
        A list with indexes of particles to use in calculation.
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
    out[2] : numpy.array
        The kinetic energy tensor.
    """
    if selection is None:
        vel, mass = particles.vel, particles.mass
    else:
        vel, mass = particles.vel[selection], particles.mass[selection]

    npart = len(mass)  # using mass, since selection may be != particles.npart
    ndof = npart * np.ones(vel[0].shape)

    if kin_tensor is None:
        kin_tensor = calculate_kinetic_energy_tensor(particles,
                                                     selection=selection)
    if dof is not None:
        ndof = ndof - dof
    temperature = (2.0 * kin_tensor.diagonal() / ndof) / boltzmann
    return temperature, np.average(temperature), kin_tensor


def calculate_linear_momentum(particles, selection=None):
    """Calculate the linear momentum for a collection of particles.

    Parameters
    ----------
    particles : object like `Particles` from `pyretis.core.particles`
        This object represent the particles.
    selection : list of integers, optional
        A list with indexes of particles to use in calculation.

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


def calculate_pressure_from_temp(particles, dim, boltzmann, volume,
                                 dof=None):
    """Evaluate the scalar pressure.

    The scalar pressure is here calculated  using the temperature
    and the degrees of freedom.

    Parameters
    ----------
    particles : object like `Particles` from `pyretis.core.particles`
        This object represent the particles.
    dim : int
        This is the dimensionality of the system.
        Typically provided by `system.get_dim()`.
    boltzmann : float
        This is the Boltzmann factor/constant in correct units.
        Typically it can be supplied by `system.get_boltzmann()`.
    volume : float
        This is the volume 'occupied' by the particles. It can typically
        be obtained by a `box.calculate_volume()`
    dof : list of floats, optional
        `dof` is the degrees of freedom to subtract. Its shape should
        be equal to the number of dimensions.

    Returns
    -------
    out[0] : float
        Pressure times volume.
    out[1] : float
        The pressure.

    Note
    ----
    This function may possibly be removed - it does not appear to be
    very useful right now.
    """
    if dof is None:
        ndof = particles.npart
    else:
        ndof = (particles.npart * dim - np.sum(dof)) / float(dim)
    _, temperature, _ = calculate_kinetic_temperature(particles, boltzmann,
                                                      dof=dof)
    pressvolume = ndof * temperature * boltzmann
    pressvolume += particles.virial.trace() / float(dim)
    press = pressvolume / volume
    return pressvolume, press


def calculate_pressure_tensor(particles, volume, kin_tensor=None):
    """Calculate the pressure tensor.

    The pressure tensor is obtained from the virial the kinetic
    energy tensor.

    Parameters
    ----------
    particles : object like `Particles` from `pyretis.core.particles`
        This object represent the particles.
    volume : float
        This is the volume 'occupied' by the particles. It can typically
        be obtained by a `box.calculate_volume()`.
    kin_tensor : numpy.array
        The kinetic energy tensor. If `kin_tensor` is not given, it will
        be calculated here.

    Returns
    -------
    out : numpy.array
        The symmetric pressure tensor, dimensions (`dim`, `dim`), where
        `dim` = the number of dimensions considered in the simulation.
    """
    if kin_tensor is None:
        kin_tensor = calculate_kinetic_energy_tensor(particles, selection=None)
    pressure = (particles.virial + 2. * kin_tensor) / volume
    return pressure


def calculate_scalar_pressure(particles, volume, dim, press_tensor=None,
                              kin_tensor=None):
    """Evaluate the scalar pressure using the pressure tensor.

    Parameters
    ----------
    particles : object like `Particles` from `pyretis.core.particles`
        This object represent the particles.
    volume : float
        This is the volume 'occupied' by the particles. It can typically
        be obtained by a `box.calculate_volume()`.
    dim : int
        This is the dimensionality of the system. Typically provided by
        `system.get_dim()`
    press_tensor : numpy.array
        If `press_tensor` is not given, the pressure tensor will be
        calculated here.
    kin_tensor : numpy.array
        If `kin_tensor` is not given, the kinetic energy tensor will be
        calculated here.

    Returns
    -------
    out : float
        The scalar pressure, averaged over the diagonal components of
        the pressure tensor.
    """
    if press_tensor is None:
        press_tensor = calculate_pressure_tensor(particles, volume,
                                                 kin_tensor=kin_tensor)
    return press_tensor.trace() / float(dim)


def calculate_thermo(system, dof=None, dim=None, volume=None, vpot=None):
    """Calculate and return several thermodynamic properties.

    The calculated properties are the potential, kinetic and total
    energies per particle, the temperature, the pressure and the
    momentum.

    Parameters
    ----------
    system : object like `System` from `pyretis.core.system`.
        This object is used to access the particles and the box.
    dof : list of floats
        `dof` is the degrees of freedom, typically provided with
        a `system.temperature['dof']`.
    dim : float
        The dimensionality of, typically provided with a
        `system.get_dim()`.
    volume : float
        This is the volume 'occupied' by the particles. It can typically
        be obtained by a `system.box.calculate_volume()`.
    vpot : float
        The potential energy of the particles. It can typically be
        obtained by from `system.v_pot`.

    Returns
    -------
    out : dict
        This dict contains the float that is calculated in this routine.
    """
    if volume is None:
        volume = system.box.calculate_volume()
    if vpot is None:
        vpot = system.v_pot
    if dim is None:
        dim = system.get_dim()
    if dof is None:
        dof = system.temperature['dof']
    kin_tens = calculate_kinetic_energy_tensor(system.particles)
    _, temp, _ = calculate_kinetic_temperature(system.particles,
                                               system.get_boltzmann(),
                                               dof=dof,
                                               kin_tensor=kin_tens)
    press_tens = calculate_pressure_tensor(system.particles, volume,
                                           kin_tensor=kin_tens)
    ekin = kin_tens.trace()
    press = calculate_scalar_pressure(system.particles, volume, dim,
                                      kin_tensor=kin_tens)
    mom = calculate_linear_momentum(system.particles)
    npart = float(system.particles.npart)
    result = {'vpot': vpot / npart, 'ekin': ekin / npart,
              'etot': (ekin + vpot) / npart,
              'temp': temp, 'press': press, 'mom': mom,
              'press-tens': press_tens}
    return result


def calculate_thermo_path(system):
    """Calculate and return several thermodynamic properties.

    The calculated properties are the potential, kinetic and total
    energies for the system and the current temperature.

    Parameters
    ----------
    system : object like `System` from `pyretis.core.system`.
        This object is used to access the particles and the box.

    Returns
    -------
    out : dict
        This dict contains the float that is calculated in this routine.
    """
    particles = system.particles
    kin_tens = calculate_kinetic_energy_tensor(particles)
    _, temp, _ = calculate_kinetic_temperature(particles,
                                               system.get_boltzmann(),
                                               dof=system.temperature['dof'],
                                               kin_tensor=kin_tens)
    ekin = kin_tens.trace()
    vpot = system.v_pot
    return {'vpot': vpot, 'ekin': ekin, 'etot': ekin + vpot, 'temp': temp}


def reset_momentum(particles, selection=None, dim=None):
    """Set the linear momentum of a selection of particles to zero.

    Parameters
    ----------
    particles : object like `Particles` from `pyretis.core.particles`
        This object represent the particles.
    selection : list of integers, optional
        A list with indexes of particles to use in calculation.
    dim : list or None, optional
        If ``dim`` is None, the momentum will be reset for ALL
        dimensions. Otherwise it will only be applied to the
        dimensions where ``dim`` is True.

    Returns
    -------
    out : None
        Returns `None` and modifies velocities of the selected
        particles.

    """
    if selection is None:
        vel, mass = particles.vel, particles.mass
    else:
        vel, mass = particles.vel[selection], particles.mass[selection]
    mom = np.sum(vel * mass, axis=0)
    if dim is not None:
        for i, reset in enumerate(dim):
            if not reset:
                mom[i] = 0
    particles.vel[selection] -= (mom / mass.sum())
