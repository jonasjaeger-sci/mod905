# -*- coding: utf-8 -*-
"""
This is a convenience script for creating TIS simulations.
"""
# pylint: disable=C0103
from __future__ import print_function
import numpy as np
import os
from pyretis.core.path import create_path_ensembles
from pyretis.core import Box, System
from pyretis.core.simulation import create_simulation
from pyretis.forcefield import ForceField
from pyretis.forcefield.potentials import DoubleWell
from pyretis.core.orderparameter import OrderParameterPosition
from pyretis.inout import create_output, generate_report
from pyretis.analysis import analyse_path_ensemble, match_probabilities

simulation_settings = {'type': 'TIS',
                       'integrator': {'name': 'Langevin', 'timestep': 0.002,
                                      'gamma': 0.3, 'seed': 10,
                                      'high-friction': False},
                       'endcycle': 200,
                       'temperature': 0.07,
                       'interfaces': [-0.9, -0.8, -0.7, -0.6,
                                      -0.5, -0.4, -0.3, 1.0],
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
                               'seed': 10,
                               'initial_path': 'kick'},
                       'output': [{'type': 'pathensemble', 'target': 'file',
                                   'when': {'every': 10}},
                                  {'type': 'trialpath', 'target': 'file',
                                   'when': {'every': 100}}]}


def set_up_tis_simulation(settings):
    """Method to do set-up for the TIS simulations"""
    box = Box(periodic=settings['periodic_boundary'])
    system = System(temperature=settings['temperature'],
                    units=settings['units'],
                    box=box)
    system.add_particle(name='A', pos=np.array([-1.0]))
    msg = 'Added one particle {} at position: {}'
    if 'generate-vel' in settings:
        system.generate_velocities(**settings['generate-vel'])
        msg = 'Generated temperatures with average: {}'
    # Set up force field:
    double_well = DoubleWell(a=1.0, b=2.0, c=0.0)
    forcefield = ForceField(potential=[double_well], desc='Double Well')
    system.forcefield = forcefield
    # add order parameter:
    orderparameter = OrderParameterPosition('position', 0, dim='x', periodic=False)
    settings['orderparameter'] = orderparameter
    simulation_tis = create_simulation(settings, system)
    return simulation_tis

path_results = []
tis_results = {'path_ensembles': [], 'detect': [],
               'tis': []}
print('Simulation type: {}'.format(simulation_settings['type']))
print('Setting up TIS simulations:')
interfaces = simulation_settings['interfaces']
ensembles, detect = create_path_ensembles(interfaces, include_zero=False)

for i, (path_ensemble, idetect) in enumerate(zip(ensembles, detect)):
    ensemble = '{:03d}'.format(i+1)
    print('\nPath ensemble: {} (no. {})'.format(path_ensemble.ensemble,
                                                ensemble))
    # create a home for the simulation:
    if not os.path.exists(ensemble):
        print('* Creating folder "{}"'.format(ensemble))
        os.makedirs(ensemble)
    else:
        print('* Folder "{}" already exist, will use it.'.format(ensemble))
    path_file = os.path.join(ensemble, 'path.dat')
    ensemble_file = os.path.join(ensemble, 'pathensemble.dat')
    settings = {}
    for key in simulation_settings:
        try:
            settings[key] = simulation_settings[key].copy()
        except AttributeError:
            settings[key] = simulation_settings[key]
    settings['path-ensemble'] = path_ensemble
    settings['ensemble'] = path_ensemble.ensemble
    settings['interfaces'] = path_ensemble.interfaces
    settings['output'] = [{'type': 'pathensemble',
                           'target': 'file',
                           'filename': ensemble_file,
                           'when': {'every': 10}},
                          {'type': 'trialpath',
                           'target': 'file',
                           'filename': path_file,
                           'when': {'every': 100}}]
    simulation_tis = set_up_tis_simulation(settings)
    print('Created:', simulation_tis)
    print('Starting', path_ensemble.ensemble)
    output = [task for task in create_output(simulation_tis.system, settings)]

    for result in simulation_tis.run():
        cycle = result['cycle']['step']
        for task in output:
            task.output(result)
    print('Done with', path_ensemble.ensemble)
    print('Will do a simple analysis')
    analysis_settings = {'skipcross': 1000,
                     'maxblock': 1000,
                     'blockskip': 1,
                     'bins': 1000,
                     'ngrid': 1001}
    local_results = {'detect': idetect,
                     'path_ensemble': path_ensemble}
    analyse = analyse_path_ensemble(path_ensemble,
                                    analysis_settings,
                                    idetect=idetect)
    local_results.update(analyse)
    path_results.append(analyse)
    tis_results['path_ensembles'].append(path_ensemble)
    tis_results['detect'].append(idetect)
    tis_results['tis'].append(analyse)
    report_txt = generate_report('tis_path', local_results, 'txt')[0]
    print(''.join(report_txt))
    if i >= 2: break
print('Done with all path simulation, will do overall analysis\n')
tis_results['matched'] = match_probabilities(path_results, detect)
report_txt = generate_report('tis', tis_results, 'txt')[0]
print(''.join(report_txt))
