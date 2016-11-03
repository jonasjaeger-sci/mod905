# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""This file contains classes to represent order parameters.

The order parameters are assumed to all be completely determined
by the system properties and they will all return at least two
values - the order parameter and the rate of change in the order
parameter (i.e. its velocity).

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

OrderParameter
    Base class for the order parameters.

OrderParameterPosition
    A class for a simple position dependent order parameter.

OrderParameterDistance
    A class for a particle-particle distance order parameter.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

order_factory
    A method to create order parameters from settings.
"""
import logging
import numpy as np
from pyretis.core.common import generic_factory
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['OrderParameter', 'OrderParameterPosition',
           'order_factory']


def order_factory(settings):
    """Create order parameters according to the given settings.

    This function is included as a convenient way of setting up and
    selecting the order parameter.

    Parameters
    ----------
    settings : dict
        This defines how we set up and select the order parameter.

    Returns
    -------
    out : object like `OrderParameter`.
        An object representing the orderparameter.
    """
    factory_map = {'orderparameter': {'cls': OrderParameter},
                   'orderparameterposition': {'cls': OrderParameterPosition},
                   'orderparameterdistance': {'cls': OrderParameterDistance}}
    return generic_factory(settings, factory_map, name='orderparameter')


class OrderParameter(object):
    """OrderParameter(object).

    This class represents an order parameter. The order parameter
    is assumed to be a function that can uniquely be determined by
    the system object and its attributes.

    The order parameter implements `__call__` so it can be calculated
    using `OrderParameter(System)`.

    Attributes
    ----------
    desc : string
        This is a short description of the order parameter.
    name : string
        A name for the order parameter (useful for output).
    extra : list of functions
        This is a list of extra order parameters to calculate.
        We will assume that this list contains functions that all
        accept an object like `System` from `pyretis.core.system`
        as input and returns a single float.
    """

    def __init__(self, name, desc='General order parameter'):
        """Initialize the OrderParameter object.

        Parameters
        ----------
        name : string
            The name for the order parameter.
        desc : string
            Short description of the order parameter.
        """
        self.name = name
        self.desc = desc
        self.extra = []

    def calculate(self, system):
        """Calculate the order parameter and return it.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`
            This object is used for the actual calculation, typically
            only `system.particles.pos` and/or `system.particles.vel`
            will be used. In some cases system.forcefield can also be
            used to include specific energies for the order parameter.

        Returns
        -------
        out : float
            The order parameter.
        """
        raise NotImplementedError

    def calculate_velocity(self, system):
        """Calculate the time derivative of the order parameter.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`
            This object is used for the actual calculation, typically
            only `system.particles.pos` and/or `system.particles.vel`
            will be used. In some cases system.forcefield can also be
            used to include specific energies for the order parameter.

        Returns
        -------
        out : float
            The velocity of the order parameter.
        """
        raise NotImplementedError

    def __call__(self, system):
        """Conveniently call `calculate` and `calculate_velocity`.

        It will also call the additional order parameters defined in
        `self.extra`, if any.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`
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
        orderv = self.calculate_velocity(system)
        ret_val = [orderp, orderv]
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
        `pyretis.core.system.System` as parameter.

        Parameters
        ----------
        func : function
            Extra function for calculation of an extra order parameter.
            It is assumed to accept only a `pyretis.core.system.System`
            object as its parameter.

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
        msg = ['Order parameter {}'.format(self.name)]
        msg += ['{}'.format(self.desc)]
        return '\n'.join(msg)


class OrderParameterPosition(OrderParameter):
    """OrderParameterPosition(OrderParameter).

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

    def __init__(self, name, index, dim='x', periodic=False):
        """Initialize `OrderParameterPosition`.

        Parameters
        ----------
        name : string
            The name for the order parameter
        index : int
            This is the index of the atom we will use the position of.
        dim : string
            This select what dimension we should consider,
            it should equal 'x', 'y' or 'z'.
        periodic : boolean, optional
            This determines if periodic boundary conditions should be
            applied to the position.
        """
        description = 'Position of particle {} (dim: {})'.format(index, dim)
        super(OrderParameterPosition, self).__init__(name, desc=description)
        self.periodic = periodic
        self.index = index
        dims = {'x': 0, 'y': 1, 'z': 2}
        try:
            self.dim = dims[dim]
        except KeyError:
            msg = 'Unknown dimension {} requested'.format(dim)
            logger.critical(msg)
            raise

    def calculate(self, system):
        """Calculate the order parameter.

        Here, the order parameter is just the coordinate of one of the
        particles.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`
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
        system : object like `System` from `pyretis.core.system`
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
    """OrderParameterDistance(OrderParameter).

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

    def __init__(self, name, index, periodic=True):
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
        description = '{} distance particles {} and {}'.format(pbc,
                                                               index[0],
                                                               index[1])
        super(OrderParameterDistance, self).__init__(name, desc=description)
        self.periodic = periodic
        self.index = index

    def calculate(self, system):
        """Calculate the order parameter.

        Here, the order parameter is just the distance between two
        particles.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`
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
        system : object like `System` from `pyretis.core.system`
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
