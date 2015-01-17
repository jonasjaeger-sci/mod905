# -*- coding: utf-8 -*-
"""
This file contains one-dimensional potentials
"""

import numpy as np
from potential import PotentialFunction
import warnings

__all__ = ['DoubleWell', 'RectangularWell']

class DoubleWell(PotentialFunction):
    """One dimensional double well potential"""
    def __init__(self, a=1.0, b=1.0, c=0.0, desc='1D double well potential'):
        """ 
        Initiates the one dimensional double well potential.
        
        Parameters
        ---------- 
        self : 
        a : float, optional. 
        b : float, optional. 
        c : float, optional. 
        desc : string, optional. Description of the force field.
        
        Returns
        -------
        N/A
        """
        super(DoubleWell, self).__init__(dim=1, desc=desc)
        self.params = {'a': a, 'b': b, 'c': c}
        self.a = a
        self.b = b
        self.c = c

    def potential(self, r):
        """ 
        Evaluate the potential for the one-dimensional double well potential.
        
        Parameters
        ---------- 
        self : 
        r : numpy.array, the position.
        
        Returns
        -------
        The potential energy
        """
        v_pot = self.a*r**4 - self.b*(r - self.c)**2
        return v_pot.sum()

    def force(self, r):
        """ 
        Evaluate the force for the one-dimensional double well potential.
        
        Parameters
        ---------- 
        self : 
        r : the position.
        
        Returns
        -------
        N/A 
        """
        return -4.0*self.a*r**3+2.0*self.b*(r-self.c)


class RectangularWell(PotentialFunction):
    """One dimensional rectangular well"""
    def __init__(self, left=0.0, right=1.0, largenumber=1e10,
                 desc="1D Rectangular well potential"):
        """ 
        Initiates a one-dimensional rectangular well.
    
        Parameters
        ----------
        self : 
        left : float, optional. The left boundary of the potential.
        right : float, optional. The right boundary of the potential.
        largenumber : float, optional. The value of the potential outside 
            (left, right).
        desc : string, optional. Description of the force field.

        Returns
        -------
        N/A 
        """
        super(RectangularWell, self).__init__(dim=1, desc=desc)
        self.params = {'left': left, 'right': right,
                       'largenumber': largenumber}
        self.largenumber = largenumber
        #self.largenumber = float('inf') # possible to use this, NOTE FOR LATER
        self.left = left
        self.right = right

    def update_left_right(self, left, right):
        """ 
        Updates the boundaries.
        
        Parameters
        ---------- 
        self : 
        left : float. The left boundary of the potential.
        right : float. The right boundary of the potential.
        
        Returns
        -------
        N/A 
        """
        self.params['left'] = left
        self.params['right'] = right
        self.left = left
        self.right = right

    def potential(self, r):
        """ 
        Evaluate the potential. 
        
        Parameters
        ---------- 
        self : 
        r : the position.
        
        Returns
        -------
        The potential energy
        """
        v_pot = np.where(np.logical_and(r > self.left, r < self.right), 
                        0.0, self.largenumber)
        return v_pot.sum()


