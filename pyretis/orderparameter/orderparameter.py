# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""This file contains classes to represent order parameters.

The order parameters are assumed to all be completely determined
by the system properties and they will all return at least one
value - the order parameter it self. The order parameters can also
return several order parameters which can be used for further analysis.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

OrderParameter (:py:class:`.OrderParameter`)
    Base class for the order parameters.

OrderParameterPosition (:py:class:`.OrderParameterPosition`)
    A class for a simple position dependent order parameter.

OrderParameterDistance (:py:class:`.OrderParameterDistance`)
    A class for a particle-particle distance order parameter.

CompositeOrderParameter (:py:class:`.CompositeOrderParameter`)
    A class for an order parameter which is made up of several order
    parameters, i.e. of several objects like
    :py:class:`.OrderParameter`.
"""
from abc import abstractmethod
import logging
import numpy as np
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['OrderParameter', 'OrderParameterPosition',
           'OrderParameterDistance']


class OrderParameter:
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
        """Initialise the OrderParameter object.

        Parameters
        ----------
        description : string
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
        out : list of floats
            The order parameter(s). The first order parameter returned
            is used as the progress coordinate in path sampling
            simulations!
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
        out : list of floats
            The order parameters(s),
        """
        ret_val = self.calculate(system)
        if not self.extra:
            return ret_val
        for func in self.extra:
            extra = func(system)
            ret_val.extend(extra)
        return ret_val

    def add_orderparameter(self, orderp):
        """Add an extra order parameter to calculate.

        The given function should accept an object like
        py:class:`.System` as parameter.

        Parameters
        ----------
        orderp : callable
            Extra function for calculation of an extra order parameter.
            It is assumed to accept only a :py:class:`.System` object
            as its parameter.

        Returns
        -------
        out : boolean
            Return True if we added the function, False otherwise.
        """
        if not callable(orderp):
            msg = 'The given method is not callable, it will not be added!'
            logger.warning(msg)
            return False
        self.extra.append(orderp)
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
        """Initialise `OrderParameterPosition`.

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
        out : list of float
            The order parameters, here the position and in addition
            (as a extra collective variable) the velocity.
        """
        particles = system.particles
        pos = particles.pos[self.index]
        lamb = pos[self.dim]
        if self.periodic:
            lamb = system.box.pbc_coordinate_dim(lamb, self.dim)
        # Also return the velocity as an additional collective
        # variable:
        vel = particles.vel[self.index]
        cv1 = vel[self.dim]
        return [lamb, cv1]


class OrderParameterDistance(OrderParameter):
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
        the position or not.
    """

    def __init__(self, index, periodic=True):
        """Initialise `OrderParameterDistance`.

        Parameters
        ----------
        index : tuple of ints
            This is the indices of the atom we will use the position of.
        periodic : boolean, optional
            This determines if periodic boundary conditions should be
            applied to the position.
        """
        try:
            if len(index) != 2:
                msg = ('Wrong number of atoms for distance definition. '
                       'Expected 2 got {}'.format(len(index)))
                logger.error(msg)
                raise ValueError(msg)
        except TypeError:
            msg = 'Distance should be defined as a tuple/list of integers!'
            logger.error(msg)
            raise TypeError(msg)
        pbc = 'Periodic' if periodic else 'Non-periodic'
        txt = '{} distance particles {} and {}'.format(pbc, index[0],
                                                       index[1])
        super().__init__(description=txt)
        self.periodic = periodic
        self.index = index

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
        out : list of floats
            The order parameter and the velocity as an additional
            collective variable.
        """
        particles = system.particles
        delta = particles.pos[self.index[1]] - particles.pos[self.index[0]]
        if self.periodic:
            delta = system.box.pbc_dist_coordinate(delta)
        lamb = np.sqrt(np.dot(delta, delta))
        # Add the velocity as an additional collective variable:
        delta_v = particles.vel[self.index[1]] - particles.vel[self.index[0]]
        cv1 = np.dot(delta, delta_v) / lamb
        return [lamb, cv1]


class CompositeOrderParameter(OrderParameter):
    """A composite order parameter

    This class represents a composite order parameter. It does not
    actually calculate order parameters itself, but it has references
    to several objects like :py:class:`.OrderParameter` which it can
    use to obtain the order parameters.

    Attributes
    ----------
    extra : list of objects like :py:class:`OrderParameter`
        This is a list of order parameters to calculate.
    """

    def __init__(self, order_parameters=None):
        """Just initialise.

        Parameters
        ----------
        order_parameters : list of objects like :py:class:`.OrderParameter`.
            A list of order parameters we can add.
        """
        super().__init__(description='Combined order parameter')
        self.extra = []
        if order_parameters is not None:
            for orderp in order_parameters:
                self.add_orderparameter(orderp)

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
        out : list of floats
            The order parameter(s). The first order parameter returned
            is used as the progress coordinate in path sampling
            simulations!
        """
        all_order = []
        for orderp in self.extra:
            all_order.extend(orderp.calculate_all(system))
        return all_order

    def calculate_all(self, system):
        """Identical to calculate, so just call it."""
        return self.calculate(system)

    def add_orderparameter(self, orderp):
        """Add an extra order parameter to calculate.

        Parameters
        ----------
        orderp : object like :py:class:`.OrderParameter`.
            An object we can use to calculate the order parameter.

        Returns
        -------
        out : boolean
            Return True if we added the function, False otherwise.
        """
        # We check that we can call .calculate() and .calculate_all():
        for func in ('calculate', 'calculate_all'):
            objfunc = getattr(orderp, func, None)
            name = orderp.__class__.__name__
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
        self.extra.append(orderp)
        return True

    def order_parameters(self):
        """Just return the order objects."""
        for i in self.extra:
            yield i

    def __str__(self):
        """Return a simple string representation of the order parameter."""
        txt = ['Order parameter, combination of:']
        for i, order in enumerate(self.extra):
            txt.append('{}: {}'.format(i, str(order)))
        msg = '\n'.join(txt)
        return msg
