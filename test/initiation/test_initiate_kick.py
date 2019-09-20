# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the initiate kick family of methods."""
import collections
from io import StringIO
import logging
import unittest
from unittest.mock import patch
import os
import numpy as np
from pyretis.initiation.initiate_kick import (
    fix_path_by_tis,
    generate_initial_path_kick,
    _get_help,
    initiate_kick,
    initiate_kicki,
    initiate_kick_max,
)
from .help import (
    turn_on_logging,
    create_test_retis_simulation,
    create_test_tis_simulation,
)
logging.disable(logging.CRITICAL)
HERE = os.path.abspath(os.path.dirname(__file__))


class TestGenericMethods(unittest.TestCase):
    """Run tests for generic methods defined in the module."""

    def test_get_help(self):
        """Testing the get_help method."""
        interfaces = [-1, 0, 1]
        # Test what happens for unknown start conditions:
        with self.assertRaises(ValueError):
            _get_help('r', interfaces)
        # Test what happens for incorrect number of interfaces:
        for i in (0, 1, 2, 4):
            with self.assertRaises(ValueError):
                _get_help('R', [1]*i)
        # For correct input we expect to be given two methods back.
        imp_r, done_r = _get_help('R', interfaces)
        # Test that these two functions behave as expected:
        fake_order_value = collections.namedtuple(
            'orderparameter', ['ordermax', 'ordermin']
        )
        # Run some checks for improvement:
        current = fake_order_value([0.4, 0], [-1, 1])
        # Cases are:
        # 1. max > currentmax and min < middle.
        # 2. max > currentmax and min > middle.
        # 3. max < currentmax and min < middle.
        # 4. max < currentmax and min > middle.
        cases = [
            [(1.1, 0), (-1, 0)],
            [(1, 0), (0.5, 0)],
            [(-0.5, 0), (-1, 0)],
            [(0.3, 0), (0.1, 0)],
        ]
        results = [True, False, False, False]

        for case, res in zip(cases, results):
            newp = fake_order_value(case[0], case[1])
            self.assertEqual(imp_r(newp, current), res)
            self.assertEqual(done_r(newp), res)

        imp_l, done_l = _get_help('L', interfaces)
        # Cases are:
        # 1. min < currentmin and max > middle.
        # 2. min < currentmin and max < middle.
        # 3. min > currentmin and max < middle.
        # 4. min > currentmin and max > middle.
        current = fake_order_value([0.4, 0], [-1, 1])
        cases = [
            [(0.5, 0), (-2, 1)],
            [(-0.9, 0), (-1, 1)],
            [(-0.9, 0), (0, 1)],
            [(0.2, 0), (0, 1)],
        ]
        results = [True, False, False, False]
        for case, res in zip(cases, results):
            newp = fake_order_value(case[0], case[1])
            self.assertEqual(imp_l(newp, current), res)
            self.assertEqual(done_l(newp), res)


def _get_kick_initial(log):
    """Extract initial points for kicking from log messages."""
    kick = []
    for msg in log.output:
        if msg.find('Kicking from') != -1:
            kick.append(float(msg.split(':')[-1]))
    return kick


def _run_generate_initial(simulation):
    """Run the generate_initial_path_kick method for a given simulation."""
    for attempt in generate_initial_path_kick(simulation.system,
                                              simulation.order_function,
                                              simulation.path_ensemble,
                                              simulation.engine,
                                              simulation.rgen,
                                              simulation.settings['tis']):
        yield attempt


