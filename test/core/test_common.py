# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test methods from pyretis.core.common"""
import logging
import unittest
from pyretis.core.common import (inspect_function,
                                 _pick_out_arg_kwargs,
                                 generic_factory,
                                 get_path_class)
from pyretis.core.path import Path, PathExt
from pyretis.core.reservoirpath import ReservoirPath


logging.disable(logging.CRITICAL)


# define some functions used for testing:
def function1(arg1, arg2, arg3, arg4):  # pylint: disable=unused-argument
    """To test positional arguments."""
    return


def function2(arg1, arg2, arg3, arg4=10):  # pylint: disable=unused-argument
    """To test positional and keyword arguments"""
    return


def function3(arg1, arg2, arg3, arg4=100, arg5=10):  # pylint: disable=unused-argument
    """To test positional and keyword arguments"""
    return


def function4(*args, **kwargs):  # pylint: disable=unused-argument
    """To test positional and keyword arguments"""
    return


def function5(arg1, arg2, *args, arg3=100, arg4=100):  # pylint: disable=unused-argument
    """To test positional and keyword arguments, python3 specific"""
    return


def function6(arg1, arg2, arg3=100, *, arg4=10):  # pylint: disable=unused-argument
    """To test positional and keyword arguments, python3 specific"""
    return


def function7(arg1, arg2, arg3=100, *args, arg4, arg5=10):  # pylint: disable=unused-argument
    """To test positional and keyword arguments, python3 specific"""
    return


def function8(arg1, arg2=100, self='something'):
    """Test name for val."""
    return


class InspectTest(unittest.TestCase):
    """Run the inspect_function method."""

    def test_inspect(self):
        """Test the inspect function method."""
        # define some test functions:
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
        """We test most kind above, here we also test the POSITIONAL_ONLY"""
        args = inspect_function(range.__eq__)
        self.assertTrue(not args['keywords'])
        self.assertTrue(not args['varargs'])
        self.assertTrue(not args['kwargs'])
        for i in ('self', 'value'):
            self.assertTrue(i in args['args'])

    def test_pick_out_kwargs(self):
        """Test pick out of self for kwargs."""
        settings = {'arg1': 10, 'arg2': 100, 'self': 'text'}

        class Abomination():
            pass

        abo = Abomination()
        abo.__init__ = function8

        args, kwargs = _pick_out_arg_kwargs(abo, settings)
        self.assertFalse('self' in args)
        self.assertFalse('self' in kwargs)


class TestGetPathClass(unittest.TestCase):
    """Test that we can get path classes."""

    def test_get_path_class(self):
        """Test that we get path classes as expected."""
        correct = {'internal': Path,
                   'external': PathExt,
                   'reservoir': ReservoirPath}
        for key, val in correct.items():
            klass = get_path_class(key)
            self.assertTrue(klass is val)

        with self.assertRaises(ValueError):
            get_path_class('Not so classy')


class Klass1():
    """A class for testing."""

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


if __name__ == '__main__':
    unittest.main()
