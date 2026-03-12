# -*- coding: utf-8 -*-
# Copyright (c) 2026, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the MD Simulation class."""
from io import StringIO
import copy
import gzip
import logging
import math
import numpy as np
import os
import pathlib
import tempfile
import unittest
from pyretis.core.box import create_box
from pyretis.core.common import big_fat_comparer
from pyretis.core.particles import Particles
from pyretis.core.random_gen import create_random_generator
from pyretis.core.system import System
from pyretis.core.units import create_conversion_factors
from pyretis.engines.internal import VelocityVerlet, Langevin
from pyretis.forcefield import ForceField
from pyretis.forcefield.potentials import (
    PairLennardJonesCutnp,
    DoubleWell,
)
from pyretis.inout.simulationio import OutputTask
from pyretis.inout.screen import ScreenOutput
from pyretis.inout.settings import add_default_settings
from pyretis.orderparameter import PositionVelocity
from pyretis.simulation.md_simulation import (
    SimulationNVE,
    SimulationMDFlux,
)
from pyretis.tools.lattice import generate_lattice
from unittest.mock import patch
from .help import turn_on_logging, TxtWriter, TEST_SETTINGS

logging.disable(logging.CRITICAL)


HERE = os.path.abspath(os.path.dirname(__file__))


class ExtraAsserts:
    """Add additional assert method for crossing.

    This class is just for defining some additional methods which
    are useful when comparing crossing data in the unit tests.

    """

    @staticmethod
    def assert_equal_cross(cross1, cross2):
        """Assert that two lists of crossing data are equal."""
        if not len(cross1) == len(cross2):
            raise AssertionError('Length of crossing data differ!')
        for cri, crj in zip(cross1, cross2):
            for i, j in zip(cri, crj):
                if not i == j:
                    raise AssertionError(
                        f'Crossing data is not equal! {cri} != {crj}'
                        )

    def assert_equal_result(self, result1, result2, skip=None):
        """Compare result dictionaries from a simulation."""
        for key1 in result1.keys():
            if key1 not in result2:
                raise AssertionError(f'{key1} missing in result2')
        for key2 in result2.keys():
            if key2 not in result1:
                raise AssertionError(f'{key2} missing in result1')
        for key1, val1 in result1.items():
            if skip and key1 in skip:
                continue
            val2 = result2[key1]
            if len(val1) != len(val2):
                raise AssertionError(
                    f'Different no. of items for {key1}'
                )
            if key1 == 'thermo':
                self.assert_equal_thermo(val1, result2[key1])
            elif key1 == 'cycle':
                self.assert_equal_dict(val1, result2[key1])
            elif key1 == 'order':
                self.assert_equal_list(val1, result2[key1])
            else:
                raise AssertionError(
                    f'Comparison for {key1} not implemented'
                )

    @staticmethod
    def assert_equal_thermo(thermo1, thermo2):
        """Compare two thermo dictionaries."""
        for key1 in thermo1.keys():
            if key1 not in thermo2:
                raise AssertionError(f'{key1} missing in thermo2')
        for key2 in thermo2.keys():
            if key2 not in thermo1:
                raise AssertionError(f'{key2} missing in thermo1')
        for key1, val1 in thermo1.items():
            if key1 in ('press-tens', 'mom'):
                comp = np.allclose(val1, thermo2[key1])
            else:
                comp = math.isclose(val1, thermo2[key1])
            if not comp:
                raise AssertionError(f'Thermo {key1} differ!')

    @staticmethod
    def assert_equal_dict(dict1, dict2):
        """Compare two plain dicts."""
        for key1 in dict1:
            if key1 not in dict2:
                raise AssertionError(f'{key1} missing in dict2')
        for key2 in dict2:
            if key2 not in dict1:
                raise AssertionError(f'{key2} missing in dict1')
        for key1, val1 in dict1.items():
            if not math.isclose(val1, dict2[key1]):
                raise AssertionError(
                    f'Values for "{key1}" differ: {val1} != {dict2[key1]}!'
                    )

    @staticmethod
    def assert_equal_list(list1, list2):
        """Compare two plain lists."""
        if not len(list1) == len(list2):
            raise AssertionError('Lists have different length')
        for i, j in zip(list1, list2):
            if not math.isclose(i, j):
                raise AssertionError(f'Lists differ {i} != {j}')


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


