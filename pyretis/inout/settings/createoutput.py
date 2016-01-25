# -*- coding: utf-8 -*-
"""Module for handling output from simulations.

This module defines functions and classes for handling the output from
simulations.

Important functions defined here:

- create_output: Function that sets up output tasks from a dictionary of
  settings.

Important classes defined here:

- OutputTask: A class for handling output tasks.
"""
from __future__ import print_function
import itertools
import logging
import os
import re
import json
# pyretis imports
from pyretis.core.simulation.simulation_task import execute_now
from pyretis.inout.fileio import (CrossFile, EnergyFile, OrderFile,
                                  PathEnsembleFile, create_traj_writer)
from pyretis.inout.txtinout import get_predefined_table
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['OutputTask', 'create_output']


WRITERS = {'screen': {'thermo': 'energies',
                      'pathensemble': 'path-stats'},
           'file': {'orderp': OrderFile,
                    'thermo': EnergyFile,
                    'cross': CrossFile,
                    'traj': create_traj_writer,
                    'pathensemble': PathEnsembleFile}}


_DEFAULT_OUTPUT = {}
_DEFAULT_OUTPUT['md-nve'] = [{'type': 'thermo', 'target': 'file',
                              'when': {'every': 10},
                              'filename': 'energy.dat'},
                             {'type': 'traj', 'target': 'file',
                              'when': {'every': 10},
                              'filename': 'traj.gro', 'format': 'gro',
                              'header': 'NVE simulation. Step: {}'},
                             {'type': 'thermo', 'target': 'screen',
                              'when': {'every': 10}}]
_DEFAULT_OUTPUT['md-flux'] = [{'type': 'orderp', 'target': 'file',
                               'when': {'every': 10},
                               'filename': 'order.dat'},
                              {'type': 'thermo', 'target': 'file',
                               'when': {'every': 100},
                               'filename': 'energy.dat'},
                              {'type': 'cross', 'target': 'file',
                               'when': {'every': 1},
                               'filename': 'cross.dat'},
                              {'type': 'traj', 'target': 'file',
                               'format': 'gro', 'when': {'every': 10},
                               'filename': 'traj.gro',
                               'header': 'MDFLUX simulation. Step: {}'},
                              {'type': 'thermo', 'target': 'screen',
                               'when': {'every': 10}}]
_DEFAULT_OUTPUT['tis'] = [{'type': 'pathensemble', 'target': 'file',
                           'when': {'every': 10},
                           'filename': 'pathensemble.dat'},
                          {'type': 'pathensemble', 'target': 'screen',
                           'when': {'every': 10}}]


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
        Some objects will have a specific header written each time we use
        the write routine. This is for instance used in the trajectory writer
        to display the current step for a written frame.
    """

    def __init__(self, writer, output_type, target, when=None,
                 header=None, kwargs=None):
        """Initiate the OutputTask object.

        Parameters
        ----------
        writer : object
            This object will handle the actual writing of the result.
        output_type : string
            This string defines the output type. It is used to get the
            output from the simulation.
        target : string
            This determines what kind out output target we have in mind,
            'file' and 'screen' are handled slightly differently.
        when : dict, optional
            Determines if the task should be executed.
        header : string, optional
            Some object will have a header written each time the we use the
            write routine. This is for instance used in the trajectory writer
            to display the current step for a written frame. It is assumed to
            contain one '{}' field so that we can insert the current step
            number.
        """
        self.output_type = output_type
        self.writer = writer  # output type can be derived from writer?
        self.target = target
        self.when = when
        self.header = header
        if kwargs is None:
            self.kwargs = {}
        else:
            self.kwargs = kwargs

    def output(self, simulation_result):
        """Output a task given results from a simulation.

        This will output the task using the result found in the
        `simulation_result` which should be the dictionary returned from a
        simulation object (e.g. object like `Simulation` from
        `pyretis.core.simulation.simulation`) after a step. For trajectories,
        we expect that `simulation_result` contain the key `traj` so we can
        pass it to the trajectory writer.

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
        if self.output_type not in simulation_result:
            # This probably just means that the required result was not
            # calculated at this step.
            return False
        result = simulation_result[self.output_type]
        if self.target == 'screen':
            out = self.writer.write(step['step'], result,
                                    first_step=(step['stepno'] == 0))
            print(out)
            return True
        else:
            if self.output_type == 'traj':
                if self.header is not None:
                    header = self.header.format(step['step'])
                    self.kwargs['header'] = header
                return self.writer.write(result, **self.kwargs)
            else:
                return self.writer.write(step['step'], result)

    def close(self):
        """Function to explicitly close a file if needed."""
        if self.target == 'file':
            self.writer.close()

    def __str__(self):
        """Output some info about this output task."""
        msg = ['Output task: {}'.format(self.output_type)]
        msg += ['* Target: {}'.format(self.target)]
        msg += ['* Writer: {}'.format(self.writer)]
        msg += ['* When: {}'.format(self.when)]
        return '\n'.join(msg)


