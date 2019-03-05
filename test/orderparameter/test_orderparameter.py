# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the order parameter classes from pyretis.orderparameter."""
import logging
import unittest
import numpy as np
from pyretis.orderparameter import order_factory
from pyretis.orderparameter import (
    OrderParameter,
    Position,
    Velocity,
    PositionVelocity,
    Distance,
    Distancevel,
    DistanceVelocity,
    CompositeOrderParameter,
    Angle,
    Dihedral,
)
from pyretis.core import System, create_box, Particles
logging.disable(logging.CRITICAL)


class SimpleOrder(OrderParameter):
    """An order parameter which equals the system temperature."""

    def __init__(self):
        super().__init__(description='Simple order parameter')

    def calculate(self, system):
        return [system.temperature['set']]


class SimpleOrderTemp(OrderParameter):
    """An order parameter which equals the system temperature."""

    def __init__(self):
        super().__init__(description='Simple order parameter', velocity=True)

    def calculate(self, system):
        return [system.temperature['set'] * -1]


class SimpleOrderFaulty:  # pylint: disable=too-few-public-methods
    """An order parameter which is faulty - missing calculate."""

    def calculate_all(self, system):  # pylint: disable=no-self-use
        """Just return the set temperature."""
        return [system.temperature['set']]


class SimpleOrderFaulty2:  # pylint: disable=too-few-public-methods
    """An order parameter which is faulty - missing callable calculate."""

    calculate = 100


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

        vals = order.calculate(system)
        self.assertAlmostEqual(vals[0], correct[0])
        self.assertEqual(len(vals), 1)


def create_system(ndim, npart, periodic=False):
    """Create a simple system for testing."""
    if periodic:
        box = create_box(low=[0]*ndim, high=[1]*ndim)
    else:
        box = create_box(periodic=[False]*ndim)
    system = System(box=box)
    system.particles = Particles(system.get_dim())
    for _ in range(npart):
        pos = np.random.random(box.dim)
        vel = np.random.random(box.dim)
        system.add_particle(name='Ar', pos=pos, vel=vel)
    return system, box


class OrderPositionTest(unittest.TestCase):
    """Run the tests for the Position class."""

    def _check_order_parameter(self, orderp, correct, system, idim, ndim):
        """Verify the order parameter."""
        for orderpi, correcti in zip(orderp, correct):
            if idim > ndim - 1:
                with self.assertRaises(IndexError):
                    orderpi.calculate(system)
            else:
                for i, j in zip(orderpi.calculate(system), correcti):
                    self.assertAlmostEqual(i, j)

    @staticmethod
    def _get_order(index, xdim, periodic=False):
        """Return the initiated order parameters."""
        orderp = [
            Position(index, dim=xdim, periodic=periodic),
            Velocity(index, dim=xdim),
            PositionVelocity(index, dim=xdim, periodic=periodic),
        ]
        return orderp

    def _get_correct(self, system, index, idim, periodic=False):
        """Return the correct order parameters."""
        correct = [
            self._correct_order1(system, index, idim,
                                 periodic=periodic),
            self._correct_order2(system, index, idim),
        ]
        correct.append(correct[0] + correct[1])
        return correct

    def test_without_pbc(self):
        """Test the order parameters without periodic boundaries."""
        periodic = False
        for npart, index in zip((1, 10), (0, 2)):
            for ndim in [1, 2, 3]:
                system, _ = create_system(ndim, npart, periodic=periodic)
                for idim, xdim in enumerate(('x', 'y', 'z')):
                    orderp = self._get_order(index, xdim, periodic=periodic)
                    correct = self._get_correct(system, index, idim,
                                                periodic=periodic)
                    self._check_order_parameter(orderp, correct, system,
                                                idim, ndim)

    def test_with_pbc(self):
        """Test the order parameters with periodic boundaries."""
        periodic = True
        for npart, index in zip((1, 10), (0, -1)):
            for ndim in [1, 2, 3]:
                # Just test for some displacements:
                for disp in [0.0, 1.5, -1.5, 100., -100.]:
                    system, _ = create_system(ndim, npart, periodic=periodic)
                    system.particles.pos += (
                        np.ones_like(system.particles.pos) * disp
                    )
                    for idim, xdim in enumerate(('x', 'y', 'z')):
                        orderp = self._get_order(index, xdim,
                                                 periodic=periodic)
                        correct = self._get_correct(system, index, idim,
                                                    periodic=periodic)
                        self._check_order_parameter(orderp, correct, system,
                                                    idim, ndim)

    @staticmethod
    def _correct_order1(system, index, idim, periodic=False):
        """The correct position order parameter."""
        try:
            pos = system.particles.pos[index][idim]
            if periodic:
                box = system.box
                return [box.pbc_coordinate_dim(pos, idim)]
            return [pos]
        except IndexError:
            return [None]

    @staticmethod
    def _correct_order2(system, index, idim):
        """The correct velocity order parameter."""
        try:
            return [system.particles.vel[index][idim]]
        except IndexError:
            return [None]

    def test_init_fail(self):
        """Check that the initiation fails if we supply strange input."""
        with self.assertRaises(ValueError):
            Position(0, dim='a')
        with self.assertRaises(ValueError):
            Velocity(0, dim='pingu')
        with self.assertRaises(ValueError):
            PositionVelocity(123, dim='chonky')


