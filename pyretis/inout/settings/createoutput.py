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
import logging
import itertools
import os
import pprint
import json
# pyretis imports
from pyretis.inout.settings.common import check_settings
from pyretis.core.simulation.simulation_task import execute_now
from pyretis.inout.writers import (CrossFile, EnergyFile, OrderFile,
                                   PathEnsembleFile, TrajXYZ, TrajGRO,
                                   get_predefined_table)
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['OutputTask', 'create_output']


# Define the known output types:
_OUTPUT_TYPES = {'energy': {'target': 'file',
                            'writer': EnergyFile,
                            'result': 'thermo'},
                 'orderp': {'target': 'file',
                            'writer': OrderFile,
                            'result': 'orderp'},
                 'cross': {'target': 'file',
                           'writer': CrossFile,
                           'result': 'cross'},
                 'traj': {'target': 'file',
                          'writer': {'gro': TrajGRO, 'xyz': TrajXYZ},
                          'result': 'traj'},
                 'thermo-screen': {'target': 'screen',
                                   'writer': 'energies',
                                   'result': 'thermo'},
                 'pathensemble': {'target': 'file',
                                  'writer': PathEnsembleFile,
                                  'result': 'pathensemble'},
                 'pathensemble-screen': {'target': 'screen',
                                         'writer': 'path-stats',
                                         'result': 'pathensemble'},
                 'trialpath': {'target': 'files',
                               'writer': None,
                               'result': 'trialpath'}}

# Define the default outputs:
_DEFAULT_OUTPUT = {}
_DEFAULT_OUTPUT['md-nve'] = [{'type': 'energy',
                              'name': 'energy-file',
                              'when': {'every': 10},
                              'filename': 'energy.dat'},
                             {'type': 'traj',
                              'name': 'traj',
                              'when': {'every': 10},
                              'filename': 'traj.gro',
                              'format': 'gro',
                              'header': 'NVE simulation. Step: {}'},
                             {'type': 'thermo-screen',
                              'name': 'thermo-screen',
                              'when': {'every': 10}}]

_DEFAULT_OUTPUT['md-flux'] = [{'type': 'orderp',
                               'name': 'orderp',
                               'target': 'file',
                               'when': {'every': 10},
                               'filename': 'order.dat'},
                              {'type': 'energy',
                               'name': 'energy-file',
                               'target': 'file',
                               'when': {'every': 100},
                               'filename': 'energy.dat'},
                              {'type': 'cross',
                               'name': 'cross',
                               'when': {'every': 1},
                               'filename': 'cross.dat'},
                              {'type': 'traj',
                               'name': 'traj',
                               'format': 'gro',
                               'when': {'every': 10},
                               'filename': 'traj.gro',
                               'header': 'MDFLUX simulation. Step: {}'},
                              {'type': 'thermo-screen',
                               'name': 'thermo-screen',
                               'when': {'every': 10}}]

_DEFAULT_OUTPUT['tis'] = [{'type': 'pathensemble',
                           'name': 'pathensemble-file',
                           'when': {'every': 10},
                           'filename': 'pathensemble.dat'},
                          {'type': 'pathensemble-screen',
                           'name': 'pathensemble-screen',
                           'when': {'every': 10}},
                          {'type': 'trialpath',
                           'name': 'trialpath',
                           'when': {'every': 1},
                           'orderp': {'filename': 'orderp.dat',
                                      'when': {'every': 10},
                                      'freq': 10},
                           'energy': {'filename': 'energyp.dat',
                                      'when': {'every': 10},
                                      'freq': 10}}]


