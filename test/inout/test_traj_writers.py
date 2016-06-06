# -*- coding: utf-8 -*-
"""A simple test module for the writers.

Here we test that we can write and read different output formats.
"""
import logging
import unittest
import numpy as np
from pyretis.core.particles import Particles
from pyretis.inout.writers.traj import _adjust_coordinate
logging.disable(logging.CRITICAL)


class TrajTest(unittest.TestCase):
    """Test trajectory writing work as intended."""

    def test_adjust_coordinates(self):
        """Test that we can adjust coordinates."""
        # 1 particle, 1D
        particles = Particles(dim=1)
        particles.add_particle(np.array([1.0]),
                               np.zeros(1),
                               np.zeros(1))
        pos = _adjust_coordinate(particles.pos)
        self.assertTrue(np.allclose(pos, np.array([1.0, 0.0, 0.0])))
        # 1 particle, 2D
        particles = Particles(dim=2)
        particles.add_particle(np.array([1.0, 1.0]),
                               np.zeros(2),
                               np.zeros(2))
        pos = _adjust_coordinate(particles.pos)
        self.assertTrue(np.allclose(pos, np.array([1.0, 1.0, 0.0])))
        # 1 particle, 3D
        particles = Particles(dim=3)
        particles.add_particle(np.array([1.0, 1.0, 1.0]),
                               np.zeros(3),
                               np.zeros(3))
        pos = _adjust_coordinate(particles.pos)
        self.assertTrue(np.allclose(pos, np.array([1.0, 1.0, 1.0])))
        # 2 particles, 1D
        particles = Particles(dim=1)
        particles.add_particle(np.array([1.0]),
                               np.zeros(1),
                               np.zeros(1))
        particles.add_particle(np.array([-1.0]),
                               np.zeros(1),
                               np.zeros(1))
        pos = _adjust_coordinate(particles.pos)
        self.assertTrue(np.allclose(pos, np.array([[1., 0., 0.],
                                                   [-1., 0., 0.]])))
        # 2 particles, 2D
        particles = Particles(dim=2)
        particles.add_particle(np.array([1.0, -1.0]),
                               np.zeros(2),
                               np.zeros(2))
        particles.add_particle(np.array([-1.0, 1.0]),
                               np.zeros(2),
                               np.zeros(2))
        pos = _adjust_coordinate(particles.pos)
        self.assertTrue(np.allclose(pos, np.array([[1., -1., 0.],
                                                   [-1., 1., 0.]])))

        # 3 particles, 3D
        particles = Particles(dim=3)
        particles.add_particle(np.array([1.0, -1.0, 0.5]),
                               np.zeros(3),
                               np.zeros(3))
        particles.add_particle(np.array([-1.0, 1.0, -0.5]),
                               np.zeros(3),
                               np.zeros(3))
        pos = _adjust_coordinate(particles.pos)
        self.assertTrue(np.allclose(pos, np.array([[1., -1., 0.5],
                                                   [-1., 1., -0.5]])))


if __name__ == '__main__':
    unittest.main()
