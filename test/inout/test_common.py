# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the common methods in pyretis.inout.common."""
import os
import logging
import unittest
from pyretis.inout.common import (
    _remove_extension,
    make_dirs,
    simplify_ensemble_name,
    add_dirname,
    name_file,
    generate_file_name,
    create_empty_ensembles
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
    def test_create_empty_ensembles(self):
        """Test that we can properly create empty ensembles."""
        settings = {'simulation': {'interfaces': [1, 2, 3, 4, 5]}}
        create_empty_ensembles(settings)
        settings = {'simulation': {'interfaces': [1, 2, 3, 4, 5]}}
        settings['ensemble'] = [settings]
        settings['ensemble'][0]['interface'] = 1
        settings['ensemble'][0]['tis'] = {'ensemble_number': 123321}
        create_empty_ensembles(settings)
        self.assertTrue(settings['ensemble'][0]['interface'] == 1)
        self.assertTrue(
            settings['ensemble'][0]['tis']['ensemble_number'] == 123321)

        settings = {'simulation': {'interfaces': [1, 2, 3, 4, 5]},
                    'tis': {'ensemble_number': 123321}}
        create_empty_ensembles(settings)
        self.assertTrue(
            settings['ensemble'][0]['tis']['ensemble_number'] == 123321)
        self.assertTrue(len(settings['ensemble']) == 1)

        settings = {'simulation': {'interfaces': [1, 2, 3, 4, 5]},
                    'ensemble': [{'interface': 3,
                                  'gnappo': 'lappo',
                                  'tis': {'ensemble_number': 3}}]}
        create_empty_ensembles(settings)
        self.assertEqual(settings['ensemble'][3]['interface'], 3)
        self.assertEqual(settings['ensemble'][3]['gnappo'], 'lappo')
        self.assertEqual(
            settings['ensemble'][3]['tis']['ensemble_number'], 3)

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

    def test_generate_filename(self):
        """Test the generation of file names."""
        settings = {'output': {}}
        name = generate_file_name('base.txt', 'dir', settings)
        self.assertEqual(name, os.path.join('dir', 'base.txt'))
        settings = {'output': {'prefix': 'abc-'}}
        name = generate_file_name('base.txt', 'dir', settings)
        self.assertEqual(name, os.path.join('dir', 'abc-base.txt'))


if __name__ == '__main__':
    unittest.main()
