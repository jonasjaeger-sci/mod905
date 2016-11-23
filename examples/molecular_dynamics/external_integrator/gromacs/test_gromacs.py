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
from pyretis.integrators import GromacsExt
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
    orderp = create_orderparameter(settings)

    input_dir = 'ext_input'

    input_files = {'configuration': 'conf.gro',
                   'input': 'grompp.mdp',
                   'topology': 'topol.top'}

    gro = GromacsExt('gmx_5.1.4', input_dir, input_files)
    md_settings = {'steps': 20, 'subcycles': 5, 'timestep': 0.002}
    gro.execute_until('initial.g96', system, md_settings, orderp)
    gro.get_trr_frame('test2.trr', 'test2.tpr', 10, 0.002, 'output.gro')
    gro.get_trr_frame('test2.trr', 'test2.tpr', 10, 0.002, 'output.g96')
