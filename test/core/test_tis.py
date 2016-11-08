# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""Test the Box class from pyretis.core"""
import logging
import unittest
import numpy as np
from pyretis.core import System, Box
from pyretis.inout.settings import (create_force_field,
                                    create_orderparameter, create_simulation)
logging.disable(logging.CRITICAL)


TISMOL_001 = [[262, 'ACC', 'ki', -0.903862, 1.007330, 1, 262],
              [262, 'BWI', 'tr', -0.903862, 1.007330, 262, 1],
              [12, 'BWI', 'sh', 0.957091, 1.002750, 12, 1],
              [262, 'BWI', 'tr', -0.903862, 1.007330, 262, 1],
              [262, 'BWI', 'tr', -0.903862, 1.007330, 262, 1],
              [262, 'BWI', 'tr', -0.903862, 1.007330, 262, 1],
              [77, 'BWI', 'sh', 0.522609, 1.003052, 77, 1],
              [262, 'BWI', 'tr', -0.903862, 1.007330, 262, 1],
              [262, 'BWI', 'tr', -0.903862, 1.007330, 262, 1],
              [262, 'BWI', 'tr', -0.903862, 1.007330, 262, 1],
              [262, 'BWI', 'tr', -0.903862, 1.007330, 262, 1]]


def prepare_test_simulation():
    """Prepare a small system we can integrate."""
    settings = {}
    # Basic settings for the simulation:
    settings['simulation'] = {'task': 'tis',
                              'steps': 10,
                              'interfaces': [-0.9, -0.9, 1.0]}
    settings['system'] = {'units': 'lj', 'temperature': 0.07}
    # Basic settings for the Langevin integrator:
    settings['integrator'] = {'class': 'Langevin',
                              'gamma': 0.3,
                              'high_friction': False,
                              'seed': 1,
                              'rgen': 'mock',
                              'timestep': 0.002}
    # Potential parameters:
    # The potential is: `V_\text{pot} = a x^4 - b (x - c)^2`
    settings['potential'] = [{'a': 1.0, 'b': 2.0, 'c': 0.0,
                              'class': 'DoubleWell'}]
    # Settings for the order parameter:
    settings['orderparameter'] = {'class': 'OrderParameterPosition',
                                  'dim': 'x', 'index': 0, 'name': 'Position',
                                  'periodic': False}
    # TIS specific settings:
    settings['tis'] = {'freq': 0.5,
                       'maxlength': 20000,
                       'aimless': True,
                       'allowmaxlength': False,
                       'sigma_v': -1,
                       'seed': 1,
                       'rgen': 'mock',
                       'zero_momentum': False,
                       'rescale_energy': False,
                       'initial_path': 'kick'}

    box = Box(periodic=[False])
    system = System(temperature=settings['system']['temperature'],
                    units=settings['system']['units'], box=box)
    system.forcefield = create_force_field(settings)
    system.order_function = create_orderparameter(settings)
    system.add_particle(np.array([-1.0]), mass=1, name='Ar', ptype=0)
    simulation = create_simulation(settings, system)
    # here we do a hack so that the simulation and langevin integrator
    # both use the same random generator:
    simulation.rgen = simulation.integrator.rgen
    system.particles.vel = np.array([[0.78008019924163818]])
    return simulation


class TISTest(unittest.TestCase):
    """Run a test for the TIS algorithm."""

    def test_tis_001(self):
        """Test a TIS simulation for 001."""
        simulation = prepare_test_simulation()
        ensemble = simulation.path_ensemble
        for i in range(10):
            simulation.step()
            path = ensemble.paths[-1]
            path_data = [path['length'], path['status'], path['generated'][0],
                         path['ordermin'][0], path['ordermax'][0]]
            for j in (0, 1, 2):
                self.assertEqual(path_data[j], TISMOL_001[i][j])
            self.assertAlmostEqual(path_data[3], TISMOL_001[i][3], places=6)
            self.assertAlmostEqual(path_data[4], TISMOL_001[i][4], places=6)


if __name__ == '__main__':
    unittest.main()
