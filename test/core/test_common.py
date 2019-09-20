# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test methods from pyretis.core.common"""
import logging
import unittest
import numpy as np
from io import StringIO
from pyretis.core.common import (
    big_fat_comparer,
    crossing_finder,
    inspect_function,
    generic_factory,
    numpy_allclose,
    select_and_trim_a_segment,
    segments_counter,
    trim_path_between_interfaces,
    _pick_out_arg_kwargs,
)
from unittest.mock import patch
from .test_path import PATHTEST0, PATHTEST1, PATHTEST2

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


CORRECT = [
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


class InspectTest(unittest.TestCase):
    """Run the inspect_function method."""

    def test_inspect(self):
        """Test the inspect function method."""
        # Define some test functions:
        functions = [function1, function2, function3, function4,
                     function5, function6, function7]

        for i, func in enumerate(functions):
            args = inspect_function(func)
            self.assertEqual(args, CORRECT[i])

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

        with self.assertRaises(ValueError):
            _, _ = _pick_out_arg_kwargs(abo, {})


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


class TestBigFatComparer(unittest.TestCase):
    """Test the big_fat_comparer."""

    def test_fat_part_1(self):
        """Test the big_fat_comparer."""
        self.assertFalse(big_fat_comparer(np.array([1]), np.array([1, 2, 3])))
        with self.assertRaises(ValueError):
            big_fat_comparer(np.array([1]), np.array([1, 2, 3]), hard=True)

        self.assertFalse(big_fat_comparer(np.array([1, 2, 4]),
                                          np.array([1, 2, 3])))
        with self.assertRaises(ValueError):
            big_fat_comparer(np.array([1, 2, 4]),
                             np.array([1, 2, 3]), hard=True)

        self.assertFalse(big_fat_comparer(1, 2))
        with self.assertRaises(ValueError):
            big_fat_comparer(1, 2, hard=True)

        self.assertFalse(big_fat_comparer(1, 2))
        with self.assertRaises(ValueError):
            big_fat_comparer(1, 2, hard=True)

        self.assertFalse(big_fat_comparer(1, [1]))
        with self.assertRaises(ValueError):
            big_fat_comparer(1, [1], hard=True)

        self.assertFalse(big_fat_comparer((1, 3, 4), (1, 3)))
        with self.assertRaises(ValueError):
            big_fat_comparer((1, 3, 4), (1, 3), hard=True)
        self.assertFalse(big_fat_comparer((1, 3), (1, 3, 4)))
        with self.assertRaises(ValueError):
            big_fat_comparer((1, 3), (1, 3, 4), hard=True)
        self.assertFalse(big_fat_comparer((1, 2, 3), (2, 3, 4)))
        with self.assertRaises(ValueError):
            big_fat_comparer((1, 2, 3), (2, 3, 4), hard=True)

        self.assertFalse(big_fat_comparer('Ciao', 'Mamma'))
        with self.assertRaises(ValueError):
            big_fat_comparer('Ciao', 'Mamma', hard=True)

        self.assertFalse(big_fat_comparer([1, 2], [0]))
        with self.assertRaises(ValueError):
            big_fat_comparer([1, 2], [0], hard=True)

        a, b = np.array([0, 2]), np.array([0, 1])
        with self.assertRaises(ValueError):
            big_fat_comparer(a, b, hard=True)

        a, b = [0, 2], [0, {'b': 'c'}]
        with self.assertRaises(ValueError):
            big_fat_comparer(a, b, hard=True)

    def test_fat_part_2(self):
        """Test the big_fat_comparer."""
        try1 = {'correct': CORRECT,
                'kkk': [1, 2, 3],
                'giorgio': {'santo': 'subito',
                            'yes': [12, 'b']}}

        try2 = {'correct': CORRECT,
                'kkk': [1, 2, 3],
                'giorgio': {'santo': 'subito',
                            'yes': [12, 'b']}}

        try3 = {'correct': CORRECT,
                'kkk': [1, 2, 3],
                'giorgio': {'santo': 'subit',
                            'yes': [12, 'b']}}
        try4 = {'correct': CORRECT,
                'kkk': [1, 2, 3],
                'giorgio': {'santo': 'subit',
                            'no': 'interest',
                            'yes': {'b': 12}}}

        self.assertFalse(big_fat_comparer(try1, try3))
        with self.assertRaises(ValueError):
            big_fat_comparer(try1, try3, hard=True)

        self.assertFalse(big_fat_comparer(try1, try4))
        with self.assertRaises(ValueError):
            big_fat_comparer(try1, try4, hard=True)

        self.assertFalse(big_fat_comparer(try3, try4))
        with self.assertRaises(ValueError):
            big_fat_comparer(try3, try4, hard=True)

        self.assertFalse(big_fat_comparer(try2, try4))
        with self.assertRaises(ValueError):
            big_fat_comparer(try2, try4, hard=True)

        self.assertFalse(big_fat_comparer(try1, {**{'Ihate': 'Cinnamon'},
                                                 **try2}))
        with self.assertRaises(ValueError):
            big_fat_comparer(try1, {**{'Ihate': 'Cinnamon'},
                                    **try2}, hard=True)

        self.assertFalse(big_fat_comparer({**{'Iate': 'Cinnamon'}, **try2},
                                          try1))
        with self.assertRaises(ValueError):
            big_fat_comparer({**{'Iate': 'Cinnamon'}, **try2},
                             try1, hard=True)

        self.assertFalse(big_fat_comparer(try1, 'TestMcTest'))
        with self.assertRaises(ValueError):
            big_fat_comparer(try1, 'TestMcTest', hard=True)

        self.assertFalse(big_fat_comparer('TestMcTest', try1))
        with self.assertRaises(ValueError):
            big_fat_comparer('TestMcTest', try1, hard=True)

        self.assertTrue(big_fat_comparer(try1, try2))
        self.assertTrue(big_fat_comparer(try1, try2, hard=True))

        try2['giorgio']['yes'][0] = 1
        self.assertFalse(big_fat_comparer(try1, try2))
        with self.assertRaises(ValueError):
            big_fat_comparer(try1, try2, hard=True)

        try2['giorgio']['yes'][0] = 'c'
        self.assertFalse(big_fat_comparer(try1, try2))
        with self.assertRaises(ValueError):
            big_fat_comparer(try1, try2, hard=True)

        try2['giorgio']['yes'][0] = 12
        try1['giorgio']['yes'].append(12)
        self.assertFalse(big_fat_comparer(try1, try2))
        with self.assertRaises(ValueError):
            big_fat_comparer(try1, try2, hard=True)

        del try1['giorgio']['yes'][2]
        self.assertTrue(big_fat_comparer(try1, try2))
        self.assertTrue(big_fat_comparer(try1, try2, hard=True))


class Test_wt(unittest.TestCase):
    """Run the tests for the wt utilities."""

    def test_crossing_counter(self):
        ph1, ph2 = crossing_finder(path=PATHTEST0, interface=2.9)
        self.assertEqual(7, len(ph1))

    def test_segments_counter(self):
        self.assertEqual(4, segments_counter(path=PATHTEST0,
                                             interface_l=2.9, interface_r=4.1))
        self.assertEqual(4, segments_counter(path=PATHTEST0,
                                             interface_l=2, interface_r=9))

    def test_trim_path_between_interfaces(self):
        """ Test for trimming trajectories withing a range in path space"""
        path0 = trim_path_between_interfaces(path=PATHTEST0, interface_l=3.0,
                                             interface_r=7.0)
        path2 = PATHTEST2.copy()
        path2.generated = 'ct'

        with patch('sys.stdout', new=StringIO()):
            self.assertTrue(path0.length == 12)
            self.assertTrue(path2 == path0)
            self.assertTrue(PATHTEST0 != path0)

    def test_select_and_trim_a_segment(self):
        """ Test to trim a selected segment keeping the crossing"""
        path_rnd = select_and_trim_a_segment(path=PATHTEST0, interface_l=4.1,
                                             interface_r=5.9)
        path3 = select_and_trim_a_segment(path=PATHTEST0, interface_l=4.1,
                                          interface_r=5.9, segment_to_pick=0)
        path1 = PATHTEST1.copy()
        path1.generated = 'sg'

        with patch('sys.stdout', new=StringIO()):
            self.assertTrue(path3 != path_rnd)
            self.assertTrue(path1 == path3)
            self.assertTrue(path3.length == 3)
            self.assertTrue(PATHTEST1 != path3)


if __name__ == '__main__':
    unittest.main()
