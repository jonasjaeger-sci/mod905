# -*- coding: utf-8 -*-
"""This file contains a class for a generic force field."""
import logging
import inspect
import sys
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
    arguments : dict
        Contains information on how to call the different functions.
        `arguments['force']` = list with information on how to call the
        corresponding potential function, i.e. it is equal to
        `inspect.getargspec(potential.force)`.
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
            Parameters for the potential(s).

        """
        self.desc = desc
        self.potential = []
        self.params = []
        self.arguments = {'force': [], 'potential': [], 'pot-and-force': []}
        if potential is not None:
            if params is None:
                for pot in potential:
                    self.add_potential(pot)
            else:
                for pot, param in zip(potential, params):
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
        arg_force, arg_pot, arg_pot_force = inspect_potential(potential)
        self.arguments['force'].append(arg_force)
        self.arguments['potential'].append(arg_pot)
        self.arguments['pot-and-force'].append(arg_pot_force)
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
            self.arguments['force'].pop(idx)
            self.arguments['potential'].pop(idx)
            self.arguments['pot-and-force'].pop(idx)
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

    def evaluate_force(self, **kwargs):
        """Evaluate the force on the particles.

        Parameters
        ----------
        kwargs : dict
            Variables needed to evaluate the forces. Typically this is
            the positions and the particle names/types.

        Returns
        -------
        out[0] : numpy.array
            The forces on the particles.
        out[1] : float
            The virial.

        Note
        ----
        See note in :py:func:`pyretis.forcefield.evaluate_potential_and_force`
        """
        force = None
        virial = None
        for pot, argu in zip(self.potential, self.arguments['force']):
            var = argu['args']
            args = [kwargs[vari] for vari in var if vari != 'self']
            if force is None or virial is None:
                force, virial = pot.force(*args)
            else:
                forcei, viriali = pot.force(*args)
                force += forcei
                virial += viriali
        return force, virial

    def evaluate_potential(self, **kwargs):
        """Evaluate the potential energy.

        Parameters
        ----------
        kwargs : dict
            Variables needed to evaluate the potential. Typically this
            is the positions and the particle names/types.

        Returns
        -------
        out : float
            The potential energy.

        Note
        ----
        See note in :py:func:`pyretis.forcefield.evaluate_potential_and_force`
        """
        v_pot = None
        for pot, argu in zip(self.potential, self.arguments['potential']):
            var = argu['args']
            args = [kwargs[vari] for vari in var if vari != 'self']
            if v_pot is None:
                v_pot = pot.potential(*args)
            else:
                v_pot += pot.potential(*args)
        return v_pot

    def evaluate_potential_and_force(self, **kwargs):
        """Evaluate the potential energy and the force.

        Parameters
        ----------
        kwargs : dict
            Variables needed to evaluate the potential and force.
            Typically this is the positions and the particle
            names/types.

        Returns
        -------
        out[0] : float
            The potential energy.
        out[1] : numpy.array
            The calculated forces.
        out[2] : float
            The calculated virial.

        Note
        ----
        In this function each potential function picks out the variable
        that it needs. This means that this function will be passed too
        many parameters. One solution might be to just pass the system
        to the potential, with additional optional arguments on what to
        override (override is here useful when calculating the energies
        in Monte Carlo moves - i.e. to use the trial positions).
        """
        v_pot = None
        force = None
        virial = None
        for pot, argu in zip(self.potential, self.arguments['pot-and-force']):
            var = argu['args']
            #args = [kwargs[vari] for vari in var if vari is not 'self']
            args = [kwargs[vari] for vari in var if vari != 'self']
            if v_pot is None or force is None or virial is None:
                v_pot, force, virial = pot.potential_and_force(*args)
            else:
                v_poti, forcei, viriali = pot.potential_and_force(*args)
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


def inspect_potential(potential):
    """A method to figure out arguments for a given function.

    This method is used when adding potential functions to the force
    field in order for the force field to figure out how these should
    be executed. Here we need to distinguish between python versions
    since the ``inspect.getargspec`` is deprecated for python3.5 and
    later.

    Parameters
    ----------
    potential : object like `PotentialFunction`
        The potential to inspect

    Returns
    -------
    out[0] : dict
        The arguments for calling `potential.force` if any.
    out[1] : dict
        The arguments for calling `potential.potential` if any.
    out[2] : dict
        The arguments for calling `potential.potential_and_force`
        if any.
    """
    args = {}
    for funcname in ['force', 'potential', 'potential_and_force']:
        args[funcname] = None
        function = getattr(potential, funcname, None)
        if function is not None:
            args[funcname] = _inspect_potential_function(function)
    return args['force'], args['potential'], args['potential_and_force']


def _inspect_potential_function(function):
    """Helper method for `inspect_potential`

    This function will do the actual inspection.

    Parameters
    ----------
    function : callable
        The function to inspect.

    Returns
    -------
    argsdict : dict
        The arguments for calling `function` if any.
    """
    argsdict = {'args': []}
    if sys.version_info > (3, 5):
        args = inspect.signature(function)  # pylint: disable=no-member
        for arg in args.parameters:
            argsdict['args'].append(arg)
        return argsdict
    else:
        args = inspect.getargspec(function)
        if args.args is not None:
            argsdict['args'] = [arg for arg in args.args]
        return argsdict
