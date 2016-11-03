# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""Test methods from pyretis.core.common"""
import logging
import unittest
import sys
import os
from pyretis.core.common import inspect_function
logging.disable(logging.CRITICAL)


# define some functions used for testing:
def function1(arg1, arg2, arg3, arg4):
    pass


def function2(arg1, arg2, arg3, arg4=10):
    pass


def function3(arg1, arg2, arg3, arg4=100, arg5=10):
    pass


def function4(*args, **kwargs):
    pass


class InspectTest(unittest.TestCase):
    """Run the inspect_function method."""

    def test_inspect(self):
        """Test the inspect function method."""
        # define some test functions:
        functions = [function1, function2, function3, function4]
        correct = [{'args': ['arg1', 'arg2', 'arg3', 'arg4'],
                    'varargs': [], 'kwargs': [], 'keywords': []},
                   {'args': ['arg1', 'arg2', 'arg3'],
                    'varargs': [], 'kwargs': ['arg4'], 'keywords': []},
                   {'args': ['arg1', 'arg2', 'arg3'], 'varargs': [],
                    'kwargs': ['arg4', 'arg5'], 'keywords': []},
                   {'args': [], 'varargs': ['args'], 'kwargs': [],
                    'keywords': ['kwargs']}]
        if sys.version_info >= (3, 0):
            # extra python3 tests:
            here = os.path.abspath(os.path.dirname(__file__))
            sys.path.insert(0, here)
            from common_python3 import function5, function6, function7
            del sys.path[0]
            functions.append(function5)
            correct.append({'args': ['arg1', 'arg2'],
                            'kwargs': ['arg3', 'arg4'],
                            'varargs': ['args'], 'keywords': []})
            functions.append(function6)
            correct.append({'args': ['arg1', 'arg2'],
                            'kwargs': ['arg3', 'arg4'],
                            'varargs': [], 'keywords': []})
            functions.append(function7)
            correct.append({'args': ['arg1', 'arg2'],
                            'kwargs': ['arg3', 'arg4', 'arg5'],
                            'varargs': ['args'], 'keywords': []})

        for i, func in enumerate(functions):
            args = inspect_function(func)
            self.assertEqual(args, correct[i])


if __name__ == '__main__':
    unittest.main()
