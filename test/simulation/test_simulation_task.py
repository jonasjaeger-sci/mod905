# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the SimulationTask class."""
import logging
import unittest
from pyretis.simulation.simulation_task import SimulationTask, execute_now
logging.disable(logging.CRITICAL)


class SimulationTaskTest(unittest.TestCase):
    """Run the tests for SimulationTask."""

    def test_create_task(self):
        """Test that we can create simulation tasks."""

        def some_function():  # pylint: disable=missing-docstring
            return 'Hello!'

        SimulationTask(some_function)
        # Test if we give wrong arguments:
        with self.assertRaises(AssertionError):
            SimulationTask(some_function, args=['dummy'])
        # Test if we give a non-callable:
        not_a_function = 100
        with self.assertRaises(AssertionError):
            SimulationTask(not_a_function, args=['dummy'])

        def some_function2(test='hello'):  # pylint: disable=missing-docstring
            return test

        inkw = {'test': 'yes'}
        task2 = SimulationTask(some_function2, kwargs=inkw)
        for key, val in inkw.items():
            self.assertTrue(key in task2.kwargs)
            self.assertEqual(val, task2.kwargs[key])
        # Test giving too many kwargs
        inkw = {'test': 'yes', 'more': 'indeed'}
        with self.assertRaises(AssertionError):
            logging.disable(logging.INFO)
            with self.assertLogs('pyretis.simulation.simulation_task',
                                 level='WARNING'):
                SimulationTask(some_function2, kwargs=inkw)
            logging.disable(logging.CRITICAL)
        # Test giving kwargs when None are expected
        inkw = {'missing': 'indeed'}
        with self.assertRaises(AssertionError):
            logging.disable(logging.INFO)
            with self.assertLogs('pyretis.simulation.simulation_task',
                                 level='WARNING'):
                SimulationTask(some_function, kwargs=inkw)
            logging.disable(logging.CRITICAL)

    def test_execute(self):
        """Test that we can execute the task."""

        def some_function():  # pylint: disable=missing-docstring
            return [10, 9, 8]

        def some_function2(pos):  # pylint: disable=missing-docstring
            return pos * pos

        def some_function3(pos, exp=10):  # pylint: disable=missing-docstring
            return pos**exp

        def some_function4(exp=10):  # pylint: disable=missing-docstring
            return 2**exp

        task1 = SimulationTask(some_function, when={'every': 2},
                               result='the-stuff', first=True)
        step = {'step': 10, 'start': 3, 'stepno': 7}
        result = task1.execute(step)
        self.assertTrue(result is None)
        step = {'step': 10, 'start': 3, 'stepno': 8}
        result = task1.execute(step)
        for i, j in zip(result, [10, 9, 8]):
            self.assertTrue(i == j)

        var = 10
        task2 = SimulationTask(some_function2, when={'every': 2},
                               args=[var], result='the-stuff', first=True)
        result = task2.execute(step)
        self.assertEqual(result, 100)

        var = 5
        task3 = SimulationTask(some_function3, when={'every': 2},
                               args=[var], kwargs={'exp': 2},
                               result='the-stuff', first=False)
        result = task3.execute(step)
        self.assertFalse(task3.run_first())
        self.assertEqual(result, 25)
        when = {'every': 3}
        task3.update_when(when)

        task4 = SimulationTask(some_function4,
                               kwargs={'exp': 2},
                               result='the-stuff', first=True)
        result = task4(step)
        self.assertEqual(result, 4)
        self.assertTrue(task4.run_first())
        self.assertEqual(task4.result, 'the-stuff')

        when = {'every': 3}
        task4.update_when(when)


class ExecuteNowTest(unittest.TestCase):
    """Test the execute now method."""

    def test_execute_now(self):
        """Test the execute now method."""
        step = {'step': 10, 'start': 2, 'stepno': 8}

        when = None
        exe = execute_now(step, when)
        self.assertTrue(exe)

        when = {'every': 2}
        exe = execute_now(step, when)
        self.assertTrue(exe)

        when = {'every': 3}
        exe = execute_now(step, when)
        self.assertFalse(exe)

        when = {'at': 10}
        exe = execute_now(step, when)
        self.assertTrue(exe)

        when = {'at': (1, 9, 10)}
        exe = execute_now(step, when)
        self.assertTrue(exe)


if __name__ == '__main__':
    unittest.main()
