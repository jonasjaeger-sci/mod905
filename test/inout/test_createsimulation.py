# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the methods in pyretis.inout.setup.createsimulation"""
import os
import logging
import unittest
import numpy as np
from pyretis.engines.internal import VelocityVerlet
from pyretis.core.units import create_conversion_factors
from pyretis.core.system import System
from pyretis.core.particles import Particles
from pyretis.core.pathensemble import (
    PathEnsemble,
    PathEnsembleExt,
)
from pyretis.inout.setup.createsimulation import (
    create_path_ensemble,
    create_path_ensembles,
    create_nve_simulation,
    create_mdflux_simulation,
    create_umbrellaw_simulation,
    create_tis_simulations,
    create_retis_simulation,
    create_simulation,
)
from pyretis.tools.lattice import generate_lattice
from pyretis.forcefield.forcefield import ForceField
from pyretis.forcefield.potentials import PairLennardJonesCutnp
from pyretis.core.box import create_box
from pyretis.simulation.md_simulation import (
    SimulationNVE,
    SimulationMDFlux,
)
from pyretis.simulation.mc_simulation import (
    UmbrellaWindowSimulation,
)
from pyretis.simulation.path_simulation import (
    SimulationSingleTIS,
    SimulationRETIS,
)
from pyretis.inout.settings import SECTIONS
logging.disable(logging.CRITICAL)


HERE = os.path.abspath(os.path.dirname(__file__))


ORDER_ERROR_MSG = (
    'No order parameter was defined, but the '
    'engine *does* require it.'
)
MISSING_STEPS_ERROR_MSG = 'Simulation setting "steps" is missing!'
MISSING_INTERFACES_ERROR_MSG = 'Simulation setting "interfaces" is missing!'


def create_test_system():
    """Create a system we can use for testing."""
    create_conversion_factors('lj')
    xyz, size = generate_lattice('fcc', [2, 2, 2], density=0.9)
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


