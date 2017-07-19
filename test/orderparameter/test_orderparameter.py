# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the order parameter classes from pyretis.orderparameter"""
import logging
import unittest
import numpy as np
from pyretis.orderparameter import order_factory
from pyretis.orderparameter.orderparameter import (
    OrderParameter,
    OrderParameterPosition,
    OrderParameterDistance,
    CompositeOrderParameter,
)
from pyretis.orderparameter.orderangle import OrderParameterAngle
from pyretis.orderparameter.orderdihedral import OrderParameterDihedral
from pyretis.core import System, create_box, Particles
from pyretis.core.units import create_conversion_factors
logging.disable(logging.CRITICAL)


class SimpleOrder(OrderParameter):
    """An order parameter which equals the system temperature."""

    def __init__(self):
        super().__init__(description='Simple order parameter')

    def calculate(self, system):
        return [system.temperature['set']]


class SimpleOrderFaulty(object):  # pylint: disable=too-few-public-methods
    """An order parameter which is faulty - missing calculate_all"""

    def calculate(self, system):  # pylint: disable=no-self-use
        """Just return the set temperature"""
        return [system.temperature['set']]


class SimpleOrderFaulty2(object):  # pylint: disable=too-few-public-methods
    """An order parameter which is faulty - missing calculate_all"""

    def calculate_all(self, system):  # pylint: disable=no-self-use
        """Just return the set temperature"""
        return [system.temperature['set']]


class SimpleOrderFaulty3(object):  # pylint: disable=too-few-public-methods
    """An order parameter which is faulty - missing calculate_all"""
    calculate = 100

    def calculate_all(self, system):  # pylint: disable=no-self-use
        """Just return the set temperature"""
        return [system.temperature['set']]


def system_units(system):
    """Just return the units."""
    return [system.units]


def system_faker(system):
    """Just try to return some parameter."""
    return [system.does_not_exist]


class OrderGenericTest(unittest.TestCase):
    """Test that we can create a class and define some parameters."""

    def test_simple_order(self):
        """Test that we can create a very simple order parameter."""
        system = System(temperature=123.0, units='lj', box=None)
        order = SimpleOrder()
        correct = [123.0, 'lj']
        val = order.calculate(system)
        self.assertAlmostEqual(val[0], correct[0])
        self.assertEqual(len(val), 1)

        vals = order.calculate_all(system)
        self.assertAlmostEqual(vals[0], correct[0])
        self.assertEqual(len(vals), 1)

        order.add_orderparameter(system_units)
        vals = order.calculate_all(system)
        self.assertEqual(len(vals), 2)
        for i, j in zip(vals, correct):
            self.assertEqual(i, j)

        order.add_orderparameter(system_faker)
        with self.assertRaises(AttributeError):
            vals = order.calculate_all(system)


