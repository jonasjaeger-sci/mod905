# -*- coding: utf-8 -*-
"""
This is a convenience script for creating TIS simulations.
"""
# pylint: disable=C0103
from __future__ import print_function
import os
import re

def simple_template_write(template, variables, outfile):
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
    
    Returns
    """
    regexp = re.compile(r'@{{(.*?)}}@')
    with open(outfile, 'w') as fileout:
        with open(template, 'r') as filein:
            for lines in filein:
                if lines.find('@{{') != -1:
                    out = lines
                    for key in regexp.findall(lines.strip()):
                        keys = key.strip()
                        repl = '@{{{{{}}}}}@'.format(key)
                        news = str(variables.get(keys, '{}'.format(keys)))
                        out = out.replace(repl, news)
                    fileout.write(out)
                else:
                    fileout.write(lines)
    return None

simulation_settings = {'type': 'TIS',
                       'integrator': {'name': 'Langevin', 'timestep': 0.002,
                                      'gamma': 0.3, 'seed': 0,
                                      'high-friction': False},
                       'endcycle': 100000,
                       'temperature': 0.07,
                       'interfaces': [-0.9, -0.8, -0.7, -0.6, 
                                      -0.5, -0.4, -0.3],
                       'reactant': -0.9,
                       'product': 1.0,
                       'periodic_boundary': [False],
                       'units': 'lj',
                       'generate-vel': {'seed': 0, 'momentum': False,
                                        'distribution': 'maxwell'},
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
TEMPLATE = 'template_tis.txt'
TEMPLATE_A = 'template_analysis.txt'
print('Simulation type: {}'.format(simulation_settings['type']))
print('Setting up TIS simulations...')
stateA = simulation_settings['reactant']
stateB = simulation_settings['product']
detect = []
for i, middle in enumerate(simulation_settings['interfaces']):
    ensemble = '{:03d}'.format(i+1)
    strensemble = '\nEnsemble: {}'.format(ensemble)
    print(strensemble)
    print(('-') * len(strensemble))
    interface = [stateA, middle, stateB]
    print('* Interfaces: {} {} {}'.format(*interface))
    try:
        detect.append(simulation_settings['interfaces'][i+1])
    except IndexError:
        detect.append(stateB)
    print('* Detect (for analysis): {}'.format(detect[-1]))
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
    print('* Creating run script in {}'.format(sim_file))
    to_write = {'simulation_settings': settings,
                'interfaces': interface,
                'ensemble': "'{}'".format(ensemble),
                'idetect': detect[-1]}
    simple_template_write(TEMPLATE, to_write , sim_file)
    print('* Creating analysis script in {}'.format(analysis_file))
    simple_template_write(TEMPLATE_A, to_write, analysis_file)