class OutputTask(object):
    """Class OutputTask(object) - Simulation output tasks.

    This class will handle a output task for a simulation. The
    output task may be something that should print to the screen or
    a file.

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
    header : string
        Some objects will have a specific header written each time we use
        the write routine. This is for instance used in the trajectory writer
        to display the current step for a written frame.
    extra : dict
        This dictionary contains some extra parameters that can be passed
        to the writers.
    """
    target = 'file'
    def __init__(self, name, result, writer, **kwargs):
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
        kwargs : dict
            This dictionary contains some extra parameters that can be passed
            to the writers. The following keywords are currently used:

            * `when`: dict. Determines if and when the task should be executed.
              Example: `{'every': 10}` will be executed at every 10th step.
            * `header`: string. Some objects will have a header written each
              time the we use the write routine. This is for instance used in
              the trajectory writer to display the current step for a written
              frame. The given `header` is assumed to contain one '{}' field
              so that we can insert the current step number.
            * `extra`: dict. Contains extra settings for the writer. For the
              trajectory writer this setting can be used to turn on writing
              of velocities, i.e. `kwargs['extra'] = {'write_vel': True}`.
        """
        self.name = name
        self.result = result
        self.writer = writer
        self.when = kwargs.get('when', None)
        self.header = kwargs.get('header', None)
        self.extra = kwargs.get('extra', {})
        if self.extra is None:
            self.extra = {}

    def __new__(cls, name, result, writer, **kwargs):
        """Check a writer is given in the input.

        Parameters
        ----------
        name : string
            This string identifies the task, it can for instance be used
            to reference the dictionary used to create the writer.
        result : string
            This string defines the result we are going to output.
        writer : object like `Writer` from `pyretis.inout.writers`
            This object will handle the actual writing of the result.
        when : dict, optional
            Determines if the task should be executed.
        header : string, optional
            Some object will have a header written each time the we use the
            write routine. This is for instance used in the trajectory writer
            to display the current step for a written frame. It is assumed to
            contain one '{}' field so that we can insert the current step
            number.
        kwargs : dict
            This dictionary contains some extra parameters that can be passed
            to the writers.

        Returns
        -------
        out : A `OutputTask` object or None
            If no writer is given, we simply return a None.
        """
        if writer is None:
            return None
        else:
            return super(OutputTask, cls).__new__(cls, name, result, writer,
                                                  **kwargs)

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
        if self.result == 'traj':
            if self.header is not None:
                try:
                    header = self.header.format(step['step'])
                    self.extra['header'] = header
                except IndexError:
                    # Something went wrong in the format. Forget that we
                    # every used that header and nuke it from self.extra
                    # if it's present.
                    msg = ['Could not use specified header in trajectory.']
                    msg += ['Ignoring']
                    msgtxt = '\n'.join(msg)
                    logger.warning(msgtxt)
                    self.header = None
                    try:
                        del self.extra['header']
                    except KeyError:
                        pass
            return self.writer.generate_output(result, **self.extra)
        else:
            return self.writer.generate_output(step['step'], result)

    def __str__(self):
        """Output some info about this output task."""
        msg = ['Output task: {} ({})'.format(self.name, self.target)]
        msg += ['* Result: {}'.format(self.result)]
        msg += ['* Writer: {}'.format(self.writer)]
        msg += ['* When: {}'.format(self.when)]
        return '\n'.join(msg)


class OutputTaskScreen(OutputTask):
    """Class OutputTaskScreen(object) - Simulation output tasks.

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
    header : string
        Some objects will have a specific header written each time we use
        the write routine. This is for instance used in the trajectory writer
        to display the current step for a written frame.
    extra : dict
        This dictionary contains some extra parameters that can be passed
        to the writers.
    """
    target = 'screen'
    def __init__(self, name, result, writer, when=None):
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
        when : dict, optional
            Determines if the task should be executed.
        header : string, optional
            Some object will have a header written each time the we use the
            write routine. This is for instance used in the trajectory writer
            to display the current step for a written frame. It is assumed to
            contain one '{}' field so that we can insert the current step
            number.
        extra : dict
            This dictionary contains some extra parameters that can be passed
            to the writers.
        """
        super(OutputTaskScreen, self).__init__(name, result, writer,
                                               when=when)
        self.print_header = True

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


