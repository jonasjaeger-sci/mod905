# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the common methods in pyretis.inout.common."""
import os
import logging
import unittest
from pyretis.inout.common import (
    apply_format,
    _remove_extension,
    make_dirs,
    simplify_ensemble_name,
    add_dirname,
    name_file,
    format_number,
    get_log_formatter,
    PyretisLogFormatter,
    LOG_FMT,
    LOG_DEBUG_FMT,
)
logging.disable(logging.CRITICAL)


HERE = os.path.abspath(os.path.dirname(__file__))


def remove_dir(dirname):
    """Remove a directory."""
    try:
        os.removedirs(dirname)
    except OSError:
        pass


class TestMethods(unittest.TestCase):
    """Test some of the methods from pyretis.inout.common."""

    def test_apply_format(self):
        """Test that we can apply a format."""
        txt = apply_format(12345.7, '{:7.2f}')
        self.assertEqual(txt, '1.2e+04')
        txt = apply_format(-1234568.9, '{:7.2f}')
        self.assertEqual(txt, ' -1e+06')
        txt = apply_format(-1234568.9, '{:8.2f}')
        self.assertEqual(txt, '-1.2e+06')
        txt = apply_format(-1234568.9, '{:9.2f}')
        self.assertEqual(txt, '-1.23e+06')
        txt = apply_format(123.45, '{:>10.2f}')
        self.assertEqual(txt, '    123.45')

    def test_remove_ext(self):
        """Test that we can remove the extenstion from a file name."""
        for case in ('filename', '.filename'):
            filename = ''.join([case, os.extsep, 'txt'])
            txt = _remove_extension(filename)
            self.assertEqual(txt, case)
        filename = ''.join(['test', os.extsep, 'txt'])
        path = os.path.join('path', 'to', filename)
        txt = _remove_extension(path)
        self.assertEqual(txt, os.path.join('path', 'to', 'test'))

    def test_make_dirs(self):
        """Test that we can create directories."""
        dirname = os.path.join(HERE, 'testdir')
        make_dirs(dirname)
        self.assertTrue(os.path.isdir(dirname))
        remove_dir(dirname)
        dirname = os.path.join(HERE, 'already_exists')
        with self.assertRaises(OSError):
            make_dirs(dirname)
        dirname = os.path.join(HERE, 'dir_exists')
        remove_dir(dirname)
        make_dirs(dirname)
        msg = make_dirs(dirname)
        self.assertTrue(msg.endswith('already exist.'))
        remove_dir(dirname)

    def test_simplify_ensemble_name(self):
        """Test that we can simplify ensemble names."""
        cases = [('[0^-]', '000'), ('[0^+]', '001'), ('[1^+]', '002')]
        for case in cases:
            txt = simplify_ensemble_name(case[0], fmt='{:03d}')
            self.assertEqual(txt, case[1])
        txt = simplify_ensemble_name('001', fmt='{:03d}')
        self.assertEqual(txt, '001')
        txt = simplify_ensemble_name('[1]', fmt='{:03d}')
        self.assertEqual(txt, '002')

    def test_add_dirname(self):
        """Test that we can add a directory to a filename."""
        path = add_dirname('filename.txt', 'path')
        self.assertEqual(path, os.path.join('path', 'filename.txt'))
        path = add_dirname('filename.txt', None)
        self.assertEqual(path, 'filename.txt')

    def test_name_file(self):
        """Test that we can name a file."""
        name = name_file('test', 'txt', path='path')
        filename = ''.join(['test', os.extsep, 'txt'])
        filepath = os.path.join('path', filename)
        self.assertEqual(name, filepath)

    def test_format_number(self):
        """Test that we can format numbers as expected."""
        txt = format_number(99.9, 0.0, 100, fmtf='{0:<4.2f}',
                            fmte='{0:<4.2e}')
        self.assertEqual(txt, '99.90')
        txt = format_number(100.1, 0.0, 100, fmtf='{0:<4.2f}',
                            fmte='{0:<4.2e}')
        self.assertEqual(txt, '1.00e+02')
        txt = format_number(-100.1, 0.0, 100, fmtf='{0:<4.2f}',
                            fmte='{0:<4.2e}')
        self.assertEqual(txt, '-1.00e+02')

    def test_get_formatter(self):
        """Test that we can select the log formatter."""
        formatter = get_log_formatter(0)
        self.assertIsInstance(formatter, PyretisLogFormatter)
        self.assertEqual(formatter._fmt,  # pylint: disable=protected-access
                         LOG_DEBUG_FMT)

        formatter = get_log_formatter(100)
        self.assertIsInstance(formatter, PyretisLogFormatter)
        self.assertEqual(formatter._fmt,  # pylint: disable=protected-access
                         LOG_FMT)


if __name__ == '__main__':
    unittest.main()
