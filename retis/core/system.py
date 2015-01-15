# -*- coding: utf-8 -*-

"""
system.py
"""
import constants
import numpy as np

__all__ = ['System']

class System(object):
    """
    This class defines a generic system for simulation.
    """
    def __init__(self, dim=0, units=None, periodic=False, box=None, 
                 temperature=None):
        """ 
        Initialization of the system.
    
        Parameters
        ----------
        self : 
        dim : int optional. The dimensionality.
        periodic : boolean, optional. True = the system has periodic boundaries. 
        box : list, optional. System boundaries in the self.dim dimensions.
        temperature : float, optional. The temperature of the system.

        Returns
        -------
        N/A, but sets derived variables:
        self.beta : float, inverse of (kB*T).
        """
        self.dim = dim 
        self.periodic = periodic # use periodic boundaries?
        self.box = box # simulation box
        self.temperature = temperature
        if not self.temperature:
            self.beta = None
        else:
            self.beta = 1.0/(self.temperature*constants.kB[units])
        # intialize other variables:
        self.v_pot = 0.0 # stores the potential energy of the system
        self.npart = 0
        self.particles = {'r': None, 'v': None, 'f':None,
                          'name': []}
        self.forcefield = None
        # Note for future: might consider making a
        # particle object, but its very convenient
        # for numpy to have d*N arrays with r, v, f, ... 
        # rather than a list of particles to loop over

    def add_particle(self, r=None, v=None, f=None, name='?'):
        """ 
        Adds a particle to the system.
    
        Parameters
        ----------
        self : 
        r : numpy.array, optional. The positions of the particle.
        v : numpy.array, optional. The velocities of the particle.
        f : numpy.array, optional. The forces on the particle.
        name : string, optional. The name of the particle.

        Returns
        -------
        N/A, but increments self.N and updates
        self.particles

        Note
        ----
        If no arguments are given a particle with name='?' will be
        created.
        """
        if not r: 
            r = np.zeros(self.dim)
        if not v: 
            v = np.zeros(self.dim)
        if not f: 
            f = np.zeros(self.dim)
        if self.npart == 0:
            self.particles = {'r': r, 'v': v, 'f': f, 'name': [name]}
        else:
            self.particles['name'].append(name)
            self.particles['r'] =  np.vstack([self.particles['r'], r])
            self.particles['v'] =  np.vstack([self.particles['v'], v])
            self.particles['f'] =  np.vstack([self.particles['f'], f])
        self.npart += 1

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
        return self.forcefield.evaluate_force(self.particles, **kwargs)

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
        self.particles['f'] = self.evaluate_force()

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
        args['r'] = kwargs.get('r', self.particles['r'])
        args['name'] = kwargs.get('name', self.particles['name'])
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
