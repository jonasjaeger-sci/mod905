# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""This module handles random number generation.

It derives most of the random number procedures from `RandomState` in
`numpy.random` and defines a class which used `RandomState` to generate
pseudo-random numbers.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

RandomGeneratorBase (:py:class:`.RandomGeneratorBase`)
    An abstract base class for random number generators.

RandomGenerator (:py:class:`.RandomGeneratorBase`)
    A class representing a random number generator.

ReservoirSampler (:py:class:`.ReservoirSampler`)
    A class for reservoir sampling.

MockRandomGenerator (:py:class:`.MockRandomGenerator`)
    A non-random number generator which is useful for testing.
"""
from __future__ import absolute_import
from abc import ABCMeta, abstractmethod
import logging
import numpy as np
from numpy.random import RandomState
from pyretis.core.particlefunctions import (calculate_kinetic_temperature,
                                            reset_momentum)
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = [
    'RandomGeneratorBase',
    'RandomGenerator',
    'ReservoirSampler',
    'MockRandomGenerator'
]


class RandomGeneratorBase(metaclass=ABCMeta):
    """A base class for random number generators.

    This is a base class for random number generators. It does not
    actually implement a generator.

    Attributes
    ----------
    seed : int
        A seed for the generator
    """

    def __init__(self, seed=0):
        """Initiate the random number generator.

        Parameters
        ----------
        seed : int, optional
            An integer used for seeding the generator if needed.
        """
        self.seed = seed

    @abstractmethod
    def rand(self, shape=1):
        """Draw random numbers in [0, 1).

        Parameters
        ----------
        shape : int
            Number of numbers to draw

        Returns
        -------
        out : float
            Pseudo random number in [0, 1)
        """
        return

    @abstractmethod
    def random_integers(self, low, high):
        """Draw random integers in [low, high].

        Parameters
        ----------
        low : int
            This is the lower limit
        high : int
            This is the upper limit

        Returns
        -------
        out : int
            The pseudo random integers in [low, high].
        """
        pass

    @abstractmethod
    def normal(self, loc=0.0, scale=1.0, size=None):
        """Return values from a normal distribution.

        Parameters
        ----------
        loc : float, optional
            The mean of the distribution
        scale : float, optional
            The standard deviation of the distribution
        size : int, tuple of ints, optional
            Output shape, i.e. how many values to generate. Default is
            None which is just a single value.

        Returns
        -------
        out : float, numpy.array of floats
            The random numbers generated
        """
        return

    @abstractmethod
    def multivariate_normal(self, mean, cov, cho=None, size=1):
        """Draw numbers from a multi-variate distribution.

        Parameters
        ----------
        mean : numpy array (1D, 2)
            Mean of the N-dimensional array
        cov : numpy array (2D, (2, 2))
            Covariance matrix of the distribution.
        cho : numpy.array (2D, (2, 2)), optional
            Cholesky factorization of cov. If not given,
            it will be calculated here.
        size : int, optional
            Number of samples to do.

        Returns
        -------
        out : float or numpy.array of floats size
            The random numbers drawn.
        """
        return

    def generate_maxwellian_velocities(self, particles, boltzmann, temperature,
                                       dof, selection=None, momentum=True):
        """Generate velocities from a Maxwell distribution.

        The velocities are drawn to match a given temperature and this
        function can be applied to a sub-set of the particles.

        The generation is done in three steps:

        1) We generate velocities from a standard normal distribution.

        2) We scale the velocity of particle `i` with
           ``1.0/sqrt(mass_i)`` and reset the momentum.

        3) We scale the velocities to the set temperature.

        Parameters
        ----------
        particles : object like :py:class:`.Particles`
            These are the particles to set the velocity of.
        boltzmann : float
            The Boltzmann factor in correct units.
        temperature : float
            The desired temperature.
            Typically, `system.temperature['set']` will be used here.
        dof : list of floats, optional
            dof is the degrees of freedom to subtract. It's shape should
            be equal to the number of dimensions.
        selection : list of ints, optional
            A list with indexes of the particles to consider.
            Can be used to only apply it to a selection of particles
        momentum : boolean
            If true, we will reset the momentum.

        Returns
        -------
        out : None
            Returns `None` but modifies velocities of the selected
            particles.
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

        _, avgtemp, _ = calculate_kinetic_temperature(particles, boltzmann,
                                                      dof=dof,
                                                      selection=selection)
        scale_factor = np.sqrt(temperature/avgtemp)
        particles.vel[selection] *= scale_factor

    def draw_maxwellian_velocities(self, system, sigma_v=None):
        """Simple function to draw numbers from a Gaussian distribution.

        Parameters
        ----------
        system : object like :py:class:`.System`
            This is used to determine the temperature parameter(s) and
            the shape (number of particles and dimensionality)
        sigma_v : numpy.array, optional
            Standard deviation in velocity, one for each particle.
            If it's not given it will be estimated.
        """
        if not sigma_v or sigma_v < 0.0:
            kbt = (1.0/system.temperature['beta'])
            # sigma_v is (n, 1) matrix
            sigma_v = np.sqrt(kbt*system.particles.imass)
        npart, dim = system.particles.vel.shape
        vel = self.normal(loc=0.0, scale=sigma_v, size=(npart, dim))
        return vel, sigma_v