class OrderPositionTest(unittest.TestCase):
    """Run the tests for the OrderParameterPosition class."""

    def test_one_particle(self):
        """Test the position order parameter for a one-particle system."""
        create_conversion_factors('lj')
        for ndim in [1, 2, 3]:
            box = create_box(periodic=[False]*ndim)
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
                else:
                    lmb, lmb_vel = orderp.calculate(system)
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
                box = create_box(periodic=[False]*ndim)
                system = System(temperature=1.0, units='lj', box=box)
                system.particles = Particles(system.get_dim())
                for _ in range(10):
                    pos = np.random.random(box.dim)
                    vel = np.random.random(box.dim)
                    system.add_particle(name='Ar', pos=pos, vel=vel, mass=1.0,
                                        ptype=0)
                if idim > ndim-1:
                    self.assertRaises(IndexError, orderp.calculate, (system))
                else:
                    lmb, lmb_vel = orderp.calculate(system)
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
                box = create_box(low=[0]*ndim, high=[1]*ndim,
                                 periodic=[True]*ndim)
                system = System(temperature=1.0, units='lj', box=box)
                system.particles = Particles(system.get_dim())
                pos = np.random.random(box.dim) * np.ones(box.dim)*disp
                vel = np.random.random(box.dim)
                system.add_particle(name='Ar', pos=pos, vel=vel, mass=1.0,
                                    ptype=0)
                for xdim in ['x', 'y', 'z'][:ndim]:
                    orderp = OrderParameterPosition(0, dim=xdim,
                                                    periodic=True)
                    lmb, _ = orderp.calculate(system)
                    idim = dim_map[xdim]
                    lmb_correct = box.pbc_coordinate_dim(pos[idim], idim)
                    self.assertAlmostEqual(lmb, lmb_correct)

    def test_multiple_particle_pbc(self):
        """Test that pbc boundaries are applied when asked for."""
        create_conversion_factors('lj')
        dim_map = {'x': 0, 'y': 1, 'z': 2}
        for disp in [0.0, 1.5, -1.5, 100., -100.]:
            for ndim in [1, 2, 3]:
                box = create_box(low=[0]*ndim, high=[1]*ndim,
                                 periodic=[True]*ndim)
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
                    self.assertAlmostEqual(lmb[0], lmb_correct)

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
            box = create_box(periodic=[False]*ndim)
            system = System(temperature=1.0, units='lj', box=box)
            system.particles = Particles(system.get_dim())
            for _ in range(2):
                pos = np.random.random(box.dim)
                vel = np.random.random(box.dim)
                system.add_particle(name='Ar', pos=pos, vel=vel, mass=1.0,
                                    ptype=0)
            lmb, lmb_vel = orderp.calculate(system)
            delta = system.particles.pos[1] - system.particles.pos[0]
            lmb_correct = np.sqrt(np.dot(delta, delta))
            self.assertAlmostEqual(lmb, lmb_correct)
            delta_v = system.particles.vel[1] - system.particles.vel[0]
            lmb_vel_correct = np.dot(delta, delta_v) / lmb_correct
            self.assertAlmostEqual(lmb_vel, lmb_vel_correct)

    def test_two_pbcparticles(self):
        """Test the distance order parameter with pbc."""
        orderp = OrderParameterDistance((0, 1),
                                        periodic=True)
        # Test for a one-particle system:
        for disp in [0.0, 1.5, -1.5, 100., -100.]:
            for ndim in [1, 2, 3]:
                box = create_box(low=[0]*ndim, high=[1]*ndim,
                                 periodic=[True]*ndim)
                system = System(temperature=1.0, units='lj', box=box)
                system.particles = Particles(system.get_dim())
                for _ in range(2):
                    pos = np.random.random(box.dim) + np.ones(box.dim)*disp
                    system.add_particle(name='Ar', pos=pos,
                                        vel=np.random.random(box.dim),
                                        mass=1.0,
                                        ptype=0)
                lmb, lmb_vel = orderp.calculate(system)
                delta = box.pbc_dist_coordinate(system.particles.pos[1] -
                                                system.particles.pos[0])
                lmb_correct = np.sqrt(np.dot(delta, delta))
                self.assertAlmostEqual(lmb, lmb_correct)
                delta_v = system.particles.vel[1] - system.particles.vel[0]
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
        """Test the angle order parameter without pbc."""
        orderp = OrderParameterAngle((1, 0, 2), periodic=False)
        # Test for SPC water
        box = create_box(periodic=[False, False, False])
        system = System(temperature=1.0, units='lj', box=box)
        system.particles = Particles(system.get_dim())
        system.add_particle(name='O', pos=np.array([0.230, 0.628, 0.113]))
        system.add_particle(name='H', pos=np.array([0.137, 0.626, 0.150]))
        system.add_particle(name='H', pos=np.array([0.231, 0.589, 0.021]))
        angle = orderp.calculate(system)[0]
        angle_deg = angle * 180. / np.pi
        self.assertAlmostEqual(angle_deg, 109.984398, places=3)

    def test_witht_pbc(self):
        """Test the angle order parameter with pbc."""
        orderp = OrderParameterAngle((1, 0, 2), periodic=True)
        # Test for SPC water
        box = create_box(periodic=[True, True, True], length=[1., 1., 1.])
        system = System(temperature=1.0, units='lj', box=box)
        system.particles = Particles(system.get_dim())
        system.add_particle(name='O', pos=np.array([0.230, 0.628, 0.113]))
        system.add_particle(name='H', pos=np.array([0.137, 0.626, 0.150]))
        system.add_particle(name='H', pos=np.array([1.231, 0.589, 0.021]))
        angle = orderp.calculate(system)[0]
        angle_deg = angle * 180. / np.pi
        self.assertAlmostEqual(angle_deg, 109.984398, places=3)

    def test_triangle(self):
        """Test the angle order parameter for a 2D case."""
        box = create_box(periodic=[False, False])
        system = System(temperature=1.0, units='lj', box=box)
        system.particles = Particles(system.get_dim())
        system.add_particle(name='X', pos=np.array([0.0, 0.0]))
        system.add_particle(name='X', pos=np.array([1.0, 0.0]))
        system.add_particle(name='X', pos=np.array([0.0, 1.0]))
        for idx, correct in zip(((1, 0, 2), (0, 1, 2), (0, 2, 1)),
                                (90., 45., 45.)):
            orderp = OrderParameterAngle(idx, periodic=False)
            angle = orderp.calculate(system)[0]
            angle_deg = np.degrees(angle)  # pylint: disable=no-member
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

    def test_special_cases(self):
        """Test the angle order parameter for some special cases:

        1. The angle between (1, 0, 0) and (0, 1, 0)
        2. The angle between (1, 0, 0) and (1, 0, 0)
        3. The angle between (1, 0, 0) and (-1, 0, 0)
        """
        orderp = OrderParameterAngle((0, 1, 2), periodic=False)
        box = create_box(periodic=[False, False, False])
        system = System(temperature=1.0, units='lj', box=box)
        system.particles = Particles(system.get_dim())
        system.add_particle(name='A', pos=np.array([-1.0, 0.0, 0.0]))
        system.add_particle(name='B', pos=np.array([0.0, 0.0, 0.0]))
        system.add_particle(name='C', pos=np.array([0.0, 1.0, 0.0]))
        angle = orderp.calculate(system)[0]
        self.assertAlmostEqual(angle, np.pi*0.5)
        system.particles.pos[0] = np.array([1.0, 0.0, 0.0])
        system.particles.pos[1] = np.array([0.0, 0.0, 0.0])
        system.particles.pos[2] = np.array([1.0, 0.0, 0.0])
        angle = orderp.calculate(system)[0]
        self.assertAlmostEqual(angle, 0.0)
        system.particles.pos[0] = np.array([1.0, 0.0, 0.0])
        system.particles.pos[1] = np.array([0.0, 0.0, 0.0])
        system.particles.pos[2] = np.array([-1.0, 0.0, 0.0])
        angle = orderp.calculate(system)[0]
        self.assertAlmostEqual(angle, np.pi)


