# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the Particles class from pyretis.core"""
import logging
import unittest
import numpy as np
from pyretis.core.particles import Particles
logging.disable(logging.CRITICAL)


class ParticleTest(unittest.TestCase):
    """Run the tests for the Particle() class."""

    def test_creation(self):
        """Test the creation a particle list."""
        particles = Particles(dim=1)
        particles.add_particle(np.zeros(1), np.zeros(1), np.zeros(1))
        self.assertEqual(particles.dim, 1)
        self.assertEqual(particles.npart, 1)
        self.assertEqual(particles.virial.shape, (1, 1))


if __name__ == '__main__':
    unittest.main()