class RandomGenerator(RandomGeneratorBase):
    """A random number generator from numpy.

    This class that defines a random number generator. It will use
    `numpy.random.RandomState` for the actual generation, and we refer
    to the numpy documentation [1]_. Here we could inherit from
    RandomState but here we do not wish (?) to inherit from an old-style
    class. That is the cause of some small functions here that will
    actually just call the corresponding function from `RandomState`.

    Attributes
    ----------
    seed : int
        A seed for the pseudo-random generator.
    rgen : object like :py:class:`numpy.random.RandomState`
        This is a container for the Mersenne Twister pseudo-random
        number generator as implemented in numpy [#]_.

    References
    ----------

    .. [#] The NumPy documentation on RandomState,
       http://docs.scipy.org/doc/numpy/reference/generated/numpy.random.RandomState.html
    """

    def __init__(self, seed=0):
        """Initiate the random number generator.

        If a seed is given, the random number generator will be seeded.

        Parameters
        ----------
        seed : int, optional
            An integer used for seeding the generator if needed.
        """
        super().__init__(seed=seed)
        self.rgen = RandomState(seed=seed)

    def rand(self, shape=1):
        """Draw random numbers in [0, 1).

        Parameters
        ----------
        shape : int
            Number of numbers to draw

        Returns
        -------
        out : float
            Pseudo random number in [0, 1)

        Note
        ----
        Here, we will just draw a list of numbers and not for
        an arbitrary shape.
        """
        return self.rgen.rand(shape)

    def random_integers(self, low, high):
        """Draw random integers in [low, high].

        Parameters
        ----------
        low : int
            This is the lower limit
        high : int
            This is the upper limit

        Returns
        -------
        out : int
            The pseudo random integers in [low, high].

        Note
        ----
        np.random.randint(low, high) is defined as drawing
        from `low` (inclusive) to `high` (exclusive).
        """
        return self.rgen.randint(low, high + 1)

    def normal(self, loc=0.0, scale=1.0, size=None):
        """Return values from a normal distribution.

        Parameters
        ----------
        loc : float, optional
            The mean of the distribution
        scale : float, optional
            The standard deviation of the distribution
        size : int, tuple of ints, optional
            Output shape, i.e. how many values to generate. Default is
            None which is just a single value.

        Returns
        -------
        out : float, numpy.array of floats
            The random numbers generated
        """
        return self.rgen.normal(loc=loc, scale=scale, size=size)

    def multivariate_normal(self, mean, cov, cho=None, size=1):
        """Draw numbers from a multi-variate distribution.

        This is an attempt on speeding up the call of
        `RandomState.multivariate_normal` if we need to call it over and
        over again. Such repeated calling will do a SVD repeatedly,
        which is wasteful. In this function, this transform can be
        supplied and it is only estimated if it's not explicitly given.

        Parameters
        ----------
        mean : numpy array (1D, 2)
            Mean of the N-dimensional array
        cov : numpy array (2D, (2, 2))
            Covariance matrix of the distribution.
        cho : numpy.array (2D, (2, 2)), optional
            Cholesky factorization of cov. If not given,
            it will be calculated here.
        size : int, optional
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


class ReservoirSampler(object):
    """A class representing a reservoir sampler.

    The reservoir sampler will maintains a list of `k` items drawn
    randomly from a set of `N > k` items. The list is created and
    maintained so that we only need to store `k`items This is useful
    when `N` is very large or when storing all `N` items require a lot
    of memory. The algorithm is described by Knuth [#]_ but here we do
    a variation, so that each item may be picked several times.


    Attributes
    ----------
    rgen : object like :py:class:`numpy.random.RandomState`
        This is a container for the Mersenne Twister pseudo-random
        number generator as implemented in numpy, see the documentation
        of `RandomGenerator`.
    items : integer
        The number of items seen so far, i.e. the current `N`.
    reservoir : list
        The items we have stored.
    length : integer
        The maximum number of items to store in the reservoir
        (i.e. `k`).
    returnidx : integer
        This is the index of the item to return if we are requesting
        items from the reservoir.

    References
    ----------

    .. [#] The Art of Computer Programming.
    """
    def __init__(self, seed=0, length=10, rgen=None):
        """Initiate the reservoir.

        Parameters
        ----------
        seed : int, optional
            An integer used for seeding the generator.
        length : int, optional
            The maximum number of items to store.
        rgen : object like :py:class:`.RandomGenerator`
            In case we want to re-use a random generator object.
            If this is specified, the parameter `seed` is ignored.
        """
        if rgen is not None:
            self.rgen = rgen
        else:
            self.rgen = RandomState(seed=seed)
        self.items = 0
        self.reservoir = []
        self.length = length
        self.ret_idx = 0

    def append(self, new_item):
        """Try to add an item to the reservoir.

        Parameters
        ----------
        new_item : any type
            This is the item we try to add to the reservoir.
        """
        self.items += 1
        if self.items == 1:
            self.reservoir = [new_item for _ in range(self.length)]
        else:
            factor = 1.0/float(self.items)
            for i in range(self.length):
                if self.rgen.rand() < factor:
                    self.reservoir[i] = new_item

    def get_item(self):
        """This method will return one of the items from the reservoir.

        Returns
        -------
        out : any type
            Returns an item from the reservoir.
        """
        if self.ret_idx >= self.length:
            self.ret_idx = 0
            msg = ['Out of bounds in the reservoir sampler!']
            msg += ['Please increase the size of the reservoir.']
            msgtxt = '\n'.join(msg)
            logger.critical(msgtxt)
        ret = self.reservoir[self.ret_idx]
        self.ret_idx += 1
        return ret


class MockRandomGenerator(RandomGeneratorBase):
    """A **mock** random generator, useful **only for testing**.

    This class represents a random generator that can be used for
    testing algorithms. It will simply return numbers from a
    small list of pseudo-random numbers. This class is only useful
    for testing algorithms on different systems. It should *NEVER*
    be used for actual production runs!
    """
    def __init__(self, seed=0):
        """Initiate the random number generator.

        Parameters
        ----------
        seed : int, optional
            An integer used for seeding the generator if needed.
        """
        super().__init__(seed=seed)
        self.rgen = [0.78008018, 0.04459916, 0.76596775, 0.97676713,
                     0.53799598, 0.98657116, 0.36343553, 0.55356511,
                     0.03172585, 0.48984682, 0.73416687, 0.98453452,
                     0.55129902, 0.40598753, 0.59448394, 0.26823255,
                     0.31168372, 0.05072849, 0.44876368, 0.94301709]
        self.length = len(self.rgen)
        self.randint = self.seed
        logger.critical('You are using a "mock" random generator!\n')

    def rand(self, shape=1):
        """Draw random numbers in [0, 1).

        Parameters
        ----------
        shape : int
            Number of numbers to draw

        Returns
        -------
        out : float
            Pseudo random number in [0, 1)
        """
        numbers = []
        for _ in range(shape):
            if self.seed >= self.length:
                self.seed = 0
            numbers.append(self.rgen[self.seed])
            self.seed += 1
        return np.array(numbers)

    def random_integers(self, low, high):
        """Return random integers in [low, high].

        Parameters
        ----------
        low : int
            This is the lower limit
        high : int
            This is the upper limit

        Returns
        -------
        out : int
            This is a pseudo random integer in [low, high]
        """
        idx = self.rand()*(high-low+1)
        return int(idx) + low

    def normal(self, loc=0.0, scale=1.0, size=None):
        """Return values from a normal distribution.

        Parameters
        ----------
        loc : float, optional
            The mean of the distribution
        scale : float, optional
            The standard deviation of the distribution
        size : int, tuple of ints, optional
            Output shape, i.e. how many values to generate. Default is
            None which is just a single value.

        Returns
        -------
        out : float, numpy.array of floats
            The random numbers generated
        """
        if size is None:
            return self.rand(shape=1)
        else:
            numbers = np.zeros(size)
            for i in np.nditer(numbers, op_flags=['readwrite']):
                i[...] = self.rand(shape=1)[0]
            return numbers

    def multivariate_normal(self, mean, cov, cho=None, size=1):
        """Draw numbers from a multi-variate distribution.

        This is an attempt on speeding up the call of
        `RandomState.multivariate_normal` if we need to call it over and
        over again. Such repeated calling will do a SVD repeatedly,
        which is wasteful. In this function, this transform can be
        supplied and it is only estimated if it's not explicitly given.

        Parameters
        ----------
        mean : numpy array (1D, 2)
            Mean of the N-dimensional array
        cov : numpy array (2D, (2, 2))
            Covariance matrix of the distribution.
        cho : numpy.array (2D, (2, 2)), optional
            Cholesky factorization of cov. If not given,
            it will be calculated here.
        size : int, optional
            Number of samples to do.

        Returns
        -------
        out : float or numpy.array of floats size
            The random numbers drawn.

        See also
        --------
        numpy.random.multivariate_normal
        """
        norm = self.normal(loc=0.0, scale=1.0, size=2*size)
        norm = norm.reshape(size, 2)
        meanm = np.array([mean, ] * size)
        return 0.01*(meanm + norm)


def create_random_generator(settings):
    """This will initiate a random generator.

    Parameters
    ----------
    settings : dict
        This is the dict used for creating the random generator.
        Currently, we will actually just look for a seed value.

    Returns
    -------
    out : object like :py:class:`.RandomGenerator`
        The random generator created.
    """
    if 'seed' not in settings:
        seed = 0
        msg = 'No seed given, setting it to "0"'
        logger.info(msg)
    else:
        seed = settings['seed']
    rgen = settings.get('rgen', None)
    if rgen is not None and rgen == 'mock':
        return MockRandomGenerator(seed=seed)
    else:
        return RandomGenerator(seed=seed)
