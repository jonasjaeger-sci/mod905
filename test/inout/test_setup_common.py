# -*- coding: utf-8 -*-
# Copyright (c) 2026, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test setup functions."""
import os
import logging
import unittest
from pyretis.setup.common import (check_settings,
                                  create_external)


logging.disable(logging.CRITICAL)
LOCAL_DIR = os.path.abspath(os.path.dirname(__file__))


class TestCheckSettings(unittest.TestCase):
    """Test that check_settings work as intented."""

    def test_check_settings(self):
        """Test that we can import."""
        settings = {'one': 1, 'two': 2, 'three': 3}
        required = ['three', 'two']
        result, not_found = check_settings(settings, required)
        self.assertTrue(result)
        self.assertEqual(0, len(not_found))
        extra = ['three fiddy']
        required += extra
        result, not_found = check_settings(settings, required)
        self.assertFalse(result)
        for i, j in zip(not_found, extra):
            self.assertEqual(i, j)


class TestCreateExternal(unittest.TestCase):
    """Test that we can import and create from other modules."""

    def test_create_from_module(self):
        """Test that we can import."""
        module = os.path.join(LOCAL_DIR, 'fooengine.py')

        settings = {}
        obj = create_external(settings, 'foo', None, None, key_settings=None)
        self.assertIs(obj, None)

        settings = {'foo': {'module': module, 'class': 'FooEngine'}}
        with self.assertRaises(ValueError):  # missing an argument:
            obj = create_external(settings, 'foo', None, [],
                                  key_settings=None)
        settings['foo']['timestep'] = 1
        create_external(settings, 'foo', None, [], key_settings=None)

        with self.assertRaises(ValueError):  # not callable:
            create_external(settings, 'foo', None, ['foo_bar'],
                            key_settings=None)

        settings = {'foo': {'module': 'three fiddy', 'class': 'NoClassHere'},
                    'simulation': {}}
        with self.assertRaises(ValueError):
            create_external(settings, 'foo', None, [], key_settings=None)


if __name__ == '__main__':
    unittest.main()