class TestInitiateKick(unittest.TestCase):
    """Run tests for the initiate kick methods."""

    def _compare_generator_functions(self, gen1, gen2):
        """Might be over-the-top, but let's compare generator functions."""
        self.assertEqual(gen1.__name__, gen2.__name__)
        # Sure, let's us just compare the compiled bytecode:
        self.assertEqual(gen1.gi_code.co_code, gen2.gi_code.co_code)

    def test_initiate_kick(self):
        """Test the initiate_kick selector method."""
        keywords = ('initial', 'previous', 'iNitiAL')
        methods = (initiate_kicki, initiate_kick_max, initiate_kicki)
        for key, method in zip(keywords, methods):
            settings = {
                'initial-path': {'kick-from': key}
            }
            init = initiate_kick(None, 0, settings)
            gen = method(None, 0)
            self._compare_generator_functions(init, gen)
        # Test for unknown method:
        settings = {
            'initial-path': {'kick-from': 'Ekki-Ekki-Ekki-Ekki-Ptang'}
        }
        with self.assertRaises(ValueError):
            initiate_kick(None, 0, settings)

    def _help_with_initiation(self, simulation, method, correct_kick):
        """Run initiation and return points for kicking."""
        kick = []
        results = []
        with turn_on_logging():
            with patch('sys.stdout', new=StringIO()):
                with self.assertLogs() as log:
                    for result in method(simulation, 0):
                        results.append(result)
                    kick = _get_kick_initial(log)
        self.assertEqual(len(kick), len(correct_kick))
        for i, j in zip(kick, correct_kick):
            self.assertAlmostEqual(i, j)
        return results

    def test_initiate_kick_max(self):
        """Test the initiate_kick_max method."""
        simulation = create_test_retis_simulation()
        correct_kick = [-1.0, -0.9016, -0.8893]
        results = self._help_with_initiation(simulation, initiate_kick_max,
                                             correct_kick)
        kick_re = [correct_kick[0]]
        for result in results:
            path = result[1]
            interfaces = result[-1].interfaces
            self.assertTrue(result[0])
            # Re-calculate the kicking point:
            order = np.array([i.order[0] for i in path.phasepoints])
            diff = order - interfaces[2]
            diff_neg = np.where(diff <= 0)[0]
            small_neg = np.argmax(diff[diff_neg])
            kick_re.append(order[diff_neg[small_neg]])
        # The last one is not used:
        kick_re.pop()
        self.assertEqual(len(kick_re), len(correct_kick))
        for i, j in zip(correct_kick, kick_re):
            self.assertAlmostEqual(i, j)
        # Check that is gets the right interface for ensemble 0
        simulation.path_ensembles[0].ensemble_number = 0
        correct_kick = [-0.8893, -0.9016, -0.508]
        self._help_with_initiation(simulation, initiate_kick_max,
                                   correct_kick)

    def test_initiate_kicki(self):
        """Test the initiate_kicki method."""
        simulation = create_test_retis_simulation()
        correct_kick = [-1.0, -1.0, -1.0]
        results = self._help_with_initiation(simulation, initiate_kicki,
                                             correct_kick)
        for result in results:
            self.assertTrue(result[0])

    def test_fix_path(self):
        """Test fix_path_by_tis."""
        simulation = create_test_tis_simulation()
        correct_kick = [-1.0]
        results = self._help_with_initiation(simulation, initiate_kicki,
                                             correct_kick)
        self.assertTrue(results[0][0])
        initial_path = results[0][1]
        # This initial path has already been accepted, but
        # try to improve it:
        new_path = fix_path_by_tis(
            initial_path,
            simulation.order_function,
            simulation.path_ensemble,
            simulation.engine,
            simulation.settings['tis'],
        )
        # This should trigger the "did not improve" branch,
        # but it is still accepted. Test that we did not change
        # the path we gave in:
        self.assertIs(initial_path, new_path)
        # Make the path start end at wrong interface:
        interfaces = simulation.path_ensemble.interfaces
        initial_path.phasepoints[0].order = [interfaces[-1] + 0.2, 0.0]
        initial_path.phasepoints[-1].order = [interfaces[-1] + 0.2, 0.0]
        check = initial_path.check_interfaces(interfaces)
        self.assertEqual(check[0], 'R')
        self.assertEqual(check[1], 'R')
        self.assertEqual(check[2], 'M')
        self.assertEqual(check[3], [False, True, True])
        # Try to improve this path:
        new_path = fix_path_by_tis(
            initial_path,
            simulation.order_function,
            simulation.path_ensemble,
            simulation.engine,
            simulation.settings['tis'],
            rgen=simulation.rgen,
        )
        # The new path starts at L, ends at R and crosses M:
        self.assertIsNot(initial_path, new_path)
        check = new_path.check_interfaces(interfaces)
        self.assertEqual(check[0], 'L')
        self.assertEqual(check[1], 'R')
        self.assertEqual(check[2], 'M')
        # Check that we crossed the left interface, the middle one,
        # and the final interface.
        self.assertEqual(check[3], [True, True, True])
        # Check that the path is accepted:
        self.assertEqual(new_path.status, 'ACC')

    def test_generate_initial_fail_forward(self):
        """Test forward failure of the generate_initial_path_kick method.

        Here, we test how the generate_initial_path_kick method behaves
        when the forward generation fails.

        """
        # Make forward fail, by limiting to a very short path:
        simulation = create_test_tis_simulation(maxlength=3)
        state = simulation.rgen.get_state()
        for i, attempt in enumerate(_run_generate_initial(simulation)):
            self.assertFalse(attempt[0])
            self.assertIsNone(attempt[-1])
            self.assertTrue(attempt[1].startswith('Forward path failed:'))
            simulation.rgen.set_state(state)
            simulation.engine.reset()
            if i >= 1:
                # Just do two iterations so that we catch the continue
                # statement after the yield.
                break

    def test_generate_initial_fail_backward(self):
        """Test backward failure of the generate_initial_path_kick method.

        Here, we test how the generate_initial_path_kick method behaves
        when the backward generation fails.

        """
        # Make backward fail, by using a special engiene.
        simulation = create_test_tis_simulation(
            engine_type='MockEngineVelocitySupremacist',
            maxlength=50,
        )
        state = simulation.rgen.get_state()
        for i, attempt in enumerate(_run_generate_initial(simulation)):
            self.assertFalse(attempt[0])
            self.assertIsNone(attempt[-1])
            self.assertTrue(attempt[1].startswith('Backward path failed:'))
            simulation.rgen.set_state(state)
            if i >= 1:
                # Just do two iterations so that we catch the continue
                # statement after the yield.
                break

    def test_generate_initial_fail_length(self):
        """Test path paste failure of generate_initial_path_kick.

        Here, we test how the generate_initial_path_kick method behaves
        when the merging of the forward and backward paths fail.

        """
        # Make path paste fail, by limiting to a short path:
        simulation = create_test_tis_simulation(maxlength=60)
        state = simulation.rgen.get_state()
        for i, attempt in enumerate(_run_generate_initial(simulation)):
            self.assertFalse(attempt[0])
            self.assertIsNone(attempt[-1])
            self.assertEqual(attempt[1], 'Initial path was too long.')
            simulation.rgen.set_state(state)
            simulation.engine.reset()
            if i >= 1:
                # Just do two iterations so that we catch the continue
                # statement after the yield.
                break

    def test_generate_initial_fail_other(self):
        """Test generate_initial_path_kick for start/end conditions.

        Here, we test how the generate_initial_path_kick method behaves
        when the start/end conditions of the path ensemble are set
        incorrectly.

        """
        # Make forward fail, by limiting to a short path:
        simulation = create_test_tis_simulation(maxlength=100)
        simulation.path_ensemble.start_condition = 'tiktok'
        state = simulation.rgen.get_state()
        for i, attempt in enumerate(_run_generate_initial(simulation)):
            self.assertFalse(attempt[0])
            self.assertIsNone(attempt[-1])
            self.assertEqual(
                attempt[1], 'Could not generate initial path will retry!'
            )
            # Reset rgen and the engine that we just do the same again:
            simulation.rgen.set_state(state)
            simulation.engine.reset()
            if i >= 1:
                # Just do two iterations so that we catch the continue
                # statement after the yield.
                break

    def test_generate_initial_fix(self):
        """Test generate_initial_path_kick with TIS fixes.

        Here, we test how this method behaves when we have a path
        that starts and ends at the wrong interface.

        """
        # Make a path that start and ends at the wrong interface,
        # by using an engine which is always increasing the order
        # parameter:
        simulation = create_test_tis_simulation(
            engine_type='MockEngineOneWay'
        )
        for i, attempt in enumerate(_run_generate_initial(simulation)):
            if i == 0:
                self.assertFalse(attempt[0])
                self.assertIsNone(attempt[-1])
                self.assertEqual(attempt[1], 'Trying to fix path by TIS moves')
                # For this to actually work, we need to allow the engine
                # to go backwards as well:
                simulation.engine.timestep = -simulation.engine.timestep
            elif i == 1:
                self.assertTrue(attempt[0])
                self.assertIsNotNone(attempt[-1])
                # We will end here, as the fix_path_by_tis is tested elsewhere.
            else:
                raise ValueError('Wrong number of iterations.')


if __name__ == '__main__':
    unittest.main()
