# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""This file contains classes to represent order parameters.

The order parameters are assumed to all be completely determined
by the system properties and they will all return at least one
value - the order parameter itself. The order parameters can also
return several order parameters which can be used for further analysis.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

OrderParameter (:py:class:`.OrderParameter`)
    Base class for the order parameters.

Position (:py:class:`.Position`)
    An order parameter equal to the position of a particle.

Velocity (:py:class:`.Velocity`)
    An order parameter equal to the velocity of a particle.

Distance (:py:class:`.Distance`)
    A class for a particle-particle distance order parameter.

Distancevel (:py:class:`.Distancevel`)
    A class for the rate of change in a particle-particle distance
    order parameter.

CompositeOrderParameter (:py:class:`.CompositeOrderParameter`)
    A class for an order parameter which is made up of several order
    parameters, i.e. of several objects like
    :py:class:`.OrderParameter`.

PositionVelocity (:py:class:`.PositionVelocity`)
    An order parameter which is equal to the composition of
    :py:class:`.Position` and
    :py:class:`.Velocity`.

DistanceVelocity (:py:class:`.DistanceVelocity`)
    An order parameter which is equal to the composition of
    :py:class:`.Distance` and :py:class:`.Distancevel`.

"""
from abc import abstractmethod
import logging
import numpy as np
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
logger.addHandler(logging.NullHandler())


__all__ = [
    'OrderParameter',
    'Position',
    'Velocity',
    'Distance',
    'Distancevel',
    'DistanceVelocity',
    'PositionVelocity',
    'CompositeOrderParameter'
]


class OrderParameter:
    """Base class for order parameters.

    This class represents an order parameter and other collective
    variables. The order parameter is assumed to be a function
    that can uniquely be determined by the system object and its
    attributes.

    Attributes
    ----------
    description : string
        This is a short description of the order parameter.
    velocity_dependent : boolean
        This flag indicates whether or not the order parameter
        depends on the velocity direction. If so, we need to
        recalculate the order parameter when reversing trajectories.

    """

    def __init__(self, description='Generic order parameter', velocity=False):
        """Initialise the OrderParameter object.

        Parameters
        ----------
        description : string
            Short description of the order parameter.

        """
        self.description = description
        self.velocity_dependent = velocity
        if self.velocity_dependent:
            logger.debug(
                'Order parameter "%s" was marked as velocity dependent.',
                self.description
            )

    @abstractmethod
    def calculate(self, system):
        """Calculate the main order parameter and return it.

        All order parameters should implement this method as
        this ensures that the order parameter can be calculated.

        Parameters
        ----------
        system : object like :py:class:`.System`
            This object contains the information needed to calculate
            the order parameter.

        Returns
        -------
        out : list of floats
            The order parameter(s). The first order parameter returned
            is used as the progress coordinate in path sampling
            simulations!

        """
        return

    def __str__(self):
        """Return a simple string representation of the order parameter."""
        msg = [
            'Order parameter: "{}"'.format(self.__class__.__name__),
            '{}'.format(self.description),
        ]
        if self.velocity_dependent:
            msg.append('This order parameter is velocity dependent.')
        return '\n'.join(msg)


class Position(OrderParameter):
    """A positional order parameter.

    This class defines a very simple order parameter which is just
    the position of a given particle.

    Attributes
    ----------
    index : integer
        This is the index of the atom which will be used, i.e.
        ``system.particles.pos[index]`` will be used.
    dim : integer
        This is the dimension of the coordinate to use.
        0, 1 or 2 for 'x', 'y' or 'z'.
    periodic : boolean
        This determines if periodic boundaries should be applied to
        the position or not.

    """

    def __init__(self, index, dim='x', periodic=False):
        """Initialise the order parameter.

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
        super().__init__(description=txt, velocity=False)
        self.periodic = periodic
        self.index = index
        self.dim = {'x': 0, 'y': 1, 'z': 2}.get(dim, None)
        if self.dim is None:
            msg = 'Unknown dimension {} requested'.format(dim)
            logger.critical(msg)
            raise ValueError(msg)

    def calculate(self, system):
        """Calculate the position order parameter.

        Parameters
        ----------
        system : object like :py:class:`.System`
            The object containing the positions.

        Returns
        -------
        out : list of floats
            The position order parameter.

        """
        particles = system.particles
        pos = particles.pos[self.index]
        lamb = pos[self.dim]
        if self.periodic:
            lamb = system.box.pbc_coordinate_dim(lamb, self.dim)
        return [lamb]


