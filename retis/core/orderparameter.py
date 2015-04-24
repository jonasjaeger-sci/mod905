# -*- coding: utf-8 -*-
"""
This file contain a class to represent an order parameter
"""
#import numpy as np
import warnings

__all__ = ['OrderParameter', 'OrderParameterPosition']

class OrderParameter(object):
    """
    OrderParameter(object)

    This class represents an order parameter. The order parameter
    is assumed to be a function that can uniquely be determined by
    the system object and its attributes.

    The order parameter implements __call__ so it can be calculated
    using OrderParameter(System)

    Attributes
    ----------
    desc : string
        This is a short description of the order parameter
    name : string
        A name for the order parameter (useful for output)
    """
    def __init__(self, name, desc='General order parameter'):
        """
        Initialize the OrderParameter object

        Parameters
        ----------
        name : string
            The name for the order parameter
        desc : string
            Short description of the order parameter
        """
        self.name = name
        self.desc = desc

    def calculate(self, system):
        """
        This function calculates the order parameter

        Parameters
        ----------
        system : object of type retis.core.system
            This object is used for the actual calculation, typically only
            system.particles.pos and/or system.particles.vel will be used.
            In some cases system.forcefield can also be used to include
            specific energies for the order parameter

        Returns
        -------
        out : float
            The order parameter
        """
        pass

    def calculate_velocity(self, system):
        """
        This function calculates the time derivative of the order parameter.

        Parameters
        ----------
        system : object of type retis.core.system
            This object is used for the actual calculation.

        Returns
        -------
        out : float
            The velocity of the order parameter
        """
        pass

    def parse_function(self, function):
        """
        This function is intended to parse an order parameter given as
        a string and return a function that can be used to evaluate
        the order parameter.

        Parameters
        ----------
        function : string
            A representation of the function
        """
        pass

    def __call__(self, system):
        """
        Method to conveniently call calculate and calculate_velocity.

        Parameters
        ----------
        system : object of type retis.core.system
            This object is used for the actual calculation.

        Returns
        -------
        out[0] : float
            The order parameter
        out[1] : float
            The velocity of the order parameter
        """
        orderp = self.calculate(system)
        orderv = self.calculate_velocity(system)
        return orderp, orderv

    def __str__(self):
        """
        Return a simple string representation of the order parameter
        """
        msg = ['Order parameter {}'.format(self.name)]
        msg += ['{}'.format(self.desc)]
        return '\n'.join(msg)


class OrderParameterPosition(OrderParameter):
    """
    This class defines a very simple order parameter which is just
    the position of a given particle.
    """
    def __init__(self, name, index, dim='x', periodic=False):
        """
        Initialize the OrderParameter object

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
            This determines if periodic boundary conditions should be applied
            to the position.
        """
        description = 'Position of particle {} (dim: {})'.format(index, dim)
        super(OrderParameterPosition, self).__init__(name, desc=description)
        self.periodic = periodic
        self.index = index
        dims = {'x': 0, 'y': 1, 'z': 2}
        try:
            self.dim = dims[dim]
        except KeyError:
            warnings.warn('Unknown dimension {} requested'.format(dim))
            raise

    def calculate(self, system):
        """
        This function calculates the order parameter. Here, the order
        parameter is just the coordinate of one of the particles.

        Parameters
        ----------
        system : object of type retis.core.system
            This object is used for the actual calculation, typically only
            system.particles.pos and/or system.particles.vel will be used.
            In some cases system.forcefield can also be used to include
            specific energies for the order parameter

        Returns
        -------
        out : float
            The order parameter
        """
        pos = system.particles.pos[self.index]
        if self.periodic:
            box = system.box
            pos = box.pbc_wrap(pos)
        if system.get_dim() == 1:
            return pos
        else:
            return pos[self.dim]

    def calculate_velocity(self, system):
        """
        This function calculates the time derivative of the order parameter.
        For this order parameter we just return the velocity.

        Parameters
        ----------
        system : object of type retis.core.system
            This object is used for the actual calculation.

        Returns
        -------
        out : float
            The velocity of the order parameter
        """
        vel = system.particles.vel[self.index]
        if system.get_dim() == 1:
            return vel
        else:
            return vel[self.dim]
