# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the Simulation class."""
import logging
import unittest
from pyretis.engines.internal import Langevin
from pyretis.core.random_gen import RandomGenerator
from pyretis.simulation.simulation import Simulation
from pyretis.inout.writers.writers import Writer
from pyretis.inout.setup.createoutput import OutputTaskScreen
logging.disable(logging.CRITICAL)


class TxtWriter(Writer):
    """A class used for testing output."""
    FMT = '{:>10d} {:>20s}'

    def __init__(self):
        header = {'labels': ['Step', 'Message'], 'width': [9, 20]}
        super().__init__(None, header=header)

    def generate_output(self, step, *message):
        yield self.FMT.format(step, message[0])


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

        def task1():  # pylint: disable=missing-docstring
            return 'Hello there!'

        task = {'func': task1, 'result': 'hello'}
        add = simulation.add_task(task)
        self.assertTrue(add)

        output = [
            OutputTaskScreen('Hello-test', ['hello'], TxtWriter(),
                             {'every': 1}),
        ]

        for i, step in enumerate(simulation.run(output=output)):
            if i == 0:
                self.assertFalse('hello' in step)
            else:
                self.assertTrue('hello' in step)

        simulation.extend_cycles(5)
        for i, step in enumerate(simulation.run()):
            self.assertEqual(i + 1 + 10, step['cycle']['step'])

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


if __name__ == '__main__':
    unittest.main()
