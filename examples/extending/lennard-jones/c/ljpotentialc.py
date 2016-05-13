# -*- coding: utf-8 -*-
"""Example of using a Lennard-Jones potential implemented in C."""
#from __future__ import absolute_import, print_function
import logging
#import sys
#import os
import numpy as np
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())
# pyretis imports
from pyretis.forcefield.potentials import PairLennardJonesCut
from pyretis.forcefield.potentials.pairpotentials import generate_pair_interactions
try:
    #HERE = os.path.abspath(os.path.dirname(__file__))
    #sys.path.insert(0, HERE)
    import ljc
    #del sys.path[0]
except ImportError:
    MSG = ('Could not import external C library.'
           '\nPlease compile with: "python setup.py build_ext --inplace"')
    logger.critical(MSG)
    raise ImportError(MSG)


__all__ = ['PairLennardJonesCutC']


class PairLennardJonesCutC(PairLennardJonesCut):
    r"""class PairLennardJonesCutC(PairLennardJonesCut).

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

    Attributes
    ----------
    params : dict
        The parameters for the potential. This dict is assumed to
        contain parameters for pairs, i.e. for interactions.
    _lj1 : numpy.array
        Lennard-Jones parameters used for calculation of the force.
        Keys are the pairs (particle types) that may interact.
        Calculated as: ``48.0 * epsilon * sigma**12``
    _lj2 : numpy.array
        Lennard-Jones parameters used for calculation of the force.
        Keys are the pairs (particle types) that may interact.
        Calculated as: ``24.0 * epsilon * sigma**6``
    _lj3 : numpy.array
        Lennard-Jones parameters used for calculation of the potential.
        Keys are the pairs (particle types) that may interact.
        Calculated as: ``4.0 * epsilon * sigma**12``
    _lj4 : numpy.array
        Lennard-Jones parameters used for calculation of the potential.
        Keys are the pairs (particle types) that may interact.
        Calculated as: ``4.0 * epsilon * sigma**6``
    _offset : numpy.array
        Potential values for shifting the potential if requested.
        This is the potential evaluated at the cutoff.
    _rcut2 : numpy.array
        Squared cut-off for each interaction type.
        Keys are the pairs (particle types) that may interact.
    """

    def __init__(self, dim=3, shift=True,
                 desc='Lennard-Jones pair potential (C)'):
        """Initiate the Lennard-Jones potential.

        Parameters
        ----------
        dim : int
            The dimensionality to use.
        shift : boolean
            Determines if the potential should be shifted or not.
        """
        super(PairLennardJonesCutC, self).__init__(dim=dim, desc=desc)
        self.ntype = 0

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
        pair_param = generate_pair_interactions(parameters)
        self.ntype = max(int(np.sqrt(len(pair_param))), 2)
        self._lj1 = np.zeros((self.ntype, self.ntype))
        self._lj2 = np.zeros_like(self._lj1)
        self._lj3 = np.zeros_like(self._lj1)
        self._lj4 = np.zeros_like(self._lj1)
        self._rcut2 = np.zeros_like(self._lj1)
        self._offset = np.zeros_like(self._lj1)
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
        v_pot = ljc.potential(particles.pos,
                              box.length, box.ilength,
                              self._lj3, self._lj4, self._offset,
                              self._rcut2, particles.ptype,
                              particles.npart,
                              box.dim, self.ntype)
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
        forces = np.zeros((particles.npart, box.dim))
        virial = np.zeros((box.dim, box.dim))
        ljc.force(particles.pos,
                  box.length, box.ilength,
                  self._lj1, self._lj2, self._rcut2,
                  particles.ptype,
                  forces, virial,
                  particles.npart,
                  box.dim, self.ntype)
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
        forces = np.zeros((particles.npart, box.dim))
        virial = np.zeros((box.dim, box.dim))
        vpot = ljc.force_and_pot(particles.pos,
                                 box.length,
                                 box.ilength,
                                 self._lj1,
                                 self._lj2,
                                 self._lj3,
                                 self._lj4,
                                 self._offset,
                                 self._rcut2,
                                 particles.ptype,
                                 forces,
                                 virial,
                                 particles.npart,
                                 box.dim,
                                 self.ntype)
        return vpot, forces, virial
