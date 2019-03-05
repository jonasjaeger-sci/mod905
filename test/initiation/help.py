# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Some common methods for the tests."""
from contextlib import contextmanager
import logging
import numpy as np
from pyretis.core.box import create_box
from pyretis.core.particles import Particles
from pyretis.core.pathensemble import PathEnsemble
from pyretis.core.random_gen import MockRandomGeneratorBorg
from pyretis.core.system import System
from pyretis.engines.internal import MDEngine
from pyretis.forcefield import ForceField, PotentialFunction
from pyretis.inout.setup.createsimulation import create_path_ensembles
from pyretis.orderparameter import PositionVelocity
from pyretis.simulation.path_simulation import (
    SimulationRETIS,
    SimulationSingleTIS,
)


@contextmanager
def turn_on_logging():
    """Turn on logging so that tests can detect it."""
    logging.disable(logging.NOTSET)
    try:
        yield
    finally:
        logging.disable(logging.CRITICAL)


class MockEngine(MDEngine):
    """Create a fake engine for testing."""

    def __init__(self, timestep):
        """Set up the engine."""
        super().__init__(timestep, 'MockEngine', dynamics='Fake')
        self.direction = 1.0
        self.steps = 0
        self.reverse_after = 10

    def integration_step(self, system):
        """Do a fake integration step."""
        system.particles.pos += self.timestep * self.direction
        self.steps += 1
        if self.steps > self.reverse_after:
            self.steps = 0
            self.reverse_after += 10
            self.direction *= -1.0
        system.potential_and_force()

    def reset(self):
        """Reset attributes to initial values."""
        self.direction = 1.0
        self.steps = 0
        self.reverse_after = 10


class MockEngineOneWay(MDEngine):
    """Create a fake engine for testing."""

    def __init__(self, timestep):
        """Set up the engine."""
        super().__init__(timestep, 'MockEngineForward', dynamics='Fake')

    def integration_step(self, system):
        """Do a fake integration step."""
        system.particles.pos += self.timestep
        system.potential_and_force()


class MockEngineVelocitySupremacist(MDEngine):
    """Create a fake engine for testing."""

    def __init__(self, timestep):
        """Set up the engine."""
        super().__init__(timestep, 'MockEngineVelocitySupremacist',
                         dynamics='Fake')

    def integration_step(self, system):
        """Do a fake integration step."""
        if (system.particles.vel < 0).all():
            pass
        else:
            system.particles.pos += self.timestep
        system.potential_and_force()


class MockPotential(PotentialFunction):
    """Create a fake potential for testing."""

    def __init__(self):
        super().__init__(dim=1, desc='A fake potential')

    def potential(self, system):
        """Return the position of the particles."""
        return system.particles.pos.sum()

    def force(self, system):
        """Return the fake force and virial."""
        forces = system.particles.pos * -1.0
        virial = np.zeros((self.dim, self.dim))
        return forces, virial

    def potential_and_force(self, system):
        """Return the fake potential, force and virial."""
        pot = self.potential(system)
        forces, virial = self.force(system)
        return pot, forces, virial


def create_system():
    """Set up a system for testing."""
    box = create_box(periodic=[False])
    system = System(units='reduced', temperature=1.0, box=box)
    system.particles = Particles(dim=1)
    system.add_particle(-1.0 * np.ones((1, 1)))
    system.forcefield = ForceField(
        'Mock force field', potential=[MockPotential()]
    )
    return system


def create_test_retis_simulation():
    """Create a simple RETIS simulation."""
    interfaces = [-0.9, -0.5, 0.0]
    system = create_system()
    engine = MockEngine(0.0123)
    order_function = PositionVelocity(0, dim='x', periodic=False)
    ensembles, _ = create_path_ensembles(interfaces, 'internal',
                                         include_zero=True)
    settings = {
        'tis': {
            'freq': 0.5,
            'maxlength': 20000,
            'aimless': True,
            'allowmaxlength': False,
            'sigma_v': -1,
            'seed': 1,
            'rgen': 'to-be-ignored-and-replaced-below',
            'zero_momentum': False,
            'rescale_energy': False,
        },
        'retis': {
            'nullmoves': True,
        }
    }
    rgen_class = MockRandomGeneratorBorg.make_new_swarm()
    simulation = SimulationRETIS(
        system, order_function, engine, ensembles, settings,
        rgen=rgen_class(seed=0)
    )
    return simulation


def create_test_tis_simulation(engine_type='MockEngine', maxlength=20000):
    """Create a simple TIS simulation."""
    interfaces = [-0.9, -0.5, 0.0]
    system = create_system()
    engines = {
        'MockEngine': MockEngine,
        'MockEngineOneWay': MockEngineOneWay,
        'MockEngineVelocitySupremacist': MockEngineVelocitySupremacist,
    }
    engine = engines.get(engine_type)(0.0123)
    order_function = PositionVelocity(0, dim='x', periodic=False)
    ensemble = PathEnsemble(1, interfaces, 0.0)
    settings = {
        'tis': {
            'freq': 0.5,
            'maxlength': maxlength,
            'aimless': True,
            'allowmaxlength': False,
            'sigma_v': -1,
            'seed': 1,
            'rgen': 'to-be-ignored-and-replaced-below',
            'zero_momentum': False,
            'rescale_energy': False,
        },
    }
    rgen_class = MockRandomGeneratorBorg.make_new_swarm()
    simulation = SimulationSingleTIS(
        system, order_function, engine, ensemble, settings,
        rgen=rgen_class(seed=0)
    )
    return simulation