class TestMethods(unittest.TestCase):
    """Test some of the methods from .createsimulation."""

    def test_create_path_ensemble(self):
        """Test create_path_ensemble."""
        settings = {
            'simulation': {'interfaces': [-1., 0, 1]},
            'tis': {'detect': 0.8, 'ensemble_number': 2}
        }
        ensemble = create_path_ensemble(settings, 'internal')
        self.assertEqual(ensemble.ensemble_number, 2)
        self.assertAlmostEqual(ensemble.detect, 0.8)
        self.assertIsInstance(ensemble, PathEnsemble)
        ensemble = create_path_ensemble(settings, 'external')
        self.assertIsInstance(ensemble, PathEnsembleExt)
        self.assertEqual(ensemble.ensemble_number, 2)
        self.assertAlmostEqual(ensemble.detect, 0.8)
        # Test with some "missing" settings:
        settings = {'simulation': {'interfaces': [-1., 0., 1.]}, 'tis': {}}
        ensemble = create_path_ensemble(settings, 'internal')
        self.assertEqual(ensemble.ensemble_number, 1)
        self.assertAlmostEqual(ensemble.detect, 1.0)
        with self.assertRaises(ValueError):
            settings = {'simulation': {'interfaces': [-1., 0.]}}
            create_path_ensemble(settings, 'internal')

    def test_create_path_ensembles(self):
        """Test create_path_ensembles."""
        interfaces = [-1., 0., 1.0, 2.0]
        ensembles, detect = create_path_ensembles(interfaces, 'internal',
                                                  include_zero=True)
        for ens in ensembles:
            self.assertIsInstance(ens, PathEnsemble)
        for i, j in zip(detect, [0.0, 1.0, 2.0]):
            self.assertAlmostEqual(i, j)

    def test_create_nve_simulation(self):
        """Test create_nve_simulation."""
        system = create_test_system()
        engine = VelocityVerlet(0.002)
        settings = {'simulation': {'steps': 10}}
        sim = create_nve_simulation(settings, system, engine)
        self.assertIsInstance(sim, SimulationNVE)
        self.assertEqual(sim.simulation_type,
                         SimulationNVE.simulation_type)
        del settings['simulation']['steps']
        with self.assertRaises(ValueError):
            create_nve_simulation(settings, system, engine)

    def test_create_mdflux_simulation(self):
        """Test create_mdflux_simulation."""
        system = create_test_system()
        engine = VelocityVerlet(0.002)
        settings = {'simulation': {}}
        # Test that the setup fails without an order parameter,
        # when the engine requires it:
        with self.assertRaises(ValueError) as err:
            create_mdflux_simulation(settings, system, engine)
        self.assertEqual(ORDER_ERROR_MSG, str(err.exception))
        settings['orderparameter'] = {'class': 'Position',
                                      'dim': 'x', 'index': 0,
                                      'periodic': False}
        # Test that we fail because required setting "steps" are missing:
        with self.assertRaises(ValueError) as err:
            create_mdflux_simulation(settings, system, engine)
        self.assertEqual(MISSING_STEPS_ERROR_MSG, str(err.exception))
        settings['simulation']['steps'] = 10
        # Test that we fail because required setting "interfaces" are
        # missing:
        with self.assertRaises(ValueError) as err:
            create_mdflux_simulation(settings, system, engine)
        self.assertEqual(MISSING_INTERFACES_ERROR_MSG, str(err.exception))
        settings['simulation']['interfaces'] = [0, 1]
        sim = create_mdflux_simulation(settings, system, engine)
        self.assertIsInstance(sim, SimulationMDFlux)

    def test_create_umbrellawsimulation(self):
        """Test create_umbreallaw_simulation."""
        system = create_test_system()
        settings = {'simulation': {}}
        with self.assertRaises(ValueError):
            create_umbrellaw_simulation(settings, system)
        settings['simulation']['umbrella'] = [-1.0, 0.0]
        with self.assertRaises(ValueError):
            create_umbrellaw_simulation(settings, system)
        settings['simulation']['over'] = -0.5
        with self.assertRaises(ValueError):
            create_umbrellaw_simulation(settings, system)
        settings['simulation']['maxdx'] = 1.0
        with self.assertRaises(ValueError):
            create_umbrellaw_simulation(settings, system)
        settings['simulation']['mincycle'] = 10
        sim = create_umbrellaw_simulation(settings, system)
        self.assertIsInstance(sim, UmbrellaWindowSimulation)

    def test_create_tis_simulation(self):
        """Test create_tis_simulations."""
        system = create_test_system()
        engine = VelocityVerlet(0.002)
        settings = {
            'simulation': {
                'task': 'tis',
                'interfaces': [-1., 0., 1.],
            },
            'tis': SECTIONS['tis'],
        }
        # Test that the set up fails, when we did not define an
        # order parameter and the engine wants it:
        with self.assertRaises(ValueError) as err:
            create_tis_simulations(settings, system, engine)
        self.assertEqual(ORDER_ERROR_MSG, str(err.exception))
        # Continue testing with an order parameter defined:
        settings['orderparameter'] = {'class': 'Position',
                                      'dim': 'x', 'index': 0,
                                      'periodic': False}
        # Test that we fail when we are missing some settings:
        with self.assertRaises(ValueError) as err:
            create_tis_simulations(settings, system, engine)
        self.assertEqual(MISSING_STEPS_ERROR_MSG, str(err.exception))
        settings['simulation']['steps'] = 10
        sim = create_tis_simulations(settings, system, engine)
        self.assertIsInstance(sim, SimulationSingleTIS)

    def test_create_tis_simulations(self):
        """Test create_tis_simulations."""
        system = create_test_system()
        engine = VelocityVerlet(0.002)
        settings = {
            'simulation': {
                'task': 'tis-multiple',
                'interfaces': [-1., 0., 1., 2],
                'steps': 10,
            },
            'tis': SECTIONS['tis'],
            'orderparameter': {
                'class': 'Position',
                'dim': 'x',
                'index': 0,
                'periodic': False,
            },
            'output': SECTIONS['output'],
        }
        simulations = create_tis_simulations(settings, system, engine)
        for sim, i in zip(simulations, [1, 2, 3]):
            self.assertEqual(sim['tis']['ensemble_number'], i)

    def test_create_retis_simulation(self):
        """Test create_retis_simulations."""
        system = create_test_system()
        engine = VelocityVerlet(0.002)
        settings = {
            'simulation': {
                'task': 'retis',
                'interfaces': [-1., 0., 1.],
            },
            'tis': SECTIONS['tis'],
            'retis': SECTIONS['retis'],
        }
        # Test that we fail without an order parameter defined:
        with self.assertRaises(ValueError) as err:
            create_retis_simulation(settings, system, engine)
        self.assertEqual(ORDER_ERROR_MSG, str(err.exception))
        settings['orderparameter'] = {'class': 'Position',
                                      'dim': 'x', 'index': 0,
                                      'periodic': False}
        # Test that we fail when we are missing some settings:
        with self.assertRaises(ValueError) as err:
            create_retis_simulation(settings, system, engine)
        self.assertEqual(MISSING_STEPS_ERROR_MSG, str(err.exception))
        settings['simulation']['steps'] = 10
        sim = create_retis_simulation(settings, system, engine)
        self.assertIsInstance(sim, SimulationRETIS)

    def test_create_simulation(self):
        """Test create_simulation."""
        settings = {'simulation': {'task': 'does-not-exist'}}
        with self.assertRaises(ValueError):
            create_simulation(settings, None)

    def test_create_simulationnve(self):
        """Test create_simulation for NVE."""
        settings = {'simulation': {'task': 'does-not-exist'}}
        system = create_test_system()
        engine = VelocityVerlet(0.002)
        settings = {'simulation': {'steps': 10, 'task': 'md-nve'}}
        kwargs = {}
        with self.assertRaises(ValueError):
            create_simulation(settings, kwargs)
        kwargs = {'system': system}
        with self.assertRaises(ValueError):
            create_simulation(settings, kwargs)
        kwargs = {'system': system, 'engine': engine}
        sim = create_simulation(settings, kwargs)
        self.assertIsInstance(sim, SimulationNVE)

    def test_create_simulationmdflux(self):
        """Test create_simulation for MD-Flux."""
        system = create_test_system()
        engine = VelocityVerlet(0.002)
        settings = {
            'simulation': {
                'steps': 10,
                'task': 'md-flux',
                'interfaces': [-1.0],
            },
            'orderparameter': {
                'class': 'Position',
                'dim': 'x',
                'index': 0,
                'periodic': False
            },
        }
        kwargs = {}
        with self.assertRaises(ValueError):
            create_simulation(settings, kwargs)
        kwargs = {'system': system}
        with self.assertRaises(ValueError):
            create_simulation(settings, kwargs)
        kwargs = {'system': system, 'engine': engine}
        sim = create_simulation(settings, kwargs)
        self.assertIsInstance(sim, SimulationMDFlux)

    def test_create_simulationumb(self):
        """Test create_simulation for UmbrellaWindow."""
        system = create_test_system()
        settings = {
            'simulation': {
                'task': 'umbrellawindow',
                'umbrella': [-1.0, 0.0],
                'over': -0.5,
                'maxdx': 1.0,
                'mincycle': 10,
            },
            'orderparameter': {
                'class': 'Position',
                'dim': 'x',
                'index': 0,
                'periodic': False
            },
        }
        kwargs = {'system': system}
        sim = create_simulation(settings, kwargs)
        self.assertIsInstance(sim, UmbrellaWindowSimulation)

    def test_create_simulationtis1(self):
        """Test create_simulation for SimulationTIS single."""
        system = create_test_system()
        engine = VelocityVerlet(0.002)
        # TIS:
        settings = {
            'simulation': {
                'task': 'tis',
                'interfaces': [-1., 0., 1.],
                'steps': 10,
            },
            'tis': SECTIONS['tis'],
            'orderparameter': {
                'class': 'Position',
                'dim': 'x',
                'index': 0,
                'periodic': False,
            },
            'output': SECTIONS['output'],
        }
        kwargs = {'system': system, 'engine': engine}
        sim = create_simulation(settings, kwargs)
        self.assertIsInstance(sim, SimulationSingleTIS)

    def test_create_simulationtis2(self):
        """Test create_simulation for SimulationTIS multiple."""
        system = create_test_system()
        engine = VelocityVerlet(0.002)
        # TIS:
        settings = {
            'simulation': {
                'task': 'tis-multiple',
                'interfaces': [-1., 0., 1., 2.0],
                'steps': 10,
            },
            'tis': SECTIONS['tis'],
            'orderparameter': {
                'class': 'Position',
                'dim': 'x',
                'index': 0,
                'periodic': False,
            },
            'output': SECTIONS['output'],
        }
        kwargs = {'system': system, 'engine': engine}
        simulations = create_simulation(settings, kwargs)
        for sim, i in zip(simulations, [1, 2, 3]):
            self.assertEqual(sim['tis']['ensemble_number'], i)

    def test_create_simulationretis(self):
        """Test create_simulation for SimulationRETIS."""
        system = create_test_system()
        engine = VelocityVerlet(0.002)
        settings = {
            'simulation': {
                'steps': 10,
                'task': 'retis',
                'interfaces': [-1., 0., 1.],
            },
            'tis': SECTIONS['tis'],
            'retis': SECTIONS['retis'],
            'orderparameter': {
                'class': 'Position',
                'dim': 'x',
                'index': 0,
                'periodic': False,
            }
        }
        kwargs = {'system': system, 'engine': engine}
        sim = create_simulation(settings, kwargs)
        self.assertIsInstance(sim, SimulationRETIS)
        self.assertEqual(sim.path_ensembles[0].interfaces, (float('-inf'),
                                                            -1.0, -1.0))

    def test_create_simulationretis_zero_left(self):
        """Test create_simulation for SimulationRETIS with zero_lef defined."""
        system = create_test_system()
        engine = VelocityVerlet(0.002)
        settings = {
            'simulation': {
                'steps': 10,
                'task': 'retis',
                'interfaces': [-1., 0., 1.],
                'zero_left': -101
            },
            'tis': SECTIONS['tis'],
            'retis': SECTIONS['retis'],
            'orderparameter': {
                'class': 'Position',
                'dim': 'x',
                'index': 0,
                'periodic': False,
            }
        }
        kwargs = {'system': system, 'engine': engine}
        sim = create_simulation(settings, kwargs)
        self.assertIsInstance(sim, SimulationRETIS)
        self.assertEqual(sim.path_ensembles[0].interfaces, (-101,
                                                            -1.0, -1.0))


if __name__ == '__main__':
    unittest.main()
