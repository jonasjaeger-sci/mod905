# -*- coding: utf-8 -*-
"""Definitions of simulation objects."""
from __future__ import absolute_import
import numpy as np
import collections
import inspect
import warnings
from retis.core.particlefunctions import calculate_thermo
from retis.core.integrators import create_integrator
from retis.core.path import check_crossing


__all__ = ['Simulation', 'UmbrellaWindowSimulation', 'SimulationNVE',
           'create_simulation']


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
        True if all required settings are persent, False otherwise.
    """
    result = True
    for setting in required:
        if setting not in settings:
            warnings.warn('Setting `{}` not found!'.format(setting))
            result = False
    return result


def create_simulation(settings, simulation_type='nve'):
    """
    This method will set up some common simulation types.
    It is meant as a helper function to automate some very common set-up
    tasks

    Parameter
    ---------
    settings : dict
        This dictionary contains the settings for the simulation.
    simulation_type : string
        This selects what kind of simulation we shall be doing

    Returns
    -------
    out : object that represents the simulation.
        This object will correspond to the selected simulation type.
    """
    simulation_type = simulation_type.lower()
    sim = None
    if simulation_type == 'nve':
        # this will set up a MD NVE simulation.
        required = ['system', 'endcycle']
        if not _check_settings(settings, required):
            return sim
        intg = create_integrator(settings.get('integrator', None),
                                 simulation_type)
        sim = SimulationNVE(settings['system'], intg,
                            endcycle=settings['endcycle'],
                            startcycle=settings.get('startcycle', 0))
    elif simulation_type == 'md-flux':
        required = ['system', 'endcycle', 'integrator', 'interfaces',
                    'orderparameter']
        if not _check_settings(settings, required):
            return sim
        intg = create_integrator(settings.get('integrator', None),
                                 simulation_type)
        sim = SimulationMdFlux(settings['system'], intg,
                               settings['interfaces'],
                               settings['orderparameter'],
                               endcycle=settings['endcycle'],
                               startcycle=settings.get('startcycle', 0))
    elif simulation_type == 'tis':
        # this will set up a TIS simulation
        warnings.warn('Simulation TIS not yet implemented')
    elif simulation_type == 'retis':
        warnings.warn('Simulation reTIS not yet implemented')
    else:
        warnings.warn('Unknown simulation {}'.format(simulation_type))
    return sim


def _do_task(task, stepnumber, currentstep):
    """
    This is a helper function for executing a task.
    It is used by the simulation class when iterating over the different
    tasks defined for the simulation.

    Parameters
    ----------
    task : dict
        This is a representation of the task to perform, it contains
        the keyword 'func' and it may contain keyword 'args', 'kwargs' and
        'extra'. task['func'] defines the function (i.e. it is assumed to be
        callable) to execute while task['args'] and task['kwargs'] are the
        optional arguments and keyword arguments to pass to the function
        defined in task['func'].
        task['extra'] can be used to execute a task at certain steps or at
        certain intervals.
    stepnumber : int
        The number of steps the simulation has done since it started.
    currentstep : int
        The current stepnumber of the simulation.

    Raises
    ------
    None, but will issue a warning if task['func'] is not callable.

    Returns
    -------
    out : The result, if any, of executing the task. The return value is
        defined in the function defining the task.
    """
    func = task['func']
    if not callable(func):
        msg = 'Task is not callable! Will not do: {}'.format(task)
        warnings.warn(msg)
        return None
    args = task.get('args', None)
    kwargs = task.get('kwargs', None)
    extra = task.get('extra', None)
    execute_task = True
    if extra:
        if 'every' in extra:
            execute_task = stepnumber % extra['every'] == 0
        if 'at' in extra:
            try:
                execute_task = currentstep in extra['at']
            except TypeError:
                execute_task = currentstep == extra['at']
    if execute_task:
        if args is None:
            if kwargs is None:
                result = func()
            else:
                result = func(**kwargs)
        else:
            if kwargs is None:
                result = func(*args)
            else:
                result = func(*args, **kwargs)
        return result
    else:
        return None


class Simulation(object):
    """
    This class defines a generic simulation.

    Attributes
    ----------
    cycle : dict of ints
        This dict stores information about the number of cycles.
        The int in cycle['end'] represents the cycle number where the
        simulation should end.
        The int in cycle['step'] represents the current cycle number.
        The int in cycle['start'] is the cycle number we started at.
        The int in cycle['stepno'] is the number of cycles we have perfomred
        to arrive at cycle['step']. This might be different from cycle['step']
        since cycle['start'] might be different from 0.
    task : list of dicts
        Each dich contain the tasks to be done. This are represented as a
        dict with the key-words 'func', 'args', 'kwargs'. Tasks are called as
        task['func'](*args, **kwargs). The keyword 'extra' can be used to tune
        how the function is executed (for instance if its desirable to only
        run it at certain steps).
    """
    def __init__(self, endcycle=0, startcycle=0):
        """
        Initialization of the simulation.

        Parameters
        ----------
        startcycle : int, optional.
            The cycle we start the simulation on, can be usefull if
            restarting.
        endcycle : int, optional.
            This number represents the cycle number where the simulation
            should end. It some simulations (e.g. MD) this would be the number
            of steps to perform, in other simulations this could be the
            minimum or maximum number of cycles to perform

        Returns
        -------
        N/A, but initiates self.tasks and set self.cycle.
        """
        self.cycle = {'step': startcycle, 'end': endcycle,
                      'start': startcycle, 'stepno': 0}
        self.task = []

    def extend_cycles(self, steps):
        """
        To extend a simulation with the given number of steps.

        Parameters
        ----------
        steps :  int
            The number of steps to extend the simulation with.

        Returns
        -------
        N/A, modifies self.cycle
        """
        self.cycle['start'] = self.cycle['end']
        self.cycle['end'] += steps

    def is_finished(self):
        """
        Function to determine if simulation is finished. In this
        version, the simulation is done if the current step number
        is larger than the end cycle. Note that the number of steps
        performed is dependent of the value of self.cycle['start'].

        Returns
        -------
        out : True if simulation is finished, false otherwise.
        """
        return self.cycle['step'] >= self.cycle['end']

    def step(self):
        """
        Run a simulation step. Here, the tasks in self.task
        will be executed sequentially.

        Returns
        -------
        out : list
            This list contains the results of the defined tasks.

        Note
        ----
        This function will have ``side effects`` and update/change
        the state of the system and other variables that are not
        explicitly shown. This is intended. In order to see what actually
        is happening when running ``step()``, investigate the definition
        of self.task and its functions in the script where the simulation
        is defined.
        """
        self.cycle['step'] += 1
        self.cycle['stepno'] += 1
        results = {}
        for task in self.task:
            resi = _do_task(task, self.cycle['stepno'], self.cycle['step'])
            label = task.get('result', None)
            if label:
                results[label] = resi
        return results

    def add_tasks(self, *tasks):
        """
        Method to add several task in sequential order.

        Parameters
        ----------
        tasks : list of dicts
            This list contain the tasks to add.
        """
        for task in tasks:
            self.add_task(task)

    def add_task(self, task, position=None):
        """
        Method for adding a task. A task can still be added manually by
        simply appending to self.task. This method will however do some
        checks so that the task added can be executed.

        Parameters
        ----------
        task : dict
            A dict defining the task. See also ``_do_taks`` for a more
            eleborate description of what this dict contains.
        position : int
            Can be used to placed the task at a specific position.

        Note
        ----
        Tasks that will fail are still added to the list of tasks. This is
        done because the program will then fail while trying to execute tasks.
        This is intended: if a task cannot be executed the program will fail,
        and the task should be corrected. The only exception are tasks that
        cannot be executed, these are not added.
        """
        if not callable(task['func']):
            msg = 'Task {} cannot be executed. Not added!'.format(task['func'])
            warnings.warn(msg)
            return False
        arguments = inspect.getargspec(task['func'])
        if not arguments.defaults:
            args = arguments.args
            defaults = None
        else:
            args = arguments.args[:len(arguments.defaults)]
            defaults = arguments.args[-len(arguments.defaults):]
        # first test the required arguments:
        task_args = task.get('args', None)
        if task_args:
            # here we need to be carefull. The expected input is a list or
            # a tuple (at least a sequence of some sort). However, it can be
            # just a single variable. It this single variable happens to be
            # a string, len(task_args) will not be correct. Here we attempt
            # to correct this, perhaps it can be done better elsewhere.
            isstring = isinstance(task_args, str)
            isiterab = isinstance(task_args, collections.Iterable)
            if isstring or not isiterab:
                msg = ['Argument is expected to be a list or tuple']
                task['args'] = [task_args]
                msg += ['Corrected {} to {}'.format(task_args, task['args'])]
                msg += ['Please verify that this is correct!']
                msg = '\n'.join(msg)
                warnings.warn(msg)
                task_args = task['args']
            ntask_args = len(task_args)
        args = [argsi for argsi in args if argsi is not 'self']
        try:
            ntask_args = len(task_args)
        except TypeError:
            ntask_args = 0
        if not len(args) == ntask_args:
            msg = ['Wrong number of arguments for task:']
            msg += ['Expected args: {}'.format(args)]
            msg += ["Arguments found in task['args']: {}".format(task_args)]
            msg = '\n'.join(msg)
            warnings.warn(msg)
        # also test keyword arguments if present.
        # here we only see if we give some arguments that the
        # function does not need.
        if defaults:
            kwargs = task.get('kwargs', None)
            if kwargs:
                extra = [key for key in kwargs if key not in defaults]
                if extra:
                    msg = ['Task Keyword arguments: {}'.format(defaults)]
                    msg += ['Attempting to pass extra: {}'.format(extra)]
                    msg = '\n'.join(msg)
                    warnings.warn(msg)
        if position is None:
            self.task.append(task)
        else:
            self.task.insert(position, task)
        return True

    def run(self):
        """
        This method can be used to run a simulation.
        The intented usage is for simulations where all tasks have been
        defined in the system object. This means that all input/output are
        also assumed to be defined as tasks.

        Note
        ----
        This method will simply run the tasks. In general this is probably
        too generic for the simulation you want. It is perhaps best to
        modify the `run` method of your simulation object.

        Yields
        ------
        out : dict
            This dict contains the results from the simulation
        """
        # do a initial yield, this is just to output the initial
        # state before we do any steps:
        results = {'cycle': self.cycle}
        for task in self.task:
            # check we we should do any initial calculations:
            if task.get('first', False):
                resi = _do_task(task, self.cycle['stepno'],
                                self.cycle['step'])
                label = task.get('result', None)
                if label:
                    results[label] = resi
        yield results
        # now, run the simulation :-)
        while not self.is_finished():
            results = self.step()
            if results is None:
                results = {}
            results['cycle'] = self.cycle
            yield results


class UmbrellaWindowSimulation(Simulation):
    """
    This class defines a Umbrella simulation which is a special case of
    the simulation class with settings to simplify the
    execution of the umbrella simulation.

    Attributes
    ----------
    umbrella : list = [float, float]
        The umbrella window.
    overlap : float
        The positions that must be crossed before the simulation is done.
    startcycle : int
        The current simulation cycle.
    mincycle : int
        The MINIMUM number of cycles to perform.
    """
    def __init__(self, umbrella, overlap, mincycle=0, startcycle=0):
        """
        Initialization of a umbrella simulation.

        Parameters
        ----------
        umbrella : list = [float, float]
            The umbrella window to consider.
        overlap : float
            The position we have to cross before the simulation is done.
        cycle : int, optional.
            The current simulation cycle.
        maxcycle : int, optional.
            The MINIMUM number of cycles to perform. Note that in the
            ``Simulation`` class this is the MAXIMUM number of
            cycles to perform. The meaning is redefined by redefining
            the ``simulation_finished`` method.

        Returns
        -------
        N/A
        """
        super(UmbrellaWindowSimulation, self).__init__(endcycle=mincycle,
                                                       startcycle=startcycle)
        self.umbrella = umbrella
        self.overlap = overlap

    def is_finished(self, system):
        """
        Check if simulation is done.

        In the umbrella simulation, the simulation is finished when we
        cycle is larger than maxcycle and all particles have
        crossed self.overlap.

        Parameters
        ----------
        system : system object
            Used to check if current position(s) satisfy the ending criterion.

        Returns
        -------
        out : True if simulation is finished, false otherwise.
        """
        return (self.cycle['step'] > self.cycle['end'] and
                np.all(system.particles.pos > self.overlap))


class SimulationNVE(Simulation):
    """
    This class is used to define a NVE simulation with some additional
    additional tasks/calculations.
    """
    def __init__(self, system, integrator, endcycle=0, startcycle=0):
        """
        Initialization of a NVE simulation.

        Parameters
        ----------
        system : object of type System
            This is the system we are investigating
        integrator : object of type Integrator
            This is the integrator that is used to propagate the system
            in time.
        startcycle : int, optional.
            The cycle we start the simulation on, can be usefull if
            restarting.
        endcycle : int, optional.
            This number represents the cycle number where the simulation
            should end.

        Parameters
        ----------

        Returns
        -------
        N/A
        """
        super(SimulationNVE, self).__init__(endcycle=endcycle,
                                            startcycle=startcycle)
        self.system = system
        self.system.potential_and_force()  # make sure forces are defined.
        self.integrator = integrator
        if not self.integrator.dynamics == 'NVE':
            msg = 'Inconsistent integrator {} for NVE dynamics!'
            warnings.warn(msg.format(integrator.desc))

        task_integrate = {'func': self.integrator.integration_step,
                          'args': [self.system]}
        task_thermo = {'func': calculate_thermo,
                       'args': [system,
                                system.temperature['dof'],
                                system.get_dim(),
                                system.box.calculate_volume()],
                       'first': True,
                       'result': 'thermo'}
        # task thermo is set up to execute at all steps
        # add propagation task:
        self.add_task(task_integrate)
        # add calculation task:
        self.add_task(task_thermo)


class SimulationMdFlux(Simulation):
    """
    SimulationMdFlux(Simulation)

    This class is used to define a MD simulation where the goal is
    to calculate crossings.
    """
    def __init__(self, system, integrator, interfaces, order_function,
                 endcycle=0, startcycle=0):
        """
        Initialization of the MD-Flux simulation.

        Parameters
        ----------
        system : object of type System.
            This is the system we are investigating
        integrator : object of type Integrator.
            This is the integrator that is used to propagate the system
            in time.
        interfaces : list of floats.
            These defines the interfaces for which we will check the
            crossing(s).
        order_function : function or object of type (derived) OrderParameter
            This function is used to calculate the order parameter. It is
            assumed to be called with ``order_function(system)`` and to return
            at least two values where the first one should be the
            order parameter.
        startcycle : int, optional.
            The cycle we start the simulation on, can be usefull if
            restarting.
        endcycle : int, optional.
            This number represents the cycle number where the simulation
            should end.

        Parameters
        ----------

        Returns
        -------
        N/A
        """
        super(SimulationMdFlux, self).__init__(endcycle=endcycle,
                                               startcycle=startcycle)
        self.system = system
        self.system.potential_and_force()  # make sure forces are defined.
        self.integrator = integrator
        self.interfaces = interfaces
        self.order_function = order_function
        # set up for initial crossing
        self.leftside_prev = None
        leftside, _ = check_crossing(self.cycle['step'], self.system.
                                     self.order_function,
                                     self.interfaces,
                                     self.leftside_prev)
        self.leftside_prev = leftside

        # also add a thermo task
        task_thermo = {'func': calculate_thermo,
                       'args': [system,
                                system.temperature['dof'],
                                system.get_dim(),
                                system.box.calculate_volume()],
                       'first': True,
                       'result': 'thermo'}

        self.add_task(task_thermo)

    def step(self):
        """
        Run a simulation step. Rather than using the tasks for the more
        general simulation, we here just execute what we need.

        Returns
        -------
        out : list
            This list contains the results of the defined tasks.
        """
        self.cycle['step'] += 1
        self.cycle['stepno'] += 1
        results = {}
        self.integrator.integration_step(self.system)
        leftside, cross = check_crossing(self.cycle['step'], self.system.
                                         self.order_function,
                                         self.interfaces,
                                         self.leftside_prev)
        self.leftside_prev = leftside
        results['cross'] = cross
        # do remaining tasks
        for task in self.task:
            resi = _do_task(task, self.cycle['stepno'], self.cycle['step'])
            label = task.get('result', None)
            if label:
                results[label] = resi
        return results
