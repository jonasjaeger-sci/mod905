# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Test the order parameter class from pyretis.core"""
import logging
import unittest
import numpy as np
from pyretis.orderparameter import order_factory
from pyretis.orderparameter.orderparameter import (
    OrderParameter,
    OrderParameterPosition,
    OrderParameterDistance
)
from pyretis.orderparameter.orderangle import OrderParameterAngle
from pyretis.core import System, Box, Particles
from pyretis.core.units import create_conversion_factors
logging.disable(logging.CRITICAL)


class OrderPositionTest(unittest.TestCase):
    """Run the tests for the OrderParameterPosition class."""

    def test_one_particle(self):
        """Test the position order parameter for a one-particle system."""
        create_conversion_factors('lj')
        for ndim in [1, 2, 3]:
            box = Box(periodic=[False]*ndim)
            system = System(temperature=1.0, units='lj', box=box)
            system.particles = Particles(system.get_dim())
            pos = np.random.random(box.dim)
            vel = np.random.random(box.dim)
            system.add_particle(name='Ar', pos=pos, vel=vel, mass=1.0,
                                ptype=0)
            for idim, xdim in enumerate(('x', 'y', 'z')):
                orderp = OrderParameterPosition(0, dim=xdim, periodic=False)
                if idim > ndim - 1:
                    self.assertRaises(IndexError, orderp.calculate, (system))
                    self.assertRaises(IndexError, orderp.calculate_velocity,
                                      (system))
                else:
                    lmb = orderp.calculate(system)
                    lmb_vel = orderp.calculate_velocity(system)
                    lmb_correct = system.particles.pos[0][idim]
                    lmb_vel_correct = system.particles.vel[0][idim]
                    self.assertAlmostEqual(lmb, lmb_correct)
                    self.assertAlmostEqual(lmb_vel, lmb_vel_correct)

    def test_multi_particle(self):
        """Test the position order parameter for many particles."""
        create_conversion_factors('lj')
        dim_map = {'x': 0, 'y': 1, 'z': 2}
        for xdim in dim_map:
            idim = dim_map[xdim]
            orderp = OrderParameterPosition(0, dim=xdim,
                                            periodic=False)
            # Test for n-component system
            for ndim in [1, 2, 3]:
                box = Box(periodic=[False]*ndim)
                system = System(temperature=1.0, units='lj', box=box)
                system.particles = Particles(system.get_dim())
                for _ in range(10):
                    pos = np.random.random(box.dim)
                    vel = np.random.random(box.dim)
                    system.add_particle(name='Ar', pos=pos, vel=vel, mass=1.0,
                                        ptype=0)
                if idim > ndim-1:
                    self.assertRaises(IndexError, orderp.calculate, (system))
                    self.assertRaises(IndexError, orderp.calculate_velocity,
                                      (system))
                else:
                    lmb = orderp.calculate(system)
                    lmb_vel = orderp.calculate_velocity(system)
                    lmb_correct = system.particles.pos[0][idim]
                    lmb_vel_correct = system.particles.vel[0][idim]
                    self.assertAlmostEqual(lmb, lmb_correct)
                    self.assertAlmostEqual(lmb_vel, lmb_vel_correct)

    def test_one_particle_pbc(self):
        """Test that pbc boundaries are applied when asked for."""
        create_conversion_factors('lj')
        dim_map = {'x': 0, 'y': 1, 'z': 2}
        for disp in [0.0, 1.5, -1.5, 100., -100.]:
            for ndim in [1, 2, 3]:
                size = [[0.0, 1.0] for _ in range(ndim)]
                box = Box(size, periodic=[True]*ndim)
                system = System(temperature=1.0, units='lj', box=box)
                system.particles = Particles(system.get_dim())
                pos = np.random.random(box.dim) * np.ones(box.dim)*disp
                vel = np.random.random(box.dim)
                system.add_particle(name='Ar', pos=pos, vel=vel, mass=1.0,
                                    ptype=0)
                for xdim in ['x', 'y', 'z'][:ndim]:
                    orderp = OrderParameterPosition(0, dim=xdim,
                                                    periodic=True)
                    lmb = orderp.calculate(system)
                    idim = dim_map[xdim]
                    lmb_correct = box.pbc_coordinate_dim(pos[idim], idim)
                    self.assertAlmostEqual(lmb, lmb_correct)

    def test_multiple_particle_pbc(self):
        """Test that pbc boundaries are applied when asked for."""
        create_conversion_factors('lj')
        dim_map = {'x': 0, 'y': 1, 'z': 2}
        for disp in [0.0, 1.5, -1.5, 100., -100.]:
            for ndim in [1, 2, 3]:
                size = [[0.0, 1.0] for _ in range(ndim)]
                box = Box(size, periodic=[True]*ndim)
                system = System(temperature=1.0, units='lj', box=box)
                system.particles = Particles(system.get_dim())
                for _ in range(10):
                    pos = np.random.random(box.dim) * np.ones(box.dim)*disp
                    vel = np.random.random(box.dim)
                    system.add_particle(name='Ar', pos=pos, vel=vel,
                                        mass=1.0, ptype=0)
                for xdim in ['x', 'y', 'z'][:ndim]:
                    orderp = OrderParameterPosition(0, dim=xdim,
                                                    periodic=True)
                    lmb = orderp.calculate(system)
                    idim = dim_map[xdim]
                    pos = system.particles.pos[0]
                    lmb_correct = box.pbc_coordinate_dim(pos[idim], idim)
                    self.assertAlmostEqual(lmb, lmb_correct)

    def test_init_fail(self):
        """Check that the initiation fails if we supply strange input."""
        with self.assertRaises(KeyError):
            OrderParameterPosition(0, dim='a')


