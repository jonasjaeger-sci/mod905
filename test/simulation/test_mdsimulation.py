# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the MD Simulation class."""
import logging
import unittest
import numpy as np
from pyretis.tools.lattice import generate_lattice
from pyretis.core.units import create_conversion_factors
from pyretis.core.box import create_box
from pyretis.core.system import System
from pyretis.core.particles import Particles
from pyretis.forcefield import ForceField
from pyretis.forcefield.potentials import (
    PairLennardJonesCutnp,
    DoubleWell,
)
from pyretis.simulation.md_simulation import (
    SimulationNVE,
    SimulationMDFlux,
)
from pyretis.engines.internal import VelocityVerlet, Langevin
from pyretis.orderparameter.orderparameter import OrderParameterPosition
logging.disable(logging.CRITICAL)


def create_test_system():
    """Just set up and create a simple test system."""
    create_conversion_factors('lj')
    xyz, size = generate_lattice('fcc', [3, 3, 3], density=0.9)
    size = np.array(size)
    box = create_box(low=size[:, 0], high=size[:, 1])
    system = System(units='lj', box=box, temperature=2.0)
    system.particles = Particles(dim=3)
    for pos in xyz:
        system.add_particle(pos, vel=np.zeros_like(pos),
                            force=np.zeros_like(pos),
                            mass=1.0, name='Ar', ptype=0)
    gen_settings = {'distribution': 'maxwell', 'momentum': True, 'seed': 0}
    system.generate_velocities(**gen_settings)
    potentials = [
        PairLennardJonesCutnp(dim=3, shift=True, mixing='geometric'),
    ]
    parameters = [
        {0: {'sigma': 1, 'epsilon': 1, 'rcut': 2.5}},
    ]
    system.forcefield = ForceField(
        'Lennard Jones force field',
        potential=potentials,
        params=parameters,
    )
    return system


def create_test_systemflux():
    """Just set up and create a simple test system."""
    create_conversion_factors('lj')
    box = create_box(periodic=[False])
    system = System(units='lj', box=box, temperature=2.0)
    system.particles = Particles(dim=1)
    pos = np.array([-1.0])
    system.add_particle(pos, vel=np.zeros_like(pos),
                        force=np.zeros_like(pos),
                        mass=1.0, name='Ar', ptype=0)
    gen_settings = {'distribution': 'maxwell', 'momentum': False, 'seed': 0}
    system.generate_velocities(**gen_settings)
    potentials = [
        DoubleWell(a=1., b=1., c=0.02),
    ]
    parameters = [
        {'a': 1.0, 'b': 1.0, 'c': 0.02},
    ]
    system.forcefield = ForceField(
        '1D Double Well force field',
        potential=potentials,
        params=parameters,
    )
    return system


class TestNVESimulation(unittest.TestCase):
    """Run the tests for NVESimulation class."""

    def test_md_simulation(self):
        """Test that we can create the simulation object."""
        system = create_test_system()
        engine = VelocityVerlet(0.002)
        simulation = SimulationNVE(system, engine, steps=10)
        for _ in simulation.run():
            pass
        self.assertTrue(
            np.allclose(system.particles.pos[0],
                        np.array([0.04907249, 0.00866652, 0.03147752]))
        )
        restart = simulation.restart_info()
        self.assertEqual(restart['type'], simulation.simulation_type)
        engine = Langevin(1.0, 2.0)
        logging.disable(logging.INFO)
        with self.assertLogs('pyretis.simulation.md_simulation',
                             level='WARNING'):
            SimulationNVE(system, engine, steps=10)
        logging.disable(logging.CRITICAL)


class TestMDFluxSimulation(unittest.TestCase):
    """Run the tests for MD Flux Simulation class."""

    def test_md_simulation(self):
        """Test that we can create the simulation object."""
        system = create_test_systemflux()
        engine = Langevin(0.002, 0.3)
        order = OrderParameterPosition(0, dim='x', periodic=False)
        interfaces = [-0.9]
        simulation = SimulationMDFlux(system, order, engine, interfaces,
                                      steps=10)
        for _ in simulation.run():
            pass
        self.assertTrue(simulation.leftside_prev[0])
        restart = simulation.restart_info()
        simulation2 = SimulationMDFlux(system, order, engine, interfaces,
                                       steps=100)
        self.assertEqual(simulation2.cycle['step'], 0)
        simulation2.load_restart_info(restart)
        self.assertEqual(simulation2.cycle['step'], 10)


if __name__ == '__main__':
    unittest.main()
