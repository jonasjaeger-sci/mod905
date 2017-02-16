# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""This file defines the order parameter used for the WCA example.
"""
import logging
import numpy as np
from pyretis.orderparameter import OrderParameter
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


class OrderXY(OrderParameter):
    """OrderXY(OrderParameter).

    This class defines a 2D order parameter such that x + y = constant.

    Attributes
    ----------
    index : integer
        This selects the particle to use for the order parameter.
    periodic : boolean
        This determines if periodic boundaries should be applied to
        the position or not.
    """

    def __init__(self, index):
        """Initialize the order parameter.

        Parameters
        ----------
        index : tuple of ints
            This is the indices of the atom we will use the position of.
        periodic : boolean, optional
            This determines if periodic boundary conditions should be
            applied to the position.
        """
        super().__init__(description='2D->1D projection')
        self.index = index
        x1 = 0.2
        y1 = 0.4
        x0 = -0.2
        y0 = -0.4
        self.x0 = x0
        self.y0 = y0
        self.origin = np.array([x0, y0])
        self.vec = np.array([x1 - x0, y1 - y0])
        self.vec /= np.sqrt(np.dot(self.vec, self.vec))

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
        pos = system.particles.pos[self.index]
        x = pos[0]
        y = pos[1]
        vec = np.array([x - self.x0, y - self.y0])
        proj = np.dot(vec, self.vec)
        return proj