class OrderDistanceTest(unittest.TestCase):
    """Run the tests for the Distance class."""

    def _check_order_parameter(self, orderp, correct, system):
        """Verify the order parameter."""
        for orderpi, correcti in zip(orderp, correct):
            for i, j in zip(orderpi.calculate(system), correcti):
                self.assertAlmostEqual(i, j)

    @staticmethod
    def _get_order(index, periodic=False):
        """Return the initiated order parameters."""
        orderp = [
            Distance(index, periodic=periodic),
            Distancevel(index, periodic=periodic),
            DistanceVelocity(index, periodic=periodic),
        ]
        return orderp

    def _get_correct(self, system, index, periodic=False):
        """Return the correct order parameters."""
        correct = [
            self._correct_order1(system, index, periodic=periodic),
            self._correct_order2(system, index, periodic=periodic),
        ]
        correct.append(correct[0] + correct[1])
        return correct

    def test_two_particles(self):
        """Test the distance order parameter without pbc."""
        # Test for a one-particle system:
        index = (0, 1)
        for ndim in [1, 2, 3]:
            system, _ = create_system(ndim, 2, periodic=False)
            orderp = self._get_order(index, periodic=False)
            correct = self._get_correct(system, index, periodic=False)
            self._check_order_parameter(orderp, correct, system)

    def test_two_particles_pbs(self):
        """Test the distance order parameter with pbc."""
        # Test for a one-particle system:
        index = (0, 1)
        for disp in [0.0, 1.5, -1.5, 100., -100.]:
            for ndim in [1, 2, 3]:
                system, box = create_system(ndim, 2, periodic=True)
                for i in index:
                    system.particles.pos[i] = (
                        np.random.random(box.dim) + np.ones(box.dim) * disp
                    )
                orderp = self._get_order(index, periodic=True)
                correct = self._get_correct(system, index, periodic=True)
                self._check_order_parameter(orderp, correct, system)

    @staticmethod
    def _correct_order1(system, index, periodic=False):
        """The correct position order parameter."""
        try:
            i, j = index
            delta = system.particles.pos[j] - system.particles.pos[i]
            if periodic:
                box = system.box
                delta = box.pbc_dist_coordinate(delta)
            return [np.sqrt(np.dot(delta, delta))]
        except IndexError:
            return [None]

    @staticmethod
    def _correct_order2(system, index, periodic=False):
        """The correct velocity order parameter."""
        try:
            i, j = index
            delta = system.particles.pos[j] - system.particles.pos[i]
            delta_v = system.particles.vel[j] - system.particles.vel[i]
            if periodic:
                box = system.box
                delta = box.pbc_dist_coordinate(delta)
            return [np.dot(delta, delta_v) / np.sqrt(np.dot(delta, delta))]
        except IndexError:
            return [None]

    def test_init_fail(self):
        """Check that the initiation fails if we supply strange input."""
        inputs = [0, [0], (0,), (0, 1, 2)]
        errors = [TypeError, ValueError, ValueError, ValueError]
        klasses = (
            Distance,
            Distancevel,
            DistanceVelocity
        )
        for cls in klasses:
            for i, j in zip(inputs, errors):
                with self.assertRaises(j):
                    cls(i)


def water_molecule(box):
    """Return a simple system with a single water molecule."""
    system = System(box=box)
    system.particles = Particles(system.get_dim())
    system.add_particle(name='O', pos=np.array([0.230, 0.628, 0.113]))
    system.add_particle(name='H', pos=np.array([0.137, 0.626, 0.150]))
    system.add_particle(name='H', pos=np.array([0.231, 0.589, 0.021]))
    return system


def triangle():
    """Return a 2D system with particles in a tright riangle."""
    box = create_box(periodic=[False, False])
    system = System(box=box)
    system.particles = Particles(system.get_dim())
    system.add_particle(name='X', pos=np.array([0.0, 0.0]))
    system.add_particle(name='X', pos=np.array([1.0, 0.0]))
    system.add_particle(name='X', pos=np.array([0.0, 1.0]))
    angles = [
        ((1, 0, 2), 90.),
        ((0, 1, 2), 45.),
        ((0, 2, 1), 45.),
    ]
    return system, angles


