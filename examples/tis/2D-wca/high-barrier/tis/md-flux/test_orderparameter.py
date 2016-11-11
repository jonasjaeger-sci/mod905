# -*- coding: utf-8 -*-
"""Test the calculation of the order parameter.

This test is checking that the order parameter is calculated
correctly.

1) The order parameter from pyretis.

2) A python implementation.

3) A C implementation.
"""
# pylint: disable=C0103
from __future__ import print_function
import unittest
import numpy as np
from pyretis.core import Particles, Box, System
from pyretis.core.units import create_conversion_factors
from wcafunctions import WCAOrderParameter
from pyretis.core.orderparameter import OrderParameterDistance


class WCAOrderTest(unittest.TestCase):
    """Run the tests for the Fortran potential class."""

    def test_wca_orderp(self):
        """Test evaluation of the order parameter."""
        box = Box(size=[[0., 3.], [0., 3.]])
        particles = Particles(dim=2)
        particles.add_particle(np.array([1.0, 1.0]), np.zeros(2), np.zeros(2),
                               mass=1.0, name='A', ptype=0)
        particles.add_particle(np.array([1.0, 2.0]), np.zeros(2), np.zeros(2),
                               mass=1.0, name='A', ptype=0)
        create_conversion_factors('lj')
        system = System(box=box, units='lj')        
        system.particles = particles

        order1 = WCAOrderParameter((0,1))
        order2 = OrderParameterDistance('WCA distance', (0,1), periodic=True)

        for i in np.arange(0.001, 5.0, 0.1):
            particles.pos[1] = np.array([1.0, i])
            particles.vel = np.random.random(particles.vel.shape)
            lmb1 = order1.calculate(system)
            vel1 = order1.calculate_velocity(system)
            lmb2 = order2.calculate(system)
            vel2 = order2.calculate_velocity(system)
            self.assertAlmostEqual(lmb1, lmb2)
            self.assertAlmostEqual(vel1, vel2)


if __name__ == '__main__':
    unittest.main()
