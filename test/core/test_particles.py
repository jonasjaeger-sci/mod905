# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the classes and methods from pyretis.core.particles"""
import logging
import unittest
import numpy as np
from scipy.special import comb
from pyretis.core.particles import (
    Particles,
    ParticlesExt,
    get_particle_type,
    particles_from_restart,
)
logging.disable(logging.CRITICAL)


class ParticleTest(unittest.TestCase):
    """Run the tests for the Particle class."""

    def test_creation(self):
        """Test the creation a particle list."""
        for dim in range(1, 4):
            particles = Particles(dim=dim)
            particles.add_particle(np.zeros(dim), np.zeros(dim), np.zeros(dim))
            particles.add_particle(np.zeros(dim), np.zeros(dim), np.zeros(dim))
            self.assertEqual(particles.dim, dim)
            self.assertEqual(particles.npart, 2)
            self.assertIsNone(particles.virial)

    def test_empty_list(self):
        """Test that we can empty the list."""
        particles = Particles(dim=3)
        for _ in range(10):
            particles.add_particle(np.zeros(3), np.zeros(3), np.zeros(3))
        self.assertEqual(particles.npart, 10)
        particles.empty_list()
        self.assertEqual(particles.npart, 0)
        particles.add_particle(np.ones(3), np.ones(3), np.ones(3))
        self.assertEqual(particles.npart, 1)

    def test_pos_setget(self):
        """Test that we can set and get positions."""
        particles = Particles(dim=3)
        particles.add_particle(np.ones(3), np.ones(3), np.ones(3))
        particles.add_particle(np.ones(3), np.ones(3), np.ones(3))
        pos = particles.get_pos()
        self.assertFalse(pos is particles.pos)
        pos[0][1] = 100
        for i in particles.pos:
            self.assertTrue(np.allclose(i, np.ones(3)))
        self.assertFalse(np.allclose(pos[0], np.ones(3)))
        particles.set_pos(pos)
        self.assertFalse(pos is particles.pos)
        for i, j in zip(pos, particles.pos):
            self.assertTrue(np.allclose(i, j))

    def test_vel_setget(self):
        """Test that we can set and get velocities."""
        particles = Particles(dim=3)
        particles.add_particle(np.ones(3), np.ones(3), np.ones(3))
        particles.add_particle(np.ones(3), np.ones(3), np.ones(3))
        vel = particles.get_vel()
        self.assertFalse(vel is particles.vel)
        vel[0][1] = 100
        for i in particles.vel:
            self.assertTrue(np.allclose(i, np.ones(3)))
        self.assertFalse(np.allclose(vel[0], np.ones(3)))
        particles.set_vel(vel)
        self.assertFalse(vel is particles.vel)
        for i, j in zip(vel, particles.vel):
            self.assertTrue(np.allclose(i, j))

    def test_force_setget(self):
        """Test that we can set and get forces."""
        particles = Particles(dim=3)
        particles.add_particle(np.ones(3), np.ones(3), np.ones(3))
        particles.add_particle(np.ones(3), np.ones(3), np.ones(3))
        force = particles.get_force()
        self.assertFalse(force is particles.force)
        force[0][1] = 100
        for i in particles.force:
            self.assertTrue(np.allclose(i, np.ones(3)))
        self.assertFalse(np.allclose(force[0], np.ones(3)))
        particles.set_force(force)
        self.assertFalse(force is particles.force)
        for i, j in zip(force, particles.force):
            self.assertTrue(np.allclose(i, j))

    def test_get_selection(self):
        """Test that we can get a selection of properties."""
        particles = Particles(dim=3)
        for i in range(10):
            particles.add_particle(np.ones(3) * i, np.ones(3) * i,
                                   np.ones(3) * i, name='H{}'.format(i))
        force = particles.get_selection(['force', 'name'], selection=None)[0]
        self.assertTrue(np.allclose(force, particles.force))
        force[0] = np.ones(3) * 101.
        self.assertTrue(np.allclose(force[0], np.array([101., 101., 101.])))
        out = particles.get_selection(['force', 'name'], selection=[1, 3])
        self.assertTrue(np.allclose(out[0][0], particles.force[1]))
        self.assertTrue(np.allclose(out[0][1], particles.force[3]))
        self.assertEqual(out[1][0], 'H1')
        self.assertEqual(out[1][1], 'H3')

    def test_iterate(self):
        """Test that we can iterate over the particles."""
        particles = Particles(dim=3)
        for i in range(10):
            particles.add_particle(np.ones(3) * i, np.ones(3) * i,
                                   np.ones(3) * i, name='A{}'.format(i))
        for i, part in enumerate(particles):
            self.assertTrue(np.allclose(part['pos'], particles.pos[i]))

    def test_pairs(self):
        """Test that we can iterate over pairs."""
        particles = Particles(dim=3)
        npart = 21
        for i in range(npart):
            particles.add_particle(np.ones(3) * i, np.ones(3) * i,
                                   np.ones(3) * i, name='A{}'.format(i))
        pairs = set()
        for pair in particles.pairs():
            pairs.add((pair[0], pair[1]))
        self.assertAlmostEqual(len(pairs), comb(npart, 2))

    def test_generate_restart_info(self):
        """Test that we can generate restart info."""
        particles = Particles(dim=3)
        particles.add_particle(np.ones(3), np.ones(3), np.ones(3))
        particles.add_particle(np.ones(3) * 10, np.ones(3), np.ones(3))
        particles.vpot = 101
        particles.ekin = 102
        restart = particles.restart_info()
        self.assertEqual(restart['class'], 'internal')
        particles2 = Particles(dim=3)
        particles2.load_restart_info(restart)
        self.assertTrue(np.allclose(particles.pos, particles2.pos))

    def test_generate_restart_missing(self):
        """Test that we can generate restart info if attribs. are missing."""
        particles = Particles(dim=3)
        particles.add_particle(np.ones(3), np.ones(3), np.ones(3))
        particles.add_particle(np.ones(3) * 10, np.ones(3), np.ones(3))
        particles.vpot = 101
        del particles.ekin
        restart = particles.restart_info()
        particles2 = Particles(dim=3)
        particles2.load_restart_info(restart)
        self.assertTrue(np.allclose(particles.pos, particles2.pos))
        self.assertTrue(hasattr(particles2, 'ekin'))
        self.assertFalse(hasattr(particles, 'ekin'))
        # Test load and create:
        simulation_restart = {'particles': restart}
        particles3 = particles_from_restart(simulation_restart)
        self.assertNotEqual(particles, particles3)
        particles.ekin = None
        self.assertEqual(particles, particles3)
        particles3 = particles_from_restart({})
        self.assertIsNone(particles3)

    def test_copy(self):
        """Test that we can copy particles."""
        particles = Particles(dim=3)
        particles.add_particle(np.ones(3), np.ones(3), np.ones(3))
        particles.add_particle(np.ones(3), np.ones(3), np.ones(3))
        particles.ekin = 102
        particles2 = particles.copy()
        self.assertIsNot(particles, particles2)
        self.assertEqual(particles, particles2)
        del particles.ekin
        particles2 = particles.copy()
        self.assertIsNot(particles, particles2)
        self.assertNotEqual(particles, particles2)
        # Test that we can change one without changing the other:
        particles2 = particles.copy()
        for attr in ('pos', 'vel', 'force'):
            val1 = getattr(particles2, attr)
            setattr(particles2, attr, np.zeros_like(val1))
            val1 = getattr(particles2, attr)
            val2 = getattr(particles, attr)
            self.assertFalse(np.allclose(val1, val2))


