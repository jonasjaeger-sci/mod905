# -*- coding: utf-8 -*-
"""Module for handling output from simulations

This module defines functions and classes for handling the output from
simulations.
"""
from pyretis.core.simulation.simulation_task import execute_now
from pyretis.inout.fileinout import (CrossFile, EnergyFile, OrderFile,
                                     PathFile, PathEnsembleFile)
from pyretis.inout.traj import create_traj_writer
from pyretis.inout.txtinout import get_predefined_table
# other imports
import warnings


__all__ = ['OutputTask', 'create_output']


class OutputTask(object):
    """Class OutputTask(object) - Simulation output tasks.

    This class will handle a output task for a simulation. The
    output task may be something that should print to the screen or
    a file.

    Attributes
    ----------
    output_type : string
        This string identifies the result we want to write.
    target : string
        This determines what kind out output target we have in mind,
        'file' and 'screen' are handled slightly differently.
    when : dict
        Determines if the task should be executed.
    writer : object like `FileWriter` from `pyretis.inout.txtinout`
        This object will handle the actual writing of the result.
    header : string
        Some objects will have a specifid header written each time we use
        the write routine. This is for instance used in the trajectory writer
        to display the current step for a written frame.
    """

    def __init__(self, writer, output_type, target, when=None, header=None):
        """Initiate the OutputTask object.

        Parameters
        ----------
        writer : object
            This object will handle the actual writing of the result.
        output_type : string
            This string defines the output type. It is used to get the
            ouput from the simulation.
        target : string
            This determines what kind out output target we have in mind,
            'file' and 'screen' are handled slightly differently.
        when : dict
            Determines if the task should be executed.
        header : string
            Some object will have a header written each time the we use the
            write routine. This is for instance used in the trajectory writer
            to display the current step for a written frame.
        """
        self.output_type = output_type
        self.writer = writer  # output type can be derived from writer?
        msg = 'Unknown target: {}'.format(target)
        assert target in ('screen', 'file'), msg
        self.target = target
        self.when = when
        self.header = header

    def output(self, simulation_step):
        """Output the task.

        This will output the task using the result found in the
        `simulation_step` which should be the dict returned from a simulation
        object (e.g. object like `Simulation` from
        `pyretis.core.simulation.simulation`) after a step. For trajectories,
        we don't need to pass the actual `system` since this is already
        attached to the trajectory writer.

        Parameters
        ----------
        simulation_step : dict
            This is the result from a simulation step
        """
        step = simulation_step['cycle']
        if not execute_now(step, self.when):
            return False
        try:
            result = simulation_step[self.output_type]
        except KeyError:  # result was not calculated at this step
            result = None
            if self.output_type != 'traj':
                return False
        # Handle the output:
        if self.target == 'screen':
            pass
        else:
            if self.output_type == 'traj':
                try:
                    header = self.header.format(step['step'])
                except AttributeError:
                    header = 'Step: {}'.format(step['step'])
                self.writer.write(header=header)
            elif self.output_type == 'cross':
                return self.writer.write(result)
            else:
                return self.writer.write(step['step'], result)

    def close(self):
        """Method to explicitly close a file if needed"""
        if self.target == 'file':
            self.writer.close()


