# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""
Example for an external pyretis interface.

In this example we will interfaces a custom made program
which performs molecular dynamics.

In order to interface an external program the following
methods are needed:
"""
# These are for the __main__.
import numpy as np
from pyretis.core import Box
from pyretis.integrators import GromacsExt
from pyretis.integrators.gromacs import read_gromos96_file
from pyretis.core.units import create_conversion_factors
from pyretis.inout.settings import create_system
from pyretis.inout.settings import create_orderparameter


if __name__ == '__main__':
    # Run a test:
    settings = {}

    settings['system'] = {'units': 'gromacs',
                          'temperature': 300,
                          'dimensions': 3}

    settings['particles'] = {'position': {'file': 'ext_input/conf.gro'}}

    settings['orderparameter'] = {'class': 'Position',
                                  'index': 1472,
                                  'name': 'Gromacs distance',
                                  'periodic': True,
                                  'dim': 'z'}
    create_conversion_factors(settings['system']['units'])

    system = create_system(settings)
    system.orderp = create_orderparameter(settings)

    input_dir = 'ext_input'

    input_files = {'configuration': 'conf.gro',
                   'input': 'grompp.mdp',
                   'topology': 'topol.top'}

    gro = GromacsExt('gmx_5.1.4', input_dir, input_files)
    md_settings = {'steps': 10, 'subcycles': 5, 'timestep': 0.002}
    steps = md_settings['steps'] * md_settings['subcycles']
    trrf, tprf, orderf = gro.execute_until('initial.g96', system,
                                           md_settings, reverse=False)
    gro.get_trr_frame(trrf, tprf, steps, md_settings['timestep'], 'last.g96')
    trrb, tprb, orderb = gro.execute_until('last.g96', system,
                                           md_settings, reverse=True)
    gro.get_trr_frame(trrb, tprb, steps, md_settings['timestep'], 'first.g96')
    
    box = Box([2.384999990, 2.384999990, 2.384999990])
    txt1, xyz1, vel1 = read_gromos96_file('first.g96')
    txt0, xyz0, vel0 = read_gromos96_file('initial.g96')
    delta = xyz1 - xyz0
    delta = box.pbc_dist_matrix(delta)
    rsq = np.einsum('ij, ij->i', delta, delta)
    mse = rsq.mean()
    print('Average distance between initial.g96 and first.g96: {}'.format(mse))
