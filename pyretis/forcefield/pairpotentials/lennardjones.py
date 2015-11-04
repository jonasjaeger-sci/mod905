# -*- coding: utf-8 -*-
"""Classes for Lennard-Jones pair potentials and variations."""
from __future__ import absolute_import
import numpy as np
import itertools
import warnings
from pyretis.forcefield.potential import PotentialFunction
from pyretis.forcefield import forcefield


__all__ = ['PairLennardJonesCut', 'PairLennardJonesCutnp']


class PairLennardJonesCut(PotentialFunction):
    """
    A Lennard-Jones 6-12 potential.

    The potential employs a simple cut-off and can be shifted.
    This implementation is in pure python (yes we are double looping) and
    is slow. It should not be used for production, rather consider the numpy
    aware `PairLennardJonesCutnp`.

    Attributes
    ----------
    params : dict
        The parameters for the potential. This is assumed to be defined
        by the force field. Some of the parameters are defined implicitly
        and are generated from the other parameters. The parameters
        are `epsilon`, `sigma` and `rcut` which defines the potential
        parameters and `factor` and `mixing` which are used when creating
        the derived parameters `epsilon`, `sigma`, `rcut`.
    lj1 : dict
        Lennard-Jones parameters used for calculation of the force.
        Keys are the pairs (particle types) that may interact.
        Calculated as: ``48.0 * epsilon * sigma**12``
    lj2 : dict
        Lennard-Jones parameters used for calculation of the force.
        Keys are the pairs (particle types) that may interact.
        Calculated as: ``24.0 * epsilon * sigma**6``
    lj3 : dict
        Lennard-Jones parameters used for calculation of the potential.
        Keys are the pairs (particle types) that may interact.
        Calculated as: ``4.0 * epsilon * sigma**12``
    lj4 : dict
        Lennard-Jones parameters used for calculation of the potential.
        Keys are the pairs (particle types) that may interact.
        Calculated as: ``4.0 * epsilon * sigma**6``
    offset : dict
        Potential values for shifting the potential if requested.
        This is the potential evaluated at the cutoff.
    rcut2 : dict
        Squared cut-off for each interaction type.
        Keys are the pairs (particle types) that may interact.
    """

    def __init__(self, dim=3, mixing='geometric', shift=True, factor=2.5,
                 desc='Lennard-Jones pair potential with simple cut-off'):
        """
        Initiate the Lennard-Jones potential.

        Parameters
        ----------
        dim : int
            The dimensionality to use.
        mixing : string
            Selection of mixing rule for the cross interactions.
        shift : boolean
            Determines if the potential should be shifted or not.
        factor : float
            The factor determines the cut-off, this is given as sigma
            times the factor.
        """
        super(PairLennardJonesCut, self).__init__(dim=dim, desc=desc)
        self.typeparams = {'epsilon': {}, 'sigma': {}, 'rcut': {},
                           'types': set()}
        self.pairparams = {'epsilon': {}, 'sigma': {}, 'rcut': {},
                           'pairs': set()}
        self.params = {'mixing': mixing, 'factor': factor,
                       'shift-potential': shift}
        self.lj1, self.lj2 = {}, {}
        self.lj3, self.lj4 = {}, {}
        self.rcut2 = {}
        self.offset = {}

    def add_parameters(self, parameters, mix=True):
        """
        Add new potential parameters for atoms or pairs.

        Parameters
        ----------
        parameters : dict
            The new parameters, they are assume to be dicts of
            type {'A': {'epsilon': 1.0, 'sigma': 1.0, 'rcut': 2.5}}
        mix : boolean
            If mix is true, the _generate_mixing_parameters will
            be executed. Default here is True since we probably need to
            generate parameters after adding new ones.
        """
        update_lj = False
        for key, params in parameters.items():
            if key in self.params:
                self.params[key] = params
                continue
            eps = params.get('epsilon', None)
            sigma = params.get('sigma', None)
            rcut = params.get('rcut', None)
            if eps is None:
                msg = 'epsilon for {} not set - ignoring!'.format(key)
                warnings.warn(msg)
                continue
            if sigma is None:
                msg = 'sigma for {} not set - ignoring!'.format(key)
                warnings.warn(msg)
                continue
            if rcut is None:
                factor = self.params['factor']
                rcut = factor * sigma
                msg = 'rcut for {} not given. Set to {}*{}'.format(key,
                                                                   factor,
                                                                   sigma)
                warnings.warn(msg)
            if isinstance(key, tuple):  # adding pair
                key_r = (key[1], key[0])
                for pair in [key, key_r]:
                    if pair in self.pairparams['pairs']:
                        msg = 'Pair {} already defined - ignored!'.format(key)
                        warnings.warn(msg)
                        continue
                    else:
                        self.pairparams['pairs'].add(pair)
                    self.pairparams['epsilon'][pair] = eps
                    self.pairparams['sigma'][pair] = sigma
                    self.pairparams['rcut'][pair] = rcut
                    update_lj = True
            else:  # adding atom
                if key in self.typeparams['types']:
                    msg = 'Atom {} already defined - ignored!'.format(key)
                    warnings.warn(msg)
                    continue
                else:
                    self.typeparams['types'].add(key)
                self.typeparams['epsilon'][key] = eps
                self.typeparams['sigma'][key] = sigma
                self.typeparams['rcut'][key] = rcut
                update_lj = True

        if update_lj:  # we have added new parameters
            if mix:
                self._generate_mixing_parameters()
            self._generate_lj_cut_offset()
        return update_lj

    def update_parameters(self, parameters, mix=False):
        """
        Update the parameters for the potential.

        Here, the values for 'epsilon', 'sigma' 'rcut', 'mixing', 'factor'
        are updated.

        Parameters
        ----------
        parameters : dict
            The parameters to update.
        mix : boolean
            If mix is true, the _generate_mixing_parameters will
            be executed. Default here is False, in case the user want
            to explicitly set some parameters.
        """
        update_lj = False
        for key, params in parameters.items():
            if key in self.params:
                if key == 'mixing' and params != self.params[key] and not mix:
                    msg = 'Mixing rule changed, but re-mixing not requested'
                    warnings.warn(msg)
                self.params[key] = params
            else:
                if isinstance(key, tuple):  # updating pair parameter
                    key_r = (key[1], key[0])
                    present = []
                    for i in [key, key_r]:
                        present.append(i in self.pairparams['pairs'])
                    if any(present):
                        update_lj = True
                        for i in params:
                            self.pairparams[i][key] = params[i]
                            self.pairparams[i][key_r] = params[i]
                    else:
                        msg = '{} not found, ignoring pair'.format(key)
                        warnings.warn(msg)
                else:
                    if key in self.typeparams['types']:
                        update_lj = True
                        for i in params:
                            self.typeparams[i][key] = params[i]
                    else:
                        msg = '{} not found, ignoring type'.format(key)
                        warnings.warn(msg)
        if mix:  # we might have to do re-mixing here independent of update_lj
            self._generate_mixing_parameters()
        if update_lj:
            self._generate_lj_cut_offset()
        return update_lj

    def _generate_mixing_parameters(self):
        """
        Generate parameters for pairs, based on the parameters for atoms.

        In order to generate the parameters, we will here make use of the
        defined mixing rule.
        """
        epsilon = self.typeparams['epsilon']
        sigma = self.typeparams['sigma']
        types = self.typeparams['types']
        rcut = self.typeparams['rcut']
        mix = self.params['mixing']
        for pair in itertools.product(types, types):
            i, j = pair
            # generate:
            eps, sig, cut = forcefield.mixing_parameters(epsilon[i], sigma[i],
                                                         rcut[i], epsilon[j],
                                                         sigma[j], rcut[j],
                                                         mixing=mix)
            self.pairparams['pairs'].add(pair)
            self.pairparams['epsilon'][pair] = eps
            self.pairparams['sigma'][pair] = sig
            self.pairparams['rcut'][pair] = cut

    def _generate_lj_cut_offset(self):
        """Generate Lennard-Jones parameters for the pair interactions."""
        self.lj1 = {}
        self.lj2 = {}
        self.lj3 = {}
        self.lj4 = {}
        self.rcut2 = {}
        self.offset = {}
        for pair in self.pairparams['pairs']:
            epsilon_ij = self.pairparams['epsilon'][pair]
            sigma_ij = self.pairparams['sigma'][pair]
            self.lj1[pair] = 48.0 * epsilon_ij * sigma_ij**12
            self.lj2[pair] = 24.0 * epsilon_ij * sigma_ij**6
            self.lj3[pair] = 4.0 * epsilon_ij * sigma_ij**12
            self.lj4[pair] = 4.0 * epsilon_ij * sigma_ij**6
            self.rcut2[pair] = self.pairparams['rcut'][pair]**2
            vcut = 0.0
            if self.params['shift-potential']:
                try:
                    rcut = sigma_ij / self.pairparams['rcut'][pair]
                    vcut = 4.0 * epsilon_ij * (rcut**12 - rcut**6)
                except ZeroDivisionError:
                    vcut = 0.0
            self.offset[pair] = vcut

    def str_parameters(self):
        """
        Generate a string with the potential parameters.

        It will generate a string with both pair and atom parameters.

        Returns
        -------
        out : string
            Table with the parameters of all interactions.
        """
        strparam = ['Potential parameters, Lennard-Jones:']
        strparam.extend(['Mixing: {}'.format(self.params['mixing'])])
        useshift = self.params['shift-potential']
        strparam.extend(['Shift potential: {}'.format(useshift)])
        atmformat = '{0:12s} {1:>9s} {2:>9s} {3:>9s}'
        atmformat2 = '{0:12s} {1:>9.4f} {2:>9.4f} {3:>9.4f}'
        strparam.append('Input parameters:')
        strparam.append(atmformat.format('Atom/pair', 'epsilon', 'sigma',
                                         'cut-off'))
        for i in self.typeparams['types']:
            epsilon = self.typeparams['epsilon'][i]
            sigma = self.typeparams['sigma'][i]
            rcut = self.typeparams['rcut'][i]
            strparam.append(atmformat2.format(i, epsilon, sigma, rcut))
        strparam.append('Pair parameters:')
        strparam.append(atmformat.format('Atom/pair', 'epsilon', 'sigma',
                                         'cut-off'))
        for i in self.pairparams['pairs']:
            epsilon = self.pairparams['epsilon'][i]
            sigma = self.pairparams['sigma'][i]
            rcut = self.pairparams['rcut'][i]
            stri = '{}-{}'.format(*i)
            strparam.append(atmformat2.format(stri, epsilon, sigma, rcut))
        return '\n'.join(strparam)

    def potential(self, particles, box):
        """
        Calculate the potential energy for the Lennard-Jones interaction.

        Parameters
        ----------
        particles : object like `Particles` from `pyretis.core.particles`
            The particle list.
        box : object like `Box` from `pyretis.core.box`
            Representation of the box used in the simulation.

        Returns
        -------
        The potential energy as a float.
        """
        v_pot = 0.0
        for pair in particles.pairs():
            i, j, itype, jtype = pair
            delta = box.pbc_dist_coordinate(particles.pos[i] -
                                            particles.pos[j])
            rsq = np.dot(delta, delta)
            if rsq < self.rcut2[itype, jtype]:
                r2inv = 1.0/rsq
                r6inv = r2inv**3
                v_pot += r6inv * ((self.lj3[itype, jtype] * r6inv -
                                   self.lj4[itype, jtype]) -
                                  self.offset[itype, jtype])
        return v_pot

    def force(self, particles, box):
        """
        Calculate the force for the Lennard-Jones interaction.

        We also calculate the virial here, since the force
        is evaluated.

        Parameters
        ----------
        particles : object like `Particles` from `pyretis.core.particles`
            The particle list.
        box : object like `Box` from `pyretis.core.box`
            Representation of the box used in the simulation.

        Returns
        -------
        The force as a numpy.array of the same shape as the positions
        in `particles.pos`.
        """
        forces = np.zeros(particles.pos.shape)
        virial = np.zeros((box.dim, box.dim))
        for pair in particles.pairs():
            i, j, itype, jtype = pair
            delta = box.pbc_dist_coordinate(particles.pos[i] -
                                            particles.pos[j])
            rsq = np.dot(delta, delta)
            if rsq < self.rcut2[itype, jtype]:
                r2inv = 1.0 / rsq
                r6inv = r2inv**3
                forcelj = r2inv * r6inv * (self.lj1[itype, jtype] * r6inv -
                                           self.lj2[itype, jtype])
                forceij = forcelj * delta
                forces[i] += forceij
                forces[j] -= forceij
                virial += np.outer(forceij, delta)
        return forces, virial

    def potential_and_force(self, particles, box):
        """
        Calculate potential and force for the Lennard-Jones interaction.

        Since the force is evaluated, the virial is also calculated.

        Parameters
        ----------
        particles : object like `Particles` from `pyretis.core.particles`
            The particle list.
        box : object like `Box` from `pyretis.core.box`
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
            in `particles.pos`.
        out[2] : numpy.array
            The virial, as a symmetric matrix with dimensions (dim, dim) where
            dim is given by the box.
        """
        v_pot = 0.0
        forces = np.zeros(particles.pos.shape)
        virial = np.zeros((box.dim, box.dim))
        for pair in particles.pairs():
            i, j, itype, jtype = pair
            delta = box.pbc_dist_coordinate(particles.pos[i] -
                                            particles.pos[j])
            rsq = np.dot(delta, delta)
            if rsq < self.rcut2[itype, jtype]:
                r2inv = 1.0 / rsq
                r6inv = r2inv**3
                v_pot += r6inv * ((self.lj3[itype, jtype] * r6inv -
                                   self.lj4[itype, jtype]) -
                                  self.offset[itype, jtype])
                forcelj = r2inv * r6inv * (self.lj1[itype, jtype] * r6inv -
                                           self.lj2[itype, jtype])
                forceij = forcelj * delta
                forces[i] += forceij
                forces[j] -= forceij
                virial += np.outer(forceij, delta)
        return v_pot, forces, virial


