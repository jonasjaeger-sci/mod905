# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""A simple test module for the writers.

Here we test that we can write and read different output formats.
"""
import logging
import unittest
import os
import numpy as np
from pyretis.core import Box, System, Particles, Path, PathExt
from pyretis.tools.lattice import generate_lattice
from pyretis.inout.writers.writers import adjust_coordinate
from pyretis.inout.writers import get_writer
logging.disable(logging.CRITICAL)


LOCAL_DIR = os.path.abspath(os.path.dirname(__file__))


def create_test_system():
    """Create a system we can use for testing."""
    xyz, size = generate_lattice('fcc', [3, 3, 3], density=0.9)
    box = Box(size=size)
    system = System(units='lj', box=box)
    system.particles = Particles(dim=3)
    for xyzi in xyz:
        system.add_particle(name='Ar', pos=xyzi, vel=np.zeros_like(xyzi))
    system.particles.vel[-1] = np.array([-1.0, 0.123, 1.0])
    return system


def create_path():
    """Setup a simple path for a test."""
    system = create_test_system()
    system.particles.name = ['X'] * system.particles.npart
    system.box = Box(size=[222.2, 222.2, 222.2])
    path = Path(None)
    phasepoints = []
    for _ in range(10):
        pos = np.random.rand(*system.particles.pos.shape)
        vel = np.random.rand(*pos.shape)
        vpot = np.random.random()
        ekin = np.random.random()
        phasepoint = {'order': [pos[0][0], pos[1][0]], 'pos': pos,
                      'vel': vel, 'vpot': vpot, 'ekin': ekin}
        phasepoints.append(phasepoint)
        path.append(phasepoint)
    return system, phasepoints, path


def generate_snaplines(path_writer, conf_writer, phasepoints, system, path):
    """Genereate snapshots using path and traj writers."""
    snapshots = [line for line in path_writer.generate_output(0, path)]
    length = len([_ for _ in conf_writer.generate_output(0, system)])
    for i, phasepoint in enumerate(phasepoints):
        system.particles.set_particle_state(phasepoint)
        snap = conf_writer.generate_output(i, system)
        snap2 = snapshots[1+i*length:1+(i+1)*length]
        for line1, line2 in zip(snap, snap2):
            yield line1, line2


class TrajTest(unittest.TestCase):
    """Test trajectory writing work as intended."""

    def test_adjust_coordinates(self):
        """Test that we can adjust coordinates."""
        # 1 particle, 1D
        particles = Particles(dim=1)
        particles.add_particle(np.array([1.0]),
                               np.zeros(1),
                               np.zeros(1))
        pos = adjust_coordinate(particles.pos)
        self.assertTrue(np.allclose(pos, np.array([1.0, 0.0, 0.0])))
        # 1 particle, 2D
        particles = Particles(dim=2)
        particles.add_particle(np.array([1.0, 1.0]),
                               np.zeros(2),
                               np.zeros(2))
        pos = adjust_coordinate(particles.pos)
        self.assertTrue(np.allclose(pos, np.array([1.0, 1.0, 0.0])))
        # 1 particle, 3D
        particles = Particles(dim=3)
        particles.add_particle(np.array([1.0, 1.0, 1.0]),
                               np.zeros(3),
                               np.zeros(3))
        pos = adjust_coordinate(particles.pos)
        self.assertTrue(np.allclose(pos, np.array([1.0, 1.0, 1.0])))
        # 2 particles, 1D
        particles = Particles(dim=1)
        particles.add_particle(np.array([1.0]),
                               np.zeros(1),
                               np.zeros(1))
        particles.add_particle(np.array([-1.0]),
                               np.zeros(1),
                               np.zeros(1))
        pos = adjust_coordinate(particles.pos)
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
        pos = adjust_coordinate(particles.pos)
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
        pos = adjust_coordinate(particles.pos)
        self.assertTrue(np.allclose(pos, np.array([[1., -1., 0.5],
                                                   [-1., 1., -0.5]])))

    def test_gro_writer(self):
        """Test the GROWriter."""
        system = create_test_system()
        gro_writer = get_writer('trajgro', {'units': None,
                                            'write_vel': True})
        snapshot = gro_writer.generate_output(0, system)
        correct = os.path.join(LOCAL_DIR, 'generated.gro')
        with open(correct, 'r') as fileh:
            for lines1, lines2 in zip(fileh, snapshot):
                self.assertEqual(lines1.rstrip(), lines2.rstrip())

    def test_xyz_writer(self):
        """Test the XYZWriter."""
        system = create_test_system()
        xyz_writer = get_writer('trajxyz', {'units': None})
        snapshot = xyz_writer.generate_output(0, system)
        correct = os.path.join(LOCAL_DIR, 'generated.xyz')
        with open(correct, 'r') as fileh:
            for lines1, lines2 in zip(fileh, snapshot):
                self.assertEqual(lines1.rstrip(), lines2.rstrip())

    def test_path_int_writer(self):
        """Test the path internal writer."""
        _, phasepoints, path = create_path()
        writer = get_writer('pathtrajint')
        idxs = 0
        idx = 0
        for i, lines in enumerate(writer.generate_output(0, path)):
            if i == 0:
                self.assertEqual('# Cycle: 0, status: None', lines)
            else:
                if lines.startswith('Snapshot'):
                    self.assertEqual('Snapshot: {}'.format(idxs), lines)
                    idxs += 1
                    idx = 0
                else:
                    posvel = '{} {} {} {} {} {}'.format(
                        *phasepoints[idxs - 1]['pos'][idx],
                        *phasepoints[idxs - 1]['vel'][idx]
                    )
                    self.assertEqual(lines, posvel)
                    idx += 1

    def test_path_ext_writer(self):
        """Test the path external writer."""
        path = PathExt(None)
        phasepoint = {'pos': ('initial.g96', None), 'vel': False,
                      'order': [np.random.random(), None], 'vpot': None,
                      'ekin': None}
        path.append(phasepoint)
        for i in range(5, 0, -1):
            phasepoint = {'pos': ('trajB.trr', i), 'vel': True,
                          'order': [np.random.random(), None], 'vpot': None,
                          'ekin': None}
            path.append(phasepoint)
        for i in range(0, 5):
            phasepoint = {'pos': ('trajF.trr', i), 'vel': False,
                          'order': [np.random.random(), None], 'vpot': None,
                          'ekin': None}
            path.append(phasepoint)
        writer = get_writer('pathtrajext')
        correct = ['# Cycle: 0, status: None',
                   '#     Step              Filename       index    vel',
                   '         0           initial.g96           0      1',
                   '         1             trajB.trr           5     -1',
                   '         2             trajB.trr           4     -1',
                   '         3             trajB.trr           3     -1',
                   '         4             trajB.trr           2     -1',
                   '         5             trajB.trr           1     -1',
                   '         6             trajF.trr           0      1',
                   '         7             trajF.trr           1      1',
                   '         8             trajF.trr           2      1',
                   '         9             trajF.trr           3      1',
                   '        10             trajF.trr           4      1']

        for corr, snap in zip(correct, writer.generate_output(0, path)):
            self.assertEqual(corr, snap)


if __name__ == '__main__':
    unittest.main()
