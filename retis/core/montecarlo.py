# -*- coding: utf-8 -*-
"""
Module for Monte Carlo Algorithms and other
"random" functions.
"""
from __future__ import absolute_import
from .particlefunctions import calculate_kinetic_temperature, reset_momentum
import numpy as np
from numpy.random import RandomState

__all__ = ['seed_random_generator', 'accept_reject', 'max_displace_step',
           'random_normal', 'generate_maxwellian_velocities',
           'draw_maxwellian_velocities',
           'multivariate_normal']

RANDOMGENERATOR = RandomState()  # this will be the random number generator


def seed_random_generator(seed=1, rgen=RANDOMGENERATOR):
    """
    Helper function to seed the random number generator

    Parameters
    ----------
    seed : int, optional.
        The seed for the random number generator.
    rgen : object, optional.
        The random number generator. Default is the global one in this module.

    Returns
    -------
    None, however ``rgen`` is seeded with the given seed.
    """
    rgen.seed(seed)


def accept_reject(system, trial, rgen=RANDOMGENERATOR):
    """
    Routine for accepting or rejecting a MC move

    Parameters
    ----------
    system : object
        The system object we are investigating.
    trial : numpy.array
        The the trial position(s)
    rgen : object, optional.
        The random number generator. Default is the global one in this module.

    Returns
    -------
    out[0] : numpy.array, same shape as input `trial`
        The accepted positions (trial or the original positions).
    out[1] : float
        The energy corresponding to the accepted positions.
    out[2] : numpy.array
        The trial positions.
    out[3] : float
        The potential energy of the trial positions.
    out[4] : boolean
        True if move is acceped, False otherwise.

    Notes
    -----
    A overflow is possible when using np.exp() here.
    This can for instance happen in a umbrella simulation
    where the bias potential is infinite or very large.
    Right now, this is just ignored.
    """
    v_trial = system.evaluate_potential(pos=trial)
    deltae = v_trial - system.v_pot
    pacc = np.exp(-system.temperature['beta'] * deltae)
    if rgen.rand() < pacc:
        return trial, v_trial, trial, v_trial, True
    else:
        return system.particles.pos, system.v_pot, trial, v_trial, False


def max_displace_step(system, maxdx=0.1, idx=None, rgen=RANDOMGENERATOR):
    """
    Monte Carlo routine for diplacing particles.

    It selects and displaces one particle randomly.
    If the move is accepted, the new positions and energy are
    return. Otherwise, the move is rejected and the old positions
    and potential energy is returned.
    The function accept_reject is used to accept/reject the move.

    Parameters
    ----------
    system : object
        The system object to operate on
    maxdx : float, optional
        The maximum displacement (default is 0.1).
    rgen : object, optional.
        The random number generator. Default is the global one in this module.
    idx : int, optional.
        Index of particle to displace. If idx is not given, the particle
        is chosen randomly.

    Returns
    -------
    out : The outcome of applying the function accept_reject to the system
        and trial position.
    """
    if idx is None:
        idx = rgen.random_integers(0, system.particles.npart - 1)
    trial = np.copy(system.particles.pos)
    trial[idx] += 2.0 * maxdx * (rgen.rand(system.get_dim()) - 0.5)
    return accept_reject(system, trial)


def random_normal(loc=0.0, scale=1.0, size=None, rgen=RANDOMGENERATOR):
    """
    Function to return numbers from a normal distribution.
    This function will actually just call np.random.normal
    the reason for including it here as a function is that we
    might want to use the random number generator with a specified
    seed.

    Parameters
    ----------
    loc : float, optional
        Mean of the distribution.
    scale : float, optional
        Standard deviation of the distribution.
    size : int or tuple of ints, optional
        Output shape. Default is None, in which case a single value is
        returned.
    rgen : object, optional
        The random number generator

    Returns
    -------
    out : float or numpy.array of floats
        The random numbers drawn.

    See also
    --------
    numpy.random.normal
    """
    return rgen.normal(loc=loc, scale=scale, size=size)