class GetParticleTest(unittest.TestCase):
    """Test that we can get the correct classes."""

    def test_get(self):
        """Test that we get correct classes."""
        cls1 = get_particle_type('internal')
        self.assertTrue(cls1 is Particles)
        cls2 = get_particle_type('external')
        self.assertTrue(cls2 is ParticlesExt)
        with self.assertRaises(ValueError):
            get_particle_type('missing someone')


class ParticleExtTest(unittest.TestCase):
    """Run the tests for the Particle class."""

    def test_creation(self):
        """Test the creation a particle list."""
        particles = ParticlesExt(dim=3)
        self.assertTrue(hasattr(particles, 'pos'))
        self.assertTrue(hasattr(particles, 'vel'))

    def test_empty_list(self):
        """Test that we can empty the list."""
        particles = ParticlesExt(dim=3)
        particles.set_pos(('test', 100))
        self.assertEqual(particles.config, ('test', 100))
        particles.empty_list()
        self.assertEqual(particles.config, (None, None))

    def test_setget_pos(self):
        """Test that we can set/get positions."""
        particles = ParticlesExt(dim=3)
        pos = ('some file', 101)
        self.assertEqual(particles.get_pos(), (None, None))
        particles.set_pos(pos)
        for i, j in zip(particles.get_pos(), pos):
            self.assertEqual(i, j)
        self.assertFalse(pos is particles.get_pos())
        pos2 = particles.get_pos()
        self.assertTrue(pos2 is particles.config)

    def test_set_vel(self):
        """Test that we can set the time direction for positions."""
        particles = ParticlesExt(dim=3)
        particles.set_vel(True)
        self.assertTrue(particles.vel_rev)
        particles.set_vel(False)
        self.assertFalse(particles.vel_rev)

    def test_restart_info(self):
        """Test restart methods."""
        particles = ParticlesExt(dim=3)
        pos = ('skinny love', 2)
        particles.set_pos(pos)
        particles.set_vel(True)
        restart = particles.restart_info()
        self.assertTrue(restart['vel_rev'])
        for i, j in zip(particles.get_pos(), pos):
            self.assertEqual(i, j)
        pos2 = ('My my my', 4)
        restart['config'] = pos2
        particles2 = ParticlesExt(dim=3)
        particles2.load_restart_info(restart)
        for i, j in zip(particles2.get_pos(), pos2):
            self.assertEqual(i, j)
        del restart['config']
        with self.assertRaises(ValueError):
            particles2.load_restart_info(restart)

    def test_copy(self):
        """Test that we can copy particles."""
        particles = ParticlesExt(dim=3)
        particles.set_pos(('filename.ext', 987))
        particles.ekin = 123
        particles.vpot = 456
        particles2 = particles.copy()
        self.assertIsNot(particles, particles2)
        self.assertEqual(particles, particles2)


if __name__ == '__main__':
    unittest.main()
