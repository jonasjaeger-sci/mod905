# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""Define the class for a generic potential function.

This module defines the generic class for potential functions.
This cass is sub-classed in all potential functions.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PotentialFunction
    A class for representing generic potential functions.
"""
import logging
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['PotentialFunction']


class PotentialFunction(object):
    """PotentialFunction(object).

    Generic class for potential functions.

    Attributes
    ----------
    desc : string
        Short description of the potential.
    dim : int
        Represents the spatial dimensionality of the potential.
    params : dict
        Contains the parameters. This dict defines on initiation what
        parameters the potential will handle and store.
    """

    def __init__(self, dim=1, desc=''):
        """Initiate the potential.

        Parameters
        ----------
        dim : int, optional.
            Represents the dimensionality.
        desc : string, optional.
            Description of the force field.
        """
        self.dim = dim
        self.desc = desc
        self.params = {}

    def set_parameters(self, parameters):
        """Update all parameters. Input is assumed to be a dict."""
        for key in parameters:
            if key in self.params:
                self.params[key] = parameters[key]
            else:
                msg = 'Could not find "{}" in parameters. Ignoring!'
                msg = msg.format(key)
                logger.warning(msg)
        self.check_parameters()

    def check_parameters(self):
        """Check on the consistency of the parameters.

        This can be implemented for the different potential functions.

        Returns
        -------
        out : boolean
            True if the check(s) pass.
        """
        if len(self.params) == 0:
            logger.warning('No parameters are set for the potential')
            return False
        return True

    def __str__(self):
        """Return the string description of the potential."""
        msg = ['Potential: {}'.format(self.desc)]
        strinfo = '{}: {}'
        for key in sorted(self.params):
            msg.append(strinfo.format(key, self.params[key]))
        return '\n'.join(msg)
