# -*- coding: utf-8 -*-
"""Define the class for a generic potential function.

This class is sub-classed in all potential functions.
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
    _params : dict
        Contains the parameters.
    params : descriptor object.
        The parameters, property variant of `_params`.
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
        self._params = {}

    @property
    def params(self):
        """Return the parameters as a dict"""
        return self._params

    @params.setter
    def params(self, parameters):
        """Update all parameters. Input is assumed to be a dict."""
        for key in parameters:
            if key in self._params:
                self._params[key] = parameters[key]
            else:
                msg = 'Could not find "{}" in parameters. Ignoring!'
                msg = msg.format(key)
                logger.warning(msg)
        self.check_parameters()

    @params.deleter
    def params(self):
        """Delete all parameters."""
        del self._params

    def check_parameters(self):
        """Check on the consistency of the parameters.

        This can be implemented for the different potential functions.

        Returns
        -------
        out : boolean
            True if the check(s) pass.
        """
        if len(self._params) == 0:
            logger.warning('No parameters are set for the potential')
            return False
        return True

    def __str__(self):
        """Return the string description of the potential."""
        msg = ['Potential: {}'.format(self.desc)]
        strinfo = '{}: {}'
        for key in sorted(self._params):
            msg.append(strinfo.format(key, self._params[key]))
        return '\n'.join(msg)
