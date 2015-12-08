# -*- coding: utf-8 -*-
"""This file contains positions dependent potentials."""
from __future__ import absolute_import
import numpy as np
import logging
from pyretis.forcefield.potential import PotentialFunction
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['DoubleWell', 'RectangularWell']


class DoubleWell(PotentialFunction):
    r"""DoubleWell(PotentialFunction).

    This class defines a one-dimensional double well potential.
    The potential energy (:math:`V_\text{pot}`) is given by

    .. math::

       V_\text{pot} = a x^4 - b (x - c)^2

    where :math:`x` is the position and :math:`a`, :math:`b` and :math:`c` are
    parameters for the potential. These parameters are stored as attributes of
    the class. Typically, both :math:`a` and :math:`b` are positive quantities
    however, we do not explicitly check that here.

    Attributes
    ----------
    params : dict
        Contains the parameters. The keys are:

        * `a`: The ``a`` parameter for the potential.
        * `b`: The ``b`` parameter for the potential.
        * `c`: The ``c`` parameter for the potential.

        These keys corresponds to the parameters in the potential,
        :math:`V_\text{pot} = a x^4 - b (x - c)^2`.
    """

    def __init__(self, a=1.0, b=1.0, c=0.0, desc='1D double well potential'):
        """Initiate the one dimensional double well potential.

        Parameters
        ----------
        a : float, optional.
            Parameter for the potential.
        b : float, optional.
            Parameter for the potential.
        c : float, optional.
            Parameter for the potential.
        desc : string, optional.
            Description of the force field.
        """
        super(DoubleWell, self).__init__(dim=1, desc=desc)
        self._params = {'a': a, 'b': b, 'c': c}

    def potential(self, pos):
        """Evaluate the potential for the one-dimensional double well.

        Parameters
        ----------
        pos : numpy.array
            Positions used for evaluation of the potential.

        Returns
        -------
        out : float
            The potential energy.
        """
        v_pot = (self._params['a'] * pos**4 -
                 self._params['b'] * (pos - self._params['c'])**2)
        return v_pot.sum()

    def force(self, pos):
        """Evaluate the force for the one-dimensional double well potential.

        Parameters
        ----------
        pos : numpy.array
            The position to use for the evaluation of the force.

        Returns
        -------
        out[0] : numpy.array
            The calculated force.
        out[1] : numpy.array
            The virial, currently not implemented for this potential
        """
        forces = (-4.0*(self._params['a'] * pos**3) +
                  2.0*(self._params['b'] * (pos - self._params['c'])))
        virial = np.zeros((self.dim, self.dim))  # just return zeros here
        return forces, virial

    def potential_and_force(self, pos):
        """Evaluate the potential and the force.

        Parameters
        ----------
        pos : numpy.array
            The position to use for the evaluation of the force.

        Returns
        -------
        out[0] : float
            The potential energy as a float.
        out[1] : numpy.array
            The force as a numpy.array of the same shape as the positions
            in particles.pos.
        out[2] : numpy.array
            The virial, currently not implemented for this potential
        """
        dist = pos - self._params['c']
        pos3 = pos**3
        v_pot = self._params['a'] * pos3 * pos - self._params['b'] * dist**2
        forces = (-4.0 * (self._params['a'] * pos3) +
                  2.0 * (self._params['b'] * dist))
        virial = np.zeros((self.dim, self.dim))  # just return zeros here
        return v_pot.sum(), forces, virial


class RectangularWell(PotentialFunction):
    r"""RectangularWell(PotentialFunction).

    This class defines a one-dimensional rectangular well potential.
    The potential energy is zero within the potential well and infinite
    outside. The well is defined with a left and right boundary.

    Attributes
    ----------
    params : dict
        The parameters for the potential. The keys are:

        * `left`: Left boundary of the potential.
        * `right`: Right boundary of the potential.
        * `largenumber`: Value of potential outside the boundaries.

        It is possible to define left > right, however a warning will
        be issued then.
    """

    def __init__(self, left=0.0, right=1.0, largenumber=float('inf'),
                 desc='1D Rectangular well potential'):
        """Initiate the one-dimensional rectangular well.

        Parameters
        ----------
        left : float, optional.
            The left boundary of the potential.
        right : float, optional.
            The right boundary of the potential.
        largenumber : float, optional.
            The value of the potential outside (left, right).
        desc : string, optional.
            Description of the force field.
        params : dict
            The parameters for this potential (left, right, largenumber).
        """
        super(RectangularWell, self).__init__(dim=1, desc=desc)
        self._params = {'left': left, 'right': right,
                        'largenumber': largenumber}
        self.check_parameters()

    def check_parameters(self):
        """Check the consistency of the parameters.

        Returns
        -------
        out : None
            Returns `None` but might give a warning.
        """
        if self._params['left'] >= self._params['right']:
            msg = 'Setting left >= right in RectangularWell potential!'
            logger.warning(msg)

    def potential(self, pos):
        """Evaluate the potential.

        Parameters
        ----------
        pos : numpy.array
            The position(s) to evaluate the potential at.

        Returns
        -------
        out : float
            The potential energy.
        """
        left = self._params['left']
        right = self._params['right']
        largenumber = self._params['largenumber']
        v_pot = np.where(np.logical_and(pos > left, pos < right),
                         0.0, largenumber)
        return v_pot.sum()