class OrderDihedralTest(unittest.TestCase):
    """Run the tests for the OrderParameterDihedral class."""

    test_cases = [
        {'angle': 180.0, 'pos': np.array([[0.0, 1.0, 0.0],
                                          [0.0, 0.0, 0.0],
                                          [1.0, 0.0, 0.0],
                                          [1.0, -1.0, 0.0]])},
        {'angle': 0.0, 'pos': np.array([[0.0, 1.0, 0.0],
                                        [0.0, 0.0, 0.0],
                                        [1.0, 0.0, 0.0],
                                        [1.0, 1.0, 0.0]])},
        {'angle': -90.0, 'pos': np.array([[0.0, 0.0, 1.0],
                                          [0.0, 0.0, 0.0],
                                          [1.0, 0.0, 0.0],
                                          [1.0, 1.0, 0.0]])},
        {'angle': 90.0, 'pos': np.array([[0.0, 0.0, -1.0],
                                         [0.0, 0.0, 0.0],
                                         [1.0, 0.0, 0.0],
                                         [1.0, 1.0, 0.0]])},
        {'angle': -60.0127, 'pos': np.array([[0.354, -2.210, -7.248],
                                             [-0.290, -2.221, -6.483],
                                             [0.472, -2.265, -5.191],
                                             [1.036, -3.090, -5.164]])},
        {'angle': 60.0319, 'pos': np.array([[0.354, -2.210, -7.248],
                                            [-0.290, -2.221, -6.483],
                                            [0.472, -2.265, -5.191],
                                            [1.058, -1.458, -5.122]])},
        {'angle': 0.0, 'pos': np.array([[1.499, -0.043, 0.000],
                                        [2.055, 1.361, 0.000],
                                        [3.481, 1.470, 0.000],
                                        [3.898, 0.528, 0.000]])},
        {'angle': -59.365971, 'pos': np.array([[0.039, -0.028, 0.000],
                                               [1.499, -0.043, 0.000],
                                               [1.956, -0.866, -1.217],
                                               [1.571, -1.903, -1.181]])},
        {'angle': 60.833130, 'pos': np.array([[0.039, -0.028, 0.000],
                                              [1.499, -0.043, 0.000],
                                              [1.956, -0.866, -1.217],
                                              [1.610, -0.425, -2.172]])},
        {'angle': -62.290916, 'pos': np.array([[-0.543, -0.938, 0.000],
                                               [0.039, -0.028, 0.000],
                                               [1.499, -0.043, 0.000],
                                               [1.847, -0.534, 0.928]])},
    ]

    def test_without_pbc(self):
        """Test the angle order parameter without pbc."""
        orderp = OrderParameterDihedral((3, 2, 1, 0), periodic=False)
        box = create_box(periodic=[False, False, False])
        system = System(temperature=1.0, units='lj', box=box)
        system.particles = Particles(system.get_dim())
        for _ in range(4):
            system.add_particle(name='A', pos=np.array([0.0, 0.0, 0.0]))
        # Test some pre-defined cases:
        for case in self.test_cases:
            system.particles.pos = case['pos']
            angle = orderp.calculate(system)[0]
            angle_deg = np.degrees(angle)  # pylint: disable=no-member
            self.assertAlmostEqual(angle_deg, case['angle'], places=4)

    def test_with_pbc(self):
        """Test the angle order parameter with pbc."""
        orderp = OrderParameterDihedral((3, 2, 1, 0), periodic=True)
        box = create_box(periodic=[True, True, True], length=[8., 8., 8.])
        system = System(temperature=1.0, units='lj', box=box)
        system.particles = Particles(system.get_dim())
        for _ in range(4):
            system.add_particle(name='A', pos=np.array([0.0, 0.0, 0.0]))
        # Test some pre-defined cases:
        for case in self.test_cases:
            system.particles.pos = case['pos']
            xmin = np.argmin(system.particles.pos[:, 0])
            displace = np.array([8., 8., 8.]) - system.particles.pos[xmin]
            for i in range(4):
                system.particles.pos[i] += displace
            system.particles.pos = box.pbc_wrap(system.particles.pos)
            angle = orderp.calculate(system)[0]
            angle_deg = np.degrees(angle)  # pylint: disable=no-member
            self.assertAlmostEqual(angle_deg, case['angle'], places=4)

    def test_order(self):
        """Test if we get the same angle if we reverse indexes"""
        order1 = OrderParameterDihedral((0, 1, 2, 3), periodic=False)
        order2 = OrderParameterDihedral((3, 2, 1, 0), periodic=False)
        box = create_box(periodic=[False, False, False])
        system = System(temperature=1.0, units='lj', box=box)
        system.particles = Particles(system.get_dim())
        for _ in range(4):
            system.add_particle(name='A', pos=np.array([0.0, 0.0, 0.0]))
        for _ in range(10):
            for i in range(4):
                # pylint: disable=no-member
                system.particles.pos[i] = np.random.rand(3)
            angle1 = order1.calculate(system)[0]
            angle2 = order2.calculate(system)[0]
            self.assertAlmostEqual(angle1, angle2)

    def test_initiate_fail(self):
        """Test that we fail if we give incorrect number of indices."""
        with self.assertRaises(TypeError):
            OrderParameterDihedral((0), periodic=False)
        with self.assertRaises(TypeError):
            OrderParameterDihedral(0, periodic=False)
        with self.assertRaises(ValueError):
            OrderParameterDihedral((0,), periodic=False)
        with self.assertRaises(ValueError):
            OrderParameterDihedral((0, 1), periodic=False)
        with self.assertRaises(ValueError):
            OrderParameterDihedral((0, 1, 2), periodic=False)
        with self.assertRaises(ValueError):
            OrderParameterDihedral((0, 1, 2, 'tre'), periodic=False)


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
            {'class': 'orderparameterdihedral', 'index': (0, 1, 2, 3),
             'periodic': True},
        ]
        correct_class = [OrderParameter,
                         OrderParameter,
                         OrderParameterPosition,
                         OrderParameterDistance,
                         OrderParameterAngle,
                         OrderParameterDihedral]
        for setting, correct in zip(test_settings, correct_class):
            orderp = order_factory(setting)
            self.assertIsInstance(orderp, correct)


