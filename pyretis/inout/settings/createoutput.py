# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Module for handling output from simulations.

This module defines functions and classes for handling the output from
simulations.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

create_output_tasks
    Function that sets up output tasks from a dictionary of settings.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

OutputTask
    A generic class for handling output tasks.

OutputTaskScreen
    A class for handling output tasks that will print to the screen.

OutputTaskFile
    A class for handling output tasks that will write to a file.

OutputTaskFileCombine
    A class for handling output tasks that will write to a file,
    but require some special pre-processing of the data to be
    written. Currently, this is only used to move files physically
    when storing external paths.
"""
import logging
# pyretis imports
from pyretis.inout.common import add_dirname
from pyretis.core.simulation.simulation_task import execute_now
from pyretis.inout.writers import get_writer, FileIO
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['OutputTask', 'create_output_tasks']


_TASK_MAP = {}
"""Define the known output tasks. The output tasks are
defined as dictionaries with the following keys:

* target : string
    "file" or "screen", defines where the task should write to.
* result : string
    Determines what item from the result dictionary we are outputting.
* when : string
    Determines what input setting from the "output" section is used to
    define the output frequency. Default values are defined in
    py:mod:`pyretis.inout.settings.settings` in the definition of the
    output section.
* writer : string
    Selects the writer used for formatting the output. Note that the
    string must be a valid input string for ``get_writer`` from
    :py:mod:`pyretis.inout.writers`.
* settings : dict
    Additional settings from the input needed to create the writer.
* engine-type : boolean
    For some tasks, the output when using external paths may depend
    on the type of engine used (external vs internal). For instance
    if we are using an external engine, then the paths must be
    physically stored, that is: moved to a safe location.
"""
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
    'result': 'path',
    'when': 'order-file',
    'writer': 'pathorder'}

_TASK_MAP['path-energy'] = {
    'target': 'file',
    'result': 'path',
    'when': 'energy-file',
    'writer': 'pathenergy'}

_TASK_MAP['path-traj-xyz'] = {
    'target': 'file',
    'result': 'path',
    'when': 'trajectory-file',
    'settings': {'system': ('units',)},
    'engine-dependent': True,
    'writer': 'pathtrajxyz'}

_TASK_MAP['path-traj-gro'] = {
    'target': 'file',
    'result': 'path',
    'when': 'trajectory-file',
    'engine-dependent': True,
    'settings': {'system': ('units',),
                 'output': ('write_vel',)},
    'writer': 'pathtrajgro'}

_SIM_OUTPUT = {}
"""This dictionary gives a list of predefined output tasks for
different simulation types. The output tasks are defined as dictionries
with the following keys:

* type : string
    This selects the output task, it corresponds to one of the
    items in ``_TASK_MAP``
* name : string
    This is just a unique name given to the task. It is only used
    for output of task information.
* filename : string
    If the task represents a file, this gives the name of the
    file created.
"""

_SIM_OUTPUT['md-nve'] = [
    {'type': 'energy',
     'name': 'nve-energy-file',
     'filename': 'energy.dat'},
    {'type': 'thermo-file',
     'name': 'nve-thermo-file',
     'filename': 'thermo.dat'},
    {'type': 'traj-gro',
     'name': 'nve-traj-file',
     'filename': 'traj.gro'},
    {'type': 'thermo-screen',
     'name': 'nve-thermo-screen'}
]

_SIM_OUTPUT['md-flux'] = [
    {'type': 'energy',
     'name': 'flux-energy-file',
     'filename': 'energy.dat'},
    {'type': 'traj-gro',
     'name': 'flux-traj-file',
     'filename': 'traj.gro'},
    {'type': 'thermo-screen',
     'name': 'flux-thermo-screen'},
    {'type': 'orderp',
     'name': 'flux-orderp-file',
     'filename': 'order.dat'},
    {'type': 'cross',
     'name': 'flux-cross-file',
     'filename': 'cross.dat'}
]

_SIM_OUTPUT['tis'] = [
    {'type': 'pathensemble',
     'name': 'tis-path-ensemble',
     'filename': 'pathensemble.dat'},
    {'type': 'pathensemble-screen',
     'name': 'tis-pathensemble-screen'},
    {'type': 'path-order',
     'name': 'tis-path-ensemble-orderp',
     'filename': 'order.dat'},
    {'type': 'path-traj-xyz',
     'name': 'tis-path-ensemble-traj',
     'filename': 'traj.xyz'},
    {'type': 'path-energy',
     'name': 'tis-path-ensemble-energy',
     'filename': 'energy.dat'}
]

_SIM_OUTPUT['retis'] = [
    {'type': 'pathensemble',
     'name': 'retis-path-ensemble',
     'filename': 'pathensemble.dat'},
    {'type': 'path-order',
     'name': 'retis-path-ensemble-orderp',
     'filename': 'order.dat'},
    {'type': 'path-traj-xyz',
     'name': 'retis-path-ensemble-traj',
     'filename': 'traj.xyz'},
    {'type': 'path-energy',
     'name': 'retis-path-ensemble-energy',
     'filename': 'energy.dat'}
]


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
        super().__init__(name, result, writer, when)
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
        super().__init__(name, result, writer, when)
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


class OutputTaskFileCombine(OutputTaskFile):
    """A class for handling output where we combine several results.

    Currently, this class is rather specialized and is only used for
    storing external paths. But it can be made more general in the
    future if such combinations are needed for other outputs.
    Here we model it as one type of output that applies a function
    to the result before outputting. Incidentally the function we
    use to output the result is contained in one of the other results.

    Attributes
    ----------
    dependency : string
        The result we need to combine with `self.result` in some way.
    """
    dependency = 'pathensemble'

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
        for res in (self.result, self.dependency):
            if res not in simulation_result:
                return False
        result = simulation_result[self.result]
        function = simulation_result[self.dependency]
        result_ = function.generate_output(step, result)
        return self.write(step, result_)


def create_writer(task_settings, writer_name, settings):
    """Create a writer for an output task

    Parameters
    ----------
    task_settings : dict
        Settings for the output task/writer we are creating for.
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