class Velocity(OrderParameter):
    """Initialise the order parameter.

    This class defines a very simple order parameter which is just
    the velocity of a given particle.

    Attributes
    ----------
    index : integer
        This is the index of the atom which will be used, i.e.
        ``system.particles.vel[index]`` will be used.
    dim : integer
        This is the dimension of the coordinate to use.
        0, 1 or 2 for 'x', 'y' or 'z'.

    """

    def __init__(self, index, dim='x'):
        """Initialise the order parameter.

        Parameters
        ----------
        index : int
            This is the index of the atom we will use the velocity of.
        dim : string
            This select what dimension we should consider,
            it should equal 'x', 'y' or 'z'.

        """
        txt = 'Velocity of particle {} (dim: {})'.format(index, dim)
        super().__init__(description=txt, velocity=True)
        self.index = index
        self.dim = {'x': 0, 'y': 1, 'z': 2}.get(dim, None)
        if self.dim is None:
            logger.critical('Unknown dimension %s requested', dim)
            raise ValueError

    def calculate(self, system):
        """Calculate the velocity order parameter.

        Parameters
        ----------
        system : object like :py:class:`.System`
            The object containing the velocities.

        Returns
        -------
        out : list of floats
            The velocity order parameter.

        """
        return [system.particles.vel[self.index][self.dim]]


def _verify_pair(index):
    """Check that the given index contains a pair."""
    try:
        if len(index) != 2:
            msg = ('Wrong number of atoms for pair definition. '
                   'Expected 2 got {}'.format(len(index)))
            logger.error(msg)
            raise ValueError(msg)
    except TypeError:
        msg = 'Atom pair should be defined as a tuple/list of integers.'
        logger.error(msg)
        raise TypeError(msg)


class Distance(OrderParameter):
    """A distance order parameter.

    This class defines a very simple order parameter which is just
    the scalar distance between two particles.

    Attributes
    ----------
    index : tuple of integers
        These are the indices used for the two particles.
        `system.particles.pos[index[0]]` and
        `system.particles.pos[index[1]]` will be used.
    periodic : boolean
        This determines if periodic boundaries should be applied to
        the distance or not.

    """

    def __init__(self, index, periodic=True):
        """Initialise order parameter.

        Parameters
        ----------
        index : tuple of ints
            This is the indices of the atom we will use the position of.
        periodic : boolean, optional
            This determines if periodic boundary conditions should be
            applied to the position.

        """
        _verify_pair(index)
        pbc = 'Periodic' if periodic else 'Non-periodic'
        txt = '{} distance, particles {} and {}'.format(
            pbc,
            index[0],
            index[1]
        )
        super().__init__(description=txt, velocity=False)
        self.periodic = periodic
        self.index = index

    def calculate(self, system):
        """Calculate the order parameter.

        Here, the order parameter is just the distance between two
        particles.

        Parameters
        ----------
        system : object like :py:class:`.System`
            The object containing the positions and box used for the
            calculation.

        Returns
        -------
        out : list of floats
            The distance order parameter.

        """
        particles = system.particles
        delta = particles.pos[self.index[1]] - particles.pos[self.index[0]]
        if self.periodic:
            delta = system.box.pbc_dist_coordinate(delta)
        lamb = np.sqrt(np.dot(delta, delta))
        return [lamb]


class Distancevel(OrderParameter):
    """A rate of change of the distance order parameter.

    This class defines a very simple order parameter which is just
    the time derivative of the scalar distance between two particles.

    Attributes
    ----------
    index : tuple of integers
        These are the indices used for the two particles.
        `system.particles.pos[index[0]]` and
        `system.particles.pos[index[1]]` will be used.
    periodic : boolean
        This determines if periodic boundaries should be applied to
        the distance or not.

    """

    def __init__(self, index, periodic=True):
        """Initialise the order parameter.

        Parameters
        ----------
        index : tuple of ints
            This is the indices of the atom we will use the position of.
        periodic : boolean, optional
            This determines if periodic boundary conditions should be
            applied to the position.

        """
        _verify_pair(index)
        pbc = 'Periodic' if periodic else 'Non-periodic'
        txt = '{} rate-of-change-distance, particles {} and {}'.format(
            pbc,
            index[0],
            index[1]
        )
        super().__init__(description=txt, velocity=True)
        self.periodic = periodic
        self.index = index

    def calculate(self, system):
        """Calculate the order parameter.

        Here, the order parameter is just the distance between two
        particles.

        Parameters
        ----------
        system : object like :py:class:`.System`
            The object containing the positions and box used for the
            calculation.

        Returns
        -------
        out : list of floats
            The rate-of-chang of the distance order parameter.

        """
        particles = system.particles
        delta = particles.pos[self.index[1]] - particles.pos[self.index[0]]
        if self.periodic:
            delta = system.box.pbc_dist_coordinate(delta)
        lamb = np.sqrt(np.dot(delta, delta))
        # Add the velocity as an additional collective variable:
        delta_v = particles.vel[self.index[1]] - particles.vel[self.index[0]]
        cv1 = np.dot(delta, delta_v) / lamb
        return [cv1]


