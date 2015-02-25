# -*- coding: utf-8 -*-
"""
This file contains a class for a generic force field
"""
import numpy as np
import warnings
import inspect

__all__ = ['ForceField']


def mixing_parameters(epsilon_i, sigma_i, rcut_i, epsilon_j, sigma_j, rcut_j,
                      mixing='geometric'):
    """
    This function defines so-called mixing rules which may be usefull
    for some force fields for generating parameters.

    Parameters
    ----------
    epsilon_i and epsilon_j : floats
        For a Lennard-Jones potential, this corresponds to the
        the epsilon parameters.
    sigma_i and sigma_j : floats
        For a Lennard-Jones potential, this corresponds to the
        sigma parameters.
    mixing :  string
        Represents what kind of mixing that should be done.

    Returns
    -------
    out[0] : float
        The mixed epsilon_ij parameter.
    out[1] : float
        The mixed sigma_ij parameter.
    """
    if mixing == 'geometric':
        epsilon_ij = np.sqrt(epsilon_i * epsilon_j)
        sigma_ij = np.sqrt(sigma_i * sigma_j)
        rcut_ij = np.sqrt(rcut_i * rcut_j)
    elif mixing == 'arithmetic':
        epsilon_ij = np.sqrt(epsilon_i * epsilon_j)
        sigma_ij = 0.5 * (sigma_i + sigma_j)
        rcut_ij = 0.5 * (rcut_i + rcut_j)
    elif mixing == 'sixthpower':
        si3 = sigma_i**3
        si6 = si3**2
        sj3 = sigma_j**3
        sj6 = sj3**2
        avgs6 = 0.5 * (si6 + sj6)
        epsilon_ij = np.sqrt(epsilon_i * epsilon_j) * si3 * sj3 / avgs6
        sigma_ij = avgs6**(1.0/6.0)
        rcut_ij = (0.5*(rcut_i**6 + rcut_j**6))**(1.0/6.0)
    else:
        warnings.warn('Unknown mixing rule requested!')
        epsilon_ij = 0.5 * (epsilon_i + epsilon_j)
        sigma_ij = 0.5 * (sigma_i + sigma_j)
        rcut_ij = 0.5 * (rcut_i + rcut_j)
    return epsilon_ij, sigma_ij, rcut_ij


