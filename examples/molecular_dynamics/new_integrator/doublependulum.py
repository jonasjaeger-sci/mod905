# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""A collection of simple position dependent potentials.

This module defines some potential functions which are useful
as simple models.
"""
from __future__ import absolute_import
import logging
import numpy as np
from pyretis.forcefield.potential import PotentialFunction
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


class DoublePendulumn(PotentialFunction):
    r"""DoublePendulumn(PotentialFunction).

    Attributes
    ----------
    l1 : float
        Length of first wire
    l2 : float
        Length of second wire
    g : float
        The acceletration of gravity.
    """

    def __init__(self, l1=1.0, l2=1.0, g=1.0, desc='2D double pendulum'):
        """Initiate the one dimensional double well potential.

        Parameters
        ----------
        l1 : float, optional.
            Parameter for the potential.
        l1 : float, optional.
            Parameter for the potential.
        g : float, optional
            Parameter for the potential.
        desc : string, optional.
            Description of the force field.
        """
        super(DoublePendulumn, self).__init__(dim=2, desc=desc)
        self.params = {'g': g, 'l1': l1, 'l2': l2}
        self.l1 = l1
        self.l2 = l2
        self.g = g

    def potential(self, system):
        """Evaluate the potential energy.

        Parameters
        ----------
        system : object like `System`.
            The system we evaluate the potential for. Here, we
            make use of the positions only.

        Returns
        -------
        out : float
            The potential energy.
        """
        g = self.g
        pos = system.particles.pos
        m1 = system.particles.mass[0][0]
        m2 = system.particles.mass[1][0]
        y1 = -self.l1 * np.cos(pos[0][0])
        y2 = y1 - self.l2 * np.cos(pos[1][0])
        pot = m1*g*y1 + m2*g*y2
        return pot

    def force(self, system):
        """Evaluate forces for the double pendulum.

        Parameters
        ----------
        system : object like `System`.
            The system we evaluate the potential for. Here, we
            make use of the positions only.

        Returns
        -------
        out[0] : numpy.array
            The calculated force.
        out[1] : numpy.array
            The virial, currently not implemented for this potential
        """
        g = self.g
        l1 = self.l1
        l2 = self.l2
        pos = system.particles.pos
        vel = system.particles.vel
        m1 = system.particles.mass[0][0]
        m2 = system.particles.mass[1][0]
        theta1 = pos[0][0]
        theta2 = pos[1][0]
        sintheta1 = np.sin(theta1)
        costheta1 = np.cos(theta1)
        sintheta2 = np.sin(theta2)
        costheta2 = np.cos(theta2)
        dtheta1 = vel[0][0]
        dtheta2 = vel[1][0]
        denom = 2.0*m1 + m2 - m2*np.cos(2.0*theta1 - 2.0*theta2)
        atheta1 = -g*(2.0*m1 + m2)*sintheta1
        atheta1 += -m2*g*np.sin(theta1 - 2.0*theta2)
        atheta1 += (-2.0*np.sin(theta1 - theta2)*m2*
                    (dtheta2**2*l2 + dtheta1**2*l1*np.cos(theta1 - theta2)))
        atheta1 /= (l1 * denom)
        atheta2 = (dtheta1**2*l1*(m1 + m2) + g*(m1 + m2)*costheta1 +
                   dtheta2**2*l2*m2*np.cos(theta1 - theta2))
        atheta2 *= 2.0*np.sin(theta1 - theta2)
        atheta2 /= (l2 * denom)
        forces = np.zeros((2, self.dim))
        forces[0, 0] = atheta1
        forces[1, 0] = atheta2
        #print(forces)
        virial = np.zeros((self.dim, self.dim))  # just return zeros here
        return forces, virial

    def potential_and_force(self, system):
        """Evaluate the potential and the force.

        Parameters
        ----------
        system : object like `System`.
            The system we evaluate the potential for. Here, we
            make use of the positions only.

        Returns
        -------
        out[0] : float
            The potential energy as a float.
        out[1] : numpy.array
            The force as a numpy.array of the same shape as the
            positions in `particles.pos`.
        out[2] : numpy.array
            The virial, currently not implemented for this potential.
        """
        pot = self.potential(system)
        forces, virial = self.force(system)
        return pot, forces, virial