class CollectionTest(unittest.TestCase):
    """Test that we can create collections of order parameters."""

    def test_init(self):
        """Test creation of an object."""
        orderp = CompositeOrderParameter()
        cv1 = OrderParameterDistance((0, 1), periodic=False)
        orderp.add_orderparameter(cv1)
        cv2 = OrderParameterDistance((1, 2), periodic=False)
        orderp.add_orderparameter(cv2)
        cv3 = OrderParameterDistance((0, 2), periodic=False)
        orderp.add_orderparameter(cv3)
        orderp2 = CompositeOrderParameter(order_parameters=[cv1, cv2, cv3])
        for i, j in zip(orderp.order_parameters(), orderp2.order_parameters()):
            self.assertTrue(i is j)
        box = create_box(periodic=[False, False, False])
        system = System(temperature=1.0, units='lj', box=box)
        system.particles = Particles(system.get_dim())
        system.add_particle(name='O', pos=np.array([0.0, 0.0, 0.0]))
        system.add_particle(name='H', pos=np.array([0.0, 0.0, 0.1]))
        system.add_particle(name='H', pos=np.array([0.0, 0.0, 0.3]))
        order = orderp.calculate_all(system)
        correct = [0.1, 0.0, 0.2, 0.0, 0.3, 0.0]
        for i, j in zip(order, correct):
            self.assertAlmostEqual(i, j)

    def test_faulty_input(self):
        """Test if we supply faulty input."""
        orderp = CompositeOrderParameter()
        cv1 = SimpleOrder()
        orderp.add_orderparameter(cv1)
        self.assertTrue(cv1 is orderp.extra[0])
        cv2 = SimpleOrderFaulty()
        with self.assertRaises(ValueError):
            orderp.add_orderparameter(cv2)
        cv3 = SimpleOrderFaulty2()
        with self.assertRaises(ValueError):
            orderp.add_orderparameter(cv3)
        cv4 = SimpleOrderFaulty3()
        with self.assertRaises(ValueError):
            orderp.add_orderparameter(cv4)


if __name__ == '__main__':
    unittest.main()
