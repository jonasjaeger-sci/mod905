# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Time the Python implementation of the Lennard-Jones potential.

This timing is simply done by evaluating the Lennard-Jones forces
(and potential) for different system sizes.
"""
# pylint: disable=invalid-name
import timeit
import numpy as np
from pyretis.core import System, create_box, Particles
from pyretis.core.units import create_conversion_factors
from pyretis.tools import generate_lattice
from pyretis.forcefield.potentials import PairLennardJonesCut
from numba import jit


def set_up_initial_state(nlattice=5):
    """Create particles for the test.

    This will set up a 3D lattice with 4*nlattice**3 particles.
    """
    create_conversion_factors('lj')
    lattice, size = generate_lattice('fcc', [nlattice] * 3, density=0.9)
    npart = len(lattice)
    lattice += np.random.randn(npart, 3) * 0.05
    size = np.array(size)
    box = create_box(low=size[:, 0], high=size[:, 1],
                     periodic=[True, True, True])
    sys = System(temperature=1.0, units='lj', box=box)
    sys.particles = Particles(dim=3)
    for pos in lattice:
        sys.add_particle(name='Ar', pos=pos, mass=1.0, ptype=0)
    msg = 'Created lattice with {} atoms.'
    print(msg.format(sys.particles.npart))
    return sys


def test_wrapper(func, *args, **kwargs):
    """A simple wrapper for calling functions."""
    def wrapped():  # pylint: disable=missing-docstring
        return func(*args, **kwargs)
    return wrapped


def test_function(function, system, repeat=3, number=5):
    """Run the test for a function."""
    print('Testing function: {}'.format(function.__name__))
    wrapped = test_wrapper(function, system)
    res = timeit.repeat(wrapped, repeat=repeat, number=number)
    best = min(res) / float(number)
    avg = np.average([resi / float(number) for resi in res])
    std = np.std([resi / float(number) for resi in res])
    print('Best: {}'.format(best))
    print('Average: {} +- {}'.format(avg, std))
    return best, avg, std


@jit
def potential_numba(system, rcut2, lj3, lj4, offset):
    """Calculate the potential energy for the Lennard-Jones interaction.

    Parameters
    ----------
    system : object like :py:class:`.System`
        The system for which we calculate the potential.

    Returns
    -------
    The potential energy as a float.

    """
    particles = system.particles
    box = system.box
    v_pot = 0.0
    for i, itype in enumerate(particles.ptype[:-1]):
        for j, jtype in enumerate(particles.ptype[i+1:]):
            delta = box.pbc_dist_coordinate(particles.pos[i] -
                                            particles.pos[j])
            rsq = np.dot(delta, delta)
            if rsq < rcut2[itype, jtype]:
                r2inv = 1.0/rsq
                r6inv = r2inv**3
                v_pot += (r6inv * (lj3[itype, jtype] * r6inv -
                                   lj4[itype, jtype]) -
                          offset[itype, jtype])
    return v_pot


@jit
def force_numba(system, rcut2, lj1, lj2):
    """Calculate force for the Lennard-Jones interaction.

    Since the force is evaluated, the virial is also calculated.

    Parameters
    ----------
    system : object like :py:class:`.System`
        The system for which we calculate the potential and force.

    Note
    ----
    Currently, the virial is only calculated for all the particles.
    It is not calculated as a virial per atom. The virial
    per atom might be useful to obtain a local pressure or stress,
    however, this needs some consideration. Perhaps it's best to
    fully implement this as a method of planes or something similar.

    Returns
    -------
    out[1] : numpy.array
        The force as a numpy.array of the same shape as the
        positions in `particles.pos`.
    out[2] : numpy.array
        The virial, as a symmetric matrix with dimensions
        (dim, dim) where dim is given by the box/system dimensions.

    """
    particles = system.particles
    box = system.box
    forces = np.zeros(particles.pos.shape)
    virial = np.zeros((box.dim, box.dim))
    for i, itype in enumerate(particles.ptype[:-1]):
        for j, jtype in enumerate(particles.ptype[i+1:]):
            delta = box.pbc_dist_coordinate(particles.pos[i] -
                                            particles.pos[j])
            rsq = np.dot(delta, delta)
            if rsq < rcut2[itype, jtype]:
                r2inv = 1.0 / rsq
                r6inv = r2inv**3
                forcelj = r2inv * r6inv * (lj1[itype, jtype] * r6inv -
                                           lj2[itype, jtype])
                forceij = forcelj * delta
                forces[i] += forceij
                forces[j] -= forceij
                virial += np.outer(forceij, delta)
    return forces, virial


@jit
def potential_and_force_numba(system, rcut2, lj1, lj2, lj3, lj4, offset):
    """Calculate potential and force for the Lennard-Jones interaction.

    Since the force is evaluated, the virial is also calculated.

    Parameters
    ----------
    system : object like :py:class:`.System`
        The system for which we calculate the potential and force.

    Note
    ----
    Currently, the virial is only calculated for all the particles.
    It is not calculated as a virial per atom. The virial
    per atom might be useful to obtain a local pressure or stress,
    however, this needs some consideration. Perhaps it's best to
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
    npart = len(particles.ptype)
    for i in range(npart-1):
        itype = particles.ptype[i]
        posi = particles.pos[i]
        for j in range(i+1, npart):
            jtype = particles.ptype[j]
            posj = particles.pos[j]
            delta = box.pbc_dist_coordinate(posi - posj)
            rsq = delta[0]**2 + delta[1]**2 + delta[2]**2
            if rsq < rcut2[itype, jtype]:
                r2inv = 1.0 / rsq
                r6inv = r2inv**3
                v_pot += (r6inv * (lj3[itype, jtype] * r6inv -
                                   lj4[itype, jtype]) -
                          offset[itype, jtype])
                forcelj = r2inv * r6inv * (lj1[itype, jtype] * r6inv -
                                           lj2[itype, jtype])
                forceij = forcelj * delta
                forces[i] += forceij
                forces[j] -= forceij
                virial += np.outer(forceij, delta)
    return v_pot, forces, virial