class OrderDistanceTest(unittest.TestCase):
    """Run the tests for the OrderParameterDistance class."""

    def test_two_particles(self):
        """Test the distance order parameter without pbc."""
        orderp = OrderParameterDistance((0, 1),
                                        periodic=False)
        # Test for a one-particle system:
        for ndim in [1, 2, 3]:
            box = Box(periodic=[False]*ndim)
            system = System(temperature=1.0, units='lj', box=box)
            system.particles = Particles(system.get_dim())
            for _ in range(2):
                pos = np.random.random(box.dim)
                vel = np.random.random(box.dim)
                system.add_particle(name='Ar', pos=pos, vel=vel, mass=1.0,
                                    ptype=0)
            lmb = orderp.calculate(system)
            delta = system.particles.pos[1] - system.particles.pos[0]
            lmb_correct = np.sqrt(np.dot(delta, delta))
            self.assertAlmostEqual(lmb, lmb_correct)
            delta_v = system.particles.vel[1] - system.particles.vel[0]
            lmb_vel = orderp.calculate_velocity(system)
            lmb_vel_correct = np.dot(delta, delta_v) / lmb_correct
            self.assertAlmostEqual(lmb_vel, lmb_vel_correct)

    def test_two_pbcparticles(self):
        """Test the distance order parameter with pbc."""
        orderp = OrderParameterDistance((0, 1),
                                        periodic=True)
        # Test for a one-particle system:
        for disp in [0.0, 1.5, -1.5, 100., -100.]:
            for ndim in [1, 2, 3]:
                size = [[0.0, 1.0] for _ in range(ndim)]
                box = Box(size, periodic=[True]*ndim)
                system = System(temperature=1.0, units='lj', box=box)
                system.particles = Particles(system.get_dim())
                for _ in range(2):
                    pos = np.random.random(box.dim) + np.ones(box.dim)*disp
                    system.add_particle(name='Ar', pos=pos,
                                        vel=np.random.random(box.dim),
                                        mass=1.0,
                                        ptype=0)
                lmb = orderp.calculate(system)
                delta = box.pbc_dist_coordinate(system.particles.pos[1] -
                                                system.particles.pos[0])
                lmb_correct = np.sqrt(np.dot(delta, delta))
                self.assertAlmostEqual(lmb, lmb_correct)
                delta_v = system.particles.vel[1] - system.particles.vel[0]
                lmb_vel = orderp.calculate_velocity(system)
                lmb_vel_correct = np.dot(delta, delta_v) / lmb_correct
                self.assertAlmostEqual(lmb_vel, lmb_vel_correct)

    def test_init_fail(self):
        """Check that the initiation fails if we supply strange input."""
        with self.assertRaises(TypeError):
            OrderParameterDistance(0)
        with self.assertRaises(TypeError):
            OrderParameterDistance((0))
        with self.assertRaises(ValueError):
            OrderParameterDistance([0])
        with self.assertRaises(ValueError):
            OrderParameterDistance((0,))
        with self.assertRaises(ValueError):
            OrderParameterDistance((0, 1, 2))


