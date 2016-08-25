# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""This file contains a class for a generic force field.

This module defines the class used for representing force field.
The forcefield class is built up of potential functions.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ForceField
    A class representing a generic Force Field.
"""
import logging
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['ForceField']


class ForceField(object):
    """ForceField(object).

    This class described a generic Force Field.
    A force field is assumed to consist of a number of potential
    functions with parameters.

    Attributes
    ----------
    desc : string
        Description of the force field.
    potential : list
        The potential functions that the force field is built up from.
    params : list
        The parameters for the corresponding potential functions.
    """

    def __init__(self, desc='Generic force field', potential=None,
                 params=None):
        """Initiate the force field object.

        Parameters
        ----------
        desc : string, optional.
            Description of the force field.
        potential : list, optional.
            Potential functions that the force field is built up from.
        params : list, optional
            Parameters for the potential(s). If too few parameters are
            given, we will just assume a `None`.
        """
        self.desc = desc
        self.potential = []
        self.params = []
        if potential is not None:
            if params is None:
                for pot in potential:
                    self.add_potential(pot)
            else:
                for i, pot in enumerate(potential):
                    try:
                        param = params[i]
                    except IndexError:
                        param = None
                        msg = 'No parameters given for potential no. {} ({})'
                        msgtxt = msg.format(i, pot)
                        logger.warning(msgtxt)
                    self.add_potential(pot, parameters=param)

    def add_potential(self, potential, parameters=None):
        """Add a potential with parameters to the force field.

        Parameters
        ----------
        potential : object
            Potential function to add.
        parameters : dict, optional
            Parameters for the potential.

        Returns
        -------
        out : None
            Returns `None` and updates `self.potential` and
            `self.params`.
        """
        if potential is None:
            msg = ('Trying to add empty potential to force field.\n'
                   'This was ignored -- please check your settings.')
            logger.warning(msg)
            return None
        self.potential.append(potential)
        if parameters is not None:
            potential.set_parameters(parameters)
        self.params.append(parameters)

    def remove_potential(self, potential):
        """Remove a selected potential from the force field.

        Parameters
        ----------
        potential : object
            The potential function to remove.

        Returns
        -------
        out : None or tuple
            Returns `None` if not potential was removed, otherwise it
            will return the removed potential and it's parameters.
        """
        if potential in self.potential:
            idx = self.potential.index(potential)
            potrm = self.potential.pop(idx)
            paramrm = self.params.pop(idx)
            return potrm, paramrm
        else:
            logger.warning('Potential not found in the force field functions')
            return None

    def update_potential_parameters(self, potential, params):
        """Update the potential parameters of the given potential function.

        Parameters
        ----------
        potential : object
            Potential to update. Should be in `self.potential`.
        params : dict
            The new parameters to set.

        Returns
        -------
        out : None
            Returns `None` but will update parameters of the selected
            potential and modify the corresponding `self.params`.
        """
        if potential in self.potential:
            potential.set_parameters(params)
            self.params[self.potential.index(potential)] = params
        else:
            logger.warning('Unknow potential. Will not update!')

    def evaluate_force(self, system):
        """Evaluate the force on the particles.

        Parameters
        ----------
        system : object like `System`
            The system we evaluate the forces in.

        Returns
        -------
        out[0] : numpy.array
            The forces on the particles.
        out[1] : float
            The virial.
        """
        force = None
        virial = None
        for pot in self.potential:
            if force is None or virial is None:
                force, virial = pot.force(system)
            else:
                forcei, viriali = pot.force(system)
                force += forcei
                virial += viriali
        return force, virial

    def evaluate_potential(self, system):
        """Evaluate the potential energy.

        Parameters
        ----------
        system : object like `System`.
            The system we evaluate the potential in.

        Returns
        -------
        out : float
            The potential energy.
        """
        v_pot = None
        for pot in self.potential:
            if v_pot is None:
                v_pot = pot.potential(system)
            else:
                v_pot += pot.potential(system)
        return v_pot

    def evaluate_potential_and_force(self, system):
        """Evaluate the potential energy and the force.

        Parameters
        ----------
        system : object like `System`.
            The system we evaluate the potential energy and force in.

        Returns
        -------
        out[0] : float
            The potential energy.
        out[1] : numpy.array
            The calculated forces.
        out[2] : float
            The calculated virial.
        """
        v_pot = None
        force = None
        virial = None
        for pot in self.potential:
            if v_pot is None or force is None or virial is None:
                v_pot, force, virial = pot.potential_and_force(system)
            else:
                v_poti, forcei, viriali = pot.potential_and_force(system)
                v_pot += v_poti
                force += forcei
                virial += viriali
        return v_pot, force, virial

    def __str__(self):
        """A string representation of the force field.

        The string representation is built using the string
        descriptions of the potential functions.

        Returns
        -------
        out : string
            Description of force field and the potential functions
            included in the force field.
        """
        msg = ['Force field: {}'.format(self.desc)]
        if len(self.potential) < 1:
            msg.append('No potential functions added yet!')
        else:
            msg.append('Potential functions:')
            for i, pot in enumerate(self.potential):
                msg.append('{}: {}'.format(i + 1, pot))
        return '\n'.join(msg)

    def print_potentials(self):
        """Print information on potentials in the force field.

        This is intended as a lighter alternative to `self.__str__`
        which can be verbose. This function will not actually do the
        printing, but it returns a string which can be printed.

        Returns
        -------
        out : string
            Description of the potential functions in this force field.
        """
        msg = ['Force field: {}'.format(self.desc)]
        for i, pot in enumerate(self.potential):
            msg.append('\t{}: {}'.format(i + 1, pot.desc))
        return '\n'.join(msg)