def check_user_output_task(task, def_tasks):
    """Add a user-specified output task.

    This method will check the user specified settings for an output task
    and check if it can be added or not.

    Parameters
    ----------
    task : dict
        A dict defining the task we want to add.
    def_tasks : list of dicts
        A list of the tasks that have already been defined.

    Returns
    -------
    out[0] : boolean
        True if the task can be added.
    out[1] : list of strings
        If a task can not be added, this list will contain some information
        on why not.
    """
    msg = []
    add = True
    task_names = set([taski['name'] for taski in def_tasks])
    task_files = set([taski.get('filename', None) for taski in def_tasks])
    if 'type' not in task:
        msg += ['Task does not define a "type"']
        add = False
    else:
        if task['type'] not in _OUTPUT_TYPES:
            msg += ['Unknown type "{}" specified'.format(task['type'])]
            keys = [key for key in _OUTPUT_TYPES]
            msg += ['Type should be one of:\n{}'.format(keys)]
            add = False
        else:
            req = ['name']
            if _OUTPUT_TYPES[task['type']]['target'] == 'file':
                req += ['filename']
            result, not_found = check_settings(task, req)
            if not result:
                msg += ['Missing output setting(s): {}'.format(not_found)]
                add = False
            else:
                if 'filename' in task and task['filename'] in task_files:
                    errtxt = 'A task using the file "{}" is already defined!'
                    msg += [errtxt.format(task['filename'])]
                    add = False
                if task['name'] in task_names:
                    errtxt = 'A task with the name "{}" is already defined!'
                    msg += [errtxt.format(task['name'])]
                    add = False
    return add, msg


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
    task_list = []
    for task in itertools.chain(_DEFAULT_OUTPUT.get(settings['task'], []),
                                settings.get('output-add', [])):
        add, msg = check_user_output_task(task, task_list)
        if not add:
            leng = len('Ignoring task:') + 1
            pretty = pprint.pformat(task, width=79-leng)
            pretty = pretty.replace('\n', '\n' + ' ' * leng)
            msg += ['Ignoring task: {}'.format(pretty)]
            msgtxt = '\n'.join(msg)
            logger.warning(msgtxt)
        else:
            task_list.append(task)

    for task in settings.get('output-modify', []):
        match = False
        for taski in task_list:
            if task['name'] == taski['name']:
                msgtxt = 'Updating task "{}"'.format(task['name'])
                logger.info(msgtxt)
                taski.update(task)
                match = True
                break
        if not match:
            msgtxt = 'No match for output-modify setting: {}'
            msgtxt = msgtxt.format(task)
            logger.warning(msgtxt)

    for task in task_list:
        if task.get('use', True):
            out_task = create_output_task(task, settings)
            if out_task is not None:
                msgtxt = 'Output task created: {}'.format(out_task)
                logger.info(msgtxt)
                yield out_task


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
    out : object like `Writer` from `pyretis.inout.writers`.
        This object can be used to write to files. It will typically be
        attached to a output task object (like `OutputTask`) as a writer.
    """
    if task['type'] == 'traj':
        writer = _OUTPUT_TYPES[task['type']]['writer'][task['format']]
        return writer(settings['units'])
    else:
        writer = _OUTPUT_TYPES[task['type']]['writer']
        return writer()


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
    target = _OUTPUT_TYPES[task['type']]['target']
    writer = None
    when = task.get('when', None)
    header = task.get('header', None)
    extra = task.get('extra', None)
    result = _OUTPUT_TYPES[task['type']]['result']
    if target == 'file':
        writer = _create_file_writer(task, settings)
        return OutputTask(task['name'], result, writer,
                          when=when, header=header, extra=extra)
    elif target == 'screen':
        writer = get_predefined_table(_OUTPUT_TYPES[task['type']]['writer'])
        return OutputTaskScreen(task['name'], result, writer,
                                when=when)
    else:
        return None


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
