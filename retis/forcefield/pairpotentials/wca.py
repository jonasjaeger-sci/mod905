# -*- coding: utf-8 -*-
"""This file contains a WCA pair potential."""
from __future__ import absolute_import
import numpy as np
from retis.forcefield.pairpotentials.lennardjones import PairLennardJonesCutnp
from retis.forcefield.potential import PotentialFunction
import warnings


__all__ = ['PairWCAnp', 'DoubleWellWCA']


class PairWCAnp(PairLennardJonesCutnp):
    """
    A simple WCA potential, based on the PairLennardJonesCutnp class.

    It is equal to the LJ potential with a shift of the energy and
    a cut-off set at sigma*2.**(1./6.)
    """

    def __init__(self, dim=3, mixing='geometric',
                 desc='WCA potential'):
        """Initiate the potential by inheriting from Lennard-Jones."""
        super(PairWCAnp, self).__init__(dim=dim, desc=desc, shift=True,
                                        factor=2.**(1./6.))


class DoubleWellWCA(PotentialFunction):
    """
    DoubleWellWCA(PotentialFunction).

    This class defines a n-dimensional Double Well potential.

    Attributes
    ----------
    params : dict
        Containins the parameters. These are:
        rzero : float
            Parameter for the potential, defines the two minima.
            One is located at rzero, the other at rzero+2*width
        width : float
            Parameter for the potential, describes the "width" of
            the potential.
        height : float
            Parameter for the potential, describes the "height" of
            the potential.
        types: set
            Types defines what kind of particle pairs to consider
            for this interaction. If types is not set (i.e. set to None),
            it will be assumed to apply to ALL partilces.
    """

    def __init__(self, dim=3, desc='A WCA double well potential'):
        """
        Initiate the Double Well potential.

        Parameters
        ----------
        dim : int, optional
            Setting for the dimensionality of the potential
        desc : string, optional.
            Description of the force field.

        Returns
        -------
        N/A
        """
        super(DoubleWellWCA, self).__init__(dim=dim, desc=desc)
        self.params = {'types': None, 'rzero': None, 'width': None,
                       'height': None}
        self.types = self.params.get('types', None)
        self.rzero = self.params.get('rzero', 0.0)
        self.width = self.params.get('width', 0.0)
        self.height = self.params.get('height', 0.0)
        self.width2 = 0.0
        self.rwidth = 0.0
        self.height4 = 0.0

    def add_parameters(self, parameters):
        """
        Add new potential parameters to the potential.

        Parameters
        ----------
        parameters : dict
            The new parameters, they are assume to be dicts of
            type {'types': set(('A','A')), 'rzero': 1.0, 'width': 0.25,
                  'height': 6.0}
        """
        for key in parameters:
            if key in self.params:
                self.params[key] = parameters[key]
            else:
                msg = 'Unknown parameter {} - ignored!'.format(key)
                warnings.warn(msg)
        self.types = self.params.get('types', None)
        if self.types is not None:
            self.types = set(self.types)
        self.rzero = self.params.get('rzero', 0.0)
        self.width = self.params.get('width', 0.0)
        self.height = self.params.get('height', 0.0)
        self.width2 = self.width**2
        self.rwidth = self.rzero + self.width
        self.height4 = 4.0 * self.height

    def update_parameters(self, parameters):
        """
        Update the potential parameters.

        For `DoubleWellWCA` this is identical to `self.add_parameters`, so
        we will just call that one.
        """
        self.add_parameters(parameters)

    def _activate(self, itype, jtype):
        """
        Determine if we should calculate a interaction or not.

        Parameters
        ----------
        itype : string
            Particle type for particle i
        jtype : string
            Particle type for particle j
        """
        if self.types is None:
            return True
        else:
            pair1, pair2 = (itype, jtype), (jtype, itype)
            return pair1 in self.types or pair2 in self.types

    def min_max(self):
        """
        Return the minima and the maximum of the `DoubleWellWCA` potential.

        The minima are located at `rzero` and ``rzero+2*width`` and the
        maximum at ``rzero+width``.

        Returns
        ------
        out[0] : float
            Minimum number one, located at: `rzero`.
        out[1] : float
            Minimum number two, located at: ``rzero+2*width``.
        out[2] : float
            Maximum, located at: ``rzero+width``.
        """
        return self.rzero, self.rzero+2.0*self.width, self.rzero+self.width

    def potential(self, particles, box):
        """
        Calculate the potential energy for the `DoubleWellWCA` potential.

        Parameters
        ----------
        particles : object as defined in retis.core.particles
            The particle list.
        box : object as defined in retis.core.box
            Representation of the box used in the simulation.

        Returns
        -------
        The potential energy as a float.
        """
        v_pot = 0.0
        for pair in particles.pairs():
            i, j, itype, jtype = pair
            if self._activate(itype, jtype):
                delta = box.pbc_dist_coordinate(particles.pos[i] -
                                                particles.pos[j])
                delr = np.sqrt(np.dot(delta, delta))
                v_pot += (self.height *
                          (1.0 - (((delr - self.rwidth)**2)/self.width2))**2)
        return v_pot

    def force(self, particles, box):
        """
        Calculate the force for the `DoubleWellWCA` potential.

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
        The force as a numpy.array of the same shape as the positions
        in particles.pos.
        """
        forces = np.zeros(particles.pos.shape)
        virial = np.zeros((box.dim, box.dim))
        for pair in particles.pairs():
            i, j, itype, jtype = pair
            if self._activate(itype, jtype):
                delta = box.pbc_dist_coordinate(particles.pos[i] -
                                                particles.pos[j])
                delr = np.sqrt(np.dot(delta, delta))
                forceij = (self.height4 *
                           (1.0 - (delr - self.rwidth)**2/self.width2) *
                           ((delr - self.rwidth)/self.width2))
                forceij = forceij * delta / delr
                forces[i] += forceij
                forces[j] -= forceij
                virial += np.outer(forceij, delta)
        return forces, virial

    def potential_and_force(self, particles, box):
        """
        Calculate the force and potential for the `DoubleWellWCA` potential.

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
        out[0] : float
            The potential energy as a float.
        out[1] : numpy.array
            The force as a numpy.array of the same shape as the positions
            in particles.pos.
        out[2] : numpy.array
            The virial, as a symmetric matrix with dimensions (dim, dim) where
            dim is given by the box.
        """
        forces = np.zeros(particles.pos.shape)
        virial = np.zeros((box.dim, box.dim))
        v_pot = 0.0
        for pair in particles.pairs():
            i, j, itype, jtype = pair
            if self._activate(itype, jtype):
                delta = box.pbc_dist_coordinate(particles.pos[i] -
                                                particles.pos[j])
                delr = np.sqrt(np.dot(delta, delta))
                v_pot += (self.height *
                          (1.0 - (delr - self.rwidth)**2/self.width2)**2)
                forceij = (self.height4 *
                           (1.0 - (delr - self.rwidth)**2/self.width2) *
                           ((delr - self.rwidth)/self.width2))
                forceij = forceij * delta / delr
                forces[i] += forceij
                forces[j] -= forceij
                virial += np.outer(forceij, delta)
        return v_pot, forces, virial
