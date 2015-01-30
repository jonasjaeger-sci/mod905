# -*- coding: utf-8 -*-

"""
system.py
"""
from __future__ import absolute_import
import numpy as np
import warnings
# from the retis package
from .units import CONSTANTS
from .particles import Particles


__all__ = ['System']

class System(object):
    """
    This class defines a generic system for simulation.
    
    Attributes
    ----------
    box : object, defines the simulation box
    temperature : float, defines the set temperature
    beta : float, defines the boltzmann factor
    v_pot : float,  the potential energy of the system
    particles : obj from particleslist which represents the 
        particles and the properties of the particles (positions, 
        velocities, forces etc.)
    forcefield : ForceField object which defines the force field to
        use.
    units : string, units to use in for the system
    """
    def __init__(self, units='eV/K', box=None, temperature=None):
        """ 
        Initialization of the system.
    
        Parameters
        ----------
        box : object of type Box
            This variable represents the simulation box. It is used to
            determine the number of dimensions
        temperature : float
            The temperature of the system, if applicable.
        units : string
            The system of units to use in the simulation box.

        Returns
        -------
        N/A, but sets derived variables:
        self.beta : float, inverse of (kB*T).
        """
        self.box = box # simulation box
        self.units = units
        self.temperature = temperature
        self.beta = self.calculate_beta()
        # intialize other variables:
        self.v_pot = 0.0 # stores the potential energy of the system
        self.particles = Particles() # empty particle list
        self.forcefield = None

    def get_kB(self):
        """
        This function returns the value of Boltzmanns constant
        in the correct units for the system
        
        Returns
        -------
        Boltzmanns constant as a float
        """
        return CONSTANTS['kB'][self.units]

    def get_dim(self):
        """
        This function returns the dimensionality of the system.
        The value is obtained from the box. In other words,
        it is the box object that defines the dimensionality of
        the system.
        
        Returns
        -------
        integer, representing the number of dimensions
        """
        try:
            return self.box.dim
        except AttributeError:
            warnings.warn('Box dimensions not set, defaulting to 1!')
            return 1

    def calculate_beta(self, temperature=None):
        """
        Updates the temperature and beta for the system
        
        Parameters
        ----------
        temperature : float, optional, the temperature of the system.
        
        Returns
        -------
        N/A, but self.temperature and self.beta are updated
        """
        if temperature is None:
            if self.temperature is None:
                return None
            else:
                temperature = self.temperature
        return 1.0/(temperature*CONSTANTS['kB'][self.units])

    def add_particle(self, pos, vel=None, force=None, 
                     mass=1.0, name='?', ptype='?'):
        """ 
        Adds a particle to the system.
    
        Parameters
        ----------
        pos : numpy.array,
            Position of the particle.
        vel : numpy.array, optional. 
            Velocity of the particle. If not given np.zeros will be used.
        force : numpy.array, optional. 
            Force on the particle. If not given np.zeros will be used.
        mass : float, optional. 
            Mass of the particle, default is 1.0
        name : string, optional. 
            Name of the particle, default is '?'
        ptype : string, optional. Particle type.
            Particle type, default is '?'

        Returns
        -------
        N/A, updates self.particles
        """
        dim = self.get_dim()
        if vel is None: 
            vel = np.zeros(dim)
        if force is None: 
            force = np.zeros(dim)
        self.particles.add_particle(pos, vel, force, mass=mass,
                                    name=name, ptype=ptype)

    def force(self):
        """ 
        Updates the forces by calling self._evaluate_potential_force()
        
        Returns
        -------
        out[1] : numpy.array. 
            Forces on the particles. Note that self.particles.force will
            also be updated.
        out[2] : float.
            The virial. Note that self.particles.virial will also be updated.
        """
        force, virial = self._evaluate_potential_force(what='force')
        self.partilces.force = force
        self.particles.virial = virial
        return self.particles.force, virial

    def potential(self):
        """ 
        Updates self.v_pot by calling self._evaluate_potential_force()
    
        Returns
        -------
        out : float.
            The potential energy, note self.v_pot is also updated.
        """
        self.v_pot = self._evaluate_potential_force(what='potential')
        return self.v_pot

    def potential_and_force(self):
        """
        Updates the potential energy in self.v_pot and the forces in
        self.particles.force by calling self._evaluate_potential_force()

        Returns
        -------
        out[1] : float
            The potential energy, note self.v_pot is also updated.
        out[2] : numpy.array. 
            Forces on the particles. Note that self.particles.force will
            also be updated.
        out[3] : float.
            The virial. Note that self.particles.virial will also be updated.
        """
        v_pot, force, virial = self._evaluate_potential_force(what='both')
        self.v_pot = v_pot
        self.particles.force = force
        self.particles.virial = virial
        return v_pot, force, virial

    def evaluate_force(self, **kwargs):
        """ 
        Evaluate the forces
    
        Parameters
        ----------
        kwargs : dictionary with settings that can be used to override
            the information in self.particles. This is useful if one
            wants to evaluate the forces for a different configuration
            of the particles.

        Returns
        -------
        out[1] : numpy.array. 
            Forces on the particles. 
        out[2] : float.
            The virial. 
        """
        return self._evaluate_potential_force(what='force', **kwargs)

    def evaluate_potential(self, **kwargs):
        """
        Evaluate the potential energy. 
    
        Parameters
        ----------
        kwargs : dictionary with settings that can be used to override
            the information in self.particles. This is useful if one
            wants to evaluate the potential for a different configuration
            of the particles.

        Returns
        -------
        out : float
            The potential energy.
        """
        return self._evaluate_potential_force(what='potential', **kwargs)
    
    def evaluate_potential_and_force(self, **kwargs):
        """
        Evaluate the potential and/or the force
        Parameters
        ----------
        kwargs : dictionary with settings that can be used to override
            the information in self.particles. This is useful if one
            wants to evaluate the potential for a different configuration
            of the particles.

        Returns
        -------
        out[1] : float
            The potential energy.
        out[2] : numpy.array. 
            Forces on the particles. 
        out[3] : float.
            The virial. 
        """
        return self._evaluate_potential_force(what='both', **kwargs)
        
    def _evaluate_potential_force(self, what='both', **kwargs):
        """
        Helper function to evaluate the potential or force
        or both.
        """
        args = {}
        args['pos'] = kwargs.get('pos', self.particles.pos)
        args['name'] = kwargs.get('name', self.particles.name)
        args['ptype'] = kwargs.get('ptype', self.particles.ptype)
        args['particles'] = kwargs.get('particles', self.particles)
        args['box'] = kwargs.get('box', self.box)
        if what == 'potential':
            return self.forcefield.evaluate_potential(**args)
        elif what == 'force':
            return self.forcefield.evaluate_force(**args)
        else:
            return self.forcefield.evaluate_potential_and_force(**args)


