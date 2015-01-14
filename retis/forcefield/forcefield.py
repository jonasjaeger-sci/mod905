#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file contains a class for a generic force field
"""

class ForceField(object):
    """Generic force field object"""

    def __init__(self, dim=1, desc="", potential=None):
        """ 
        Initiates the force field object.
    
        Parameters
        ----------
        self : 
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
        self.potential = potential

    def evaluate_force(self, r, particles=None):
        """ 
        Evaluate the force on the particles.
    
        Parameters
        ----------
        self : 
        r : np.array, the position of the particles.
        particles : list, optional (default is none). Some potentials
            require the particle id's to determine how the
            potential is to be evaluated.

        Returns
        -------
        force : np.array with the forces.
        """
        force = None
        args = [r]
        if particles: args.append(particles)
        for potential in self.potential:
            if force is None:
                force = potential.force(*args)
            else:
                force += potential.force(*args)
        return force

    def evaluate_potential(self, r, particles=None):
        """ 
        Evaluate the potential energy.
    
        Parameters
        ----------
        self : 
        r : np.array, the position of the particles.
        particles : list, optional (default is none). Some potentials
            require the particle id's to determine how the
            potential is to be evaluated.

        Returns
        -------
        v_pot : float equal to the potential energy.
        """
        v_pot = None
        args = [r]
        if particles: 
            args.append(particles)
        for pot in self.potential:
            if v_pot is None:
                v_pot = pot.potential(*args)
            else:
                v_pot += pot.potential(*args)
        return v_pot

    def __str__(self):
        """ 
        A string representation of the force field. 
        It it returns the string descriptions of the potential functions.
    
        Parameters
        ----------
        self : 

        Returns
        -------
        String with description of force field.
        """
        pots = "\n *".join([ff.desc for ff in self.potential])
        force = "Force field: {}".format(self.desc)
        desc = "{}\nPotential functions: \n *{}".format(force, pots)
        return desc