#def multivariate_normal(mean, cov, size=None, rgen=RANDOMGENERATOR):
#    """
#    Function to return numbers from a multivariate distribution.
#    This function will actually just call np.random.multivariate_normal
#    the reason for including it here as a function is that we might want
#    to use the random number generator with a specified seed.
#
#    Parameters
#    ----------
#    mean : numpy array (1D, N)
#        Mean of the N-dimensional array
#    cov : numpy array (2D, (N, N))
#        Covariance matrix of the distribution.
#    size : int or tuple of ints, optional
#        Output shape. Default is None, in which case a single value is
#        returned.
#    rgen : object, optional
#        The random number generator
#
#    Returns
#    -------
#    out : float or numpy.array of floats
#        The random numbers drawn.
#
#    See also
#    --------
#    numpy.random.random.multivariate_normal
#    """
#    return rgen.multivariate_normal(mean, cov, size=size)

def multivariate_normal(mean, cov, cho=None, size=1, rgen=RANDOMGENERATOR):
    """
    Function to return numbers from a multivariate distribution.
    This is an attempt on speeding up the call of
    numpy.random.multivariate_normal if we need to call it over and
    over again. Such repeated calling will do a svd repeatedly, which
    is waste full.
    In this function, such a transform can be supplied, it is only
    estimated if it's not given.

    Parameters
    ----------
    mean : numpy array (1D, 2)
        Mean of the N-dimensional array
    cov : numpy array (2D, (2, 2))
        Covariance matrix of the distribution.
    cho : numpy.array (2D, (2, 2)), optional
        Cholesky factorization of cov. If not given,
        it will be calculated here.
    size : int, optional.
        Number of samples to do.
    rgen : object, optional
        The random number generator

    Returns
    -------
    out : float or numpy.array of floats size
        The random numbers drawn.

    See also
    --------
    self.multivariate_normal
    """
    if cho is None:
        cho = np.linalg.cholesky(cov)
    norm = random_normal(loc=0.0, scale=1.0, size=2*size, rgen=rgen)
    norm = norm.reshape(size, 2)
    meanm = np.array([mean, ] * size)
    return meanm + np.dot(norm, cho.T)


def generate_maxwellian_velocities(system, temperature=None, selection=None,
                                   momentum=True, rgen=RANDOMGENERATOR):
    """
    Function to generate velocities from a Maxwell distribution for a
    group of particles. We do this in three steps:
    1) We generate velocities from a standard normal distribution
    2) We scale the velocity of particle i with 1.0/sqrt(mass_i) and
    reset the momentum
    3) We scale the velocities to the set temperature

    Parameters
    ----------
    system : object of type system
        This object is assumed to have a particle list type.
    temperature : float, optional
        The desired temperature, if this is not set, the value in
        system.temperature['set'] will be used.
    selection : list of ints, optional
        A list with indices of the particles to consider.
        Can be used to only apply it to a selection of particles
    momentum : boolean
        If true, we will reset the momentum.
    rgen : object, optional
        The random number generator
    Returns
    -------
    N/A, but modifies the velocities of the selected particles
    """
    particles = system.particles
    if selection is None:
        vel, imass = particles.vel, particles.imass
    else:
        vel, imass = particles.vel[selection], particles.imass[selection]
    vel = np.sqrt(imass) * random_normal(loc=0.0, scale=1.0,
                                         size=vel.shape, rgen=rgen)
    if selection is None:  # this if might be removed as x[None] is x
        system.particles.vel = vel
    else:
        system.particles.vel[selection] = vel

    if momentum:
        reset_momentum(system, selection=selection)

    if temperature is None:
        temperature = system.temperature['set']
    _, avgtemp, _ = calculate_kinetic_temperature(system, selection=selection)
    scale_factor = np.sqrt(temperature/avgtemp)

    if selection is None:  # this if might be removed as x[None] is x
        system.particles.vel *= scale_factor
    else:
        system.particles.vel[selection] *= scale_factor

def draw_maxwellian_velocities(system, sigma_v=None, rgen=RANDOMGENERATOR):
    """
    Simple function to draw numbers from a gaussian distribution.

    Parameters
    ----------
    system : object of type system
        This is used to determine the temperature parameter(s) and
        the shape (number of particles and dimensionality)
    sigma_v : numpy.array, optional
        Standard deviation in velocity, one for each particle.
        If it's not given it will be estimated.
    rgen : object, optional
        The random number generator
    """
    if not sigma_v:
        kbt = (1.0/system.temperature['beta'])
        sigma_v = np.sqrt(kbt*system.particles.imass)
    vel = random_normal(loc=0.0, scale=sigma_v,
                        size=system.particles.vel.shape, rgen=rgen)
    return vel
