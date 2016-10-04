# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
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
from __future__ import print_function
import logging
# pyretis imports
from pyretis.inout.common import add_dirname
from pyretis.core.simulation.simulation_task import execute_now
from pyretis.inout.writers import get_writer, FileIO
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['OutputTask', 'create_output']


# Define the known output types:
_OUTPUT_TYPES = {'energy': {'target': 'file',
                            'result': 'thermo',
                            'when': 'energy-file',
                            'writer': 'energy'},
                 'orderp': {'target': 'file',
                            'result': 'orderp',
                            'when': 'order-file',
                            'writer': 'order'},
                 'cross': {'target': 'file',
                           'result': 'cross',
                           'when': 'cross-file',
                           'writer': 'cross'},
                 'traj-gro': {'target': 'file',
                              'result': 'traj',
                              'when': 'trajectory-file',
                              'writer': 'trajgro'},
                 'traj-xyz': {'target': 'file',
                              'result': 'traj',
                              'when': 'trajectory-file',
                              'writer': 'trajxyz'},
                 'thermo-screen': {'target': 'screen',
                                   'result': 'thermo',
                                   'when': 'energy-screen',
                                   'writer': 'thermotable'},
                 'pathensemble': {'target': 'file',
                                  'result': 'pathensemble',
                                  'when': 'pathensemble-file',
                                  'writer': 'pathensemble'},
                 'pathensemble-screen': {'target': 'screen',
                                         'result': 'pathensemble',
                                         'when': 'pathensemble-screen',
                                         'writer': 'pathtable'}}
# Define the outputs for simulations.
_DEFAULT_OUTPUT = {}
_DEFAULT_OUTPUT['md-nve'] = [{'type': 'energy',
                              'name': 'nve-energy-file',
                              'when': {'every': 10},
                              'filename': 'energy.dat'},
                             {'type': 'traj-gro',
                              'name': 'nve-traj-file',
                              'when': {'every': 10},
                              'filename': 'traj.gro',
                              'settings': {'system': ('units',),
                                           'output': ('write_vel',)},
                              'header': 'NVE simulation. Step: {}'},
                             {'type': 'thermo-screen',
                              'name': 'nve-thermo-screen',
                              'when': {'every': 10}}]

_DEFAULT_OUTPUT['md-flux'] = [{'type': 'orderp',
                               'target': 'file',
                               'filename': 'order.dat'},
                              {'type': 'energy',
                               'target': 'file',
                               'filename': 'energy.dat'},
                              {'type': 'cross',
                               'filename': 'cross.dat'},
                              {'type': 'traj-gro',
                               'filename': 'traj.gro',
                               'header': 'MDFLUX simulation. Step: {}'},
                              {'type': 'thermo-screen'}]

_DEFAULT_OUTPUT['tis-single'] = [{'type': 'pathensemble',
                                  'filename': 'pathensemble.dat'},
                                 {'type': 'pathensemble-screen'}]

_DEFAULT_OUTPUT['retis'] = [{'type': 'pathensemble',
                             'filename': 'pathensemble.dat'}]


class OutputTask(object):
    """Class OutputTask(object) - Simulation output tasks.

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

    def __init__(self, name, result, writer, when, header=None):
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
        header: string.
            Some objects will have a header written each time the we
            use the write routine. This is for instance used in the
            trajectory writer to display the current step for a written
            frame. The given `header` is assumed to contain one '{}'
            field so that we can insert the current step number.
        """
        self.name = name
        self.result = result
        self.writer = writer
        self.when = when
        self.header = header

    @classmethod
    def task_from_settings(cls, task, settings):
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
        out = _OUTPUT_TYPES[task['type']]
        writer_settings = {}
        req_settings = task.get('settings', {})  # required settings
        for sec in req_settings:
            for key in req_settings[sec]:
                writer_settings[key] = settings[sec][key]
        writer = get_writer(out['writer'], settings=writer_settings)
        when = {'every': settings['output'][out['when']]}
        target = out['target']
        if target == 'file':
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
                                  out['result'],
                                  writer,
                                  when,
                                  filename,
                                  old,
                                  header=task.get('header', None))
        elif target == 'screen':
            return OutputTaskScreen(task['name'],
                                    out['result'],
                                    writer,
                                    when)
        else:
            msg = 'Unknown target "{}" ignored!'.format(target)
            logger.warning(msg)
            return None

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
    """Class OutputTaskScreen(object) - Simulation output tasks.

    This class will handle a output task for a simulation to the screen.
    Note the different handling of the header here -> it is assumed
    that the writer defines the header and this is the one we will use.

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
        super(OutputTaskScreen, self).__init__(name, result, writer,
                                               when, header=None)
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


class OutputTaskFile(OutputTask):
    """Class OutputTaskFile(object) - Simulation output tasks.

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
    header : string
        Some objects will have a specific header written each time we
        use the write routine. This is for instance used in the
        trajectory writer to display the current step for a written
        frame.
    """
    target = 'file'

    def __init__(self, name, result, writer, when, filename, backup,
                 header=None):
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
            Determines how we should treat old files. Valid strings
            are given in the
        header: string.
            Some objects will have a header written each time the we
            use the write routine. This is for instance used in the
            trajectory writer to display the current step.
            * `oldfile` : string. Determines if we should
              overwrite/backup/append to old files.
        """
        super(OutputTaskFile, self).__init__(name, result, writer, when,
                                             header=header)
        self.print_header = True
        self.fileh = FileIO(filename, oldfile=backup)
        if self.writer.header is not None:
            self.fileh.write(self.writer.header)

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
        if self.result == 'traj':
            header = None
            if self.header is not None:
                try:
                    header = self.header.format(step['step'])
                except IndexError:
                    # Something went wrong in the format. To save us
                    # some trouble on the next pass, we just forget
                    # about it.
                    msg = ['Could not use specified header in trajectory.']
                    msg += ['Ignoring']
                    msgtxt = '\n'.join(msg)
                    logger.warning(msgtxt)
                    self.header = None
            for lines in self.writer.generate_output(result, header=header):
                self.fileh.write(lines)
        else:
            for lines in self.writer.generate_output(step['step'], result):
                self.fileh.write(lines)
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
    for task in _DEFAULT_OUTPUT.get(sim_task, []):
        out_task = OutputTask.task_from_settings(task, settings)
        if out_task is not None:
            msgtxt = 'Output task created: {}'.format(out_task)
            logger.debug(msgtxt)
            yield out_task
