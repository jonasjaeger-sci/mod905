# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""Definitions of generic simulation objects.

This module defines the generic simulation object. This is the base
class for all other simulations.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Simulation
    Object defining a generic simulation.
"""
from __future__ import absolute_import
import logging
from .simulation_task import SimulationTask
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['Simulation']


class Simulation(object):
    """This class defines a generic simulation.

    Attributes
    ----------
    cycle : dict of integers
        This dictionary stores information about the number of cycles.
        The keywords are:

        * `end`: Represents the cycle number where the simulation
          should end.
        * `step`: The current cycle number.
        * `start`: The cycle number we started at.
        * `stepno`: The number of cycles we have performed to arrive at
          cycle number given by `cycle['step']`.

        Note that `cycle['stepno']` might be different from
        `cycle['step']` since `cycle['start']` might be != 0.
    task : list of objects like `SimulationTask` from `.simulation_task`
        This is the list of simulation tasks to execute.
    first_step : boolean
        True if the first step has not been executed yet.
    system : object like `System` from `pyretis.core.system`
        This is the system the simulation will act on.
    """

    def __init__(self, steps=0, startcycle=0):
        """Initialization of the simulation.

        Parameters
        ----------
        steps : int, optional.
            The number of simulation steps to perform.
        startcycle : int, optional.
            The cycle we start the simulation on, can be useful if
            restarting.
        """
        self.cycle = {'step': startcycle, 'end': startcycle + steps,
                      'start': startcycle, 'stepno': 0}
        self.task = []
        self.first_step = True
        self.system = None

    def extend_cycles(self, steps):
        """Extend a simulation with the given number of steps.

        Parameters
        ----------
        steps :  int
            The number of steps to extend the simulation with.

        Returns
        -------
        out : None
            Returns `None` but modifies `self.cycle`.
        """
        self.cycle['start'] = self.cycle['end']
        self.cycle['end'] += steps

    def is_finished(self):
        """Determine if the simulation is finished.

        In this object, the simulation is done if the current step
        number is larger than the end cycle. Note that the number of
        steps performed is dependent of the value of
        `self.cycle['start']`.

        Returns
        -------
        out : True if simulation is finished, False otherwise.
        """
        return self.cycle['step'] >= self.cycle['end']

    def step(self):
        """Execute a simulation step.

        Here, the tasks in `self.task` will be executed sequentially.

        Returns
        -------
        out : dict
            This dictionary contains the results of the defined tasks.
            It is obtained as the return value from
            `self.execute_tasks()`.

        Note
        ----
        This function will have 'side effects' and update/change
        the state of other attached variables such as the system or
        other variables that are not explicitly shown. This is intended.
        In order to see what actually is happening when running
        `step()`, investigate the tasks defined in `self.task`.
        """
        if not self.first_step:
            self.cycle['step'] += 1
            self.cycle['stepno'] += 1
        results = self.execute_tasks()
        if self.first_step:
            self.first_step = False
        return results

    def execute_tasks(self):
        """Execute all the tasks in sequential order.

        Returns
        -------
        results : dict
            The results from the different tasks (if any).
        first : boolean
            This is just to do the initial tasks, i.e. tasks that should
            be done before the simulation starts.
        """
        results = {'cycle': self.cycle}
        for task in self.task:
            if not self.first_step or task.run_first():
                resi = task.execute(self.cycle)
                if task.result is not None:
                    results[task.result] = resi
        results['traj'] = self.system
        return results

    def add_task(self, task, position=None):
        """Add a new simulation task.

        A task can still be added manually by simply appending to
        `self.task`. This function will however do some checks so that
        the task added can be executed.

        Parameters
        ----------
        task : dict
            A dict defining the task. A task is represented by a
            object of type `SimulationTask` from `.simulation_task`
            with some additional settings on how to store the output
            and when to execute the task. Note that the actual
            execution of the task in controlled in the object.
            The keywords are:

            * `func`: A function to execute.
            * `args` which stores the arguments for the function.
            * `kwargs` which store the keyword arguments for the
              function.
            * `when` which stores when the task should be executed.
            * `first` which is a boolean which determines if the task
              should be executed on the initial step, i.e. before the
              full simulation starts.
            * `result` which is used to label the result. This is used
              for output.
        position : int
            Can be used to placed the task at a specific position.

        Note
        ----
        `SimulationTask` will do some tests on the consistency of the
        keys 'func', 'args' and 'kwargs'. If this is not consistent,
        it will raise an AssertionError.

        See Also
        --------
        `SimulationTask` object in `.simulation_task`.
        """
        try:
            # create task in an explicit way - use 'get'.
            new_task = SimulationTask(task['func'],
                                      args=task.get('args', None),
                                      kwargs=task.get('kwargs', None),
                                      when=task.get('when', None),
                                      result=task.get('result', None),
                                      first=task.get('first', False))
            if position is None:
                self.task.append(new_task)
            else:
                self.task.insert(position, new_task)
            return True
        except AssertionError:
            msg = 'Could not add task: {}'.format(task)
            logger.warning(msg)
            return False

    def run(self, output=None):
        """Run a simulation.

        The intended usage is for simulations where all tasks have
        been defined in `self.tasks`.

        Note
        ----
        This function will simply run the tasks. In general this is
        probably too generic for the simulation you want. It is perhaps
        best to modify the `run` function of your simulation object to
        tailor your simulation.

        Parameters
        ----------
        output : list, objects like `OutputTask` from `pyretis.inout.settings`.
            If outputs are given, they will be executed here.

        Yields
        ------
        out : dict
            This dictionary contains the results from the simulation.
        """
        if output is None:
            output = []
        while not self.is_finished():
            result = self.step()
            for task in output:
                task.output(result)
            yield result

    def __str__(self):
        """Just a small function to return some info about the simulation."""
        ntask = len(self.task)
        mtask = 'task' if ntask == 1 else 'tasks'
        msg = ['General simulation with {} {}.'.format(ntask, mtask)]
        return '\n'.join(msg)