class OrderAngleTest(unittest.TestCase):
    """Run the tests for the Angle class."""

    def test_without_pbc(self):
        """Test the angle order parameter without pbc."""
        orderp = Angle((1, 0, 2), periodic=False)
        box = create_box(periodic=[False]*3)
        # Test angle for the SPC water geometry.
        system = water_molecule(box)
        angle = orderp.calculate(system)[0]
        self.assertAlmostEqual(np.degrees(angle), 109.984398, places=3)

    def test_witht_pbc(self):
        """Test the angle order parameter with pbc."""
        orderp = Angle((1, 0, 2), periodic=True)
        # Test angle for the SPC water geometry.
        box = create_box(periodic=[True, True, True], cell=[1., 1., 1.])
        system = water_molecule(box)
        angle = orderp.calculate(system)[0]
        self.assertAlmostEqual(np.degrees(angle), 109.984398, places=3)

    def test_triangle(self):
        """Test the angle order parameter for a 2D case."""
        system, angles = triangle()
        for idx, correct in angles:
            orderp = Angle(idx, periodic=False)
            angle = orderp.calculate(system)[0]
            self.assertAlmostEqual(np.degrees(angle), correct)

    def test_initiate_fail(self):
        """Test that we fail if we give incorrect number of indices."""
        with self.assertRaises(TypeError):
            Angle(0, periodic=False)
        with self.assertRaises(ValueError):
            Angle((0,), periodic=False)
        with self.assertRaises(ValueError):
            Angle((0, 1), periodic=False)
        with self.assertRaises(ValueError):
            Angle((0, 1, 2, 3), periodic=False)

    def test_special_cases(self):
        """Test the angle order parameter for some special cases:

        1. The angle between (1, 0, 0) and (0, 1, 0) -> pi/2.
        2. The angle between (1, 0, 0) and (1, 0, 0) -> 0.
        3. The angle between (1, 0, 0) and (-1, 0, 0) -> -pi.

        """
        orderp = Angle((0, 1, 2), periodic=False)
        test_cases = [
            {'angle': 0.5 * np.pi, 'pos': np.array([[1.0, 0.0, 0.0],
                                                    [0.0, 0.0, 0.0],
                                                    [0.0, 1.0, 0.0]])},
            {'angle': 0.0, 'pos': np.array([[1.0, 0.0, 0.0],
                                            [0.0, 0.0, 0.0],
                                            [1.0, 0.0, 0.0]])},
            {'angle': np.pi, 'pos': np.array([[1.0, 0.0, 0.0],
                                              [0.0, 0.0, 0.0],
                                              [-1.0, 0.0, 0.0]])},
        ]
        system, _ = create_system(3, 3, periodic=False)
        for case in test_cases:
            system.particles.pos = case['pos']
            angle = orderp.calculate(system)[0]
            self.assertAlmostEqual(angle, case['angle'])


class OrderDihedralTest(unittest.TestCase):
    """Run the tests for the Dihedral class."""

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
        orderp = Dihedral((3, 2, 1, 0), periodic=False)
        system, _ = create_system(3, 4, periodic=False)
        # Test some pre-defined cases:
        for case in self.test_cases:
            system.particles.pos = case['pos']
            angle = orderp.calculate(system)[0]
            angle_deg = np.degrees(angle)  # pylint: disable=no-member
            self.assertAlmostEqual(angle_deg, case['angle'], places=4)

    def test_with_pbc(self):
        """Test the angle order parameter with pbc."""
        orderp = Dihedral((3, 2, 1, 0), periodic=True)
        system, _ = create_system(3, 4, periodic=True)
        # Define a new box for this test:
        box = create_box(periodic=[True, True, True], cell=[8., 8., 8.])
        system.box = box
        # Test same cases, just displaced.
        for case in self.test_cases:
            displace = np.ones_like(case['pos']) * 9
            system.particles.pos = case['pos'] + displace
            angle = orderp.calculate(system)[0]
            angle_deg = np.degrees(angle)  # pylint: disable=no-member
            self.assertAlmostEqual(angle_deg, case['angle'], places=4)

    def test_order(self):
        """Test if we get the same angle if we reverse indices."""
        order1 = Dihedral((0, 1, 2, 3), periodic=False)
        order2 = Dihedral((3, 2, 1, 0), periodic=False)
        system, _ = create_system(3, 4, periodic=False)
        for _ in range(3):
            system.particles.pos = np.random.rand(4, 3)
            angle1 = order1.calculate(system)[0]
            angle2 = order2.calculate(system)[0]
            self.assertAlmostEqual(angle1, angle2)

    def test_initiate_fail(self):
        """Test that we fail if we give incorrect number of indices."""
        with self.assertRaises(TypeError):
            Dihedral(0, periodic=False)
        with self.assertRaises(ValueError):
            Dihedral((0,), periodic=False)
        with self.assertRaises(ValueError):
            Dihedral((0, 1), periodic=False)
        with self.assertRaises(ValueError):
            Dihedral((0, 1, 2), periodic=False)
        with self.assertRaises(ValueError):
            Dihedral((0, 1, 2, 'tre'), periodic=False)


