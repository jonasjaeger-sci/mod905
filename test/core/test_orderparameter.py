# -*- coding: utf-8 -*-
"""Test the order parameter class from pyretis.core"""
import logging
import unittest
import numpy as np
from pyretis.core.orderparameter import OrderParameterPosition
from pyretis.core import System, Box
from pyretis.core.units import create_conversion_factors
logging.disable(logging.CRITICAL)


class OrderPositionTest(unittest.TestCase):
    """Run the tests for the OrderParameterPosition class."""

    def test_one_particle(self):
        """Test the position order parameter for a one-particle system."""
        create_conversion_factors('lj')
        dim_map = {'x': 0, 'y': 1, 'z': 2}
        for xdim in dim_map:
            idim = dim_map[xdim]
            orderp = OrderParameterPosition('Positional order parameter', 0,
                                            dim=xdim, periodic=False)
            # Test for a one-particle system:
            for ndim in [1, 2, 3]:
                box = Box(periodic=[False]*ndim)
                system = System(temperature=1.0, units='lj', box=box)
                for _ in range(1):
                    pos = np.random.random(box.dim)
                    vel = np.random.random(box.dim)
                    system.add_particle(name='Ar', pos=pos, vel=vel, mass=1.0,
                                        ptype=0)
                if idim > ndim-1 and ndim != 1:
                    self.assertRaises(IndexError, orderp.calculate, (system))
                    self.assertRaises(IndexError, orderp.calculate_velocity,
                                      (system))
                else:
                    lmb = orderp.calculate(system)
                    lmb_vel = orderp.calculate_velocity(system)
                    if ndim == 1:
                        lmb_correct = system.particles.pos[0]
                        lmb_vel_correct = system.particles.vel[0]
                    else:
                        lmb_correct = system.particles.pos[idim]
                        lmb_vel_correct = system.particles.vel[idim]
                    self.assertAlmostEqual(lmb, lmb_correct)
                    self.assertAlmostEqual(lmb_vel, lmb_vel_correct)

    def test_multi_particle(self):
        """Test the position order parameter for many particles."""
        create_conversion_factors('lj')
        dim_map = {'x': 0, 'y': 1, 'z': 2}
        for xdim in dim_map:
            idim = dim_map[xdim]
            orderp = OrderParameterPosition('Positional order parameter', 0,
                                            dim=xdim, periodic=False)
            # Test for n-component system
            for ndim in [1, 2, 3]:
                box = Box(periodic=[False]*ndim)
                system = System(temperature=1.0, units='lj', box=box)
                for _ in range(10):
                    pos = np.random.random(box.dim)
                    vel = np.random.random(box.dim)
                    system.add_particle(name='Ar', pos=pos, vel=vel, mass=1.0,
                                        ptype=0)
                if idim > ndim-1 and ndim != 1:
                    self.assertRaises(IndexError, orderp.calculate, (system))
                    self.assertRaises(IndexError, orderp.calculate_velocity,
                                      (system))
                else:
                    lmb = orderp.calculate(system)
                    lmb_vel = orderp.calculate_velocity(system)
                    if ndim == 1:
                        lmb_correct = system.particles.pos[0]
                        lmb_vel_correct = system.particles.vel[0]
                    else:
                        lmb_correct = system.particles.pos[0, idim]
                        lmb_vel_correct = system.particles.vel[0, idim]
                    self.assertAlmostEqual(lmb, lmb_correct)
                    self.assertAlmostEqual(lmb_vel, lmb_vel_correct)


if __name__ == '__main__':
    unittest.main()
