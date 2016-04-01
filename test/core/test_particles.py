# -*- coding: utf-8 -*-
"""Test the Box class from pyretis.core"""
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
        


if __name__ == '__main__':
    unittest.main()
