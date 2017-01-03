# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Module for handling output from simulations.

This module defines functions and classes for handling the output from
simulations.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

create_output
    Function that sets up output tasks from a dictionary of settings.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

OutputTask
    A class for handling output tasks.
"""
import logging
# pyretis imports
from pyretis.inout.common import add_dirname
from pyretis.core.simulation.simulation_task import execute_now
from pyretis.inout.writers import get_writer, FileIO
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['OutputTask', 'create_output']


# Define the known output tasks
_TASK_MAP = {}
_TASK_MAP['energy'] = {
    'target': 'file',
    'result': 'thermo',
    'when': 'energy-file',
    'writer': 'energy'}

_TASK_MAP['orderp'] = {
    'target': 'file',
    'result': 'orderp',
    'when': 'order-file',
    'writer': 'order'}

_TASK_MAP['cross'] = {
    'target': 'file',
    'result': 'cross',
    'when': 'cross-file',
    'writer': 'cross'}

_TASK_MAP['traj-gro'] = {
    'target': 'file',
    'result': 'system',
    'when': 'trajectory-file',
    'settings': {'system': ('units',),
                 'output': ('write_vel',)},
    'writer': 'trajgro'}

_TASK_MAP['traj-xyz'] = {
    'target': 'file',
    'result': 'system',
    'when': 'trajectory-file',
    'settings': {'system': ('units',)},
    'writer': 'trajxyz'}

_TASK_MAP['thermo-screen'] = {
    'target': 'screen',
    'result': 'thermo',
    'when': 'energy-screen',
    'writer': 'thermotable'}

_TASK_MAP['thermo-file'] = {
    'target': 'file',
    'result': 'thermo',
    'when': 'energy-file',
    'writer': 'thermotable'}

_TASK_MAP['pathensemble'] = {
    'target': 'file',
    'result': 'pathensemble',
    'when': 'pathensemble-file',
    'settings': {'simulation': ('ensemble',
                                'interfaces')},
    'writer': 'pathensemble'}

_TASK_MAP['pathensemble-screen'] = {
    'target': 'screen',
    'result': 'pathensemble',
    'when': 'pathensemble-screen',
    'writer': 'pathtable'}

_TASK_MAP['path-order'] = {
    'target': 'file',
    'result': 'retis',
    'when': 'order-file',
    'writer': 'pathorder'}

_TASK_MAP['path-energy'] = {
    'target': 'file',
    'result': 'retis',
    'when': 'energy-file',
    'writer': 'pathenergy'}

_TASK_MAP['path-traj-xyz'] = {
    'target': 'file',
    'result': 'retis',
    'when': 'trajectory-file',
    'settings': {'system': ('units',)},
    'writer': 'pathtrajxyz'}

_TASK_MAP['path-traj-gro'] = {
    'target': 'file',
    'result': 'retis',
    'when': 'trajectory-file',
    'settings': {'system': ('units',),
                 'output': ('write_vel',)},
    'writer': 'pathtrajgro'}

# Predefined outputs for simulations.
_SIM_OUTPUT = {}

_SIM_OUTPUT['md-nve'] = [

    {'type': 'energy',
     'name': 'nve-energy-file',
     'when': {'every': 10},
     'filename': 'energy.dat'},

    {'type': 'thermo-file',
     'name': 'nve-thermo-file',
     'when': {'every': 10},
     'filename': 'thermo.dat'},
    {'type': 'traj-gro',
     'name': 'nve-traj-file',
     'when': {'every': 10},
     'filename': 'traj.gro'},
    {'type': 'thermo-screen',
     'name': 'nve-thermo-screen',
     'when': {'every': 10}}]

_SIM_OUTPUT['md-flux'] = [
    {'type': 'energy',
     'name': 'flux-energy-file',
     'when': {'every': 10},
     'filename': 'energy.dat'},
    {'type': 'traj-gro',
     'name': 'flux-traj-file',
     'when': {'every': 10},
     'filename': 'traj.gro'},
    {'type': 'thermo-screen',
     'name': 'flux-thermo-screen',
     'when': {'every': 10}},
    {'type': 'orderp',
     'name': 'flux-orderp-file',
     'when': {'every': 10},
     'filename': 'order.dat'},
    {'type': 'cross',
     'name': 'flux-cross-file',
     'when': {'every': 1},
     'filename': 'cross.dat'}]

_SIM_OUTPUT['tis'] = [
    {'type': 'pathensemble',
     'name': 'tis-path-ensemble',
     'when': {'every': 1},
     'filename': 'pathensemble.dat'},
    {'type': 'pathensemble-screen',
     'name': 'tis-pathensemble-screen',
     'when': {'every': 10}}]

_SIM_OUTPUT['retis'] = [
    {'type': 'pathensemble',
     'name': 'retis-path-ensemble',
     'when': {'every': 1},
     'filename': 'pathensemble.dat'},
    {'type': 'path-order',
     'name': 'retis-path-ensemble-orderp',
     'when': {'every': 10},
     'filename': 'order.dat'},
    {'type': 'path-traj-xyz',
     'name': 'retis-path-ensemble-traj',
     'when': {'every': 10},
     'filename': 'traj.xyz'},
    # {'type': 'path-traj-gro',
    #  'name': 'retis-path-ensemble-traj',
    #  'when': {'every': 10},
    #  'filename': 'traj.gro'},
    {'type': 'path-energy',
     'name': 'retis-path-ensemble-energy',
     'when': {'every': 10},
     'filename': 'energy.dat'}]


class OutputTask(object):
    """A base class for writing simulation output.

    This class will handle a output task for a simulation. The
    output task may be something that should print to the screen or
    a file. This object is a general class for output tasks and the
    specific writers for file and screen are implemented in the
    `OutputTaskFile` and `OutputTaskScreen` tasks.

    Attributes
    ----------
    name : string
        This string identifies the task, it can for instance be used
        to reference the dictionary used to create the writer.
    result : string
        This string defines the result we are going to output.
    writer : object like `Writer` from `pyretis.inout.writers`
        This object will handle the actual formatting of the result.
    when : dict
        Determines if the task should be executed.
    """
    target = 'undefined'

    def __init__(self, name, result, writer, when):
        """Initiate a OutputTask object.

        Parameters
        ----------
        name : string
            This string identifies the task, it can for instance be used
            to reference the dictionary used to create the writer.
        result : string
            This string defines the result we are going to output.
        writer : object like `Writer` from `pyretis.inout.writers`
            This object will handle formatting of the actual result
            which can be printed to the screen or to a file.
        when : dict
            Determines when the output should be written. Example:
            `{'every': 10}` will be executed at every 10th step.
        """
        self.name = name
        self.result = result
        self.writer = writer
        self.when = when

    def output(self, simulation_result):
        """Output a task given results from a simulation.

        This will output the task using the result found in the
        `simulation_result` which should be the dictionary returned
        from a simulation object (e.g. object like `Simulation` from
        `pyretis.core.simulation.simulation`) after a step.
        For trajectories, we expect that `simulation_result` contain
        the key `traj` so we can pass it to the trajectory writer.

        Parameters
        ----------
        simulation_result : dict
            This is the result from a simulation step.

        Returns
        -------
        out : boolean
            True if the writer wrote something, False otherwise.
        """
        step = simulation_result['cycle']
        if not execute_now(step, self.when):
            return False
        if self.result not in simulation_result:
            # This probably just means that the required result was not
            # calculated at this step.
            return False
        result = simulation_result[self.result]
        return self.write(step, result)

    def write(self, step, result):
        """Write the obtained result using the writer.

        Parameters
        ----------
        step : dict
            Information about the current simulation step.
        result : Any type
            This is the result to be written, handled by the writer.

        Returns
        -------
        out : boolean
            True if we managed to do the writing, False otherwise.
        """
        raise NotImplementedError

    def __str__(self):
        """Output some info about this output task."""
        msg = ['Output task: {} ({})'.format(self.name, self.target)]
        msg += ['* Result: {}'.format(self.result)]
        msg += ['* Writer: {}'.format(self.writer)]
        msg += ['* When: {}'.format(self.when)]
        return '\n'.join(msg)


class OutputTaskScreen(OutputTask):
    """A class for writing simulation output to screen.

    This class will handle a output task for a simulation to the screen.

    Attributes
    ----------
    name : string
        This string identifies the task, it can for instance be used
        to reference the dictionary used to create the writer.
    result : string
        This string defines the result we are going to output.
    writer : object like `Writer` from `pyretis.inout.writers`
        This object will handle the actual writing of the result.
    when : dict
        Determines if the task should be executed.
    """
    target = 'screen'

    def __init__(self, name, result, writer, when):
        """Initiate the OutputTask object.

        Parameters
        ----------
        name : string
            This string identifies the task, it can for instance be used
            to reference the dictionary used to create the writer.
        result : string
            This string defines the result we are going to output.
        writer : object like `Writer` from `pyretis.inout.writers`
            This object will handle the actual writing of the result.
        when : dict
            Determines when the task should be executed.
        """
        super(OutputTaskScreen, self).__init__(name, result, writer, when)
        self.print_header = writer.print_header

    def write(self, step, result):
        """Ouput the result to screen

        Parameters
        ----------
        step : dict
            Information about the current simulation step.
        result : Any type
            This is the result to be written, handled by the writer.

        Returns
        -------
        out : boolean
            True if we are printing something, False otherwise.
        """
        if self.print_header:
            print(self.writer.header)
            self.print_header = False
        for lines in self.writer.generate_output(step['step'], result):
            print(lines)
        return None


class OutputTaskFile(OutputTask):
    """A class for writing simulation output to files.

    This class will handle a output task for a simulation to a file.

    Attributes
    ----------
    name : string
        This string identifies the task, it can for instance be used
        to reference the dictionary used to create the writer.
    result : string
        This string defines the result we are going to output.
    writer : object like `Writer` from `pyretis.inout.writers`
        This object will handle the actual writing of the result.
    when : dict
        Determines if the task should be executed.
    """
    target = 'file'

    def __init__(self, name, result, writer, when, filename, backup):
        """Initiate the OutputTaskFile object.

        Parameters
        ----------
        name : string
            This string identifies the task, it can for instance be used
            to reference the dictionary used to create the writer.
        result : string
            This string defines the result we are going to output.
        writer : object like `Writer` from `pyretis.inout.writers`
            This object will handle the actual writing of the result.
        when: dict.
            Determines if and when the task should be executed.
            Example: `{'every': 10}` will be executed at every 10th
            step.
        filename : string
            The name of the file to write to.
        backup : string
            Determines how we should treat old files.
        """
        super(OutputTaskFile, self).__init__(name, result, writer, when)
        self.print_header = writer.print_header
        self.fileh = FileIO(filename, oldfile=backup)
        if self.print_header:
            if self.writer.header is not None:
                self.fileh.write(self.writer.header)

    def write(self, step, result):
        """Ouput the result.

        Parameters
        ----------
        step : dict
            Information about the current simulation step.
        result : Any type
            This is the result to be written, handled by the writer.

        Returns
        -------
        out : boolean
            True if we are printing something, False otherwise.
        """
        for lines in self.writer.generate_output(step['step'], result):
            self.fileh.write(lines)
        return None


def create_writer(task_settings, writer_name, settings):
    """Create a writer for an output task

    Parameters
    ----------
    task_settings : dict
        Settings for the output taks/writer we are creating for.
    writer_name : string
        The type of writer we are going to create.
    settings : dict
        Simulation settings. Some may be needed to create the
        writer.

    Returns
    -------
    out : object like :py:class:`.writers.Writer`
        The writer to use for formatting output.
    """
    writer_settings = {}
    req_settings = task_settings.get('settings', {})  # required settings
    for sec in req_settings:
        for key in req_settings[sec]:
            writer_settings[key] = settings[sec][key]
    writer = get_writer(writer_name, settings=writer_settings)
    return writer


def task_from_settings(task, settings):
    """Method to create output task from simulation settings.

    Parameters
    ----------
    task : dict
        Settings related to the specific task.
    settings : dict
        Settings for the simulation.

    Returns
    -------
    out : object like `OutputTask`
        An output task we can use in the simulation
    """
    task_settings = _TASK_MAP[task['type']]
    when = {'every': settings['output'][task_settings['when']]}
    if when['every'] < 1:
        msg = 'Skipping output task "{}"'.format(task['type'])
        logger.info(msg)
        return None
    when = {'every': settings['output'][task_settings['when']]}
    writer_name = task_settings['writer']
    writer = create_writer(task_settings, writer_name, settings)
    if writer is None:
        msg = 'Could not create writer "{}"'.format(writer_name)
        logger.warning(msg)
        return None
    target = task_settings['target']
    if target == 'screen':
        return OutputTaskScreen(task['name'],
                                task_settings['result'],
                                writer,
                                when)
    elif target == 'file':
        prefix = settings['output'].get('prefix', None)
        if prefix is not None:
            filename = '{}{}'.format(prefix, task['filename'])
        else:
            filename = task['filename']
        filename = add_dirname(filename,
                               settings['output'].get('directory', None))
        try:
            old = settings['output']['backup'].lower()
        except AttributeError:
            old = 'backup' if settings['output']['backup'] else 'overwrite'
        return OutputTaskFile(task['name'],
                              task_settings['result'],
                              writer,
                              when,
                              filename,
                              old)
    else:
        msg = 'Unknown target "{}" ignored!'.format(target)
        logger.warning(msg)
        return None


def create_output(settings):
    """Generate output tasks from settings and defaults.

    This function will return actual objects that can be added to the
    simulation. It uses `_get_output_tasks` to generate dictionaries
    for the output tasks which are here converted to objects using
    `create_output_task`.

    Parameters
    ----------
    settings : dict
        These are the settings for the simulation.

    Yields
    ------
    out : object like `OutputTask`
    """
    sim_task = settings['simulation']['task'].lower()
    for task in _SIM_OUTPUT.get(sim_task, []):
        out_task = task_from_settings(task, settings)
        if out_task is not None:
            msgtxt = 'Output task created: {}'.format(out_task)
            logger.debug(msgtxt)
            yield out_task
