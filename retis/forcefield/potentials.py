# -*- coding: utf-8 -*-
"""
This file contains positions dependent potentials
"""
from __future__ import absolute_import
import numpy as np
import warnings
from .potential import PotentialFunction

__all__ = ['DoubleWell', 'RectangularWell']


class DoubleWell(PotentialFunction):
    """
    DoubleWell(PotentialFunction)

    This class defines a one-dimensional double well potential.

    Attributes
    ----------
    a : float
        Parameter for the potential.
    b : float
        Parameter for the potential.
    c : float
        Parameter for the potential.
    params : dict
        Containins the parameters.
    """

    def __init__(self, a=1.0, b=1.0, c=0.0, desc='1D double well potential'):
        """
        Initiates the one dimensional double well potential.

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

        Returns
        -------
        N/A
        """
        super(DoubleWell, self).__init__(dim=1, desc=desc)
        self.a = a
        self.b = b
        self.c = c
        self.parameters_to_dict()

    def potential(self, pos):
        """
        Evaluate the potential for the one-dimensional double well potential.

        Parameters
        ----------
        pos : numpy.array
            Potitions used for evaluation of the potential.

        Returns
        -------
        out : float
            The potential energy.
        """
        v_pot = self.a*pos**4 - self.b*(pos - self.c)**2
        return v_pot.sum()

    def force(self, pos):
        """
        Evaluate the force for the one-dimensional double well potential.

        Parameters
        ----------
        pos : numpy.array
            The position to use for the evaluation of the force.

        Returns
        -------
        out : numpy.array
            The calculated force.
        """
        return -4.0*(self.a * pos**3) + 2.0*(self.b * (pos - self.c))

    def parameters_to_dict(self):
        """
        Generate a dictionary with the parameters of
        the potential.

        Returns
        -------
        N/A but updates self.params
        """
        self.params = {'a': {'value': self.a,
                             'desc': 'Parameter for double well'},
                       'b': {'value': self.b,
                             'desc': 'Parameter for double well'},
                       'c': {'value': self.c,
                             'desc': 'Parameter for double well'}}


class RectangularWell(PotentialFunction):
    """
    RectangularWell(PotentialFunction)

    This class defines a one-dimensional rectangular well potential.

    Attributes
    ----------
    left : float
        Left boundary of the potential.
    right : float
        Right boundary of the potential.
    largenumber : float
        Value of potential outside the boundaries.
    """

    def __init__(self, left=0.0, right=1.0, largenumber=1e10,
                 desc='1D Rectangular well potential'):
        """
        Initiates a one-dimensional rectangular well.

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

        Returns
        -------
        N/A
        """
        super(RectangularWell, self).__init__(dim=1, desc=desc)
        #self.largenumber = float('inf') # possible to use this, NOTE FOR LATER
        self.largenumber = largenumber
        self.left = left
        self.right = right
        self.parameters_to_dict()

    def check_parameters(self):
        """
        Function to check the consistensy of the parameters.

        Returns
        -------
        N/A, but might raise a warning.
        """
        if self.left >= self.right:
            msg = 'Setting left >= right in RectangularWell potential!'
            warnings.warn(msg)

    def potential(self, pos):
        """
        Evaluate the potential.

        Parameters
        ----------
        pos : numpy.array
            The position(s) to evaluate the potential at.

        Returns
        -------
        out : float
            The potential energy.
        """
        v_pot = np.where(np.logical_and(pos > self.left, pos < self.right),
                         0.0, self.largenumber)
        return v_pot.sum()

    def parameters_to_dict(self):
        """
        Generate a dictionary with the parameters of
        the potential.

        Returns
        -------
        N/A but updates self.params
        """
        self.params = {'left': {'value': self.left,
                                'desc': 'Left boundary'},
                       'right': {'value': self.right,
                                 'desc': 'Right boundary'},
                       'largenumber': {'value': self.largenumber,
                                       'desc': 'Potential value\
                                                outside boundaries'}}
