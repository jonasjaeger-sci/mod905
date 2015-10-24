# -*- coding: utf-8 -*-
"""
This package defines different simulations for use with pyretis.

The different simulations are defined as objects which inherits from
the base Simulation object defined in `simulation.py`. The simulation
object defines as simulation as a series of tasks to be executed,
typically at each step of the simulation. Output is handled with a
different set out 'ouput' tasks which make use of the results obtained
in the simulation steps.

Package structure
=================

Modules
-------

- __init__.py: Imports simulations from the other modules and defines a method
  for creating simulations from a dict with settings.

- md_simulation.py: Defines simulation objects for molecular dynamics
  simulations.

- mc_simulation.py: Define simulation objects for monte carlo simulations.

- path_simulation.py: Defines simulation objects for path simulations.

- simulation.py: Defines the Simulation object which is the base object for
  simulations.

- simulation_task.py: Defines objects for handling of simulation tasks and
  output tasks.

Important classes and functions
-------------------------------

- Simulation: The base class for simulations.

- SimulationTask: A class for creating tasks for simulations.

- OutputTask: A class for handling output tasks for simulations.

- create_simulation: A function to create a simulation object from
  a dictionary of given settings.

- create_output_task: A function to create output tasks for simulations
  from a dictionary of settings.
"""
# local pyretis imports
from .simulation import Simulation
from .mc_simulation import UmbrellaWindowSimulation
from .md_simulation import SimulationNVE, SimulationMDFlux
from .path_simulation import SimulationTIS
from .simulation_task import OutputTask, SimulationTask
# other pyretis imports
from pyretis.core.integrators import create_integrator
from pyretis.inout.fileinout import (CrossFile, EnergyFile, OrderFile,
                                     PathFile, PathEnsembleFile)
from pyretis.inout import create_traj_writer, get_predefined_table
# other imports
import warnings


_OUTPUT = {'nve': [{'type': 'thermo', 'target': 'file', 'when': {'every': 10},
                    'filename': 'energy.dat'},
                   {'type': 'traj', 'target': 'file', 'when': {'every': 10},
                    'filename': 'traj.gro', 'format': 'gro',
                    'header': 'NVE simulation. Step: {}'},
                   {'type': 'thermo', 'target': 'screen',
                    'when': {'every': 10}}],
           'md-flux': [{'type': 'orderp', 'target': 'file',
                        'when': {'every': 10}, 'filename': 'order.dat'},
                       {'type': 'thermo', 'target': 'file',
                        'when': {'every': 100}, 'filename': 'energy.dat'},
                       {'type': 'cross', 'target': 'file',
                        'when': {'every': 1}, 'filename': 'cross.dat'},
                       {'type': 'traj', 'target': 'file', 'format': 'gro',
                        'when': {'every': 10}, 'filename': 'traj.gro',
                        'header': 'MD FLUX simulation. Step: {}'},
                       {'type': 'thermo', 'target': 'screen',
                        'when': {'every': 10}}],
           'tis': [{'type': 'pathensemble', 'target': 'file',
                    'when': {'every': 10}, 'filename': 'pathensemble.dat'},
                   {'type': 'trialpath', 'target': 'file',
                    'when': {'every': 10}, 'filename': 'paths.dat'}]}


def _check_settings(settings, required):
    """
    Helper function to check if required settings actually are set

    Parameters
    ----------
    settings : dict
        This dict contains the given settings
    required : list of strings
        This list contains the settings that are required and which
        we will check the presence of.

    Returns
    -------
    out : boolean
        True if all required settings are present, False otherwise.
    """
    result = True
    for setting in required:
        if setting not in settings:
            warnings.warn('Setting `{}` not found!'.format(setting))
            result = False
    return result


def create_simulation(settings, system):
    """
    This method will set up some common simulation types.
    It is meant as a helper function to automate some very common set-up
    tasks

    Parameters
    ----------
    settings : dict
        This dictionary contains the settings for the simulation.
    system : object like `System` from `pyretis.core.system`
        This is the system for which the simulation will run.

    Returns
    -------
    out : object that represents the simulation.
        This object will correspond to the selected simulation type.
    """
    simulation_type = settings.get('type', 'nve').lower()
    simulation = None
    required = {'nve': ['endcycle'],
                'md-flux': ['endcycle', 'integrator', 'interfaces',
                            'orderparameter'],
                'tis': ['endcycle', 'tis', 'integrator', 'interfaces']}
    msg = 'Unknown simulation type {} requested'.format(simulation_type)
    assert simulation_type in required, msg
    if not _check_settings(settings, required[simulation_type]):
        return None
    if simulation_type == 'nve':
        # Set up a MD NVE simulation.
        intg = create_integrator(settings.get('integrator', None),
                                 simulation_type)
        simulation = SimulationNVE(system, intg,
                                   endcycle=settings['endcycle'],
                                   startcycle=settings.get('startcycle', 0))
    elif simulation_type == 'md-flux':
        # Set up MD FLUX simulation.
        intg = create_integrator(settings.get('integrator', None),
                                 simulation_type)
        simulation = SimulationMDFlux(system, intg,
                                      settings['interfaces'],
                                      settings['orderparameter'],
                                      endcycle=settings['endcycle'],
                                      startcycle=settings.get('startcycle', 0))
    elif simulation_type == 'tis':
        intg = create_integrator(settings.get('integrator', None),
                                 simulation_type)
        simulation = SimulationTIS(system, intg, settings,
                                   endcycle=settings['endcycle'],
                                   startcycle=settings.get('startcycle', 0))
    # add output tasks:
    for out_task in _get_output_tasks(settings.get('output', []),
                                      simulation_type):
        task = create_output_task(out_task, system, settings)
        simulation.add_output_task(task)
    return simulation