def task_dict_equal(task1, task2):
    """Check if two given tasks are equak by comparing their settings.

    This function will determine if two tasks are identical. The test for
    similarity depends on the target of the two tasks. If the target is
    `screen` then the two tasks are equal if and only if their type is also
    identical. If the target is `file` then the tasks are equal if their
    file name is the same.

    In addition we have the complicating fact that not all settings need
    to be set and here, the matching is greedy for settings not defined.
    This is to make it easy to update tasks, especially the default
    tasks.
    """
    match_type = task1['type'] == task2['type']
    target1 = task1.get('target', '(.+)')
    target2 = task2.get('target', '(.+)')
    match_target = (re.match(target1, target2) is not None or
                    re.match(target2, target1) is not None)
    file1 = task1.get('filename', '(.+)')
    file2 = task2.get('filename', '(.+)')
    match_filename = (re.match(file1, file2) is not None or
                      re.match(file2, file1) is not None)
    # now, two tasks are equal if:
    # 1) match_type is True
    # 2) match_target is True
    # 3) In addition, for files if the file_name match
    equal = match_type and match_target
    if match_target and 'file' in (target1, target2):
        equal = equal and match_filename
    return equal


def task_dict_ok(task):
    """Check if a task has enough settings given.

    Parameters
    ----------
    task : dict
        The settings for creating a task

    Returns
    -------
    out : boolean
        True if a task can be created from the settings.
    """
    task_ok = 'type' in task and 'target' in task
    if task_ok:
        if task['target'] == 'file':
            task_ok = 'filename' in task
    return task_ok


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
    defaults = _DEFAULT_OUTPUT.get(settings['task'], [])
    from_settings = settings.get('output', [])
    task_list = []
    for task in itertools.chain(defaults, from_settings):
        to_update = []
        for i, task1 in enumerate(task_list):
            if task_dict_equal(task1, task):
                to_update.append(i)
        if len(to_update) > 0:
            for i in to_update:
                task_list[i].update(task)
        else:
            if task_dict_ok(task):
                task_list.append(task)
    for out_task in task_list:
        if out_task.get('use', True):
            task = create_output_task(out_task, settings)
            if task is not None:
                msgtxt = 'Output task created: {}'.format(task)
                logger.info(msgtxt)
                yield task


def _create_file_writer(task, settings):
    """This will create an object for writing to files.

    Parameters
    ----------
    task : dict
        This dictionary describes the task.
    settings : dict
        These are the settings used for setting up the simulation.
        Some of these settings might be useful for creating the output tasks.

    Returns
    -------
    out : object like `FileWriter` from `pyretis.inout.fileio`.
        This object can be used to write to files. It will typically be
        attached to a output task object (like `OutputTask`) as a writer.
    """
    dirname = settings.get('output-dir', None)
    if dirname is not None:
        filename = os.path.join(dirname, task['filename'])
    else:
        filename = task['filename']
    oldfile = task.get('oldfile', 'overwrite')
    if task['type'] == 'traj':
        return create_traj_writer(filename, task['format'], settings['units'],
                                  oldfile=oldfile)
    elif task['type'] == 'pathensemble':
        return PathEnsembleFile(filename,
                                settings['ensemble'],
                                settings['interfaces'],
                                mode='w',
                                oldfile=oldfile)
    else:
        if task['type'] in WRITERS['file']:
            writer = WRITERS['file'][task['type']]
            return writer(filename, mode='w', oldfile=oldfile)
        else:
            msg = ['Unknown type "{}" for target "file"'.format(task['type'])]
            msg += ['Ignoring task: {}'.format(task)]
            msgtxt = '\n'.join(msg)
            logger.warning(msgtxt)
            return None


def create_output_task(task, settings):
    """Create object for a output task.

    This function will create an object for a given output task.
    It will make use of some of the predefined output possibilities
    defined in `pyretis.inout`

    Parameters
    ----------
    task : dict
        This dict describes the task.
    settings : dict
        These are the settings used for setting up the simulation.
        Some of these settings might be useful for creating the output tasks.

    Returns
    -------
    out : object like `OutputTask` from `core.simulation.simulation_task`.
        This is the output task that can be added to a simulation.
    """
    writer = None
    msgtxt = None
    if task['target'] == 'file':
        writer = _create_file_writer(task, settings)
    elif task['target'] == 'screen':
        if task['type'] in WRITERS['screen']:
            writer = get_predefined_table(WRITERS['screen'][task['type']])
        else:
            msg = ['Unknown task type "{}" for screen'.format(task['type'])]
            msg += ['Ignoring task: {}'.format(task)]
            msgtxt = '\n'.join(msg)
    else:
        msg = ['Unknown task target: {}'.format(task['target'])]
        msg += ['Ignoring task: {}'.format(task)]
        msgtxt = '\n'.join(msg)
    if writer is None:
        if msgtxt:
            logger.warning(msgtxt)
        return None
    else:
        return OutputTask(writer,
                          task['type'],
                          task['target'],
                          when=task.get('when', None),
                          header=task.get('header', None),
                          kwargs=task.get('kwargs', None))


def store_settings_as_json(settings, outfile, path=None):
    """Write simulation settings to a json file.

    This will just write a dictionary to a file in a way such that
    it can be imported into another file.

    Parameters
    ----------
    settings : dict
        The dictionary to write
    outfile : string
        The file to create
    path : string, optional
        A path which determines where the file should be written.

    Note
    ----
    This will currently fail for objects.
    """
    if path is not None:
        filename = os.path.join(path, outfile)
    else:
        filename = outfile
    with open(filename, 'w') as fileh:
        json.dump(settings, fileh, indent=4)


def read_json_file(inputfile):
    """Read simulation settings from a pure json file.

    This method will read simulation settings from a json file and
    return the data stored in a file as a dictionary.

    Parameters
    ----------
    inputfile : string
        The file to open and decode.

    Returns
    -------
    out : dict
        The decoded json file.
    """
    data = None
    with open(inputfile) as json_data:
        data = json.load(json_data)
    return data
