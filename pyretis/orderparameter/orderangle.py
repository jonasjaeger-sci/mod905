# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""This file contains classes to represent angle order parameters.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

OrderParameterAngle (:py:class:`.OrderParameterAngle`)
    An angle defined by three atoms.
"""
import logging
import numpy as np
from pyretis.orderparameter.orderparameter import OrderParameter
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['OrderParameterAngle']


class OrderParameterAngle(OrderParameter):
    """An angle order parameter.

    This class defines an order parameter which is an angle
    ABC for 3 particles A, B and C. The angle is defined as the
    angle given by the two vectors BA and BC.

    Attributes
    ----------
    index : integer
        This is the index of the atom which will be used, i.e.
        system.particles.pos[index] will be used.
    periodic : boolean
        This determines if periodic boundaries should be applied to
        the position or not.
    """

    def __init__(self, index, periodic=False):
        """Initialize `OrderParameterAngle`.

        Parameters
        ----------
        index : int
            This is the index of the atom we will use the position of.
        periodic : boolean, optional
            This determines if periodic boundary conditions should be
            applied to the distance vectors.
        """
        try:
            if len(index) != 3:
                msg = ('Wrong number of atoms for angle definition. '
                       'Expected 3 got {}'.format(len(index)))
                logger.error(msg)
                raise ValueError(msg)
        except TypeError:
            msg = 'Angle should be defined as a tuple/list of integers!'
            logger.error(msg)
            raise TypeError(msg)
        txt = 'Angle between particles {}, {} and {}'.format(index[0],
                                                             index[1],
                                                             index[2])
        super().__init__(description=txt)
        self.periodic = periodic
        self.index = [int(i) for i in index]

    def calculate(self, system):
        """Calculate the order parameter.

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
        pos = system.particles.pos
        vector_ba = pos[self.index[1]] - pos[self.index[0]]
        vector_bc = pos[self.index[1]] - pos[self.index[2]]
        if self.periodic:
            vector_ba = system.box.pbc_dist_coordinate(vector_ba)
            vector_bc = system.box.pbc_dist_coordinate(vector_bc)
        cosabc = (np.dot(vector_ba, vector_bc) /
                  np.sqrt(np.dot(vector_ba, vector_ba) *
                          np.dot(vector_bc, vector_bc)))
        angleabc = np.arccos(cosabc)
        return [angleabc]