def create_test_systemflux(temperature=2.0):
    """Just set up and create a simple test system."""
    create_conversion_factors('lj')
    box = create_box(periodic=[False])
    system = System(units='lj', box=box, temperature=temperature)
    system.particles = Particles(dim=1)
    pos = np.array([-1.0])
    system.add_particle(pos, vel=np.zeros_like(pos),
                        force=np.zeros_like(pos),
                        mass=1.0, name='Ar', ptype=0)
    gen_settings = {'distribution': 'maxwell', 'momentum': False, 'seed': 0}
    system.generate_velocities(**gen_settings)
    potentials = [
        DoubleWell(a=1., b=2., c=0.0),
    ]
    parameters = [
        {'a': 1.0, 'b': 2.0, 'c': 0.0},
    ]
    system.forcefield = ForceField(
        '1D Double Well force field',
        potential=potentials,
        params=parameters,
    )
    return system


def load_energy(filename):
    """Load energy data from the given file."""
    energies = []
    with gzip.open(filename, 'rt') as infile:
        for lines in infile:
            energy = [float(i) for i in lines.strip().split()]
            energies.append(energy)
    return energies


def load_traj(filename):
    """Load trajectory data from the given file."""
    snapshots = []
    snapshot = []
    with gzip.open(filename, 'rt') as infile:
        for lines in infile:
            if lines.startswith('# Snapshot'):
                if snapshot:
                    snapshots.append(snapshot)
                snapshot = []
            else:
                posvel = [float(i) for i in lines.strip().split()]
                snapshot.append(posvel)
    if snapshot:
        snapshots.append(snapshot)
    return snapshots