class OrderFactoryTest(unittest.TestCase):
    """Test the order factory."""

    def test_factory(self):
        """Test that we can create order parameters with the factory."""
        test_cases = [
            {
                'setting': {'class': 'orderparameter'},
                'class': OrderParameter,
            },
            {
                'setting': {'class': 'OrderPARAMetEr'},
                'class': OrderParameter,
            },
            {
                'setting': {'class': 'position', 'index': 0},
                'class': Position,
            },
            {
                'setting': {'class': 'velocity', 'index': 0},
                'class': Velocity,
            },
            {
                'setting': {'class': 'distance', 'index': (0, 1)},
                'class': Distance,
            },
            {
                'setting': {'class': 'distancevel', 'index': (0, 1)},
                'class': Distancevel,
            },
            {
                'setting': {'class': 'PositionVelocity', 'index': 0},
                'class': PositionVelocity,
            },
            {
                'setting': {'class': 'distancevelocity', 'index': (0, 1)},
                'class': DistanceVelocity,
            },
            {
                'setting': {'class': 'angle', 'index': (0, 1, 2)},
                'class': Angle,
            },
            {
                'setting': {'class': 'dihedral', 'index': (0, 1, 2, 3)},
                'class': Dihedral,
            },
        ]
        for case in test_cases:
            orderp = order_factory(case['setting'])
            self.assertIsInstance(orderp, case['class'])


class CollectionTest(unittest.TestCase):
    """Test that we can create collections of order parameters."""

    def test_init(self):
        """Test creation of an object."""
        orderp = CompositeOrderParameter()
        cv1 = Distance((0, 1), periodic=False)
        orderp.add_orderparameter(cv1)
        cv2 = Distance((1, 2), periodic=False)
        orderp.add_orderparameter(cv2)
        cv3 = Distance((0, 2), periodic=False)
        orderp.add_orderparameter(cv3)
        orderp2 = CompositeOrderParameter(order_parameters=[cv1, cv2, cv3])
        for i, j in zip(orderp.order_parameters, orderp2.order_parameters):
            self.assertTrue(i is j)
        system, _ = create_system(3, 3, periodic=False)
        system.particles.pos = np.array([[0.0, 0.0, 0.0],
                                         [0.0, 0.0, 0.1],
                                         [0.0, 0.0, 0.3]])
        order = orderp.calculate(system)
        correct = [0.1, 0.2, 0.3]
        self.assertEqual(len(order), len(correct))
        for i, j in zip(order, correct):
            self.assertAlmostEqual(i, j)

    def test_faulty_input(self):
        """Test if we supply faulty input."""
        orderp = CompositeOrderParameter()

        cv1 = SimpleOrder()
        orderp.add_orderparameter(cv1)
        self.assertTrue(cv1 is orderp.order_parameters[0])
        # Try to add some faulty order parameters.
        cv2 = SimpleOrderFaulty()
        with self.assertRaises(ValueError):
            orderp.add_orderparameter(cv2)
        cv3 = SimpleOrderFaulty2()
        with self.assertRaises(ValueError):
            orderp.add_orderparameter(cv3)

    def test_velocity_dependence(self):
        """Test that the combined is marked as velocity dependent."""
        orderp = CompositeOrderParameter()

        cv1 = SimpleOrder()
        orderp.add_orderparameter(cv1)
        self.assertFalse(orderp.velocity_dependent)

        cv2 = SimpleOrder()
        orderp.add_orderparameter(cv2)
        self.assertFalse(orderp.velocity_dependent)

        cv3 = SimpleOrderTemp()
        orderp.add_orderparameter(cv3)
        self.assertTrue(orderp.velocity_dependent)

        cv4 = SimpleOrder()
        orderp.add_orderparameter(cv4)
        self.assertTrue(orderp.velocity_dependent)


if __name__ == '__main__':
    unittest.main()
