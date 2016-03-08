# -*- coding: utf-8 -*-
"""Test the Fortran implementation of the Lennard Jones potential.

This test is comparing the three versions of the Lennard Jones
potential:

1) The pure python implementation

2) The numpy python implementation

3) The Fortran implementation.
"""
# pylint: disable=C0103
from __future__ import print_function
import numpy as np
from pyretis.core import System, Box
from pyretis.core.units import create_conversion_factors
from pyretis.forcefield.potentials import PairLennardJonesCut
from pyretis.forcefield.potentials import PairLennardJonesCutnp
from pyretis.tools import generate_lattice
from ljpotentialf import PairLennardJonesCutF
import timeit


def set_up_initial_state(nlattice=5):
    """Create particles for the test.

    This will set up a 3D lattice with 4*nlattice**3 particles.
    """
    create_conversion_factors('lj')
    lattice, size = generate_lattice('fcc', [nlattice] * 3, density=0.9)
    npart = len(lattice)
    lattice += np.random.randn(npart, 3) * 0.05
    box = Box(size, periodic=[True, True, True])
    sys = System(temperature=1.0, units='lj', box=box)
    for pos in lattice:
        sys.add_particle(name='Ar', pos=pos, mass=1.0, ptype=0)
    msg = 'Created lattice with {} atoms.'
    print(msg.format(sys.particles.npart))
    return sys


def test_wrapper(func, *args, **kwargs):
    """A simple wrapper for calling functions."""
    def wrapped():
        return func(*args, **kwargs)
    return wrapped


def test_function(function, particles, box, repeat=3, number=5):
    """Run the test for a function"""
    print('Testing function: {}'.format(function.__name__))
    wrapped = test_wrapper(function, particles, box)
    res = timeit.repeat(wrapped, repeat=repeat, number=number)
    best = min(res) / float(number)
    print('Best: {}'.format(best))
    print('Average: {} +- {}'.format(np.average(res) / float(number),
                                     np.std(res) / float(number)))
    return best


if __name__ == '__main__':
    parameters = {0: {'sigma': 1.0, 'epsilon': 1.0, 'rcut': 2.5},
                  'mixing': 'geometric'}
    # set up potentials:
    potential = PairLennardJonesCut(dim=3, shift=True)
    potential.set_parameters(parameters)

    potentialnp = PairLennardJonesCutnp(dim=3, shift=True)
    potentialnp.set_parameters(parameters)

    potentialf = PairLennardJonesCutF(dim=3, shift=True)
    potentialf.set_parameters(parameters)

    for i in range(3,11):
        # generate a fcc lattice:
        system = set_up_initial_state(nlattice=i)
        print('Testing pure python...')
        time1 = test_function(potential.potential_and_force,
                              system.particles, system.box,
                              number=10, repeat=3)
        print('Testing python/numpy')
        time2 = test_function(potentialnp.potential_and_force,
                              system.particles, system.box,
                              number=10, repeat=3)
        print('Testing python/fortran')
        time3 = test_function(potentialf.potential_and_force,
                              system.particles, system.box,
                              number=10, repeat=3)
