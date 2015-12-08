# -*- coding: utf-8 -*-
"""Classes for Lennard-Jones pair potentials and variations."""
from __future__ import absolute_import
import numpy as np
import logging
# pyretis imports
from pyretis.forcefield.potential import PotentialFunction
from .pairpotential import generate_pair_interactions

logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['PairLennardJonesCut', 'PairLennardJonesCutnp']


class PairLennardJonesCut(PotentialFunction):
    r"""class PairLennardJonesCut(PotentialFunction).

    This class implements as simple Lennard-Jones 6-12 potential which employs
    a simple cut-off and can be shifted. The potential energy
    (:math:`V_\text{pot}`) is defined in the usual way for an interacting pair
    of particles a distance :math:`r` apart,

    .. math::

       V_\text{pot} = 4 \varepsilon \left( x^{12} - x^{6} \right),

    where :math:`x = \sigma/r` and :math:`\varepsilon` and :math:`\sigma` are
    the potential parameters. The parameters are stored as attributes of the
    potential and we store one set for each kind of pair interaction.
    Parameters can be generated with a specific mixing rule by the force
    field.

    This implementation is in pure python (yes we are double looping) and it
    is slow. It should not be used for production, please consider the numpy
    aware `PairLennardJonesCutnp` which is somewhat better.

    Attributes
    ----------
    params : dict
        The parameters for the potential. This dict is assumed to contain
        parameters for pairs, i.e. for interactions.
    _lj1 : dict
        Lennard-Jones parameters used for calculation of the force.
        Keys are the pairs (particle types) that may interact.
        Calculated as: ``48.0 * epsilon * sigma**12``
    _lj2 : dict
        Lennard-Jones parameters used for calculation of the force.
        Keys are the pairs (particle types) that may interact.
        Calculated as: ``24.0 * epsilon * sigma**6``
    _lj3 : dict
        Lennard-Jones parameters used for calculation of the potential.
        Keys are the pairs (particle types) that may interact.
        Calculated as: ``4.0 * epsilon * sigma**12``
    _lj4 : dict
        Lennard-Jones parameters used for calculation of the potential.
        Keys are the pairs (particle types) that may interact.
        Calculated as: ``4.0 * epsilon * sigma**6``
    _offset : dict
        Potential values for shifting the potential if requested.
        This is the potential evaluated at the cutoff.
    _rcut2 : dict
        Squared cut-off for each interaction type.
        Keys are the pairs (particle types) that may interact.
    """

    def __init__(self, dim=3, shift=True, desc='Lennard-Jones pair potential'):
        """Initiate the Lennard-Jones potential.

        Parameters
        ----------
        dim : int
            The dimensionality to use.
        shift : boolean
            Determines if the potential should be shifted or not.
        factor : float
            The factor determines the cut-off, this is given as sigma
            times the factor.
        """
        super(PairLennardJonesCut, self).__init__(dim=dim, desc=desc)
        self.shift = shift
        self._lj1 = {}
        self._lj2 = {}
        self._lj3 = {}
        self._lj4 = {}
        self._rcut2 = {}
        self._offset = {}
        self._params = {}

    @property
    def params(self):
        """Return the parameters as a dict."""
        return self._params

    @params.setter
    def params(self, parameters):
        """Update all parameters.

        Here, we generate pair interactions, since that is what this potential
        actually is using.

        Parameters
        ----------
        parameters : dict
            The input base parameters
        """
        self._params = {}
        pair_param = generate_pair_interactions(parameters)
        for pair in pair_param:
            eps_ij = pair_param[pair]['epsilon']
            sig_ij = pair_param[pair]['sigma']
            rcut = pair_param[pair]['rcut']
            self._lj1[pair] = 48.0 * eps_ij * sig_ij**12
            self._lj2[pair] = 24.0 * eps_ij * sig_ij**6
            self._lj3[pair] = 4.0 * eps_ij * sig_ij**12
            self._lj4[pair] = 4.0 * eps_ij * sig_ij**6
            self._rcut2[pair] = rcut**2
            vcut = 0.0
            if self.shift:
                try:
                    vcut = 4.0 * eps_ij * ((sig_ij / rcut)**12 -
                                           (sig_ij / rcut)**6)
                except ZeroDivisionError:
                    vcut = 0.0
            self._offset[pair] = vcut
            self._params[pair] = pair_param[pair]

    @params.deleter
    def params(self):
        """Delete all parameters."""
        del self._params

    def __str__(self):
        """Generate a string with the potential parameters.

        It will generate a string with both pair and atom parameters.

        Returns
        -------
        out : string
            Table with the parameters of all interactions.
        """
        strparam = ['Potential parameters, Lennard-Jones:']
        useshift = 'yes' if self.shift else 'no'
        strparam.append('Shift potential: {}'.format(useshift))
        atmformat = '{0:12s} {1:>9s} {2:>9s} {3:>9s}'
        atmformat2 = '{0:12s} {1:>9.4f} {2:>9.4f} {3:>9.4f}'
        strparam.append('Pair parameters:')
        strparam.append(atmformat.format('Atom/pair', 'epsilon', 'sigma',
                                         'cut-off'))
        for pair in sorted(self._params):
            eps_ij = self._params[pair]['epsilon']
            sig_ij = self._params[pair]['sigma']
            rcut = np.sqrt(self._rcut2[pair])
            stri = '{}-{}'.format(*pair)
            strparam.append(atmformat2.format(stri, eps_ij, sig_ij, rcut))
        return '\n'.join(strparam)

    def potential(self, particles, box):
        """Calculate the potential energy for the Lennard-Jones interaction.

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
            if rsq < self._rcut2[itype, jtype]:
                r2inv = 1.0/rsq
                r6inv = r2inv**3
                v_pot += r6inv * ((self._lj3[itype, jtype] * r6inv -
                                   self._lj4[itype, jtype]) -
                                  self._offset[itype, jtype])
        return v_pot

    def force(self, particles, box):
        """Calculate the force for the Lennard-Jones interaction.

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
            if rsq < self._rcut2[itype, jtype]:
                r2inv = 1.0 / rsq
                r6inv = r2inv**3
                forcelj = r2inv * r6inv * (self._lj1[itype, jtype] * r6inv -
                                           self._lj2[itype, jtype])
                forceij = forcelj * delta
                forces[i] += forceij
                forces[j] -= forceij
                virial += np.outer(forceij, delta)
        return forces, virial

    def potential_and_force(self, particles, box):
        """Calculate potential and force for the Lennard-Jones interaction.

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
            if rsq < self._rcut2[itype, jtype]:
                r2inv = 1.0 / rsq
                r6inv = r2inv**3
                v_pot += r6inv * ((self._lj3[itype, jtype] * r6inv -
                                   self._lj4[itype, jtype]) -
                                  self._offset[itype, jtype])
                forcelj = r2inv * r6inv * (self._lj1[itype, jtype] * r6inv -
                                           self._lj2[itype, jtype])
                forceij = forcelj * delta
                forces[i] += forceij
                forces[j] -= forceij
                virial += np.outer(forceij, delta)
        return v_pot, forces, virial


class PairLennardJonesCutnp(PairLennardJonesCut):
    """class PairLennardJonesCutnp(PairLennardJonesCut).

    A Lennard-Jones 6-12 potential with a simple cut-off which can be shifted.
    `PairLennardJonesCutnp` uses numpy for calculations, i.e. most operations
    are recast as numpy.array operations. Otherwise it is similar to
    `PairLennardJonesCut`.

    Attributes
    ----------
    matrix_np : dict
        This dict contains numpy matrix versions of the Lennard-Jones
        parameters.
    """

    def __init__(self, dim=3, shift=True, desc='Lennard-Jones pair potential'):
        """Initiate the Lennard-Jones potential.

        Parameters
        ----------
        dim : int
            The dimensionality to use.
        shift : boolean
            Determines if the potential should be shifted or not.
        """
        super(PairLennardJonesCutnp, self).__init__(dim=dim, desc=desc,
                                                    shift=shift)
        self.matrix_np = {'lj1': [], 'lj2': [], 'lj3': [], 'lj4': [],
                          'rcut2': [], 'offset': []}

    def _reset_matrix_np(self):
        """Reset `self.matrix_np`."""
        for key in self.matrix_np:
            self.matrix_np[key] = []

    def _generate_tables_for_numpy(self, particles):
        """Generate tables for interactions for use with numpy.

        This is a helper function since we are using numpy. It will create
        matrices for the Lennard-Jones parameters (`lj1`, `lj2`, `lj3`, `lj4`)
        the cut-offs and the offset. This makes it possible to do slices when
        calculating the energy. That is, instead of looping over particles
        explicitly in python, we can calculate interaction energies using
        numpy array operations.
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
                    rcut2.append(self._rcut2[itype, jtype])
                    lj1.append(self._lj1[itype, jtype])
                    lj2.append(self._lj2[itype, jtype])
                    lj3.append(self._lj3[itype, jtype])
                    lj4.append(self._lj4[itype, jtype])
                    offset.append(self._offset[itype, jtype])
                self.matrix_np['rcut2'].append(np.array(rcut2))
                self.matrix_np['lj1'].append(np.array(lj1))
                self.matrix_np['lj2'].append(np.array(lj2))
                self.matrix_np['lj3'].append(np.array(lj3))
                self.matrix_np['lj4'].append(np.array(lj4))
                self.matrix_np['offset'].append(np.array(offset))

    def potential(self, particles, box):
        """Calculate the potential energy for the Lennard-Jones interaction.

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
        """Calculate the force for the Lennard-Jones interaction.

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
        """Calculate the potential & force for the Lennard-Jones interaction.

        We also calculate the virial here, since the force is evaluated.

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
