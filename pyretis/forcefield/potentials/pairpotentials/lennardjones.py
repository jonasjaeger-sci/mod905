# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""Module defining Lennard-Jones pair potentials.

This module defines the Lennard-Jones potential for pyretis.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PairLennardJonesCut
    A class represening a Lennard-Jones 6-12 potential implemented
    in pure python.

PairLennardJonesCutnp
    A class represening a Lennard-Jones 6-12 potential implemented
    with usage of numpy.
"""
from __future__ import absolute_import
import logging
import numpy as np
# pyretis imports
from pyretis.forcefield.potential import PotentialFunction
from .pairpotential import generate_pair_interactions

logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['PairLennardJonesCut', 'PairLennardJonesCutnp']


class PairLennardJonesCut(PotentialFunction):
    r"""class PairLennardJonesCut(PotentialFunction).

    This class implements as simple Lennard-Jones 6-12 potential which
    employs a simple cut-off and can be shifted. The potential energy
    (:math:`V_\text{pot}`) is defined in the usual way for an
    interacting pair of particles a distance :math:`r` apart,

    .. math::

       V_\text{pot} = 4 \varepsilon \left( x^{12} - x^{6} \right),

    where :math:`x = \sigma/r` and :math:`\varepsilon`
    and :math:`\sigma` are the potential parameters. The parameters are
    stored as attributes of the potential and we store one set for each
    kind of pair interaction. Parameters can be generated with a
    specific mixing rule by the force field.

    This implementation is in pure python (yes we are double looping!)
    and it is slow. It should not be used for production, please
    consider the numpy aware `PairLennardJonesCutnp` which is somewhat
    better.

    Attributes
    ----------
    params : dict
        The parameters for the potential. This dict is assumed to
        contain parameters for pairs, i.e. for interactions.
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

    def __init__(self, dim=3, shift=True, mixing='geometric',
                 desc='Lennard-Jones pair potential'):
        """Initiate the Lennard-Jones potential.

        Parameters
        ----------
        dim : int
            The dimensionality to use.
        shift : boolean
            Determines if the potential should be shifted or not.
        mixing : string
            Determines how we should mix potential parameters.
        """
        super(PairLennardJonesCut, self).__init__(dim=dim, desc=desc)
        self.shift = shift
        self._lj1 = {}
        self._lj2 = {}
        self._lj3 = {}
        self._lj4 = {}
        self._rcut2 = {}
        self._offset = {}
        self.params = {}
        self.mixing = mixing

    def set_parameters(self, parameters):
        """Update all parameters.

        Here, we generate pair interactions, since that is what this
        potential actually is using.

        Parameters
        ----------
        parameters : dict
            The input base parameters
        """
        self.params = {}
        pair_param = generate_pair_interactions(parameters, self.mixing)
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
            self.params[pair] = pair_param[pair]

    def __str__(self):
        """Generate a string with the potential parameters.

        It will generate a string with both pair and atom parameters.

        Returns
        -------
        out : string
            Table with the parameters of all interactions.
        """
        strparam = [self.desc]
        strparam += ['Potential parameters, Lennard-Jones:']
        useshift = 'yes' if self.shift else 'no'
        strparam.append('Shift potential: {}'.format(useshift))
        atmformat = '{0:12s} {1:>9s} {2:>9s} {3:>9s}'
        atmformat2 = '{0:12s} {1:>9.4f} {2:>9.4f} {3:>9.4f}'
        strparam.append('Pair parameters:')
        strparam.append(atmformat.format('Atom/pair', 'epsilon', 'sigma',
                                         'cut-off'))
        for pair in sorted(self.params):
            eps_ij = self.params[pair]['epsilon']
            sig_ij = self.params[pair]['sigma']
            rcut = np.sqrt(self._rcut2[pair])
            stri = '{}-{}'.format(*pair)
            strparam.append(atmformat2.format(stri, eps_ij, sig_ij, rcut))
        return '\n'.join(strparam)

    def potential(self, system):
        """Calculate the potential energy for the Lennard-Jones interaction.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`.
            The system for which we calculate the potential.

        Returns
        -------
        The potential energy as a float.
        """
        particles = system.particles
        box = system.box
        v_pot = 0.0
        for pair in particles.pairs():
            i, j, itype, jtype = pair
            delta = box.pbc_dist_coordinate(particles.pos[i] -
                                            particles.pos[j])
            rsq = np.dot(delta, delta)
            if rsq < self._rcut2[itype, jtype]:
                r2inv = 1.0/rsq
                r6inv = r2inv**3
                v_pot += (r6inv * (self._lj3[itype, jtype] * r6inv -
                                   self._lj4[itype, jtype]) -
                          self._offset[itype, jtype])
        return v_pot

    def force(self, system):
        """Calculate the force for the Lennard-Jones interaction.

        We also calculate the virial here, since the force
        is evaluated.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`.
            The system for which we calculate the force.

        Returns
        -------
        The force as a numpy.array of the same shape as the positions
        in `particles.pos`.
        """
        particles = system.particles
        box = system.box
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

    def potential_and_force(self, system):
        """Calculate potential and force for the Lennard-Jones interaction.

        Since the force is evaluated, the virial is also calculated.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`.
            The system for which we calculate the potential and force.

        Note
        ----
        Currently, the virial is only calculated for the particles as a
        whole. It is not calculated as a virial per atom. The virial
        per atom might be useful to obtain a local pressure or stress,
        however this needs some consideration. Perhaps it's best to
        fully implement this as a method of planes or something similar.

        Returns
        -------
        out[0] : float
            The potential energy as a float.
        out[1] : numpy.array
            The force as a numpy.array of the same shape as the
            positions in `particles.pos`.
        out[2] : numpy.array
            The virial, as a symmetric matrix with dimensions
            (dim, dim) where dim is given by the box/system dimensions.
        """
        particles = system.particles
        box = system.box
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
                v_pot += (r6inv * (self._lj3[itype, jtype] * r6inv -
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

    A Lennard-Jones 6-12 potential with a simple cut-off which can be
    shifted. `PairLennardJonesCutnp` uses numpy for calculations, i.e.
    most operations are recast as numpy.array operations. Otherwise it
    is similar to `PairLennardJonesCut`.
    """

    def __init__(self, dim=3, shift=True, mixing='geometric',
                 desc='Lennard-Jones pair potential (numpy)'):
        """Initiate the Lennard-Jones potential.

        Parameters
        ----------
        dim : int
            The dimensionality to use.
        shift : boolean
            Determines if the potential should be shifted or not.
        """
        super(PairLennardJonesCutnp, self).__init__(dim=dim, desc=desc,
                                                    shift=shift, mixing=mixing)

    def potential(self, system):
        """Calculate the potential energy for the Lennard-Jones interaction.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`.
            The system for which we calculate the potential.

        Returns
        -------
        out : float
            The potential energy as a float.
        """
        particles = system.particles
        box = system.box
        pot = 0.0
        # the particle list may implement a list which we can
        # loop over. This could be some kind of fancy neighborlist
        # here, we ignore this and loop over all pairs using numpy.
        for i, particle_i in enumerate(particles.pos[:-1]):
            itype = particles.ptype[i]
            delta = particle_i - particles.pos[i+1:]
            delta = box.pbc_dist_matrix(delta)
            rsq = np.einsum('ij, ij->i', delta, delta)
            k = np.where(_check_cutoff(self._rcut2, rsq,
                                       particles.ptype[i+1:],
                                       itype))[0]
            if len(k) > 0:
                r6inv = 1.0 / rsq[k]**3
                pot += np.sum(_pot_term(self._lj3, self._lj4, self._offset,
                                        r6inv, particles.ptype[k+i+1], itype))
        return pot

    def force(self, system):
        """Calculate the force for the Lennard-Jones interaction.

        We also calculate the virial here, since the force
        is evaluated.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`.
            The system for which we calculate the force.

        Note
        ----
        The way the "dim" is used may be reconsidered. There is
        already a self.dim parameter for the potential class.

        Returns
        -------
        out[0] : numpy.array
            The force as a numpy.array of the same shape as the
            positions in particles.pos.
        out[1] : numpy.array
            The virial, as a symmetric matrix with dimensions (dim, dim)
            where dim is given by the box.
        """
        particles = system.particles
        box = system.box
        forces = np.zeros(particles.pos.shape)
        virial = np.zeros((box.dim, box.dim))
        for i, particle_i in enumerate(particles.pos[:-1]):
            itype = particles.ptype[i]
            delta = particle_i - particles.pos[i+1:]
            delta = box.pbc_dist_matrix(delta)
            rsq = np.einsum('ij, ij->i', delta, delta)
            k = np.where(_check_cutoff(self._rcut2, rsq,
                                       particles.ptype[i+1:],
                                       itype))[0]
            if len(k) > 0:
                r2inv = 1.0 / rsq[k]
                r6inv = r2inv**3
                forcelj = _force_term(self._lj1, self._lj2, r2inv, r6inv,
                                      particles.ptype[k+i+1], itype)
                forceij = np.einsum('i,ij->ij', forcelj, delta[k])
                forces[i] += np.sum(forceij, axis=0)
                forces[k+i+1] -= forceij
                virial += np.einsum('ij,ik->jk', forceij, delta[k])
        return forces, virial

    def potential_and_force(self, system):
        """Calculate the potential & force for the Lennard-Jones interaction.

        We also calculate the virial here, since the force is evaluated.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`.
            The system for which we calculate the potential and force.

        Note
        ----
        Currently, the virial is only calculated for the particles as a
        whole. It is not calculated as a virial per atom. The virial per
        atom might be useful to obtain a local pressure or stress,
        however this needs some consideration. Perhaps it's best to
        fully implement this as a method of planes or something similar.

        Returns
        -------
        out[0] : float
            The potential energy as a float.
        out[1] : numpy.array
            The force as a numpy.array of the same shape as the
            positions in `particles.pos`.
        out[2] : numpy.array
            The virial, as a symmetric matrix with dimensions (dim, dim)
            where dim is given by the box.
        """
        particles = system.particles
        box = system.box
        pot = 0.0
        forces = np.zeros(particles.pos.shape)
        virial = np.zeros((box.dim, box.dim))
        for i, particle_i in enumerate(particles.pos[:-1]):
            itype = particles.ptype[i]
            delta = particle_i - particles.pos[i+1:]
            delta = box.pbc_dist_matrix(delta)
            rsq = np.einsum('ij, ij->i', delta, delta)
            k = np.where(_check_cutoff(self._rcut2, rsq,
                                       particles.ptype[i+1:],
                                       itype))[0]
            if len(k) > 0:
                jtype = particles.ptype[k+i+1]
                r2inv = 1.0 / rsq[k]
                r6inv = r2inv**3
                pot += np.sum(_pot_term(self._lj3, self._lj4, self._offset,
                                        r6inv, jtype, itype))
                forcelj = _force_term(self._lj1, self._lj2, r2inv, r6inv,
                                      jtype, itype)
                forceij = np.einsum('i,ij->ij', forcelj, delta[k])
                forces[i] += np.sum(forceij, axis=0)
                forces[k+i+1] -= forceij
                virial += np.einsum('ij,ik->jk', forceij, delta[k])
        return pot, forces, virial


@np.vectorize
def _pot_term(lj3, lj4, offset, r6inv, jtype, itype):
    """Lennard Jones potential term."""
    return (r6inv * (lj3[itype, jtype] * r6inv - lj4[itype, jtype]) -
            offset[itype, jtype])


@np.vectorize
def _force_term(lj1, lj2, r2inv, r6inv, jtype, itype):
    """Lennard Jones force term."""
    return r2inv * r6inv * (lj1[itype, jtype] * r6inv -
                            lj2[itype, jtype])


@np.vectorize
def _check_cutoff(rcut2, rsq, jtype, itype):
    """Check if we are close than the cut-off."""
    return rsq < rcut2[itype, jtype]
