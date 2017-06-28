# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""This file tests the Python implementation of the order parameter."""
import logging
import numpy as np
import unittest
from pyretis.engines.gromacs import read_gromos96_file
from pyretis.core import System, Particles
from orderp import RingDiffusion
from ordermod import ordermod
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


class TestOrder(unittest.TestCase):
    """Just test that we can reproduce the FORTRAN implementation."""

    def test_orderp(self):
        testo = RingDiffusion()
        _, pos, _, _ = read_gromos96_file('gromacs_input/conf.g96')
        system = System()
        system.particles = Particles(dim=3)
        system.particles.pos = pos
        lambpy = testo.calculate(system)[0]
        lambf = ordermod.calculate(pos)
        self.assertAlmostEqual(lambpy, lambf)
    


if __name__ == '__main__':
    testo = RingDiffusion()
    print('Indexes for the two groups:')
    print('Idx1', testo.idx1)
    print('Idx2', testo.idx2)
    print('Testing')
    unittest.main()
