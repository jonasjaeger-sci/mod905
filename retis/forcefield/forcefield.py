# -*- coding: utf-8 -*-
"""
This file contains a class for a generic force field
"""
import numpy as np
import warnings

__all__ = ['ForceField']

def mixing_parameters(epsilon_i, sigma_i, epsilon_j, sigma_j, 
                      mixing='geometric'):
    """
    This function defines so-called mixing rules which may be usefull
    for some force fields for generating parameters.
    
    Parameters
    ----------
    epsilon_i and epsilon_j : float, which, for a Lennard-Jones potential 
        corresponds to the epsilon parameter
    sigma_i and sigma_j : float, which, for a Lennard-Jones potential
        corresponds to the sigma parameter
    mixing :  string, represents what kind of mixing that should be done
    
    Returns
    -------
    epsilon_ij and sigma_ij : float, the mixed parameters according to the 
        specified mixing rule.
    """
    if mixing == 'geometric':
        epsilon_ij = np.sqrt(epsilon_i * epsilon_j)
        sigma_ij = np.sqrt(sigma_i * sigma_j)
    elif mixing == 'arithmetic':
        epsilon_ij = np.sqrt(epsilon_i * epsilon_j)
        sigma_ij = 0.5*(sigma_i + sigma_j)
    elif mixing == 'sixthpower':
        si3 = sigma_i**3
        si6 = si3**2
        sj3 = sigma_j**3
        sj6 = sj3**2
        avgs6 = (si6+sj6)*0.5
        epsilon_ij = np.sqrt(epsilon_i * epsilon_j) * si3 * sj3 / avgs6
        sigma_ij = (avgs6)**(1.0/6.0)
    else:
        warnings.warn('Unknown mixing rule requested!')
        epsilon_ij = 1.0
        sigma_ij = 1.0
    return epsilon_ij, sigma_ij

class ForceField(object):
    """Generic force field object"""

    def __init__(self, dim=1, desc="", potential=None):
        """ 
        Initiates the force field object.
    
        Parameters
        ----------
        dim : int, optional. Represents the dimensionality.
        desc : string, optional. Description of the force field.
        potential : list, optional. Potential functions that the force
        filed is built up from.

        Returns
        -------
        N/A 
        """
        self.dim = dim # dimensionality
        self.desc = desc
        if type(potential)==type([]) or (potential is None):
            self.potential = potential
        else:
            self.potential = [potential]
        
    def update_potential_parameters(self, potential, **params):
        """
        This method will update the potential parameters of the
        given potential function.

        Returns
        -------
        N/A, but will update parameters of the selected potential!
        """
        if potential in self.potential:
            potential.update_parameters(**params)
        else:
            warnings.warn('Unknow potential')
            
            

    def evaluate_force(self, **kwargs):
        """ 
        Evaluate the force on the particles.
    
        Parameters
        ----------
        kwargs : dictionary of variables needed to evaluate the forces.
            Typically this is the positions and the particle names.

        Returns
        -------
        force : np.array with the forces.
        
        Note
        ----
        See the note for evaluate_potential
        """
        force = None
        for pot in self.potential:
            nvar = pot.force.func_code.co_argcount 
            var = pot.force.func_code.co_varnames[:nvar]
            args = [kwargs[vari] for vari in var[1:]]
            if force is None:
                force = pot.force(*args)
            else:
                force += pot.force(*args)
        return force

    def evaluate_potential(self, **kwargs):
        """ 
        Evaluate the potential energy.
    
        Parameters
        ----------
        kwargs : dictionary of variables needed to evaluate the potential.
            Typically this is the positions and the particle names.

        Returns
        -------
        v_pot : float equal to the potential energy.

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
            nvar = pot.potential.func_code.co_argcount 
            var = pot.potential.func_code.co_varnames[:nvar]
            args = [kwargs[vari] for vari in var[1:]]
            if v_pot is None:
                v_pot = pot.potential(*args)
            else:
                v_pot += pot.potential(*args)
        return v_pot

    def __str__(self):
        """ 
        A string representation of the force field. 
        It it returns the string descriptions of the potential functions.

        Returns
        -------
        String with description of force field and the potential
        functions included in the force field.
        """
        pots = "\n *".join([ff.desc for ff in self.potential])
        force = "Force field: {}".format(self.desc)
        desc = "{}\nPotential functions: \n *{}".format(force, pots)
        return desc

