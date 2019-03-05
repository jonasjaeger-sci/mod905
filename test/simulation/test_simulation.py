# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the Simulation class."""
from io import StringIO
import os
import logging
import unittest
from unittest.mock import patch
import tempfile
import pathlib
from pyretis.engines.internal import Langevin
from pyretis.core.random_gen import RandomGenerator
from pyretis.simulation.simulation import Simulation
from pyretis.inout.simulationio import OutputTask
from pyretis.inout.screen import ScreenOutput
from pyretis.inout.formats.formatter import OutputFormatter
from pyretis.inout.settings import add_default_settings
from pyretis.inout.setup.createsystem import create_system_from_settings
from pyretis.core.units import units_from_settings
from .test_helpers import turn_on_logging, TEST_SETTINGS
logging.disable(logging.CRITICAL)


class TxtWriter(OutputFormatter):
    """A class used for testing output."""
    FMT = '{:>10d} {:>20s}'

    def format(self, step, data):
        yield self.FMT.format(step, data)


class TestSimulation(unittest.TestCase):
    """Run the tests for Simulation class."""

    def test_add_task(self):
        """Test that we can add task(s) to the simulation."""
        simulation = Simulation()

        def task1():  # pylint: disable=missing-docstring
            return 'Hello there!'

        def task0():  # pylint: disable=missing-docstring
            return 'I should be first!'

        task = {'func': task1, 'result': 'hello'}
        add = simulation.add_task(task)
        self.assertTrue(add)

        task = {'func': task0, 'result': 'first'}
        add = simulation.add_task(task, position=0)
        self.assertTrue(add)

        task = {'func': 100, 'result': 'should-not-be-added'}
        add = simulation.add_task(task, position=0)
        self.assertFalse(add)

    def test_run_extend(self):
        """Test that we can run and extend a simulation."""
        simulation = Simulation(steps=10)

        def task1(simulation):
            """Dummy task for the simulation."""
            return 'Hello there {:03d}'.format(simulation.cycle['step'])

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

        lines = []
        with patch('sys.stdout', new=StringIO()) as stdout:
            for i, step in enumerate(simulation.run()):
                if i == 0:
                    self.assertFalse('hello' in step)
                else:
                    self.assertTrue('hello' in step)
            simulation.extend_cycles(5)
            for i, step in enumerate(simulation.run()):
                self.assertEqual(i + 1 + 10, step['cycle']['step'])
            for linei in stdout.getvalue().strip().split('\n'):
                if linei:
                    lines.append(linei)
        for i, linei in enumerate(lines):
            if i == 0:
                self.assertEqual('#    Step              Message', linei)
            else:
                msg = 'Hello there {:03d}'.format(i)
                correct = '{:>10d} {:>20s}'.format(i, msg)
                self.assertEqual(correct, linei)

    def test_restart_simple(self):
        """Test restart methods."""
        simulation = Simulation(steps=10)
        for _ in simulation.run():
            pass
        restart = simulation.restart_info()
        simulation2 = Simulation(steps=1)
        self.assertEqual(simulation2.cycle['stepno'], 0)
        simulation2.load_restart_info(restart)
        self.assertEqual(simulation2.cycle['stepno'], 10)
        # Try setting for rgen when we don't expect it:
        restart['rgen'] = 'dummy'
        simulation2.load_restart_info(restart)
        # Add random generator and try again:
        rgen = RandomGenerator(seed=101)
        simulation2.rgen = rgen
        restart['rgen'] = rgen.get_state()
        simulation2.load_restart_info(restart)
        # Try setting engine when we don't expect it:
        restart['engine'] = {'rgen': rgen.get_state()}
        simulation2.load_restart_info(restart)
        simulation2.engine = 'dummy'
        simulation2.load_restart_info(restart)
        # Add and try again:
        simulation2.engine = Langevin(1.0, 2.0)
        simulation2.load_restart_info(restart)

    def test_set_up_output(self):
        """Test the set_up_output things."""
        simulation = Simulation(steps=100)
        settings = {}
        add_default_settings(settings)
        with tempfile.TemporaryDirectory() as tempdir:
            settings['simulation']['exe-path'] = tempdir
            simulation.set_up_output(settings)
            self.assertEqual(simulation.restart_freq,
                             settings['output']['restart-file'])
            settings['output']['restart-file'] = -1
            with turn_on_logging():
                with self.assertLogs('pyretis.simulation.simulation',
                                     level='WARNING'):
                    simulation.set_up_output(settings)
                    self.assertIsNone(simulation.restart_freq)

    def test_soft_exit(self):
        """Test the soft exit method."""
        settings = TEST_SETTINGS.copy()
        with tempfile.TemporaryDirectory() as tempdir:
            simulation = Simulation(steps=100)
            add_default_settings(settings)
            units_from_settings(settings)
            system = create_system_from_settings(settings, None)
            simulation.system = system
            settings['simulation']['exe-path'] = tempdir
            simulation.set_up_output(settings)
            self.assertEqual(tempdir, simulation.exe_dir)
            for i, _ in enumerate(simulation.run()):
                if i > simulation.restart_freq:
                    break
            files = [i.name for i in os.scandir(tempdir)]
            self.assertEqual(1, len(files))
            self.assertIn('pyretis.restart', files)
            exit_file = os.path.join(tempdir, 'EXIT')
            pathlib.Path(exit_file).touch()
            with patch('sys.stdout', new=StringIO()) as stdout:
                for _ in enumerate(simulation.run()):
                    pass
                self.assertIn('soft exit', stdout.getvalue().strip())
            self.assertEqual(simulation.cycle['step'],
                             simulation.restart_freq + 2)


if __name__ == '__main__':
    unittest.main()
