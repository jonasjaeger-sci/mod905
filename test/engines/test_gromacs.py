# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the GromacsEngine class."""
import logging
import unittest
import os
from pyretis.engines import GromacsEngine
logging.disable(logging.CRITICAL)


HERE = os.path.abspath(os.path.dirname(__file__))


class GromacsEngineTest(unittest.TestCase):
    """Run the tests for the GromacsEngine"""

    def test_init(self):
        """Test that we can invert time."""
        dir_name = os.path.join(HERE, 'gmx_input')
        eng = GromacsEngine('echo', 'echo', dir_name, 0.002, 10,
                            maxwarn=10, gmx_format='gro', write_vel=True,
                            write_force=False)
        eng.exe_dir = dir_name
        with self.assertRaises(ValueError):
            GromacsEngine('echo', 'echo', 'gmx_input', 0.002, 10,
                          gmx_format='not-a-format')
        with self.assertRaises(ValueError):
            GromacsEngine('echo', 'echo', 'missing-files', 0.002, 10,
                          gmx_format='g96')


if __name__ == '__main__':
    unittest.main()
