# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""A test for the potential base class."""
import logging
import unittest
from pyretis.forcefield.potential import PotentialFunction
logging.disable(logging.CRITICAL)


class TestPotentialFunction(unittest.TestCase):
    """Test the PotentialFunction class."""

    def test_potential_function(self):
        """Test PotentialFunction class."""
        pot = PotentialFunction()
        params = {'a': 10}
        pot.set_parameters(params)
        self.assertFalse(pot.params)


if __name__ == '__main__':
    unittest.main()
