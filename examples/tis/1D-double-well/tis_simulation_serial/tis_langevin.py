# -*- coding: utf-8 -*-
"""
This is a convenience script for creating TIS simulations.
"""
# pylint: disable=C0103
from __future__ import print_function
import numpy as np
import Queue
from pyretis.core.path import create_path_ensembles
from pyretis.core import Box, System
from pyretis.inout.settings import create_simulation
from pyretis.forcefield import ForceField
from pyretis.forcefield.potentials import DoubleWell
from pyretis.core.orderparameter import OrderParameterPosition
from pyretis.inout import create_output, generate_report
from pyretis.analysis import analyse_path_ensemble, match_probabilities
from pyretis.inout.common import make_dirs


simulation_settings = {'task': 'TIS',
                       'integrator': {'name': 'Langevin', 'timestep': 0.002,
                                      'gamma': 0.3, 'seed': 0,
                                      'high-friction': False},
                       'endcycle': 20000,
                       #'endcycle': 200,
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
                                   'when': {'every': 10}},
                                  {'type': 'trialpath', 'target': 'file',
                                   'when': {'every': 100}}]}


common = ['task', 'integrator', 'orderparameter',
          'endcycle',
          'temperature',
          'periodic_boundary',
          'units',
          'generate-vel',
          'tis']


def set_up_tis_simulation(settings):
    """Method to set up a single TIS simulation.

    Parameters
    ----------
    settings : dict
        This dict contains the simulation settings

    Returns
    -------
    out : object like `Simulation` from pyretis.core.simulation`
        This object can be used to run the simulation we create here.

    Note
    ----
    `settings` will be updated with a new key - `orderparameter` which
    stores info about the order parameter object we create here.
    """
    box = Box(periodic=settings['periodic_boundary'])
    system = System(temperature=settings['temperature'],
                    units=settings['units'],
                    box=box)
    system.add_particle(name='A', pos=np.array([-1.0]))
    if 'generate-vel' in settings:
        system.generate_velocities(**settings['generate-vel'])
    # Set up force field:
    double_well = DoubleWell(a=1.0, b=2.0, c=0.0)
    forcefield = ForceField(potential=[double_well], desc='Double Well')
    system.forcefield = forcefield
    return create_simulation(settings, system)


def run_simulation(simulation, settings, analysis_settings=None):
    """This method will run a simulation and a simple analysis.

    Parameters
    ----------
    """
    output = [tsk for tsk in create_output(simulation.system, settings)]
    print('')
    msg = 'Running simulation:'
    print(msg)
    msg = ('=') * len(msg)
    print(msg)
    print(simulation)
    try:
        msg = 'Output directory: {}'.format(settings['output-dir'])
        print(msg)
    except KeyError:
        pass
    for result in simulation.run():
        for otask in output:
            otask.output(result)
    msg = 'Simulation done!'
    print(msg)
    if analysis_settings is not None:
        msg = 'Will do a simple analysis...'
        print(msg)
        local_results = {'detect': simulation.path_ensemble.detect,
                         'interfaces': settings['interfaces'],
                         'ensemble': settings['ensemble']}
        analyse = analyse_path_ensemble(simulation.path_ensemble,
                                        analysis_settings,
                                        idetect=local_results['detect'])
        local_results.update(analyse)
        report_txt = generate_report('tis_path', local_results, 'txt')[0]
        print(''.join(report_txt))
    return report_txt, analyse

# for storing results etc:
tis_results = {'tis': [],
               'ensembles': [],
               'interfaces': [],
               'detect': []}

print('Simulation type: {}'.format(simulation_settings['task']))
print('Setting up TIS simulations:')

interfaces = simulation_settings['interfaces']

simulations_to_run = Queue.Queue()
ensembles, detect = create_path_ensembles(interfaces, include_zero=False)
for i, (path_ensemble, idetect) in enumerate(zip(ensembles, detect)):
    ensemble = '{:03d}'.format(i+1)
    print('\nPath ensemble: {} (no. {})'.format(path_ensemble.ensemble,
                                                ensemble))
    # store results for this ensemble
    tis_results['tis'].append(None)
    tis_results['ensembles'].append(path_ensemble.ensemble)
    tis_results['interfaces'].append(path_ensemble.interfaces)
    tis_results['detect'].append(idetect)
    print('Creating directories:')
    msg_dir = make_dirs(ensemble)
    print('* {}'.format(msg_dir))
    # set up local settings:
    local_settings = {}
    for key in common:  # this common for all simulations:
        local_settings[key] = simulation_settings[key]
    # things we change for each simulation
    local_settings['path-ensemble'] = path_ensemble
    local_settings['ensemble'] = path_ensemble.ensemble
    local_settings['interfaces'] = path_ensemble.interfaces
    # copy output settings since these will be modified (with path):
    local_settings['output'] = [task.copy() for task in
                                simulation_settings['output']]
    print(local_settings['output'])
    local_settings['output-dir'] = ensemble
    simulation_tis = set_up_tis_simulation(local_settings)
    simulations_to_run.put((simulation_tis, local_settings, i))

# all simulations are set up, time to run:
ANALYSIS_SETTINGS = {'skipcross': 1000,
                     'maxblock': 1000,
                     'blockskip': 1,
                     'bins': 1000,
                     'ngrid': 1001}
while not simulations_to_run.empty():
    sim, sim_settings, idx = simulations_to_run.get()
    report_tis, analyse_tis = run_simulation(sim, sim_settings,
                                             ANALYSIS_SETTINGS)
    # store output from analysis:
    tis_results['tis'][idx] = analyse_tis
print('\nDone with all TIS path ensembles, will do overall analysis\n')
tis_results['matched'] = match_probabilities(tis_results['tis'], detect)
report_overall = generate_report('tis', tis_results, 'txt')[0]
print(''.join(report_overall))
