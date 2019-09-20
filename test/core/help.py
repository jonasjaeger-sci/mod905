# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Some common methods for the tests."""
from contextlib import contextmanager
import logging
import warnings
import numpy as np
from pyretis.core.box import create_box
from pyretis.core.system import System
from pyretis.core.particles import Particles
from pyretis.core.path import Path
from pyretis.core.random_gen import MockRandomGenerator
from pyretis.orderparameter import OrderParameter
from pyretis.engines.internal import MDEngine
from pyretis.forcefield import ForceField, PotentialFunction


@contextmanager
def turn_on_logging():
    """Turn on logging so that tests can detect it."""
    logging.disable(logging.NOTSET)
    try:
        yield
    finally:
        logging.disable(logging.CRITICAL)


class MockEngine(MDEngine):
    """An engine used for testing. It will not do actual dynamics."""

    def __init__(self, timestep, turn_around=20):
        """Just set the time step."""
        super().__init__(timestep, 'Engie McEngineface', dynamics='Fake')
        self.time = 0
        self.total_eclipse = turn_around  # every now and then
        self.delta_v = 0.0123456

    def integration_step(self, system):
        """Do a fake integration step."""
        self.time += 1
        particles = system.particles
        particles.pos += self.timestep * self.delta_v
        system.potential_and_force()
        if self.time > self.total_eclipse:
            self.time = 0
            self.delta_v *= -1.


class MockEngine2(MDEngine):
    """An engine used for testing. It will not do actual dynamics."""

    def __init__(self, timestep, interfaces):
        """Just set the time step."""
        super().__init__(timestep, 'Engie McEngineface', dynamics='Fake')
        self.time = 0
        self.delta_v = 0.0123456
        self.cross_left = False
        self.interfaces = interfaces

    def integration_step(self, system):
        """Do a fake integration step."""
        self.time += 1
        particles = system.particles
        if not self.cross_left:
            particles.pos += self.timestep * self.delta_v
            if particles.pos[0][0] < self.interfaces[0]:
                self.cross_left = True
                self.delta_v *= -1.
        system.potential_and_force()


class MockOrder(OrderParameter):
    """Just return the position as the order parameter."""

    def __init__(self):
        super().__init__(description='Ordey McOrderface')
        self.index = 0
        self.dim = 0

    def calculate(self, system):
        return [system.particles.pos[self.index][self.dim]]


class MockOrder2(OrderParameter):
    """Just return the position as the order parameter."""

    def __init__(self):
        super().__init__(description='Ordey McOrderface')

    def calculate(self, system):
        return [11.]


class NegativeOrder(OrderParameter):
    """An order parameter which is just the negative of the input order."""

    def __init__(self):
        """Set up the order parameter."""
        super().__init__(description='Mock order parameter', velocity=True)

    def calculate(self, system):
        """Return the negative order parameter."""
        order = system.order
        if order is None:
            return order
        return [i * -1 for i in order]


class SameOrder(OrderParameter):
    """An order parameter which is just the same as the input order."""

    def __init__(self):
        """Set up the order parameter."""
        super().__init__(description='Mock order parameter', velocity=False)

    def calculate(self, system):
        """Return the order parameter."""
        return system.order


class MockPotential(PotentialFunction):
    """Set the potential equal to `x**2`."""

    def __init__(self):
        super().__init__(dim=1, desc='Potey McPotentialface')

    def potential(self, system):
        # pylint: disable=no-self-use,missing-docstring
        pos = system.particles.pos
        vpot = pos**2
        return vpot.sum()

    def force(self, system):
        # pylint: disable=missing-docstring
        pos = system.particles.pos
        forces = pos * 1.0
        virial = np.zeros((self.dim, self.dim))
        return forces, virial

    def potential_and_force(self, system):
        # pylint: disable=missing-docstring
        pot = self.potential(system)
        force, virial = self.force(system)
        return pot, force, virial


def make_internal_system(order=None, pos=None, vel=None,
                         vpot=None, ekin=None):
    """Create a system for testing internal paths."""
    box = create_box(periodic=[False])
    system = System(units='reduced', temperature=1.0, box=box)
    system.particles = Particles(dim=1)
    system.forcefield = ForceField('empty force field',
                                   potential=[MockPotential()])
    system.order = order
    if pos is not None and vel is not None:
        for posi, veli in zip(pos, vel):
            system.add_particle(posi, vel=veli)
    # This is to ensure that the virial is set:
    system.potential_and_force()
    # Update with the given potential and kinetic energy:
    system.particles.vpot = vpot
    system.particles.ekin = ekin
    return system


def make_internal_path(start, end, maxorder, interface=None, points=100):
    """Return a dummy path.

    Parameters
    ----------
    start : tuple of floats
        The starting point for the path.
    end : tuple of floats
        The ending point for the path.
    maxorder : tuple of floats
        The maximum order parameter the path should attain.
    interface : integer or None
        The interface can be used to remove points from the path so
        that the path will be valid.
    points : integer, optional
        The number of points to add to the path.

    """
    xxx = [start[0], maxorder[0], end[0]]
    yyy = [start[1], maxorder[1], end[1]]
    warnings.simplefilter('ignore', np.RankWarning)
    par = np.polyfit(xxx, yyy, 2)
    xre = np.linspace(0., xxx[-1], points)
    yre = np.polyval(par, xre)
    # Delete some points from "yre" so that the path will be ok:
    if interface is not None:
        idx = [0]
        if yre[0] < interface:
            for i in np.where(yre > interface)[0]:
                idx.append(i)
        else:
            for i in np.where(yre < interface)[0]:
                idx.append(i)
        idx.append(-1)
        yre2 = [yre[i] for i in idx]
    else:
        yre2 = yre
    path = Path(rgen=MockRandomGenerator(seed=0))
    previous = None
    for order in yre2:
        if previous is None:
            vel = 0.0
        else:
            vel = order - previous
        ekin = 0.5 * vel**2
        phasepoint = make_internal_system(
            order=[order],
            pos=np.array([[order, ]]),
            vel=np.array([[vel, ]]),
            vpot=order**2,
            ekin=ekin
        )
        path.append(phasepoint)
        previous = order
    path.generated = ('fake', 0, 0, 0)
    path.maxlen = 10000
    return path
