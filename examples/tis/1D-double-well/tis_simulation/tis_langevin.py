# -*- coding: utf-8 -*-
"""
This is a convenience script for creating TIS simulations.
"""
# pylint: disable=C0103
from __future__ import print_function
import pprint
import os
import jinja2
from pyretis.inout.settings import write_settings_file

def simple_template_write(template, variables, outfile, path=None):
    """
    This will write a new file, inserting the value of
    `variables[key]` in locations @{{ key @}} in the given
    `template`.

    Parameters
    ----------
    template : string
        This is the input template to use
    variables : dict
        A dict with the keys we want to write
    outfile : string
        The file to create
    path : string
        Path to where the template is stored.

    Returns
    """
    if path is None:
        path = os.path.dirname(os.path.abspath(__file__))
    env = jinja2.Environment(block_start_string='@{%',
                             block_end_string='%}@',
                             variable_start_string='@{{',
                             variable_end_string='}}@',
                             loader=jinja2.FileSystemLoader(path))
    # pylint: disable=maybe-no-member
    render = env.get_template(template).render(variables)
    # pylint: enable=maybe-no-member
    with open(outfile, 'w') as fileout:
        fileout.write(render)
    return None

simulation_settings = {'task': 'TIS',
                       'integrator': {'name': 'Langevin', 'timestep': 0.002,
                                      'gamma': 0.3, 'seed': 0,
                                      'high-friction': False},
                       'endcycle': 100000,
                       'temperature': 0.07,
                       'interfaces': [-0.9, -0.8, -0.7, -0.6,
                                      -0.5, -0.4, -0.3, 1.0],
                       'periodic_boundary': [False],
                       'units': 'lj',
                       'generate-vel': {'seed': 0, 'momentum': False,
                                        'distribution': 'maxwell'},
                       'orderparameter': {'class': 'OrderParameterPosition',
                                          'args': ['position', 0],
                                          'kwargs': {'dim': 'x',
                                                     'periodic': False}},

                       'tis': {'start_cond': 'L',
                               'freq': 0.5,
                               'maxlength': 10000,
                               'aimless': True,
                               'allowmaxlength': False,
                               'sigma_v': -1,
                               'seed': 0,
                               'initial_path': 'kick'},
                       'output': [{'type': 'pathensemble', 'target': 'file',
                                   'when': {'every': 10}}]}
TEMPLATE_TIS = 'template_tis.txt'
TEMPLATE_A = 'template_analysis.txt'

print('Simulation type: {}'.format(simulation_settings['task']))
print('Setting up TIS simulations:')
stateA = simulation_settings['interfaces'][0]
stateB = simulation_settings['interfaces'][-1]
detect = []
for i, middle in enumerate(simulation_settings['interfaces'][:-1]):
    ensemble = '{:03d}'.format(i+1)
    strensemble = '\nEnsemble: {}'.format(ensemble)
    print(strensemble)
    print('-' * len(strensemble))
    interface = [stateA, middle, stateB]
    print('* Interfaces: {} {} {}'.format(*interface))
    try:
        detect.append(simulation_settings['interfaces'][i+1])
    except IndexError:
        detect.append(stateB)
    print('* "Detect" interface for analysis: {}'.format(detect[-1]))
    settings = {key: simulation_settings[key] for key in simulation_settings}
    settings['interfaces'] = interface
    settings['detect'] = detect[-1]
    settings['ensemble'] = ensemble
    # create a home for the simulation:
    if not os.path.exists(ensemble):
        print('* Creating folder "{}"'.format(ensemble))
        os.makedirs(ensemble)
    else:
        print('* Folder "{}" already exist, will use it.'.format(ensemble))
    sim_file = os.path.join(ensemble, 'tis_langevin.py')
    analysis_file = os.path.join(ensemble, 'analysis_tis.py')
    print('* Creating run script in "{}"'.format(sim_file))
    to_write = {'simulation_settings': pprint.pformat(settings, width=79),
                'interfaces': interface,
                'ensemble': "'{}'".format(ensemble),
                'idetect': detect[-1]}
    simple_template_write(TEMPLATE_TIS, to_write, sim_file)
    write_settings_file(settings, os.path.join(ensemble, 'input.txt'))
    print('* Creating analysis script in "{}"'.format(analysis_file))
    simple_template_write(TEMPLATE_A, to_write, analysis_file)
