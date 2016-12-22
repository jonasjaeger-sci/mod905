# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""
Example test for an interface for pyretis and a external MD package.

Here we test the following:

1. That we can run plain MD forward in time.

2. That we after performing 1, can reverse the velocities
   and end up back at the starting point.

3. That we can generate several trajectories.
"""
import os
import numpy as np
from pyretis.core import Box
from pyretis.core.particles import ParticlesExt
from pyretis.integrators import GromacsExt, ExternalScript
from pyretis.integrators.gromacs import read_gromos96_file
from pyretis.core.units import create_conversion_factors
from pyretis.inout.settings import create_system
from pyretis.inout.settings import create_orderparameter
from pyretis.inout.common import make_dirs
from matplotlib import pyplot as plt


def do_setup(md_settings):
    """Do initial setup needed for running the test.

    Parameters
    ----------
    md_settings : dict
        A dict containing settings for the gromacs integrator.

    Returns
    -------
    system : object like :py:class`pyretis.core.system.System`
        A system which we are integrating. It contains information
        about the order parameter and how to calculate it.
    gro : object like :py:class:`pyretis.integrators.gromacs.GromacsExt`
        The object used for interfacing gromacs.
    """
    settings = {}

    settings['system'] = {'units': 'gromacs',
                          'temperature': 200,
                          'dimensions': 3}

    settings['particles'] = {'position': {'file': 'ext_input/conf.gro'}}

    settings['orderparameter'] = {'class': 'Position',
                                  'index': 1472,
                                  'name': 'Gromacs distance',
                                  'periodic': True,
                                  'dim': 'z'}
    create_conversion_factors(settings['system']['units'])

    system = create_system(settings)
    # Transition to new particle class
    particles = ParticlesExt(dim=system.get_dim())
    for p in system.particles:
        particles.add_particle(p['pos'], p['vel'], p['force'],
                               mass=p['mass'], name=p['name'], ptype=p['type'])
    system.particles = particles
    # Transition done!
    initial = os.path.join(os.getcwd(), 'initial.g96')
    phase_point = {'pos': (initial, None), 'vel': False, 'vpot': None,
                   'ekin': None}
    system.particles.set_particle_state(phase_point)
    order_function = create_orderparameter(settings)

    input_dir = os.path.join(os.getcwd(), 'ext_input')

    input_files = {'configuration': 'conf.g96',
                   'input': 'grompp.mdp',
                   'topology': 'topol.top'}
    gro = GromacsExt('gmx_5.1.4', input_dir, input_files,
                     md_settings['timestep'], md_settings['subcycles'])
    return system, order_function, gro


if __name__ == '__main__':
    md_settings = {'subcycles': 5, 'timestep': 0.002}
    sys, order_fun, grom = do_setup(md_settings)

    exe_dir = os.path.join(os.getcwd(), '000', 'generate')

    make_dirs(exe_dir)

    print(sys.particles.config)
    grom.exe_dir = exe_dir
    grom.modify_velocities(sys, None, sigma_v=None, aimless=True,
                           momentum=False, rescale=None)
    print(sys.particles.config)
    from pyretis.core.random_gen import RandomGenerator
    from pyretis.core.pathext import PathExt
    rnd = RandomGenerator()
    path = PathExt(rnd, maxlen=30, time_origin=0)
    interfaces = [0.0, 1.0, 1.7]
    grom.propagate(path, sys, order_fun, interfaces, reverse=False)

    pathb = PathExt(rnd, maxlen=10, time_origin=0)
    interfaces = [0.0, 1.0, 1.7]
    grom.propagate(pathb, sys, order_fun, interfaces, reverse=True)

    print('Forward')
    for p in path.trajectory():
        print(p)
    print('Backward')
    for p in pathb.trajectory():
        print(p)
    from pyretis.core.path import paste_paths
    new_path = paste_paths(pathb, path, overlap=True, maxlen=100)

    print('Picking a shooting point:')
    shooting_point, idx = new_path.get_shooting_point()
    print('Shooting point:', shooting_point)
    print('Particle state 1:', sys.particles.get_particle_state())
    sys.particles.set_particle_state(shooting_point)
    print('Particle state 2:', sys.particles.get_particle_state())
    dek, _, = grom.modify_velocities(
        sys,
        rnd,
        sigma_v=None,
        aimless=True,
        momentum=True,
        rescale=False)
    print('Particle state 3:', sys.particles.get_particle_state())
    #path = PathExt(rnd, maxlen=30, time_origin=0)
    #interfaces = [0.0, 1.0, 1.7]
    #grom.propagate(path, sys, order_fun, interfaces, reverse=False,
    #               exe_dir=exe_dir)