class TestNVESimulation(unittest.TestCase, ExtraAsserts):
    """Run the tests for NVESimulation class."""

    def test_md_simulation(self):
        """Test that we can create the simulation object."""
        system = create_test_system()
        engine = VelocityVerlet(0.002)
        simulation = SimulationNVE({'system': system, 'engine': engine},
                                   {'settings': 'empty'}, {'steps': 10})
        thermo = load_energy(os.path.join(HERE, 'md-thermo.txt.gz'))
        traj = load_traj(os.path.join(HERE, 'md-traj.txt.gz'))
        keys = ('temp', 'vpot', 'ekin', 'etot', 'press')

        def task1(simulation):
            """Dummy task for the simulation."""
            return f"Hello there {simulation.cycle['step']:03d}"

        task = {'func': task1, 'result': 'hello', 'args': (simulation,)}
        add = simulation.add_task(task)
        self.assertTrue(add)
        writer = ScreenOutput(
            TxtWriter(
                'test',
                header={'labels': ['Step', 'Message'], 'width': [9, 20]}
            )
        )

        simulation.output_tasks = [
            OutputTask('Hello-test', ['hello'], writer, {'every': 1}),
        ]

        with patch('sys.stdout', new=StringIO()):
            for i_s, (step, thermoi, snap) in enumerate(zip(simulation.run(),
                                                            thermo,
                                                            traj)):
                if i_s == 0:
                    self.assertFalse('hello' in step)
                else:
                    self.assertTrue('hello' in step)

                for i, key in enumerate(keys):
                    self.assertAlmostEqual(step['thermo'][key], thermoi[i])
                posvel = np.array(snap)
                system = step['system']
                self.assertTrue(
                    np.allclose(posvel[:, :3], system.particles.pos)
                )
                self.assertTrue(
                    np.allclose(posvel[:, 3:], system.particles.vel)
                )
                self.assertFalse('order' in step)
        restart = simulation.restart_info()
        self.assertEqual(restart['simulation']['type'],
                         simulation.simulation_type)
        engine = Langevin(1.0, 2.0, rgen=None)
        with turn_on_logging():
            with self.assertLogs('pyretis.simulation.md_simulation',
                                 level='WARNING'):
                SimulationNVE(ensemble={'system': system,
                                        'engine': engine},
                              settings={'all': 'empty'},
                              controls={'steps': 10})

    def test_soft_exit_md(self):
        """Test the soft exit method for md simulation."""
        settings = TEST_SETTINGS.copy()
        add_default_settings(settings)
        with tempfile.TemporaryDirectory() as tempdir:
            engine = VelocityVerlet(0.002)
            system = create_test_system()
            settings['simulation']['exe_path'] = tempdir
            simulation = SimulationNVE({'system': system, 'engine': engine},
                                       settings=settings,
                                       controls={'steps': 10})

            with patch('sys.stdout', new=StringIO()) as stdout:
                print(simulation)
            self.assertEqual('NVE simulation\nNumber of steps to do:'
                             ' 10\nMD engine: Velocity Verlet MD integrator\n'
                             'Time step: 0.002', stdout.getvalue().strip())

            simulation.set_up_output(settings)
            self.assertEqual(tempdir, simulation.exe_dir)

            with patch('sys.stdout', new=StringIO()):
                for i, _ in enumerate(simulation.run()):
                    if i > simulation.restart_freq:
                        break
            files = [i.name for i in os.scandir(tempdir)]
            self.assertEqual(4, len(files))
            self.assertIn('pyretis.restart', files)
            self.assertIn('traj.xyz', files)
            self.assertIn('energy.txt', files)
            self.assertIn('thermo.txt', files)
            exit_file = os.path.join(tempdir, 'EXIT')
            pathlib.Path(exit_file).touch()
            with patch('sys.stdout', new=StringIO()) as stdout:
                for _ in enumerate(simulation.run()):
                    pass
                self.assertIn('soft exit', stdout.getvalue().strip())
            self.assertEqual(simulation.cycle['step'],
                             simulation.restart_freq + 2)

    def test_md_simulation_old(self):
        """Test that we can create the simulation object."""
        system = create_test_system()
        engine = VelocityVerlet(0.002)
        simulation = SimulationNVE(ensemble={'system': system,
                                             'engine': engine},
                                   settings={'all': 'empty'},
                                   controls={'steps': 10})
        for _ in simulation.run():
            pass
        self.assertTrue(
            np.allclose(system.particles.pos[0],
                        np.array([0.04907249, 0.00866652, 0.03147752]))
        )
        restart = simulation.restart_info()
        self.assertEqual(restart['simulation']['type'],
                         simulation.simulation_type)
        engine = Langevin(1.0, 2.0, rgen=None)
        with turn_on_logging():
            with self.assertLogs('pyretis.simulation.md_simulation',
                                 level='WARNING'):
                SimulationNVE(ensemble={'system': system,
                                        'engine': engine},
                              settings={'all': 'empty'},
                              controls={'steps': 10})

    def test_md_simulation_restart(self):
        """Test that we can continue with the simulation object."""
        system1 = create_test_system()
        system2 = create_test_system()
        engine1 = VelocityVerlet(0.002)
        engine2 = VelocityVerlet(0.002)
        simulation1 = SimulationNVE(
            ensemble={'system': system1,
                      'engine': engine1},
            settings={'all': 'empty'},
            controls={'steps': 5})
        simulation2 = SimulationNVE(
            ensemble={'system': system2,
                      'engine': engine2},
            settings={'all': 'empty'},
            controls={'steps': 50})
        for _ in simulation1.run():
            pass

        restart1 = simulation1.restart_info()

        simulation1.cycle['steps'] = 50
        simulation1.cycle['endcycle'] = 50

        simulation2.load_restart_info(copy.deepcopy(restart1))

        simulation2.cycle['steps'] = 50
        simulation2.cycle['endcycle'] = 50

        for _ in simulation1.run():
            pass
        for _ in simulation2.run():
            pass

        info_parts = simulation1.restart_info()
        info_single = simulation2.restart_info()
        info_parts['system'] = simulation1.system.restart_info()
        info_single['system'] = simulation2.system.restart_info()

        self.assertTrue(np.allclose(info_parts['system']['box']['length'],
                                    info_single['system']['box']['length']))
        self.assertTrue(np.allclose(info_parts['system']['particles']['pos'],
                                    info_single['system']['particles']['pos']))
        self.assertTrue(np.allclose(info_parts['system']['particles']['vel'],
                                    info_single['system']['particles']['vel']))
        self.assertEqual(info_parts['simulation']['cycle']['steps'],
                         info_single['simulation']['cycle']['steps'])
        self.assertEqual(info_parts['system']['particles']['vpot'],
                         info_single['system']['particles']['vpot'])

        simulation1 = SimulationNVE(
            ensemble={'system': system1,
                      'engine': engine1},
            settings={'all': 'empty'},
            controls={'steps': 51})

        for _ in simulation1.run():
            pass

        info_parts = simulation1.restart_info()
        info_parts['system'] = simulation1.system.restart_info()

        self.assertFalse(
            np.allclose(info_parts['system']['particles']['pos'],
                        info_single['system']['particles']['pos']))
        self.assertFalse(
            np.allclose(info_parts['system']['particles']['vel'],
                        info_single['system']['particles']['vel']))
        self.assertNotEqual(info_parts['simulation']['cycle']['steps'],
                            info_single['simulation']['cycle']['steps'])
        self.assertNotEqual(info_parts['system']['particles']['vpot'],
                            info_single['system']['particles']['vpot'])

    def test_with_order(self):
        """Test that we can add order parameter to the simulation."""
        system = create_test_system()
        engine = VelocityVerlet(0.002)
        order = PositionVelocity(0, dim='x', periodic=False)
        simulation = SimulationNVE(
            ensemble={'system': system,
                      'order_function': order,
                      'engine': engine},
            settings={'all': 'empty'},
            controls={'steps': 3})
        correct = [
            [0.0, 2.4659841156924998],
            [0.0049319682313849998, 2.4655954880460191],
            [0.009862381952184078, 2.4644409982835884],
            [0.014789732224519354, 2.4625397443524371],
        ]
        for i, step in enumerate(simulation.run()):
            self.assertTrue('order' in step)
            self.assert_equal_list(correct[i], step['order'])

    def test_step(self):
        """Test the step method wrt. the run method."""
        system = create_test_system()
        engine = VelocityVerlet(0.002)
        order = PositionVelocity(0, dim='x', periodic=False)
        simulation = SimulationNVE(
            ensemble={'system': system,
                      'order_function': order,
                      'engine': engine},
            settings={'simulation': {}},
            controls={'steps': 3})
        results1 = []
        for step in simulation.run():
            results1.append(step)

        system = create_test_system()
        engine = VelocityVerlet(0.002)
        order = PositionVelocity(0, dim='x', periodic=False)
        simulation = SimulationNVE(
            ensemble={'system': system,
                      'order_function': order,
                      'engine': engine},
            settings={'simulation': {}},
            controls={'steps': 3})
        results2 = []
        while not simulation.is_finished():
            result = simulation.step()
            results2.append(result)

        self.assertEqual(len(results1), len(results2))
        for resulti, resultj in zip(results1, results2):
            self.assert_equal_result(resulti, resultj, skip=('system',))


