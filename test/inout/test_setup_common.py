# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test setup functions."""
import os
import logging
import unittest
import sys
import inspect
from pyretis.inout.setup.common import (import_from,
                                        check_settings,
                                        create_external)


logging.disable(logging.CRITICAL)
LOCAL_DIR = os.path.abspath(os.path.dirname(__file__))


class TestImportFrom(unittest.TestCase):
    """Test that we can import from other modules."""

    def test_import(self):
        """Test that we can import."""
        module = os.path.join(LOCAL_DIR, 'fooengine.py')
        klass = 'FooEngine'
        imp = import_from(module, klass)
        sys.path.insert(0, LOCAL_DIR)
        from fooengine import FooEngine
        del sys.path[0]
        self.assertEqual(
            inspect.getsource(imp),
            inspect.getsource(FooEngine)
        )

    def test_import_importerror(self):
        """Test that we can import."""
        module = os.path.join(LOCAL_DIR, 'fooengine.py')
        klass = 'DoesNotExist'
        with self.assertRaises(ValueError):
            import_from(module, klass)
        module = 'path-that-should-not-be'
        with self.assertRaises(ValueError):
            import_from(module, klass)
        module = os.path.join(LOCAL_DIR, 'isnothere.py')
        with self.assertRaises(ValueError):
            import_from(module, klass)


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
