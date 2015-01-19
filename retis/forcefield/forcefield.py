# -*- coding: utf-8 -*-
"""
This file contains a class for a generic force field
"""
import warnings

__all__ = ['ForceField']

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