def _task_dict_eq(task1, task2):
    """Check if two task dicts are similar.

    This method is used when we decide if we should add a new task or update
    an existing one. The two tasks are checked differently depending on the
    target of the task.

    - If the 'target' equals 'screen', then two tasks are equal if they are
      of the same 'type'.

    - If the 'target' equals 'file' then the two tasks are equal if they write
      to the same 'filename' or if they are of the same 'type'. In we find
      that the two tasks have different 'type' but are using the same
      'filename', then this is probably an error and we raise an `ValueError`.

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
    # check that the tasks make sense:
    same_target = task1['target'] == task2['target']
    same_type = task1['type'] == task2['type']
    if not same_target:  # different target, just stop
        return False
    if task1['target'] == 'screen':  # same targets are equal if same type
        return same_type
    elif task1['target'] == 'file':
        # check if they both give file name or just one of them
        same_file = False
        try:
            same_file = task1['filename'] == task2['filename']
        except KeyError:
            # if just one of them gives a file name, we will assume that we
            # will write to the same file if types are equal.
            same_file = same_type
        if same_file and not same_type:
            # different types writing to same file!
            msg = ['Two different task attempting to write to the same file:']
            msg.append('Task1: {}'.format(task1))
            msg.append('Task2: {}'.format(task2))
            raise ValueError('\n'.join(msg))
        return same_type
    else:
        msg = ['Did not understand output target:']
        msg.append('Task1: {}'.format(task1))
        msg.append('Task2: {}'.format(task2))
        raise ValueError('\n'.join(msg))


def create_output(system, settings):
    """Generate output tasks from settings and defaults.

    This method will return actual objects that can be added to the
    simulation. It uses `_get_output_tasks` to generate dictionaries
    for the output tasks which are here converted to objects using
    `create_output_task`.

    Parameters
    ----------
    system : object like `System` from `pyretis.core.system`.
        The system we are investigating in the simulation.
    settings : dict
        These are the settings for the simulation.
    default_output : list of dicts
        These defines the default outputs for a given simulation.

    Yields
    ------
    out : object like `OuputTask`
    """
    for out_task in _get_output_tasks(settings.get('output', []),
                                      default_output=[]):
        task = create_output_task(out_task, system, settings)
        if task is not None:
            yield task


def _get_output_tasks(output_settings, default_output=None):
    """Generate output tasks (dict representation) from settings.

    This method will generate output tasks from given settings and add
    default output settings. It will check to see if the given output
    settings can be used to update the default settings. Note that the
    returned list of output tasks are dicts and that the `create_output_task`
    method should be used to generate the output task objects.

    Parameters
    ----------
    output_settings : list of dicts
        These are user-specified output tasks.
    default_output : list of dicts
        These are default tasks.

    Returns
    -------
    output_tasks : list of dicts
        List of output tasks that can be added to the simulation.
        Note that the tasks should be created with `create_output_task`
        before they can be added.
    """
    output_tasks = []
    # First add default outputs:
    # we do not add if it has been turned off by the user
    if default_output is not None:
        for default in default_output:
            # check if this task is turned off:
            add = True
            for output in output_settings:
                if _task_dict_eq(default, output):  # found a similar task
                    add = output.get('use', True)
            if add:
                output_tasks.append(default)
    # Next, add user specified outputs, but check if we can update
    # already added defaults:
    for output in output_settings:
        add = output.get('use', True)
        update = []
        for i, task in enumerate(output_tasks):  # loop over the added
            if _task_dict_eq(output, task):  # True if found similar
                add = False
                update.append(i)  # will try to update task no. i
        if add:  # this is a completely new task, will add
            output_tasks.append(output)
        else:  # we should possibly update or not add it
            for i in update:
                output_tasks[i].update(output)  # just update dict
    return output_tasks


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

    Returns
    -------
    out : object like `FileWriter` from `pyretis.inout.txtinout`.
        This object can be used to write to files. It will typically be
        attached to a output task object (like `OutputTask`) as a writer.
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
        msg = ['Unknown type {} for target file'.format(task['type'])]
        msg += ['Ignoring task: {}'.format(task)]
        warnings.warn('\n'.join(msg))
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

    Returns
    -------
    out : object like `OutputTask` from `core.simulation.simulation_task`.
        This is the output task that can be added to a simulation.
    """
    writer = None
    if task['target'] == 'file':
        writer = _create_file_writer(task, system, settings)
    elif task['target'] == 'screen':
        if task['type'] == 'thermo':
            writer = get_predefined_table('energies')
    else:
        msg = ['Unknown task target: {}'.format(task['target'])]
        msg += ['Ignoring task: {}'.format(task)]
        warnings.warn('\n'.join(msg))
    if writer is not None:
        return OutputTask(writer, task['type'], task['target'],
                          when=task.get('when', None),
                          header=task.get('header', None))
    else:
        return None