class OrderAngleTest(unittest.TestCase):
    """Run the tests for the OrderParameterAngle class."""

    def test_without_pbc(self):
        """Test the distance order parameter without pbc."""
        orderp = OrderParameterAngle((1, 0, 2), periodic=False)
        # Test for SPC water
        box = Box(periodic=[False, False, False])
        system = System(temperature=1.0, units='lj', box=box)
        system.particles = Particles(system.get_dim())
        system.add_particle(name='O', pos=np.array([0.230, 0.628, 0.113]))
        system.add_particle(name='H', pos=np.array([0.137, 0.626, 0.150]))
        system.add_particle(name='H', pos=np.array([0.231, 0.589, 0.021]))
        angle = orderp.calculate(system)
        angle_deg = angle * 180. / np.pi
        self.assertAlmostEqual(angle_deg, 109.984398, places=3)

    def test_witht_pbc(self):
        """Test the distance order parameter with pbc."""
        orderp = OrderParameterAngle((1, 0, 2), periodic=True)
        # Test for SPC water
        box = Box(periodic=[True, True, True], size=[1., 1., 1.])
        system = System(temperature=1.0, units='lj', box=box)
        system.particles = Particles(system.get_dim())
        system.add_particle(name='O', pos=np.array([0.230, 0.628, 0.113]))
        system.add_particle(name='H', pos=np.array([0.137, 0.626, 0.150]))
        system.add_particle(name='H', pos=np.array([1.231, 0.589, 0.021]))
        angle = orderp.calculate(system)
        angle_deg = angle * 180. / np.pi
        self.assertAlmostEqual(angle_deg, 109.984398, places=3)

    def test_triangle(self):
        """Test the distance order parameter for a 2D case."""
        box = Box(periodic=[False, False])
        system = System(temperature=1.0, units='lj', box=box)
        system.particles = Particles(system.get_dim())
        system.add_particle(name='X', pos=np.array([0.0, 0.0]))
        system.add_particle(name='X', pos=np.array([1.0, 0.0]))
        system.add_particle(name='X', pos=np.array([0.0, 1.0]))
        for idx, correct in zip(((1, 0, 2), (0, 1, 2), (0, 2, 1)),
                                (90., 45., 45.)):
            orderp = OrderParameterAngle(idx, periodic=False)
            angle = orderp.calculate(system)
            angle_deg = angle * 180. / np.pi
            self.assertAlmostEqual(angle_deg, correct)

    def test_initiate_fail(self):
        """Test that we fail if we give incorrect number of indices."""
        with self.assertRaises(TypeError):
            OrderParameterAngle((0), periodic=False)
        with self.assertRaises(TypeError):
            OrderParameterAngle(0, periodic=False)
        with self.assertRaises(ValueError):
            OrderParameterAngle((0,), periodic=False)
        with self.assertRaises(ValueError):
            OrderParameterAngle((0, 1), periodic=False)
        with self.assertRaises(ValueError):
            OrderParameterAngle((0, 1, 2, 3), periodic=False)


class OrderFactoryTest(unittest.TestCase):
    """Test the order factory."""

    def test_factory(self):
        """Test that we can create order parameters with the factory."""
        test_settings = [
            {'class': 'orderparameter'},
            {'class': 'OrderPARAMetEr'},
            {'class': 'orderparameterposition',
             'index': 0, 'dim': 'x', 'periodic': False},
            {'class': 'orderparameterdistance',
             'index': (0, 1), 'periodic': True},
            {'class': 'orderparameterangle', 'index': (0, 1, 2),
             'periodic': True},
        ]
        correct_class = [OrderParameter,
                         OrderParameter,
                         OrderParameterPosition,
                         OrderParameterDistance,
                         OrderParameterAngle]
        for setting, correct in zip(test_settings, correct_class):
            orderp = order_factory(setting)
            self.assertIsInstance(orderp, correct)


if __name__ == '__main__':
    unittest.main()