class PairLennardJonesCutNumba(PairLennardJonesCut):
    """Lennard-Jones 6-12 potential in pure Python + Numba."""

    def potential(self, system):
        """Calculate the potential energy for the Lennard-Jones interaction.

        Parameters
        ----------
        system : object like :py:class:`.System`
            The system for which we calculate the potential.

        Returns
        -------
        The potential energy as a float.

        """
        v_pot = potential_numba(system, self._rcut2, self._lj3, self._lj4,
                                self._offset)
        return v_pot

    def force(self, system):
        """Calculate the force for the Lennard-Jones interaction.

        We also calculate the virial here, since the force
        is evaluated.

        Parameters
        ----------
        system : object like :py:class:`.System`
            The system for which we calculate the force.

        Returns
        -------
        The force as a numpy.array of the same shape as the positions
        in `particles.pos`.

        """
        forces, virial = force_numba(system, self._rcut2, self._lj1,
                                     self._lj2)
        return forces, virial

    def potential_and_force(self, system):
        """Calculate potential and force for the Lennard-Jones interaction.

        Since the force is evaluated, the virial is also calculated.

        Parameters
        ----------
        system : object like :py:class:`.System`
            The system for which we calculate the potential and force.

        Note
        ----
        Currently, the virial is only calculated for all the particles.
        It is not calculated as a virial per atom. The virial
        per atom might be useful to obtain a local pressure or stress,
        however, this needs some consideration. Perhaps it's best to
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
        v_pot, forces, virial = potential_and_force_numba(
            system,
            self._rcut2,
            self._lj1,
            self._lj2,
            self._lj3,
            self._lj4,
            self._offset
        )
        return v_pot, forces, virial


def main():
    """Run all test cases."""
    parameters = {0: {'sigma': 1.0, 'epsilon': 1.0, 'rcut': 2.5}}
    # set up potentials:
    potential = PairLennardJonesCutNumba(dim=3, shift=True, mixing='geometric')
    potential.set_parameters(parameters)

    results = []

    for i in range(3, 11):
        syst = set_up_initial_state(nlattice=i)
        print('Testing pure Python implementation')
        time1 = test_function(potential.potential_and_force,
                              syst, number=10, repeat=3)
        results.append((syst.particles.npart, time1[0], time1[1], time1[2]))
    results = np.array(results)
    np.savetxt('timings-python-numba.txt', results, fmt='%i %.9e %.9e %.9e',
               header='N best avg std')


if __name__ == '__main__':
    main()
