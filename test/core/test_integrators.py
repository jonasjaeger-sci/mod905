# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""Test the Box class from pyretis.core"""
import logging
import unittest
import numpy as np
from pyretis.core.integrators import Langevin
from pyretis.core import System, Box
from pyretis.forcefield import ForceField
from pyretis.forcefield.potentials.potentials import DoubleWell
logging.disable(logging.CRITICAL)


class IntegratorTest(unittest.TestCase):
    """Run the tests for the different Integrators."""

    def test_langevin(self):
        """Test the creation a particle list."""
        inth = Langevin(0.02, 0.3, rgen='mock', seed=0, high_friction=False)
        intl = Langevin(0.02, 0.3, rgen='mock', seed=0, high_friction=True)
        box = Box(periodic=[False])
        system = System(temperature=1.0, units='lj', box=box)
        pos = np.array([-1.0])
        vel = np.array([1.0])
        system.add_particle(name='Ar', pos=pos, vel=vel, mass=1.0, ptype=0)
        forcefield = ForceField()
        param = {'a': 1.0, 'b': 1.0, 'c': 0.0}
        pot = DoubleWell()
        forcefield.add_potential(pot, parameters=param)
        system.forcefield = forcefield
        traj = []
        for _ in range(10):
            pos = np.copy(system.particles.pos)
            vel = np.copy(system.particles.vel)
            force = np.copy(system.particles.force)
            traj.append([pos, vel, force])
            inth.integration_step(system)


if __name__ == '__main__':
    unittest.main()