class CompositeOrderParameter(OrderParameter):
    """A composite order parameter.

    This class represents a composite order parameter. It does not
    actually calculate order parameters itself, but it has references
    to several objects like :py:class:`.OrderParameter` which it can
    use to obtain the order parameters. Note that the first one of
    these objects will be interpreted as the main progress coordinate
    in path sampling simulations.

    Attributes
    ----------
    extra : list of objects like :py:class:`OrderParameter`
        This is a list of order parameters to calculate.

    """

    def __init__(self, order_parameters=None):
        """Set up the composite order parameter.

        Parameters
        ----------
        order_parameters : list of objects like :py:class:`.OrderParameter`
            A list of order parameters we can add.

        """
        super().__init__(description='Combined order parameter',
                         velocity=False)
        self.order_parameters = []
        if order_parameters is not None:
            for order_function in order_parameters:
                self.add_orderparameter(order_function)

    def calculate(self, system):
        """Calculate the main order parameter and return it.

        This is defined as a method just to ensure that at least this
        method will be defined in the different order parameters.

        Parameters
        ----------
        system : object like :py:class:`.System`
            This object contains the information needed to calculate
            the order parameter.

        Returns
        -------
        out : list of floats
            The order parameter(s). The first order parameter returned
            is assumed to be the progress coordinate for path sampling
            simulations.

        """
        all_order = []
        for order_function in self.order_parameters:
            all_order.extend(order_function.calculate(system))
        return all_order

    def add_orderparameter(self, order_function):
        """Add an extra order parameter to calculate.

        Parameters
        ----------
        order_function : object like :py:class:`.OrderParameter`
            An object we can use to calculate the order parameter.

        Returns
        -------
        out : boolean
            Return True if we added the function, False otherwise.

        """
        # We check that the ``calculate`` method is present and callable.
        for func in ('calculate', ):
            objfunc = getattr(order_function, func, None)
            name = order_function.__class__.__name__
            if not objfunc:
                msg = 'Missing method "{}" in order parameter {}'.format(
                    func,
                    name,
                )
                logger.error(msg)
                raise ValueError(msg)
            if not callable(objfunc):
                msg = '"{}" in order parameter {} is not callable!'.format(
                    func,
                    name,
                )
                raise ValueError(msg)
        self.velocity_dependent |= order_function.velocity_dependent
        if self.velocity_dependent:
            logger.debug(
                'Order parameter "%s" was marked as velocity dependent.',
                self.description
            )
        self.order_parameters.append(order_function)
        return True

    def __str__(self):
        """Return a simple string representation of the order parameter."""
        txt = ['Order parameter, combination of:']
        for i, order in enumerate(self.order_parameters):
            txt.append('{}: {}'.format(i, str(order)))
        msg = '\n'.join(txt)
        return msg


class PositionVelocity(CompositeOrderParameter):
    """An order parameter equal to the position & velocity of a given atom."""

    def __init__(self, index, dim='x', periodic=False):
        """Initialise the order parameter.

        Parameters
        ----------
        index : int
            This is the index of the atom we will use the position
            and velocity of.
        dim : string
            This select what dimension we should consider,
            it should equal 'x', 'y' or 'z'.
        periodic : boolean, optional
            This determines if periodic boundary conditions should be
            applied to the position.

        """
        position = Position(index, dim=dim, periodic=periodic)
        velocity = Velocity(index, dim=dim)
        orderparameters = [position, velocity]
        super().__init__(order_parameters=orderparameters)


class DistanceVelocity(CompositeOrderParameter):
    """An order parameter equal to a distance and its rate of change."""

    def __init__(self, index, periodic=True):
        """Initialise the order parameter.

        Parameters
        ----------
        index : tuple of integers
            These are the indices used for the two particles.
            `system.particles.pos[index[0]]` and
            `system.particles.pos[index[1]]` will be used.
        periodic : boolean, optional
            This determines if periodic boundary conditions should be
            applied to the position.

        """
        position = Distance(index, periodic=periodic)
        velocity = Distancevel(index, periodic=periodic)
        orderparameters = [position, velocity]
        super().__init__(order_parameters=orderparameters)