class PairLennardJonesCutnp(PairLennardJonesCut):
    """
    A Lennard-Jones 6-12 potential with a simple cut-off.

    The potential can be shifted. `PairLennardJonesCutnp` uses
    numpy for calculations, i.e. most operations are recast as
    vector operations.

    Attributes
    ----------
    matrix_np : dict
        This dict contains numpy matrix versions of the Lennard-Jones
        parameters.
    """

    def __init__(self, dim=3, mixing='geometric', shift=True, factor=2.5,
                 desc='Lennard-Jones pair potential with simple cut-off'):
        """
        Initiate the Lennard-Jones potential.

        Parameters
        ----------
        dim : int
            The dimensionality to use.
        mixing : string
            Selection of mixing rule for the cross interactions.
        shift : boolean
            Determines if the potential should be shifted or not.
        factor : float
            The factor determines the cut-off, this is given as sigma
            times the factor.
        """
        super(PairLennardJonesCutnp, self).__init__(dim=dim, desc=desc,
                                                    shift=shift,
                                                    factor=factor,
                                                    mixing=mixing)
        self.matrix_np = {'lj1': [], 'lj2': [], 'lj3': [], 'lj4': [],
                          'rcut2': [], 'offset': []}

    def _reset_matrix_np(self):
        """Reset `self.matrix_np`."""
        for key in self.matrix_np:
            self.matrix_np[key] = []

    def _generate_tables_for_numpy(self, particles):
        """
        Generate tables for interactions for use with numpy.

        This is a helper function since we are using numpy. It will create
        matrices for the Lennard-Jones parameters (lj1, lj2, lj3, lj4) the
        cut-offs and the offset.
        This makes it possible to do slices when calculating the energy. That
        is, instead of looping over particles explicitly in python, we can
        calculate interaction energies using numpy array.
        Of course, this is not viable for a very large system, then one would
        do something else like C or Fortran or a more clever division of the
        work.

        Parameters
        ----------
        particles : object
            The particle list.

        Returns
        -------
        out : None
            Returns `None` but updates `self.matrix_np` if required.
        """
        npart = particles.npart
        update = False
        try:  # this will only check for correct size
            update = not len(self.matrix_np['lj1'][0]) == (npart - 1)
        except IndexError:
            update = True
        if update:
            self._reset_matrix_np()
            for i, itype in enumerate(particles.ptype):
                rcut2, lj1, lj2, lj3, lj4 = [], [], [], [], []
                offset = []
                for jtype in particles.ptype[i+1:]:
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

    def potential(self, particles, box):
        """
        Calculate the potential energy for the Lennard-Jones interaction.

        Parameters
        ----------
        particles : object like `Particles` from `pyretis.core.particles`
            The particle list.
        box : object like `Box` from `pyretis.core.box`
            Representation of the box used in the simulation.

        Returns
        -------
        out : float
            The potential energy as a float.
        """
        pot = 0.0
        # the particle list may implement a list which we can
        # loop over. This could be some kind of fancy neghborlist
        # here, we ignore this and loop over all pairs using numpy.
        self._generate_tables_for_numpy(particles)
        for i, particle_i in enumerate(particles.pos[:-1]):
            delta = box.pbc_dist_matrix(particle_i - particles.pos[i+1:])
            rsq = np.einsum('ij, ij->i', delta, delta)
            k = np.where(rsq < self.matrix_np['rcut2'][i])[0]
            lj3 = self.matrix_np['lj3'][i][k]
            lj4 = self.matrix_np['lj4'][i][k]
            offset = self.matrix_np['offset'][i][k]
            r2inv = 1.0 / rsq[k]
            r6inv = r2inv**3
            pot += np.sum((r6inv * (lj3 * r6inv - lj4) - offset))
        return pot

    def force(self, particles, box):
        """
        Calculate the force for the Lennard-Jones interaction.

        We also calculate the virial here, since the force
        is evaluated.

        Parameters
        ----------
        particles : object like `Particles` from `pyretis.core.particles`
            The particle list.
        box : object like `Box` from `pyretis.core.box`
            Representation of the box used in the simulation.

        Note
        ----
        The way the "dim" is used may be reconsidered. There is
        already a self.dim parameter for the potential class.

        Returns
        -------
        out[0] : numpy.array
            The force as a numpy.array of the same shape as the positions
            in particles.pos.
        out[1] : numpy.array
            The virial, as a symmetric matrix with dimensions (dim, dim) where
            dim is given by the box.
        """
        forces = np.zeros(particles.pos.shape)
        virial = np.zeros((box.dim, box.dim))
        self._generate_tables_for_numpy(particles)
        for i, particle_i in enumerate(particles.pos[:-1]):
            delta = box.pbc_dist_matrix(particle_i - particles.pos[i+1:])
            rsq = np.einsum('ij, ij->i', delta, delta)
            k = np.where(rsq < self.matrix_np['rcut2'][i])[0]
            lj1 = self.matrix_np['lj1'][i][k]
            lj2 = self.matrix_np['lj2'][i][k]
            r2inv = 1.0 / rsq[k]
            r6inv = r2inv**3
            forcelj = r2inv * r6inv * (lj1 * r6inv - lj2)
            forceij = np.einsum('i,ij->ij', forcelj, delta[k])
            forces[i] += np.sum(forceij, axis=0)
            forces[k+i+1] -= forceij
            virial += np.einsum('ij,ik->jk', forceij, delta[k])
        return forces, virial

    def potential_and_force(self, particles, box):
        """
        Calculate the potential and force for the Lennard-Jones interaction.

        We also calculate the virial here, since the force
        is evaluated.

        Parameters
        ----------
        particles : object like `Particles` from `pyretis.core.particles`
            The particle list.
        box : object like `Box` from `pyretis.core.box`
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
        pot = 0.0
        forces = np.zeros(particles.pos.shape)
        virial = np.zeros((box.dim, box.dim))
        self._generate_tables_for_numpy(particles)
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
            r2inv = 1.0 / rsq[k]
            r6inv = r2inv**3
            pot += np.sum((r6inv * (lj3 * r6inv - lj4)) - offset)
            forcelj = r2inv * r6inv * (lj1 * r6inv - lj2)
            forceij = np.einsum('i,ij->ij', forcelj, delta[k])
            forces[i] += np.sum(forceij, axis=0)
            forces[k+i+1] -= forceij
            virial += np.einsum('ij,ik->jk', forceij, delta[k])
        return pot, forces, virial

    def add_parameters(self, parameters, mix=True):
        """
        Add parameters to the potential.

        Here, we run the `add_parameters` of the super class.
        This is done just in case the adding of parameters should trigger
        an update of `self.matrix_np`.
        """
        res = super(PairLennardJonesCutnp, self).add_parameters(parameters,
                                                                mix=mix)
        if res:
            self._reset_matrix_np()

    def update_parameters(self, parameters, mix=False):
        """
        Update parameters for the potential.

        This function will just run the `update_parameters` of the
        super class. This is done just in case the updating of
        parameters should trigger an update of `self.matrix_np`.
        """
        res = super(PairLennardJonesCutnp, self).update_parameters(parameters,
                                                                   mix=mix)
        if res:
            self._reset_matrix_np()
