# -*- coding: utf-8 -*-
"""Define the class for a generic potential function.

This class is sub-classed in all potential functions.
"""
import warnings


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
        Contains the parameters. This is a variable included
        for convenience in case other methods/classes wants to know all
        the parameters of the potential.
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

    def check_parameters(self):
        """Check on the consistency of the parameters.

        This can be implemented for the different potential functions.

        Returns
        -------
        out : boolean
            True if the check(s) pass.
        """
        if len(self.params) == 0:
            warnings.warn('No parameters are set for the potential')
            return False
        return True

    def update_parameters(self, params):
        """Update the parameters for the potential.

        In this generic function, it will just try to set attributes
        for the object.

        Parameters
        ----------
        params : dict
            The parameters to update.

        Returns
        -------
        out : boolean
            False if parameters could not be set.
            True if they could be set and if the pass the consistency test.

        Note
        ----
        A parameter in params which is not a attribute of the object will be
        ignored.
        """
        if not isinstance(params, dict):
            msg = 'Did not understand the parameters...'
            warnings.warn(msg)
            return False
        for param in params:
            if hasattr(self, param):
                value = params[param]
                setattr(self, param, value)
                self.params[param]['value'] = value
            else:
                msg = 'Ignoring unknown parameter {}'.format(param)
                warnings.warn(msg)
        return self.check_parameters()

    def get_parameters(self):
        """Return information about the parameters for the potential.

        Returns
        -------
        out : string
            Information about the parameters.
        """
        allinfo = []
        strinfo = '{}: {}, Value: {}'
        for param in sorted(self.params):
            value = self.params[param]['value']
            desc = self.params[param]['desc']
            allinfo.append(strinfo.format(param, desc, value))
        return 'Parameters:\n'+'\n'.join(allinfo)

    def parameters_to_dict(self):
        """Generate a dictionary containing the parameters for the potential.

        Returns
        -------
        out : None
            Returns `None` and modifies `self.params`.
        """
        self.params = {}

    def __str__(self):
        """Return the string description of the potential."""
        return self.desc
