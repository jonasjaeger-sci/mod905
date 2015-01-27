# -*- coding: utf-8 -*-

"""
system.py
"""
import numpy as np
# from the retis package
from units import CONSTANTS
from particles import Particles


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

    Note
    ----
    It might be more clean to lump the dim variable, the periodic variable
    and the box variable into a box-object.
    """
    def __init__(self, dim=1, units='eV/K', box=None, temperature=None):
        """ 
        Initialization of the system.
    
        Parameters
        ----------
        dim : number of dimensions to consider in this simulation
        box : list, optional. System boundaries in the self.dim dimensions.
        temperature : float, optional. The temperature of the system.

        Returns
        -------
        N/A, but sets derived variables:
        self.beta : float, inverse of (kB*T).
        """
        self.dim = dim
        self.box = box # simulation box
        self.units = units
        self.temperature = temperature
        self.beta = self.calculate_beta()
        # intialize other variables:
        self.v_pot = 0.0 # stores the potential energy of the system
        self.particles = Particles() # empty particle list
        self.forcefield = None

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
        pos : numpy.array, optional. Positions of the particle.
        vel : numpy.array, optional. Velocities of the particle.
        force : numpy.array, optional. Forces on the particle.
        mass : float, optional. Mass of the particle
        name : string, optional. Name of the particle.
        ptype : string, optional. Particle type.

        Returns
        -------
        N/A, updates self.particles

        Note
        ----
        If no arguments are given a particle with name='?' will be
        created.
        """
        if pos is None: 
            pos = np.zeros(self.dim)
        if vel is None: 
            vel = np.zeros(self.dim)
        if force is None: 
            force = np.zeros(self.dim)
        self.particles.add_particle(pos, vel, force, mass=mass,
                                    name=name, ptype=ptype)


    def force(self):
        """ 
        Updates the forces by calling self._evaluate_potential_force()
        
        Returns
        -------
        The new forces as a numpy.array, it will also update self.particles.force
        """
        self.particles.force = self._evaluate_potential_force(what='force')
        return self.particles.force

    def potential(self):
        """ 
        Updates self.v_pot by calling self._evaluate_potential_force()
    
        Returns
        -------
        The potential as a float, it will also update self.v_pot
        """
        self.v_pot = self._evaluate_potential_force(what='potential')
        return self.v_pot

    def potential_and_force(self):
        """
        Updates the potential energy in self.v_pot and the forces in
        self.particles.force by calling self._evaluate_potential_force()

        Returns
        -------
        The potential as a float and the forces as a numpy.array. It will
        also update self.v_pot and self.particles.force
        """
        v_pot, force = self._evaluate_potential_force(what='both')
        self.v_pot = v_pot
        self.particles.force = force
        return v_pot, force

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
        The forces as a numpy.array
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
        The scalar potential energy correspoding to the given r.
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
        The scalar potential and the force
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


