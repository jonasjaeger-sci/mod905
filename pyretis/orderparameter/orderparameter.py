# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""This file contains classes to represent order parameters.

The order parameters are assumed to all be completely determined
by the system properties and they will all return at least two
values - the order parameter and the rate of change in the order
parameter (i.e. its velocity).

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

OrderParameter (:py:class:`.OrderParameter`)
    Base class for the order parameters.

OrderParameterPosition (:py:class:`.OrderParameterPosition`)
    A class for a simple position dependent order parameter.

OrderParameterDistance (:py:class:`.OrderParameterDistance`)
    A class for a particle-particle distance order parameter.
"""
from abc import abstractmethod
import logging
import numpy as np
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['OrderParameter', 'OrderParameterPosition',
           'OrderParameterDistance']


class OrderParameter(object):
    """Base class for order parameters.

    This class represents an order parameter and other collective
    variables (CV's). The order parameter is assumed to be a
    function that can uniquely be determined by the system object
    and its attributes.

    Attributes
    ----------
    description : string
        This is a short description of the order parameter.
    extra : list of functions
        This is a list of extra order parameters to calculate.
        We will assume that this list contains functions that all
        accept an object like :py:class:`.System` as input and return
        a single float.
    """

    def __init__(self, description='Generic order parameter'):
        """Initialize the OrderParameter object.

        Parameters
        ----------
        desc : string
            Short description of the order parameter.
        """
        self.description = description
        self.extra = []

    @abstractmethod
    def calculate(self, system):
        """Calculate the main order parameter and return it.

        This is defined as a method just to ensure that at least this
        method will be defined in the different order parameters.

        Parameters
        ----------
        system : object like :py:class:`.System`
            This object is used for the actual calculation, typically
            only `system.particles.pos` and/or `system.particles.vel`
            will be used. In some cases system.forcefield can also be
            used to include specific energies for the order parameter.

        Returns
        -------
        out : float
            The order parameter.
        """
        pass

    def calculate_all(self, system):
        """Call :py:meth:`.calculate` and calculate other CV's.

        It will also call the additional order parameters defined in
        `self.extra`, if any.

        Parameters
        ----------
        system : object like :py:class:`.System`
            This object is used for the actual calculation.

        Returns
        -------
        out[0] : float
            The order parameter.
        out[1] : float
            The velocity of the order parameter.
        out[2, ...] : float(s)
            Additional order parameters, if any.
        """
        orderp = self.calculate(system)
        ret_val = [orderp]
        if self.extra is None:
            return ret_val
        else:
            for func in self.extra:
                try:
                    extra = func(system)
                except TypeError:
                    extra = float('nan')
                ret_val.append(extra)
            return ret_val

    def add_orderparameter(self, func):
        """Add an extra order parameter to calculate.

        The given function should accept an object like
        py:class:`.System` as parameter.

        Parameters
        ----------
        func : function
            Extra function for calculation of an extra order parameter.
            It is assumed to accept only a :py:class:`.System` object
            as its parameter.

        Returns
        -------
        out : boolean
            Return True if we added the function, False otherwise.
        """
        if not callable(func):
            msg = 'The given function is not callable, it will not be added!'
            logger.warning(msg)
            return False
        else:
            self.extra.append(func)
            return True

    def __str__(self):
        """Return a simple string representation of the order parameter."""
        return 'Order parameter: "{}"\n{}'.format(self.__class__.__name__,
                                                  self.description)


class OrderParameterPosition(OrderParameter):
    """A positional order parameter.

    This class defines a very simple order parameter which is just
    the position of a given particle.

    Attributes
    ----------
    name : string
        A human readable name for the order parameter
    index : integer
        This is the index of the atom which will be used, i.e.
        system.particles.pos[index] will be used.
    dim : integer
        This is the dimension of the coordinate to use.
        0, 1 or 2 for 'x', 'y' or 'z'.
    periodic : boolean
        This determines if periodic boundaries should be applied to
        the position or not.
    """

    def __init__(self, index, dim='x', periodic=False):
        """Initialize `OrderParameterPosition`.

        Parameters
        ----------
        index : int
            This is the index of the atom we will use the position of.
        dim : string
            This select what dimension we should consider,
            it should equal 'x', 'y' or 'z'.
        periodic : boolean, optional
            This determines if periodic boundary conditions should be
            applied to the position.
        """
        txt = 'Position of particle {} (dim: {})'.format(index, dim)
        super().__init__(description=txt)
        self.periodic = periodic
        self.index = index
        dims = {'x': 0, 'y': 1, 'z': 2}
        try:
            self.dim = dims[dim]
        except KeyError:
            msg = 'Unknown dimension {} requested'.format(dim)
            logger.critical(msg)
            raise
        self.add_orderparameter(self.calculate_velocity)

    def calculate(self, system):
        """Calculate the order parameter.

        Here, the order parameter is just the coordinate of one of the
        particles.

        Parameters
        ----------
        system : object like :py:class:`.System`
            This object is used for the actual calculation, typically
            only `system.particles.pos` and/or `system.particles.vel`
            will be used. In some cases `system.forcefield` can also be
            used to include specific energies for the order parameter.

        Returns
        -------
        out : float
            The order parameter.
        """
        particles = system.particles
        pos = particles.pos[self.index]
        lmb = pos[self.dim]
        if self.periodic:
            return system.box.pbc_coordinate_dim(lmb, self.dim)
        else:
            return lmb

    def calculate_velocity(self, system):
        """Calculate the time derivative of the order parameter.

        For this order parameter we just return the velocity.

        Parameters
        ----------
        system : object like :py:class:`.System`
            This object is used for the actual calculation.

        Returns
        -------
        out : float
            The velocity of the order parameter
        """
        particles = system.particles
        vel = particles.vel[self.index]
        return vel[self.dim]


class OrderParameterDistance(OrderParameter):
    """A distance order parameter.

    This class defines a very simple order parameter which is just
    the scalar distance between two particles.

    Attributes
    ----------
    name : string
        A human readable name for the order parameter
    index : tuple of integers
        These are the indices used for the two particles.
        `system.particles.pos[index[0]]` and
        `system.particles.pos[index[1]]` will be used.
    periodic : boolean
        This determines if periodic boundaries should be applied to
        the position or not.
    """

    def __init__(self, index, periodic=True):
        """Initialize `OrderParameterDistance`.

        Parameters
        ----------
        name : string
            The name for the order parameter
        index : tuple of ints
            This is the indices of the atom we will use the position of.
        periodic : boolean, optional
            This determines if periodic boundary conditions should be
            applied to the position.
        """
        pbc = 'Periodic' if periodic else 'Non-periodic'
        txt = '{} distance particles {} and {}'.format(pbc, index[0],
                                                       index[1])
        super().__init__(description=txt)
        self.periodic = periodic
        self.index = index
        self.add_orderparameter(self.calculate_velocity)

    def calculate(self, system):
        """Calculate the order parameter.

        Here, the order parameter is just the distance between two
        particles.

        Parameters
        ----------
        system : object like :py:class:`.System`
            This object is used for the actual calculation, typically
            only ``system.particles.pos`` and/or
            ``system.particles.vel`` will be used. In some cases
            ``system.forcefield`` can also be used to include specific
            energies for the order parameter.

        Returns
        -------
        out : float
            The order parameter.
        """
        particles = system.particles
        delta = particles.pos[self.index[1]] - particles.pos[self.index[0]]
        if self.periodic:
            delta = system.box.pbc_dist_coordinate(delta)
        return np.sqrt(np.dot(delta, delta))

    def calculate_velocity(self, system):
        """Calculate the time derivative of the order parameter.

        For this order parameter it is given by the time derivative of
        the distance vector.

        Parameters
        ----------
        system : object like :py:class:`.System`
            This object is used for the actual calculation.

        Returns
        -------
        out : float
            The velocity of the order parameter
        """
        particles = system.particles
        delta = particles.pos[self.index[1]] - particles.pos[self.index[0]]
        if self.periodic:
            delta = system.box.pbc_dist_coordinate(delta)
        lamb = np.sqrt(np.dot(delta, delta))
        delta_v = particles.vel[self.index[1]] - particles.vel[self.index[0]]
        return np.dot(delta, delta_v) / lamb