def generate_file_name(task, settings):
    """Generate file name for an output task from settings.

    Parameters
    ----------
    task : dict
        The task we are generating for.
    settings : dict
        The input settings

    Returns
    -------
    filename : string
        The file name to use.
    """
    prefix = settings['output'].get('prefix', None)
    if prefix is not None:
        filename = '{}{}'.format(prefix, task['filename'])
    else:
        filename = task['filename']
    filename = add_dirname(filename,
                           settings['output'].get('directory', None))
    return filename


def get_backup_settings(settings):
    """Get backup settings from simulation settings.

    Parameters
    ----------
    settings : dict
        The simulation settings

    Returns
    -------
    out : string
        A string representing the backup settings to use.
    """
    try:
        old = settings['output']['backup'].lower()
    except AttributeError:
        logger.warning('"backup" not found in "output" settings')
        old = 'backup' if settings['output']['backup'] else 'overwrite'
        logger.warning('Handling backup as %s', old)
    return old


def task_from_settings(task, settings, engine=None):
    """Method to create output task from simulation settings.

    Parameters
    ----------
    task : dict
        Settings related to the specific task.
    settings : dict
        Settings for the simulation.
    engine : object like :py:class:`pyretis.engines.engine.EngineBase`
        This object is used to determine if we need to do something
        special for external engines. If no engine is given, we do
        not do anything special.

    Returns
    -------
    out : object like `OutputTask`
        An output task we can use in the simulation
    """
    task_settings = _TASK_MAP[task['type']]

    when = {'every': settings['output'][task_settings['when']]}

    if when['every'] < 1:
        logger.info('Skipping output task %s (freq < 1)', task['type'])
        return None

    writer_name = task_settings['writer']
    writer = create_writer(task_settings, writer_name, settings)
    if writer is None:
        logger.warning('Could not create writer %s', writer_name)
        return None

    target = task_settings['target']

    # Currently there are only two cases: screen and file.
    # And this will probably not change in the near future,
    # so we do nothing fancy here. Note: It would be cool
    # if someone made a new target!

    if target == 'screen':
        return OutputTaskScreen(
            task['name'],
            task_settings['result'],
            writer,
            when)
    elif target == 'file':
        filename = generate_file_name(task, settings)
        backup_settings = get_backup_settings(settings)
        if engine is None or engine.engine_type == 'internal':
            klass = OutputTaskFile
        else:
            if task_settings.get('engine-dependent', False):
                klass = OutputTaskFileCombine
            else:
                klass = OutputTaskFile

        return klass(task['name'],
                     task_settings['result'],
                     writer,
                     when,
                     filename,
                     backup_settings)
    else:
        logger.warning('Unknown target "%s" ignored.', target)
        return None


def create_output_tasks(settings, engine=None):
    """Generate output tasks from settings and defaults.

    This function will return actual objects that can be added to the
    simulation. It uses `task_from_settings` to generate the output
    tasks which can be added to a simulation.

    Parameters
    ----------
    settings : dict
        These are the settings for the simulation.
    engine : object like :py:class:`pyretis.engines.engine.EngineBase`
        This object is used to determine if we need to do something
        special for external engines. If no engine is given, we do
        not do anything special.

    Yields
    ------
    out : object like `OutputTask`
    """
    sim_task = settings['simulation']['task'].lower()
    for task in _SIM_OUTPUT.get(sim_task, []):
        out_task = task_from_settings(task, settings, engine=engine)
        if out_task is not None:
            logger.debug('Output task created: %s', out_task)
            yield out_task