class ForceField(object):
    """
    ForceField(object)

    This class described a generic Force Field.
    A force field is assumed to consist of a number of potential
    functions with parameters.

    Attributes
    ----------
    desc : string
        Description of the force field.
    potential : list
        The potential functions that the force field is built up from.
    param : list
        The parameters for the corresponding potential functions.
    """

    def __init__(self, desc='', potential=None, params=None):
        """
        Initiates the force field object.

        Parameters
        ----------
        desc : string, optional.
            Description of the force field.
        potential : list, optional.
            Potential functions that the force field is built up from.
        params : list, optional
            Parameters for the potential(s).

        Returns
        -------
        N/A
        """
        self.desc = desc
        if potential is None:
            self.potential = []
        else:
            if isinstance(potential, list):
                self.potential = potential
            else:
                self.potential = [potential]

        if params is None:  # try to get them from the potential
            self.params = [pot.params for pot in self.potential]
        else:
            if isinstance(params, list):
                self.params = params
            else:
                self.params = [params]
            # also assume that we indend to set the parameters:
            for pot, param in zip(self.potential, self.params):
                pot.add_parameters(param)

    def add_potential(self, potential, parameters=None):
        """
        Adds a potential with parameters to the force field

        Parameters
        ----------
        potential : object
            Potential function to add.
        parameters : dict, optional
            Parameters for the potential.

        Returns
        -------
        N/A but it will upsate self.potential and self.params
        """
        self.potential.append(potential)
        if not parameters is None:
            potential.add_parameters(parameters)
        self.params.append(potential.params)

    def remove_potential(self, potential):
        """
        Removes a selected potential from the force field

        Parameters
        ----------
        potential : object
            The potential function to remove.

        Returns
        -------
        N/A but it will upsate self.potential and self.params
        """
        if potential in self.potential:
            idx = self.potential.index(potential)
            potrm = self.potential.pop(idx)
            paramrm = self.params.pop(idx)
            return (potrm, paramrm)
        else:
            warnings.warn('Unknow potential --- will not remove')
            return None

    def update_potential_parameters(self, potential, params):
        """
        This method will update the potential parameters of the
        given potential function.

        Parameters
        ----------
        potential : object
            Potential to update. Should be in the self.potential list.
        params : dict
            The new parameters to set.

        Returns
        -------
        N/A, but will update parameters of the selected potential
        and modified the corresponding self.params
        """
        if potential in self.potential:
            potential.update_parameters(params)
            self.params[self.potential.index(potential)] = potential.params
        else:
            warnings.warn('Unknow potential')

    def evaluate_force(self, **kwargs):
        """
        Evaluate the force on the particles.

        Parameters
        ----------
        kwargs : dict
            Variables needed to evaluate the forces.
            Typically this is the positions and the particle names/types.

        Returns
        -------
        out[0] : numpy.array
            The forces on the particles.
        out[1] : float
            The virial.

        Note
        ----
        See the note for evaluate_potential
        """
        force = None
        virial = None
        for pot in self.potential:
            arguments = inspect.getargspec(pot.force)
            var = arguments.args
            args = [kwargs[vari] for vari in var if vari is not 'self']
            if force is None or virial is None:
                force, virial = pot.force(*args)
            else:
                forcei, viriali = pot.force(*args)
                force += forcei
                virial += viriali
        return force, virial

    def evaluate_potential(self, **kwargs):
        """
        Evaluate the potential energy.

        Parameters
        ----------
        kwargs : dict
            Variables needed to evaluate the potential.
            Typically this is the positions and the particle names/types.

        Returns
        -------
        out : float
            The potential energy.

        Note
        ----
        In this function each potential function picks out the
        variable that it needs. This might be stupid,
        as these variable names will have to match (names will have
        to be know anyway if I use optional keywords.
        One solution might be to just pass the system to the
        potential, with additional optional arguments on what to
        override (override is here usefull when calculating the energies
        in Monte Carlo moves - i.e. to use the trial positions).
        """
        v_pot = None
        for pot in self.potential:
            arguments = inspect.getargspec(pot.potential)
            var = arguments.args
            args = [kwargs[vari] for vari in var if vari is not 'self']
            if v_pot is None:
                v_pot = pot.potential(*args)
            else:
                v_pot += pot.potential(*args)
        return v_pot

    def evaluate_potential_and_force(self, **kwargs):
        """
        Evaluate the potential energy and the force.

        Parameters
        ----------
        kwargs : dict
            Variables needed to evaluate the potential and force.
            Typically this is the positions and the particle names/types.

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
        In this function each potential function picks out the
        variable that it needs. This might be stupid,
        as these variable names will have to match (names will have
        to be know anyway if I use optional keywords.
        One solution might be to just pass the system to the
        potential, with additional optional arguments on what to
        override (override is here usefull when calculating the energies
        in Monte Carlo moves - i.e. to use the trial positions).
        """
        v_pot = None
        force = None
        virial = None
        for pot in self.potential:
            arguments = inspect.getargspec(pot.potential_and_force)
            var = arguments.args
            args = [kwargs[vari] for vari in var if vari is not 'self']
            if v_pot is None or force is None or virial is None:
                v_pot, force, virial = pot.potential_and_force(*args)
            else:
                v_poti, forcei, viriali = pot.potential_and_force(*args)
                v_pot += v_poti
                force += forcei
                virial += viriali
        return v_pot, force, virial

    def __str__(self):
        """
        A string representation of the force field.
        It it returns the string descriptions of the potential functions.

        Returns
        -------
        out : string
        Description of force field and the potential functions included
        in the force field.
        """
        pots = '\n *'.join([ff.desc for ff in self.potential])
        force = 'Force field: {}'.format(self.desc)
        desc = '{}\nPotential functions: \n *{}'.format(force, pots)
        return desc
