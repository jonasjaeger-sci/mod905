# -*- coding: utf-8 -*-
"""
This module handles random number generation.

It derives most of the random number procedures from `RandomState` in
`numpy.random`.
"""
from __future__ import absolute_import
from pyretis.core.particlefunctions import (calculate_kinetic_temperature,
                                            reset_momentum)
import numpy as np
from numpy.random import RandomState

__all__ = ['RandomGenerator']


class RandomGenerator(object):
    """
    RandomGenerator(object).

    This class that defines a random number generator.
    It will use `numpy.random.RandomState` for the actual generation, and we
    refer to the numpy documentation [1]_.
    Here we could inherit from RandomState but here we do not wish (?) to
    inherit from an old-style class. Here, this results in some unfortunate(?)
    small functions here that will actually just call `RandomState`.

    Attributes
    ----------
    rgen : object of type `RandomState`
        This is a container for the Mersenne Twiser pseudo-random number
        generator as implemented in numpy.

    References
    ----------

    .. [1] http://docs.scipy.org/doc/numpy/reference/generated/numpy.random.RandomState.html
    """

    def __init__(self, seed=None):
        """
        Initiate the random number generator.

        If a seed is given, the random number generator will be seeded.

        Parameters
        ----------
        seed : int, optional
            An integer used for seeding the generator if needed.
        """
        self.rgen = RandomState(seed=seed)

    def rand(self, shape=1):
        """
        Call `self.rgen.rand()`, see the description of this method.

        Parameters
        ----------
        shape : int
            Number of numbers to draw

        Returns
        -------
        out : float
            Pseudorandom number in [0, 1)
        """
        return self.rgen.rand(shape)

    def random_integers(self, low, high):
        """
        Draw random integers using `self.rgen.random_integers(low, high)`.

        Parameters
        ----------
        low : int
            This is the lower limit
        high : int
            This is the upper limit

        Returns
        -------
        out : int
            This is a psudorandom integer in [low, high]
        """
        return self.rgen.random_integers(low, high)

    def normal(self, loc=0.0, scale=1.0, size=None):
        """
        Run `self.rgen.normal` and return values from a normal distribution.

        Parameters
        ----------
        loc : float, optional
            The mean of the distribution
        scale : float, optional
            The standard deviation of the distribution
        size : int, tuple of ints, optional
            Output shape, i.e. how many values to generate. Default is None
            which is just a single value.

        Returns
        -------
        out : float, numpy.array of floats
            The random numbers generated
        """
        return self.rgen.normal(loc=loc, scale=scale, size=size)

    def multivariate_normal(self, mean, cov, cho=None, size=1):
        """
        Draw numbers from a multivariate distribution.

        This is an attempt on speeding up the call of
        RandomState.multivariate_normal if we need to call it over and
        over again. Such repeated calling will do a svd repeatedly, which
        is wastefull. In this function, this transform can be supplied and it
        is only estimated if it's not explicitly given.

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

        Returns
        -------
        out : float or numpy.array of floats size
            The random numbers drawn.

        See also
        --------
        numpy.random.multivariate_normal
        """
        if cho is None:
            cho = np.linalg.cholesky(cov)
        norm = self.normal(loc=0.0, scale=1.0, size=2*size)
        norm = norm.reshape(size, 2)
        meanm = np.array([mean, ] * size)
        return meanm + np.dot(norm, cho.T)

    def generate_maxwellian_velocities(self, particles, temperature, dof,
                                       selection=None, momentum=True):
        """
        Generate velocities from a Maxwell distribution for a group of
        particles with a given temperature.

        The generation is done in three steps:
        1) We generate velocities from a standard normal distribution
        2) We scale the velocity of particle i with 1.0/sqrt(mass_i) and
        reset the momentum
        3) We scale the velocities to the set temperature

        Parameters
        ----------
        particles : object of type particlelist
            These are the particles to set the velocity of.
        temperature : float
            The desired temperature. Typically, system.temperature['set']
            will be used here.
        dof : list of floats, optional
            dof is the degrees of freedom to subtract. It's shape should
            be equal to the number of dimensions.
        selection : list of ints, optional
            A list with indices of the particles to consider.
            Can be used to only apply it to a selection of particles
        momentum : boolean
            If true, we will reset the momentum.

        Returns
        -------
        N/A, but modifies the velocities of the selected particles
        """
        if selection is None:
            vel, imass = particles.vel, particles.imass
        else:
            vel, imass = particles.vel[selection], particles.imass[selection]
        vel = np.sqrt(imass) * self.normal(loc=0.0, scale=1.0,
                                           size=vel.shape)
        # NOTE: x[None] = x for a numpy.array - this is not valid for a list.
        particles.vel[selection] = vel
        if momentum:
            reset_momentum(particles, selection=selection)

        _, avgtemp, _ = calculate_kinetic_temperature(particles, dof=dof,
                                                      selection=selection)
        scale_factor = np.sqrt(temperature/avgtemp)
        particles.vel[selection] *= scale_factor

    def draw_maxwellian_velocities(self, system, sigma_v=None):
        """
        Simple function to draw numbers from a gaussian distribution.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`
            This is used to determine the temperature parameter(s) and
            the shape (number of particles and dimensionality)
        sigma_v : numpy.array, optional
            Standard deviation in velocity, one for each particle.
            If it's not given it will be estimated.
        """
        if not sigma_v:
            kbt = (1.0/system.temperature['beta'])
            sigma_v = np.sqrt(kbt*system.particles.imass)
        vel = self.normal(loc=0.0, scale=sigma_v,
                          size=system.particles.vel.shape)
        return vel, sigma_v
