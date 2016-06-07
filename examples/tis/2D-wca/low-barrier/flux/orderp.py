# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""This file defines the order parameter used for the WCA example.
"""
import logging
import numpy as np
from pyretis.core.orderparameter import OrderParameter
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


class OrderParameterWCAJCP1(OrderParameter):
    """OrderParameterWCAJCP1(OrderParameter).

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
        """Initialize the order parameter.

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
        super(OrderParameterWCAJCP1, self).__init__(name, desc=description)
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
        r = np.sqrt(np.dot(delta, delta))
	potential_func = system.forcefield.potential[1]
	return r

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
