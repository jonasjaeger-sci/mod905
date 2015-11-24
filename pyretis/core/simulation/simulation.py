# -*- coding: utf-8 -*-
"""Definitions of generic simulation objects.

This module defines the generic simulation object. This is the base
class for all other simulations.

Important classes and functions defined here

- Simulation: Object defining a generic simulation.
"""
from __future__ import absolute_import
from .simulation_task import SimulationTask
import warnings


__all__ = ['Simulation']


class Simulation(object):
    """This class defines a generic simulation.

    Attributes
    ----------
    cycle : dict of ints
        This dict stores information about the number of cycles. The keywords
        are 'end' which represents the cycle number where the simulation
        should end, 'step' which is the current cycle number, 'start' which
        is the cycle number we started at, 'stepno' which is the number
        cycles we have performed to arrive at cycle no 'step'. 'stepno' might
        be different from 'step' since 'start' might be != 0.
    task : dict
        Each dich contain the tasks to be done. A task is represented by a
        object of type `SimulationTask` from `.simulation_task` with some
        additional settings on how to store the output and when to execute
        the task. Note that the actual execution of the task in controlled in
        the object. The keywords are:

            - `func` which is the object
            - `args` which stores the arguments for the function
            - `kwargs` which store the keyword arguments for the function
            - `when` which stores when the task should be executed
            - `first` which is a boolean which determines if the task should
              be executed on the initial step, i.e. before the full
              simulation starts
            - `result` which is used to label the result. This is used for
              output.
    first_step : boolean
        True if the first step has not been executed yet.
    system : object like `System` from `pyretis.core.system`
        This is the system the simulation will act on.
    """

    def __init__(self, endcycle=0, startcycle=0):
        """Initialization of the simulation.

        Parameters
        ----------
        startcycle : int, optional.
            The cycle we start the simulation on, can be useful if
            restarting.
        endcycle : int, optional.
            This number represents the cycle number where the simulation
            should end. It some simulations (e.g. MD) this would be the number
            of steps to perform, in other simulations this could be the
            minimum or maximum number of cycles to perform
        """
        self.cycle = {'step': startcycle, 'end': endcycle,
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

        In this object, the simulation is done if the current step number
        is larger than the end cycle. Note that the number of steps
        performed is dependent of the value of self.cycle['start'].

        Returns
        -------
        out : True if simulation is finished, false otherwise.
        """
        return self.cycle['step'] >= self.cycle['end']

    def step(self):
        """Execute a simulation step.

        Here, the tasks in `self.task` will be executed sequentially.

        Returns
        -------
        out : dict
            This dict contains the results of the defined tasks. Here, this
            dict is obtained as the return value from self.execute_tasks().

        Note
        ----
        This function will have ``side effects`` and update/change
        the state of other attached variables such as the system or other
        variables that are not explicitly shown. This is intended. In order
        to see what actually is happening when running `step()`, investigate
        the tasks defined in self.task.
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
                results[task.get_result_label()] = task.execute(self.cycle)
        return results

    def add_task(self, task, position=None):
        """Add a new simulation task.

        A task can still be added manually by simply appending to `self.task`.
        This method will however do some checks so that the task added can
        be executed.

        Parameters
        ----------
        task : dict
            A dict defining the task. The recognized keys are 'func'
            'args', 'kwargs', 'first', 'when', 'result' which correspond
            to attributes of a (new) `SimulationTask` object. See this object
            for a definition of the different attributes.
        position : int
            Can be used to placed the task at a specific position.

        Note
        ----
        SimulationTask will do some tests on the consistency of the keys
        'func', 'args' and 'kwargs'. If this is not consistent, it will
        throw an AssertionError.

        See Also
        --------
        `SimulationTask` object in `pyretis.core.simulation.simulation_task`.
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
            msg = 'Could not add task: {}'
            warnings.warn(msg.format(task))
            return False

    def run(self):
        """Run a simulation.

        The intended usage is for simulations where all tasks have
        been defined in `self.tasks`.

        Note
        ----
        This method will simply run the tasks. In general this is probably
        too generic for the simulation you want. It is perhaps best to
        modify the `run` method of your simulation object to tailor the
        simulation.

        Yields
        ------
        out : dict
            This dict contains the results from the simulation.
        """
        while not self.is_finished():
            yield self.step()

    def __str__(self):
        """Just a small function to return some info about the simulation."""
        ntask = len(self.task)
        mtask = 'task' if ntask == 1 else 'tasks'
        msg = ['General simulation with {} {}.'.format(ntask, mtask)]
        return '\n'.join(msg)
