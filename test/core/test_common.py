# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test methods from pyretis.core.common"""
import logging
import unittest
import numpy as np
from pyretis.core.common import (
    inspect_function,
    _pick_out_arg_kwargs,
    generic_factory,
    numpy_allclose,
)


logging.disable(logging.CRITICAL)


# Define some functions used for testing:
# pylint: disable=unused-argument
def function1(arg1, arg2, arg3, arg4):
    """To test positional arguments."""
# pylint: enable=unused-argument


# pylint: disable=unused-argument
def function2(arg1, arg2, arg3, arg4=10):
    """To test positional and keyword arguments."""
# pylint: enable=unused-argument


# pylint: disable=unused-argument
def function3(arg1, arg2, arg3, arg4=100, arg5=10):
    """To test positional and keyword arguments."""
# pylint: enable=unused-argument


# pylint: disable=unused-argument
def function4(*args, **kwargs):
    """To test positional and keyword arguments."""
# pylint: enable=unused-argument


# pylint: disable=unused-argument
def function5(arg1, arg2, *args, arg3=100, arg4=100):
    """To test positional and keyword arguments."""
# pylint: enable=unused-argument


# pylint: disable=unused-argument
def function6(arg1, arg2, arg3=100, *, arg4=10):
    """To test positional and keyword arguments."""
# pylint: enable=unused-argument


# pylint: disable=unused-argument, keyword-arg-before-vararg
def function7(arg1, arg2, arg3=100, *args, arg4, arg5=10):
    """To test positional and keyword arguments."""
# pylint: enable=unused-argument, keyword-arg-before-vararg


# pylint: disable=unused-argument
def function8(arg1, arg2=100, self='something'):
    """To test redifinition of __init__."""
# pylint: enable=unused-argument


class InspectTest(unittest.TestCase):
    """Run the inspect_function method."""

    def test_inspect(self):
        """Test the inspect function method."""
        # Define some test functions:
        functions = [function1, function2, function3, function4,
                     function5, function6, function7]
        correct = [
            {'args': ['arg1', 'arg2', 'arg3', 'arg4'],
             'varargs': [], 'kwargs': [], 'keywords': []},
            {'args': ['arg1', 'arg2', 'arg3'],
             'varargs': [], 'kwargs': ['arg4'], 'keywords': []},
            {'args': ['arg1', 'arg2', 'arg3'], 'varargs': [],
             'kwargs': ['arg4', 'arg5'], 'keywords': []},
            {'args': [], 'varargs': ['args'], 'kwargs': [],
             'keywords': ['kwargs']},
            {'args': ['arg1', 'arg2'], 'kwargs': ['arg3', 'arg4'],
             'varargs': ['args'], 'keywords': []},
            {'args': ['arg1', 'arg2'], 'kwargs': ['arg3', 'arg4'],
             'varargs': [], 'keywords': []},
            {'args': ['arg1', 'arg2'], 'kwargs': ['arg3', 'arg4', 'arg5'],
             'varargs': ['args'], 'keywords': []},
        ]

        for i, func in enumerate(functions):
            args = inspect_function(func)
            self.assertEqual(args, correct[i])

    def test_arg_kind(self):
        """Test a function with only positional arguments."""
        args = inspect_function(range.__eq__)
        self.assertTrue(not args['keywords'])
        self.assertTrue(not args['varargs'])
        self.assertTrue(not args['kwargs'])
        for i in ('self', 'value'):
            self.assertTrue(i in args['args'])

    def test_pick_out_kwargs(self):
        """Test pick out of "self" for kwargs."""
        settings = {'arg1': 10, 'arg2': 100, 'self': 'text'}

        # pylint: disable=too-few-public-methods
        class Abomination:
            """Just to allow redefination of __init__."""
        # pylint: enable=too-few-public-methods

        abo = Abomination()
        abo.__init__ = function8

        args, kwargs = _pick_out_arg_kwargs(abo, settings)
        self.assertFalse('self' in args)
        self.assertFalse('self' in kwargs)


class Klass1:
    """A class used for factory testing."""

    def __init__(self):
        self.stuff = 10

    def method1(self):
        """Return stuff."""
        return self.stuff

    def method2(self, add):
        """Add to stuff."""
        self.stuff += add


class TestGenericFactory(unittest.TestCase):
    """Test the generic factory."""

    def test_factory(self):
        """Test that the factory works as intended."""
        factory_map = {'klass1': {'cls': Klass1}}

        settings = {'class': 'Klass1'}
        cls = generic_factory(settings, factory_map, name='Testing')
        self.assertIsInstance(cls, Klass1)

        settings = {'clAsS': 'Klass1'}
        logging.disable(logging.INFO)
        with self.assertLogs('pyretis.core.common', level='CRITICAL'):
            cls = generic_factory(settings, factory_map, name='Testing')
        logging.disable(logging.CRITICAL)
        self.assertTrue(cls is None)

        settings = {'Klass': 'Klass1'}
        logging.disable(logging.INFO)
        with self.assertLogs('pyretis.core.common', level='CRITICAL'):
            cls = generic_factory(settings, factory_map, name='Testing')
        logging.disable(logging.CRITICAL)
        self.assertTrue(cls is None)


class TestNumpyComparison(unittest.TestCase):
    """Test the numpy_allclose method."""

    def test_numpy_allclose(self):
        """Test that the numpy allclose comparison works as intended."""
        val1 = np.array([1.2345, 2.34567, 9.87654321])
        val2 = np.array([1.2345, 2.34567, 9.87654321])
        val3 = np.array([1.2345, 2.34567, 10.])
        # Both are valid:
        self.assertTrue(numpy_allclose(val1, val2))
        self.assertFalse(numpy_allclose(val1, val3))
        # Both are None:
        self.assertTrue(numpy_allclose(None, None))
        # One is None:
        self.assertFalse(numpy_allclose(val1, None))
        self.assertFalse(numpy_allclose(None, val1))
        # One is something else:
        self.assertFalse(numpy_allclose(val1, 'the roof is on fire'))
        # Both is something else:
        self.assertFalse(numpy_allclose('the roof is on fire',
                                        'the roof is on fire'))


if __name__ == '__main__':
    unittest.main()