class PairLennardJonesCut(PotentialFunction):
    """
    A Lennard Jones 6-12 potential
    """
    def __init__(self, interactions=None, dim=3, factor=2.5,
                 mixing='geometric',
                 desc='Lennard Jones pair potential with simple cut-off'):
        """
        Initiates the Lennard-Jones potential
        interactions = {'a': {'sigma': 0.1, 'epsilon': 1.0, 'rcut':5.6},
                        'b': {'sigma': 0.2, 'epsilon': 2.0}}
        """
        super(PairLennardJonesCut, self).__init__(dim=dim, desc=desc)
        if interactions is None:
            interactions = {'?': {'sigma': 1.0, 'epsilon': 1.0,
                                  'rcut': 2.5}}
        self.factor = factor
        self.mixing = mixing
        self.epsilon_ij = {}
        self.sigma_ij = {}
        self.rcut_ij = {}
        self.interactions = {}
        self.all_interactions = {}
        self.lj1 = {}
        self.lj2 = {}
        self.lj3 = {}
        self.lj4 = {}
        self.add_interactions(interactions)

    def lj_force_and_potential(self, rsq, itype='?', jtype='?'):
        r2inv = 1.0/rsq
        r6inv = r2inv**3
        forcelj = r6inv * (self.lj1[itype, jtype]*r6inv - 
                  self.lj2[itype, jtype])
        forcelj *= r2inv
        energy = r6inv * (self.lj3[itype, jtype]*r6inv 
                 - self.lj4[itype, jtype])
        return forcelj, energy

    def lj_scalar_potential(self, rsq, itype='?', jtype='?'):
        r2inv = 1.0/rsq
        r6inv = r2inv**3
        energy = r6inv * (self.lj3[itype, jtype]*r6inv 
                 - self.lj4[itype, jtype])
        return energy
    
    def lj_scalar_force(self, rsq, itype='?', jtype='?'):
        r2inv = 1.0/rsq
        r6inv = r2inv**3
        forcelj = r6inv * (self.lj1[itype, jtype]*r6inv - 
                  self.lj2[itype, jtype])
        forcelj *= r2inv
        return forcelj
        

    def force_and_potential(self, particles):
        forces = np.zeros(particles.force.shape)
        v_pot = 0.0
        for pairs in particles.pairs:
            i, j, type_i, type_j = pairs
            delta_r = particles.pos[i] - particles.pos[j]
            rsq = np.dot(delta_r, delta_r)
            if rsq < self.rcut_ij[type_i, type_j]:
                force, energy = self.lj_force_and_potential(self, rsq,itype=type_i, jtype=type_j)
                force *= delta_r
                forces[i, j] += force
                forces[j, i] -= force
                v_pot += energy
        return forces, v_pot

    def force(self, particles, box):
        forces = np.zeros(particles.force.shape)
        for pairs in particles.pairs:
            i, j, type_i, type_j = pairs
            delta_r = particles.pos[i] - particles.pos[j]
            rsq = np.dot(delta_r, delta_r)
            if rsq < self.rcut_ij[type_i, type_j]:
                force = delta_r * self.lj_scalar_force(rsq, 
                                               itype=type_i, jtype=type_j)
                forces[i, j] += force
                forces[j, i] -= force
        return forces

    def potential(self, particles):
        v_pot = 0.0
        for pairs in particles.pairs:
            i, j, type_i, type_j = pairs
            delta_r = particles.pos[i] - particles.pos[j]
            rsq = np.dot(delta_r, delta_r)
            if rsq < self.rcut_ij[type_i, type_j]:
                v_pot += self.lj_scalar_potential(rsq, 
                                                  itype=type_i, jtype=type_j)
        return v_pot

    def add_interactions(self, interactions):
        for (i, inter_i) in interactions.items():
            if not ('sigma' in inter_i and 'epsilon' in inter_i):
                wsig = "Missing parameters in LJ interaction: {}".format(i)
                warnings.warn(wsig)
                continue
            self.interactions[i] = inter_i
        # update mixed values:
        self.epsilon_ij = {}
        self.sigma_ij = {}
        self._update_mixing_parameters()
        self._generate_rcut()
        self._generate_table()
        self._generate_lj_parameters()
    
    def _generate_lj_parameters(self):
        self.lj1 = {}
        self.lj2 = {}
        self.lj3 = {}
        self.lj4 = {}
        for i in self.epsilon_ij:
            if type(i) == type(()): 
                epsilon_ij = self.epsilon_ij[i]
                sigma_ij = self.sigma_ij[i]
                self.lj1[i] = 48.0 * epsilon_ij * sigma_ij**12
                self.lj2[i] = 24.0 * epsilon_ij * sigma_ij**6
                self.lj3[i] = 4.0 * epsilon_ij * sigma_ij**12
                self.lj4[i] = 4.0 * epsilon_ij * sigma_ij**6

    def _generate_table(self):
        self.all_interactions = {}
        for i in self.epsilon_ij:
            inter_i = {'sigma': self.sigma_ij[i], 
                       'epsilon': self.epsilon_ij[i],
                       'rcut': self.rcut_ij[i],
                       'generated': i in self.interactions}
            self.all_interactions[i] = inter_i

    def _generate_rcut(self):
        """
        To generate missing rcut
        """
        for (i, inter) in self.interactions.items():
            if not 'rcut' in inter:
                inter['rcut'] = inter['sigma']*self.factor
        
        for (i, sigma_ij) in self.sigma_ij.items():
            if i in self.interactions:
                self.rcut_ij[i] = self.interactions[i]['rcut']
            else:
                self.rcut_ij[i] = self.factor*sigma_ij

    def _update_mixing_parameters(self):
        for (i, inter_i) in self.interactions.items():
            epsilon_i = inter_i['epsilon']
            sigma_i = inter_i['sigma']
            if type(i)==type(()): # i defines a cross interaction, just copy
                self.epsilon_ij[i] = epsilon_i
                self.sigma_ij[i] = sigma_i
                continue
            for (j, inter_j) in self.interactions.items():
                epsilon_j = inter_j['epsilon']
                sigma_j = inter_j['sigma']
                if type(j)==type(()): # j defines a cross interaction, just copy
                    self.epsilon_ij[j] = epsilon_j
                    self.sigma_ij[j] = sigma_j
                    continue
                if self.mixing == 'geometric':
                    epsilon_ij = np.sqrt(epsilon_i * epsilon_j)
                    sigma_ij = np.sqrt(sigma_i * sigma_j)
                elif self.mixing == 'arithmetic':
                    epsilon_ij = np.sqrt(epsilon_i * epsilon_j)
                    sigma_ij = 0.5*(sigma_i + sigma_j)
                elif self.mixing == 'sixthpower':
                    epsilon_ij = (2.0 * np.sqrt(epsilon_i * epsilon_j) *\
                                 sigma_i**3 *  sigma_j**3) / \
                                 (sigma_i**6 + sigma_j**6)
                    sigma_ij = ((sigma_i**6 + sigma_j**6)*0.5)**(1./6.)
                else:
                    warnings.warn('Unknown mixing rule requested!')
                    epsilon_ij = 1.0
                    sigma_ij = 1.0
                if not (i, j) in self.epsilon_ij:
                    self.epsilon_ij[i, j] = epsilon_ij
                if not (i, j) in self.sigma_ij:
                    self.sigma_ij[i, j] = sigma_ij
                if not (i==j):
                    self.epsilon_ij[j, i] = epsilon_ij
                    self.sigma_ij[j, i] = sigma_ij
            
#class PairWCA(PairLJ_cut):
#    """ 
#    The WCA pair potential.
#    """
#    def __init__(self, epsilon=None, sigma=None,
#                 desc='WCA pair potential'):
#        """ 
#        Initiates the WCA potential.
#        
#        Parameters
#        ---------- 
#        self : 
#        desc : string, optional. Description of the force field.
#        
#        Returns
#        -------
#        N/A
#        """
#        rcut = {ptype: (2.0**(1./6.))*sigi for (ptype, sigi) in sigma}
#        super(PairWCA, self).__init__(dim=3, desc=desc)