class TestMDFluxSimulation(unittest.TestCase, ExtraAsserts):
    """Run the tests for MD Flux Simulation class."""

    def test_md_simulation(self):
        """Test that we can create the simulation from scratch & restart."""
        system = create_test_systemflux()
        rgen = create_random_generator({'seed': 0})
        engine = Langevin(0.002, 0.3, rgen)
        order = PositionVelocity(0, dim='x', periodic=False)
        interfaces = [-0.9]
        simulation = SimulationMDFlux(
            ensemble={'system': system,
                      'order_function': order,
                      'engine': engine},
            settings={'simulation': {'interfaces': interfaces}},
            controls={'steps': 10})
        for _ in simulation.run():
            pass
        self.assertTrue(simulation.leftside_prev[0])
        # Test loading of restart info:
        restart = simulation.restart_info()
        simulation2 = SimulationMDFlux(
            ensemble={'system': system,
                      'order_function': order,
                      'engine': engine},
            settings={'simulation': {'interfaces': interfaces}},
            controls={'steps': 100})
        self.assertEqual(simulation2.cycle['step'], 0)
        simulation2.load_restart_info(restart)
        self.assertEqual(simulation2.cycle['step'], 10)

    def test_flux_results(self):
        """Test the md-flux results."""
        system = create_test_systemflux(temperature=0.05)
        engine = Langevin(0.002, 0.3)
        order = PositionVelocity(0, dim='x', periodic=False)
        interfaces = [-0.99]
        simulation = SimulationMDFlux(
            ensemble={'system': system,
                      'order_function': order,
                      'engine': engine},
            settings={'simulation': {'interfaces': interfaces}},
            controls={'endcycle': 1000})

        correct = {
            19: [(19, 0, '+')],
            374: [(374, 0, '-')],
            855: [(855, 0, '+')],
        }

        for step in simulation.run():
            if step['cycle']['steps'] in correct:
                self.assert_equal_cross(correct[step['cycle']['steps']],
                                        step['cross'])

    def test_soft_exit_md_flux(self):
        """Test the soft exit method for MDflux method."""
        settings = TEST_SETTINGS.copy()
        add_default_settings(settings)
        with tempfile.TemporaryDirectory() as tempdir:
            system = create_test_systemflux()
            settings['simulation']['exe_path'] = tempdir
            rgen = create_random_generator({'seed': 0})
            engine = Langevin(0.002, 0.3, rgen)
            order = PositionVelocity(0, dim='x', periodic=False)
            interfaces = [-0.9]
            simulation = SimulationMDFlux(
                ensemble={'system': system,
                          'order_function': order,
                          'engine': engine},
                settings={'simulation': {'interfaces': interfaces,
                                         'exe_path': tempdir}},
                controls={'steps': 10})

            with patch('sys.stdout', new=StringIO()) as stdout:
                print(simulation)
            self.assertEqual('MD-flux simulation\nNumber of steps to do: 10'
                             '\nMolecular Dynamics engine: Langevin MD '
                             'integrator\nTime step: 0.002',
                             stdout.getvalue().strip())

            simulation.set_up_output(settings)
            self.assertEqual(tempdir, simulation.exe_dir)
            with patch('sys.stdout', new=StringIO()):
                for i, _ in enumerate(simulation.run()):
                    if i > simulation.restart_freq:
                        break
            files = [i.name for i in os.scandir(tempdir)]
            self.assertEqual(5, len(files))
            self.assertIn('pyretis.restart', files)
            self.assertIn('order.txt', files)
            self.assertIn('traj.xyz', files)
            self.assertIn('cross.txt', files)
            self.assertIn('energy.txt', files)

            exit_file = os.path.join(tempdir, 'EXIT')
            pathlib.Path(exit_file).touch()
            with patch('sys.stdout', new=StringIO()) as stdout:
                for _ in enumerate(simulation.run()):
                    pass
                self.assertIn('soft exit', stdout.getvalue().strip())
            self.assertEqual(simulation.cycle['step'],
                             simulation.restart_freq + 2)

    def test_flux_restart(self):
        """Test md-flux when we are restarting."""
        system = create_test_systemflux(temperature=0.05)
        engine = Langevin(0.002, 0.3)
        order = PositionVelocity(0, dim='x', periodic=False)
        interfaces = [-0.99]
        correct = {
            19: [(19, 0, '+')],
            374: [(374, 0, '-')],
        }
        simulation1 = SimulationMDFlux(
            ensemble={'system': system,
                      'order_function': order,
                      'engine': engine},
            settings={'simulation': {'interfaces': interfaces}},
            controls={'steps': 18})
        # Test 1: We stop before a crossing
        for step in simulation1.run():
            if step['cycle']['steps'] in correct:
                self.assert_equal_cross(correct[step['cycle']['step']],
                                        step['cross'])
        restart1 = simulation1.restart_info()
        simulation2 = SimulationMDFlux(
            ensemble={'system': system,
                      'order_function': order,
                      'engine': engine},
            settings={'simulation': {'interfaces': interfaces}},
            controls={'steps': 356})
        simulation2.load_restart_info(restart1)
        for step in simulation2.run():
            if step['cycle']['steps'] in correct:
                self.assert_equal_cross(correct[step['cycle']['steps']],
                                        step['cross'])
        restart2 = simulation2.restart_info()
        simulation3 = SimulationMDFlux(
            ensemble={'system': system,
                      'order_function': order,
                      'engine': engine},
            settings={'simulation': {'interfaces': interfaces}},
            controls={'steps': 1})
        simulation3.load_restart_info(restart2)
        for step in simulation3.run():
            if step['cycle']['steps'] in correct:
                self.assert_equal_cross(correct[step['cycle']['steps']],
                                        step['cross'])

    def test_flux_simulation_restart(self):
        """Test that we can continue with the simulation object."""
        system1 = create_test_systemflux()
        system2 = create_test_systemflux()
        rgen1 = create_random_generator({'seed': 0})
        rgen2 = create_random_generator({'seed': 16})
        engine1 = Langevin(0.002, 0.3, rgen1)
        engine2 = Langevin(0.002, 0.3, rgen2)
        order1 = PositionVelocity(0, dim='x', periodic=False)
        order2 = PositionVelocity(0, dim='x', periodic=False)
        interfaces = [-0.9]
        simulation1 = SimulationMDFlux(
            ensemble={'system': system1,
                      'order_function': order1,
                      'rgen': rgen1,
                      'engine': engine1},
            settings={'simulation': {'interfaces': interfaces}},
            controls={'endcycle': 3})
        simulation2 = SimulationMDFlux(
            ensemble={'system': system2,
                      'order_function': order2,
                      'rgen': rgen2,
                      'engine': engine2},
            settings={'simulation': {'interfaces': interfaces}},
            controls={'endcycle': 8})

        for _ in simulation1.run():
            pass

        restart1 = copy.deepcopy(simulation1.restart_info())
        restart_sys1 = copy.deepcopy(simulation1.system.restart_info())

        simulation2.load_restart_info(copy.deepcopy(restart1))
        simulation2.system.load_restart_info(copy.deepcopy(restart_sys1))

        restart2 = simulation2.restart_info()
        restart_sys2 = simulation2.system.restart_info()

        self.assertTrue(big_fat_comparer(restart_sys1,
                                         restart_sys2, hard=True))
        restart1['engine']['param_iner'] = restart2['engine']['param_iner']
        restart1['engine']['init_params'] = restart2['engine']['init_params']
        restart1['simulation']['cycle'] = restart2['simulation']['cycle']
        self.assertTrue(big_fat_comparer(restart1, restart2, hard=True))

        simulation1.cycle['endcycle'] = 8
        simulation2.cycle['endcycle'] = 8
        simulation1.first_step = True

        for _ in simulation1.run():
            pass

        info_parts = simulation1.restart_info()
        info_parts['system'] = simulation1.system.restart_info()

        for _ in simulation2.run():
            pass

        pp1 = simulation1.system.particles.restart_info()
        pp2 = simulation2.system.particles.restart_info()

        self.assertTrue(big_fat_comparer(pp1, pp2, hard=True))
        info_single = simulation2.restart_info()
        info_single['system'] = simulation2.system.restart_info()

        self.assertTrue(big_fat_comparer(info_parts, info_single, hard=True))

        self.assertEqual(info_parts['simulation']['cycle']['steps'],
                         info_single['simulation']['cycle']['steps'])
        self.assertTrue(np.allclose(info_parts['system']['box']['length'],
                                    info_single['system']['box']['length']))
        self.assertTrue(np.allclose(info_parts['system']['particles']['pos'],
                                    info_single['system']['particles']['pos']))
        self.assertEqual(info_parts['system']['particles']['vpot'],
                         info_single['system']['particles']['vpot'])
        self.assertTrue(np.allclose(info_parts['system']['particles']['vel'],
                                    info_single['system']['particles']['vel']))

        simulation1 = SimulationMDFlux(
            ensemble={'system': system1,
                      'order_function': order1,
                      'rgen': rgen1,
                      'engine': engine1},
            settings={'simulation': {'interfaces': interfaces}},
            controls={'endcycle': 18})

        for _ in simulation1.run():
            pass

        info_parts = copy.deepcopy(simulation1.restart_info())
        info_parts['system'] = copy.deepcopy(simulation1.system.restart_info())

        self.assertFalse(
            np.allclose(info_parts['system']['particles']['pos'],
                        info_single['system']['particles']['pos']))
        self.assertFalse(
            np.allclose(info_parts['system']['particles']['vel'],
                        info_single['system']['particles']['vel']))
        self.assertNotEqual(info_parts['simulation']['cycle']['endcycle'],
                            info_single['simulation']['cycle']['endcycle'])
        self.assertNotEqual(info_parts['system']['particles']['vpot'],
                            info_single['system']['particles']['vpot'])


if __name__ == '__main__':
    unittest.main()
