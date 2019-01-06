# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the FileIO class."""
import logging
import unittest
import tempfile
import os
from pyretis.inout.writers.fileio import FileIO
logging.disable(logging.CRITICAL)


HERE = os.path.abspath(os.path.dirname(__file__))


def _remove_file(filename):
    """Remove a file, fail silently if somethings fails."""
    try:
        os.remove(filename)
    except OSError:
        pass


class TestFileIO(unittest.TestCase):
    """Test the FileIO class."""

    def test_initiation(self):
        """Test initiation and opening of files."""
        with tempfile.NamedTemporaryFile() as tmp:
            fileio = FileIO(tmp.name, oldfile='unknownsetting', header='test')
            self.assertTrue(fileio.fileh is None)
            fileio = FileIO(tmp.name, oldfile='overwrite', header='test')
            self.assertFalse(fileio.fileh is None)
            fileio = FileIO(tmp.name, oldfile='append', header='test')
            self.assertFalse(fileio.fileh is None)
        logging.disable(logging.INFO)
        with self.assertLogs('pyretis.inout.writers.fileio',
                             level='CRITICAL'):
            fileio = FileIO(None, oldfile='append', header='test')
        logging.disable(logging.CRITICAL)
        self.assertTrue(fileio.fileh is None)
        # test for completely new file:
        filename = os.path.join(HERE, 'a_new_file')
        _remove_file(filename)
        fileio = FileIO(filename, oldfile='overwrite', header='test')
        self.assertFalse(fileio.fileh is None)
        fileio.close()
        _remove_file(filename)
        # test for completely existing file:
        filename = os.path.join(HERE, 'already_exists2')
        _remove_file(filename)
        _remove_file('{}_000'.format(filename))
        with open(filename, 'w') as fileh:
            fileh.write('test')
        fileio = FileIO(filename, oldfile='backup', header='test')
        self.assertFalse(fileio.fileh is None)
        fileio.close()
        _remove_file(filename)
        _remove_file('{}_000'.format(filename))
        # test for invalid filename
        fileio = FileIO('/', oldfile='backup', header='test')
        self.assertTrue(fileio.fileh is None)

    def test_write(self):
        """Test writing to the file."""
        with tempfile.NamedTemporaryFile() as tmp:
            fileio = FileIO(tmp.name, oldfile='overwrite', header='test')
            status = fileio.write(None)
            self.assertFalse(status)
            status = fileio.write('some text')
            self.assertTrue(status)
            status = fileio.write('some text', end=None)
            self.assertTrue(status)
            fileio.force_flush()
            fileio.close()
            status = fileio.write('some text')
            self.assertFalse(status)


if __name__ == '__main__':
    unittest.main()
