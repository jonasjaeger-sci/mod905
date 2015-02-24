# -*- coding: utf-8 -*-
"""
This file contains different pair potentials
"""
from __future__ import absolute_import
import numpy as np
import itertools
import warnings

from .potential import PotentialFunction
from . import forcefield

__all__ = ['PairLennardJonesCut']


class PairLennardJonesCut(PotentialFunction):
    """
    A Lennard-Jones 6-12 potential with a simple cut-off.

    Attributes
    ----------
    params : dict
        The parameters for the potential. This is assumed to be defined
        by the force field. Some of the parameters are defined implicitly
        and are generated from the other parameters. The parameters
        are `epsilon`, `sigma` and `rcut` which defines the potential
        parameters and `factor` and `mixing` which are used when creating
        the derived parameters `epsilon_ij`, `sigma_ij`, `rcut_ij`.
    lj1 : dict
        Lennard Jones parameters used for calculation of the force.
        Keys are the pairs (particle types) that may interact.
        Calculated as: 48.0 * epsilon_ij * sigma_ij**12
    lj2 : dict
        Lennard Jones parameters used for calculation of the force.
        Keys are the pairs (particle types) that may interact.
        Calculated as: 24.0 * epsilon_ij * sigma_ij**6
    lj3 : dict
        Lennard Jones parameters used for calculation of the potential.
        Keys are the pairs (particle types) that may interact.
        Calculated as: 4.0 * epsilon_ij * sigma_ij**12
    lj4 : dict
        Lennard Jones parameters used for calculation of the potential.
        Keys are the pairs (particle types) that may interact.
        Calculated as: 4.0 * epsilon_ij * sigma_ij**6
    offset : dict
        Potential values for shifting the potential if requested.
        This is the potential evaluated at the cutoff.
    rcut2 : dict
        Squared cut-off for each interaction type.
        Keys are the paris (particle types) that may interact.
    matrix_np : dict of numpy arrays.
        Copies of the corresponding lj1, lj2, ... etc.
        Used as helper variables for numpy calculation of forces
        and potential.
    """
    def __init__(self, dim=3, mixing='geometric', factor=2.5,
                 shift=True,
                 desc='Lennard Jones pair potential with simple cut-off'):
        """
        Initialization of the force field

        Parameters
        ----------
        factor : float
            factor is used to calculate rcut if it's not explicitly given.
            rcut will then be equal to factor*sigma.
        shift : boolean
            determines if the potential will be shifted at the cutoff
            default is true since this is consistent with the force
        """
        super(PairLennardJonesCut, self).__init__(dim=dim, desc=desc)
        self.lj1 = {}
        self.lj2 = {}
        self.lj3 = {}
        self.lj4 = {}
        self.rcut2 = {}
        self.offset = {}
        self.params = {'epsilon': {}, 'sigma': {}, 'rcut': {},
                       'epsilon_ij': {}, 'sigma_ij': {}, 'rcut_ij': {},
                       'mixing': mixing, 'factor': factor,
                       'shift-potential': shift}
        self.matrix_np = {'lj1': [], 'lj2': [], 'lj3': [], 'lj4': [],
                          'rcut2': [], 'offset':[]}

    def update_parameters(self, params):
        """
        Updates the parameters for the potential, that is the
        values for 'epsilon', 'sigma' 'rcut', 'mixing', 'factor'.

        Parameters
        ----------
        params : dict
            The parameters to update.
        """
        special = ['mixing', 'factor']
        for key in special:
            self.params[key] = params.get(key, self.params[key])

        add_eps_sig, add_cut = False, False
        for i, parameter in params.items():
            if i in special:
                continue
            if all(key in parameter for key in ('epsilon', 'sigma')):
                # set both epsilon and sigma at the same time:
                self.params['epsilon'][i] = parameter['epsilon']
                sigma = parameter['sigma']
                self.params['sigma'][i] = sigma
                # generate rcut if it's not there...
                self.params['rcut'][i] = parameter.get('rcut',
                                                       self.params['factor'] *\
                                                       sigma)
                add_eps_sig = True
            else:
                # not both epsilon and sigma were specified, this only
                # makes sence if we just specify rcut for a pair-pair
                # interaction
                if 'rcut' in parameter and isinstance(i, tuple):
                    self.params['rcut'][i] = parameter['rcut']
                    j = tuple([k for k in reversed(i)])
                    self.params['rcut'][j] = parameter['rcut']
                    add_cut = True
                else:
                    msg = 'Did not understand parameter for: {}'.format(i)
                    warnings.warn(msg)
        if add_eps_sig:
            self._update_mixing_parameters()
            self._generate_lj_parameters()
        if add_eps_sig or add_cut:
            self._generate_rcut()
            self._generate_offsets()

    def add_parameters(self, parameters):
        """
        This method will add new potential parameters.

        Parameters
        ----------
        parameters : dict
            Tthe new parameters. They are assumed to be dicts
            of type {'A': {'epsilon': 1.0, 'sigma': 1.2, 'rcut': 2.0}}.
        """
        add_eps_sig, add_cut = False, False
        for i, params in parameters.items():
            if 'epsilon' in params and 'sigma' in params:
                self.params['epsilon'][i] = params['epsilon']
                sigma = params['sigma']
                self.params['sigma'][i] = sigma
                self.params['rcut'][i] = params.get('rcut',
                                                    self.params['factor'] *\
                                                    sigma)
                add_eps_sig = True
            else:
                if 'rcut' in params:
                    self.params['rcut'][i] = params['rcut']
                    j = tuple([k for k in reversed(i)])
                    self.params['rcut'][j] = params['rcut']
                    add_cut = True
        if add_eps_sig:
            self._update_mixing_parameters()
            self._generate_lj_parameters()
        if add_eps_sig or add_cut:
            self._generate_rcut()
            self._generate_offsets()

    def remove_parameter(self, particle):
        """
        This method will remove parameters for the specified particle

        Parameters
        ----------
        particle : string
            Identifier (particle type) for interaction to remove.

        Returns
        -------
        N/A, but modifies self.parameters, self.lj1, self.lj2, self.lj3,
        self.lj4, self.rcut2
        """
        remove_eps_sig = False
        try:
            del self.params['epsilon'][particle]
            del self.params['sigma'][particle]
            remove_eps_sig = True
        except KeyError:
            remove_eps_sig = False

        try:
            del self.params['rcut'][particle]
            remove_cut = True
        except KeyError:
            remove_cut = False

        if remove_eps_sig:
            self._update_mixing_parameters()
            self._generate_lj_parameters()
        if remove_eps_sig or remove_cut:
            self._generate_rcut()
            self._generate_offsets()

    def _generate_rcut(self):
        """
        This method will set rcut (and rcut2) for the different pair
        interactions. Here, it's possible that the rcut value for a pair
        is specified even though the sigma_ij and epsilon_ij are not. This
        is typicaly done when sigma_ij and epsilon_ij are generated and
        rcut_ij is explicitly set.

        Returns
        -------
        N/A, but modifies self.rcut2
        """
        rcut_ij = {}
        rcut2 = {}
        for i in self.params['epsilon_ij']:
            if i in self.params['rcut']:
                rcut_ij[i] = self.params['rcut'][i]
            elif i[0] == i[1]:
                rcut_ij[i] = self.params['rcut'][i[0]]
            else:
                rcut_ij[i] = self.params['sigma_ij'][i] * self.params['factor']
            rcut2[i] = rcut_ij[i]**2
        self.params['rcut_ij'] = rcut_ij
        self.rcut2 = rcut2

    def _generate_offsets(self):
        """
        This function will generate offset if shifting of the potential
        is requested.
        """
        self.offset = {}
        for i in self.params['epsilon_ij']:
            if isinstance(i, tuple):
                lj3 = self.lj3[i]
                lj4 = self.lj4[i]
                rcut2 = self.rcut2[i]
                if self.params['shift-potential']:
                    r2inv = 1.0/rcut2
                    r6inv = r2inv**3
                    vcut = r6inv * (lj3 * r6inv - lj4)
                else:
                    vcut = 0.0
                self.offset[i] = vcut

    def _make_tables_for_numpy(self, particles):
        """
        This is a helper function for using numpy.
        It is, perhaps, not so elegant as is will just create some new
        attributes to help with the calculation for forces and potential.
        It will, for each particle i store the particle types of the
        i+1 other atoms it will interact with in the force/potential
        calculation. This makes it possible to do slices of the parameters
        in the calculations.

        Paramters
        ---------
        particles : object
            The particle list.

        Returns
        -------
        N/A, but sets self.matrix_np
        """
        npart = particles.npart
        update = False
        try:
            update = not (len(self.matrix_np['lj1'][0]) == (npart - 1))
        except IndexError:
            update = True
        if update:
            try:  # "stupid" python2 <-3 hack
                xrange
            except NameError:
                xrange = range

            for key in self.matrix_np:
                self.matrix_np[key] = []
            for i, itype in enumerate(particles.ptype):
                rcut2, lj1, lj2, lj3, lj4 = [], [], [], [], []
                offset = []
                for j in xrange(i+1, npart):  # note xrange here -> hack above
                    jtype = particles.ptype[j]
                    rcut2.append(self.rcut2[itype, jtype])
                    lj1.append(self.lj1[itype, jtype])
                    lj2.append(self.lj2[itype, jtype])
                    lj3.append(self.lj3[itype, jtype])
                    lj4.append(self.lj4[itype, jtype])
                    offset.append(self.offset[itype, jtype])
                self.matrix_np['rcut2'].append(np.array(rcut2))
                self.matrix_np['lj1'].append(np.array(lj1))
                self.matrix_np['lj2'].append(np.array(lj2))
                self.matrix_np['lj3'].append(np.array(lj3))
                self.matrix_np['lj4'].append(np.array(lj4))
                self.matrix_np['offset'].append(np.array(offset))

    def force(self, particles, box):
        """
        This method calculates the force for the Lennard Jones
        interaction.

        We also calculate the virial here, since the force
        is evaluated.

        Parameters
        ----------
        particles : object as defined in retis.core.particles
            The particle list.
        box : object as defined in retis.core.box
            Representation of the box used in the simulation.

        Returns
        -------
        out[0] : numpy.array
            The force as a numpy.array of the same shape as the positions
            in particles.pos.
        out[1] : numpy.array
            The virial, as a symmetric matrix with dimensions (dim, dim) where
            dim is given by the box.
        """
        force = np.zeros(particles.pos.shape)
        virial = np.zeros((box.dim, box.dim))
        try:
            raise AttributeError
            #for pair in particles.pairs():
            #    i, j, itype, jtype = pair
            #    delta_pos = particles.pos[i]-particles.pos[j]
            #    delta = box.pbc_dist_coordinate(delta_pos)
            #    rsq = np.dot(delta, delta)
            #    if rsq < self.rcut2[itype, jtype]:
            #        r2inv = 1.0/rsq
            #        r6inv = r2inv**3
            #        forcelj = r2inv*r6inv * (self.lj1[itype, jtype]*r6inv -
            #                                 self.lj2[itype, jtype])
            #        forceij = forcelj*delta
            #        force[i] += forceij
            #        force[j] -= forceij
            #        virial += np.outer(forceij, delta)
        except AttributeError:
            self._make_tables_for_numpy(particles)
            for i, particle_i in enumerate(particles.pos[:-1]):
                delta = box.pbc_dist_matrix(particle_i - particles.pos[i+1:])
                rsq = np.einsum('ij, ij->i', delta, delta)
                k = np.where(rsq < self.matrix_np['rcut2'][i])[0]
                lj1 = self.matrix_np['lj1'][i][k]
                lj2 = self.matrix_np['lj2'][i][k]
                r2inv = 1.0/rsq[k]
                r6inv = r2inv**3
                forcelj = r2inv * r6inv * (lj1 * r6inv - lj2)
                forceij = np.einsum('i,ij->ij', forcelj, delta[k])
                force[i] += np.sum(forceij, axis=0)
                force[k+i+1] -= forceij
                virial += np.einsum('ij,ik->jk', forceij, delta[k])
        return force, virial

    def potential(self, particles, box):
        """
        This method calculates the potential energy for the Lennard Jones
        interaction.

        Parameters
        ----------
        particles : object as defined in retis.core.particles
            The particle list.
        box : object as defined in retis.core.box
            Representation of the box used in the simulation.

        Returns
        -------
        out : float
            The potential energy as a float.
        """
        v_pot = 0.0
        try:
            raise AttributeError
            #for pair in particles.pairs():
            #    i, j, itype, jtype = pair
            #    delta_pos = particles.pos[i]-particles.pos[j]
            #    delta = box.pbc_dist_coordinate(delta_pos)
            #    rsq = np.dot(delta, delta)
            #    if rsq < self.rcut2[itype, jtype]:
            #        r2inv = 1.0/rsq
            #        r6inv = r2inv**3
            #        v_pot += r6inv * (self.lj3[itype, jtype]*r6inv -
            #                          self.lj4[itype, jtype]) - self.offset[itype, type]
        except AttributeError:
            self._make_tables_for_numpy(particles)
            for i, particle_i in enumerate(particles.pos[:-1]):
                delta = box.pbc_dist_matrix(particle_i - particles.pos[i+1:])
                rsq = np.einsum('ij, ij->i', delta, delta)
                k = np.where(rsq < self.matrix_np['rcut2'][i])[0]
                lj3 = self.matrix_np['lj3'][i][k]
                lj4 = self.matrix_np['lj4'][i][k]
                offset = self.matrix_np['offset'][i][k]
                r2inv = 1.0/rsq[k]
                r6inv = r2inv**3
                v_pot += np.sum((r6inv * (lj3 * r6inv - lj4)-offset))
        return v_pot

    def potential_and_force(self, particles, box):
        """
        Method for calculating the potential and force for the
        Lennard-Jones interaction.

        Parameters
        ----------
        particles : object as defined in retis.core.particles
            The particle list.
        box : object as defined in retis.core.box
            Representation of the box used in the simulation.

        Note
        ----
        Currently, the virial is only calculated for the particles as a whole.
        It is not calculated as a virial per atom. The virial per atom might
        be useful to obtain a local pressure or stress, however this needs
        some consideration. Perhaps it's best to fully implement this as a
        method of planes or something similar. Some commented lines below are
        included to show how a per-atom virial can be obtained.

        Returns
        -------
        out[0] : float
            The potential energy as a float.
        out[1] : numpy.array
            The force as a numpy.array of the same shape as the positions
            in particles.pos.
        out[2] : numpy.array
            The virial, as a symmetric matrix with dimensions (dim, dim) where
            dim is given by the box.
        """
        v_pot = 0.0
        force = np.zeros(particles.pos.shape)
        virial = np.zeros((box.dim, box.dim))
        #virial2 = np.zeros((len(force),box.dim, box.dim))  # per atom virial
        try:
            raise AttributeError
            #for pair in particles.pairs():
            #    i, j, itype, jtype = pair
            #    delta_pos = particles.pos[i]-particles.pos[j]
            #    delta = box.pbc_dist_coordinate(delta_pos)
            #    rsq = np.dot(delta, delta)
            #    if rsq < self.rcut2[itype, jtype]:
            #        r2inv = 1.0/rsq
            #        r6inv = r2inv**3
            #        v_pot += r6inv * (self.lj3[itype, jtype]*r6inv
            #                           - self.lj4[itype, jtype]) - offset[itype, jtype]
            #        forcelj = r2inv*r6inv * (self.lj1[itype, jtype]*r6inv -
            #                                 self.lj2[itype, jtype])
            #        forceij = forcelj*delta
            #        force[i] += forceij
            #        force[j] -= forceij
            #        virial += np.outer(forceij, delta)
        except AttributeError:
            self._make_tables_for_numpy(particles)
            for i, particle_i in enumerate(particles.pos[:-1]):
                delta = particle_i - particles.pos[i+1:]
                delta = box.pbc_dist_matrix(delta)
                rsq = np.einsum('ij, ij->i', delta, delta)
                k = np.where(rsq < self.matrix_np['rcut2'][i])[0]
                lj1 = self.matrix_np['lj1'][i][k]
                lj2 = self.matrix_np['lj2'][i][k]
                lj3 = self.matrix_np['lj3'][i][k]
                lj4 = self.matrix_np['lj4'][i][k]
                offset = self.matrix_np['offset'][i][k]
                r2inv = 1.0/rsq[k]
                r6inv = r2inv**3
                v_pot += np.sum((r6inv * (lj3 * r6inv - lj4))-offset)
                forcelj = r2inv * r6inv * (lj1 * r6inv - lj2)
                forceij = np.einsum('i,ij->ij', forcelj, delta[k])
                force[i] += np.sum(forceij, axis=0)
                force[k+i+1] -= forceij
                #virialij = np.einsum('ij,ik->ijk', forceij, delta[k])
                #virialijs = np.sum(virialij, axis=0)
                virial += np.einsum('ij,ik->jk', forceij, delta[k])
                #virial += virialijs
                #virial2[i] += 0.5*virialijs  # per atom virial
                #virial2[k+i+1] += 0.5*virialij  # per atom virial
        return v_pot, force, virial

    def _generate_lj_parameters(self):
        """
        Method to calculate/generate all Lennard Jones parameters
        self.lj1, self.lj2, self.lj3, self.lj4 from the values defined
        in self.params.

        Parameters
        ----------
        N/A

        Returns
        -------
        None, but modifies self.lj1, self.lj2, self.lj3, self.lj4

        Note
        ----
        self.params is assumed to contain the parameters for all interactions,
        that is we assume that they are defined for ALL paris we might
        encounter. Typically, this requires that we have done some kind of
        mixing (by running self._) or that these are explicitly set.
        """
        self.lj1 = {}
        self.lj2 = {}
        self.lj3 = {}
        self.lj4 = {}
        for i in self.params['epsilon_ij']:
            if isinstance(i, tuple):
                epsilon_ij = self.params['epsilon_ij'][i]
                sigma_ij = self.params['sigma_ij'][i]
                self.lj1[i] = 48.0 * epsilon_ij * sigma_ij**12
                self.lj2[i] = 24.0 * epsilon_ij * sigma_ij**6
                self.lj3[i] = 4.0 * epsilon_ij * sigma_ij**12
                self.lj4[i] = 4.0 * epsilon_ij * sigma_ij**6

    def _update_mixing_parameters(self):
        """
        This method will update/create parameters for pairs, based
        on the parameters for atoms.

        Returns
        -------
        N/A, but will update self.params['epsilon_ij'] and
        self.params['sigma_ij'].
        """
        epsilon_ij, sigma_ij = {}, {}
        epsilon, sigma = self.params['epsilon'], self.params['sigma']
        for pair in itertools.product(epsilon.keys(), epsilon.keys()):
            i = pair[0]
            j = pair[1]
            epsilon_i, epsilon_j = epsilon[i], epsilon[j]
            sigma_i, sigma_j = sigma[i], sigma[j]
            if isinstance(i, tuple):
                # pair interaction is specified, assume that this is
                # intended:
                epsilon_ij[i], sigma_ij[i] = epsilon_i, sigma_i
                j = tuple([k for k in reversed(i)])
                epsilon_ij[j], sigma_ij[j] = epsilon_i, sigma_i
                continue
            if isinstance(j, tuple):
                epsilon_ij[j], sigma_ij[j] = epsilon_j, sigma_j
                i = tuple([k for k in reversed(j)])
                epsilon_ij[i], sigma_ij[i] = epsilon_j, sigma_j
                continue
            # generate:
            eps, sig = forcefield.mixing_parameters(epsilon_i, sigma_i,
                                                    epsilon_j, sigma_j,
                                                mixing=self.params['mixing'])
            if not (i, j) in epsilon_ij:
                epsilon_ij[i, j] = eps
                sigma_ij[i, j] = sig
            if not (j, i) in epsilon_ij:
                epsilon_ij[j, i] = epsilon_ij[i, j]
                sigma_ij[j, i] = sigma_ij[i, j]
        self.params['epsilon_ij'] = epsilon_ij
        self.params['sigma_ij'] = sigma_ij

    def str_parameters(self):
        """
        This method will just generate a string with the potential
        parameters and the generated pair parameters.

        Returns
        -------
        out : string
            Table with the parameters of all interactions.
        """
        strparam = ['Potential parameters, Lennard-Jones:']
        strparam.extend(['Mixing: {}'.format(self.params['mixing'])])
        atmformat = '{0:12s} {1:>9s} {2:>9s} {3:>9s}'
        atmformat2 = '{0:12s} {1:>9.4f} {2:>9.4f} {3:>9.4f}'
        atmformat3 = '{0:12s} {1:>9s} {2:>9s} {3:>9.4f}'
        strparam.append('Input parameters:')
        strparam.append(atmformat.format('Atom/pair', 'epsilon', 'sigma',
                                         'cut-off'))
        for i in self.params['epsilon']:
            epsilon = self.params['epsilon'][i]
            sigma = self.params['sigma'][i]
            rcut = self.params['rcut'][i]
            strparam.append(atmformat2.format(i, epsilon, sigma, rcut))
        for i in self.params['rcut']:
            if not i in self.params['epsilon']:
                rcut = self.params['rcut'][i]
                if isinstance(i, tuple):
                    stri = '{}-{}'.format(*i)
                else:
                    stri = '{}'.format(i)
                strparam.append(atmformat3.format(stri, '', '', rcut))
        strparam.append('Generated parameters:')
        strparam.append(atmformat.format('Atom/pair', 'epsilon', 'sigma',
                                         'cut-off'))
        for i in self.params['epsilon_ij']:
            epsilon = self.params['epsilon_ij'][i]
            sigma = self.params['sigma_ij'][i]
            rcut = self.params['rcut_ij'][i]
            if isintance(i, tuple):
                stri = '{}-{}'.format(*i)
            strparam.append(atmformat2.format(stri, epsilon, sigma, rcut))
        return '\n'.join(strparam)
