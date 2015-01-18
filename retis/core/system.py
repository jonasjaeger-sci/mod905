# -*- coding: utf-8 -*-

"""
system.py
"""
import constants
import numpy as np
from particlelist import Particles


__all__ = ['System']

class System(object):
    """
    This class defines a generic system for simulation.
    
    Attributes
    ----------
    box : list, defines the simulation box
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
        self : 
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
        self.beta = None
        self.temperaure = None
        self.set_temperature(temperature=temperature)
        # intialize other variables:
        self.v_pot = 0.0 # stores the potential energy of the system
        self.particles = Particles() # empty particle list
        self.forcefield = None

    def set_temperature(self, temperature=None):
        """
        Updates the temperature and beta for the system
        
        Parameters
        ----------
        self :
        temperature : float, optional, the temperature of the system.
        
        Returns
        -------
        N/A, but self.temperature and self.beta are updated
        """
        self.temperature = temperature
        if self.temperature is None:
            self.beta = None
        else:
            self.beta = 1.0/(self.temperature*constants.kB[self.units])

    def add_particle(self, pos, vel=None, force=None, 
                     mass=1.0, name='?', ptype='?'):
        """ 
        Adds a particle to the system.
    
        Parameters
        ----------
        self : 
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

    def evaluate_force(self, **kwargs):
        """ 
        Evaluate the forces
    
        Parameters
        ----------
        self : 

        Returns
        -------
        The forces as a numpy.array
        """
        args = {}
        args['pos'] = kwargs.get('pos', self.particles.pos)
        args['name'] = kwargs.get('name', self.particles.name)
        args['ptype'] = kwargs.get('ptype', self.particles.ptype)
        return self.forcefield.evaluate_force(**args)

    def force(self):
        """ 
        Updates the forces by calling self.evaluate_force()
    
        Parameters
        ----------
        self : 
        
        Returns
        -------
        N/A, but updates self.forces
        """
        self.particles.force = self.evaluate_force()

    def evaluate_potential(self, **kwargs):
        """
        Evaluate the potential energy. Here we pick out what variables
        we are going to pass on to the forcefield object.
    
        Parameters
        ----------
        self : 

        Returns
        -------
        The scalar potential energy correspoding to the given r.
        """
        args = {}
        args['pos'] = kwargs.get('pos', self.particles.pos)
        args['name'] = kwargs.get('name', self.particles.name)
        args['ptype'] = kwargs.get('ptype', self.particles.ptype)
        return self.forcefield.evaluate_potential(**args)

    def potential(self):
        """ 
        Updates self.v_pot by calling self.evaluate_potential()
    
        Parameters
        ----------
        self : 
        
        Returns
        -------
        N/A, but updates self.v_pot
        """
        self.v_pot = self.evaluate_potential()