def _get_output_tasks(output_settings, simulation_type):
    """
    This will add output tasks to a simulation

    Parameters
    ----------
    output_settings : list of dicts
        These are user-specified output tasks.
    simulation_type : string
        This is a string identifying the type of simulation ('nve', etc.)

    Returns
    -------
    output_tasks : list of dicts
        List of output tasks that can be added to the simulation.
        Note that the tasks should be created with `create_output_task`
        before they can be added.
    """
    output_tasks = []
    for default in _OUTPUT[simulation_type]:
        add = True
        for output in output_settings:
            if _task_dict_eq(default, output) and not output.get('use', True):
                add = False
        if add:
            output_tasks.append(default)
    # Should we add from output_settings or update?
    for output in output_settings:
        add = output.get('use', True)
        update = []
        for i, task in enumerate(output_tasks):
            if _task_dict_eq(output, task):
                add = False
                update.append(i)
        if add:  # this is a completely new task, will add
            output_tasks.append(output)
        else:  # we should possibly update or not add it
            for i in update:
                output_tasks[i].update(output)
    return output_tasks


def _task_dict_eq(task1, task2):
    """
    Method to see to two tasks are similar. This is usefull if we want
    to check if we should update a task or add a new task. Here we check if
    tasks are similar before they are added/created.

    Parameters
    ----------
    task1 : dict
        Representation of a task. The possible keys are 'type',
        'target', 'when', 'filename', 'format', 'header'.
        'type' and 'target' will always be given and we use these two
        as a first test to see if the two tasks are similar.
    task2 : dict
        Representation of a task. See definition above for `task1`.

    Returns
    -------
    out : boolean
        True if the tasks are similar.
    """
    same_type = task1['type'] == task2['type']
    same_target = task1['target'] == task2['target']
    if same_type and same_target:
        if task1['target'] == 'screen':  # they are equal
            return True
        elif task1['target'] == 'file':
            # here we have several options
            try:  # both give filename
                same_file = task1['filename'] == task2['filename']
            except KeyError:  # only one give filename
                same_file = True
            try:  # both give format
                fmt = task1['format'] == task2['format']
            except KeyError:  # only one give format
                fmt = True
            return same_file and fmt
        else:
            return False
    else:
        return False


def _create_file_writer(task, system, settings):
    """
    This will create an object for writing to files.

    Parameters
    ----------
    task : dict
        This dict describes the task.
    system : object like `System` from `pyretis.core.system`
        The system we are describing. Needed for creating the
        trajectory writer.
    settings : dict
        These are the settings used for setting up the simulation.
        Some of these settings might be usefull for creating the
        output tasks.
    """
    writer = None
    if task['type'] == 'orderp':
        writer = OrderFile(task['filename'],
                           mode=task.get('mode', 'w'),
                           oldfile=task.get('oldfile', 'overwrite'))
    elif task['type'] == 'thermo':
        writer = EnergyFile(task['filename'],
                            mode=task.get('mode', 'w'),
                            oldfile=task.get('oldfile', 'overwrite'))
    elif task['type'] == 'cross':
        writer = CrossFile(task['filename'],
                           mode=task.get('mode', 'w'),
                           oldfile=task.get('oldfile', 'overwrite'))
    elif task['type'] == 'traj':
        writer = create_traj_writer(task['filename'], task['format'],
                                    task.get('oldfile', 'overwrite'),
                                    system)
    elif task['type'] == 'pathensemble':
        writer = PathEnsembleFile(task['filename'],
                                  settings.get('ensemble', '000'),
                                  settings.get('interfaces', None),
                                  mode=task.get('mode', 'w'),
                                  oldfile=task.get('oldfile', 'overwrite'))
    elif task['type'] == 'trialpath':
        writer = PathFile(task['filename'],
                          mode=task.get('mode', 'w'),
                          oldfile=task.get('oldfile', 'overwrite'))
    else:
        msg = 'Unknown type {} for target file'.format(task['type'])
        warnings.warn(msg)
    return writer


def create_output_task(task, system, settings):
    """Create object for a output task.

    This method will create an object for a given output task.
    It will make use of some of the pre-defined output possibilities
    defined in `pyretis.inout`

    Parameters
    ----------
    task : dict
        This dict describes the task.
    system : object like `System` from `pyretis.core.system`
        The system we are describing. Needed for creating the
        trajectory writer.
    settings : dict
        These are the settings used for setting up the simulation.
        Some of these settings might be usefull for creating the
        output tasks.
    """
    writer = None
    if task['target'] == 'file':
        writer = _create_file_writer(task, system, settings)
    elif task['target'] == 'screen':
        if task['type'] == 'thermo':
            writer = get_predefined_table('energies')
    else:
        pass
    if writer is not None:
        return OutputTask(writer, task['type'], task['target'],
                          when=task.get('when', None),
                          header=task.get('header', None))
    else:
        return None
