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
from retis.inout import (CrossFile, EnergyFile, OrderFile,
                         create_traj_writer, get_predefined_table)


__all__ = ['Simulation', 'UmbrellaWindowSimulation', 'SimulationNVE',
           'SimulationMdFlux',
           'create_simulation']


# define default outputs for the different simulations:
_OUTPUT = {'md-flux': [{'target': 'file', 'type': 'orderp', 'every': 10},
                       {'target': 'file', 'type': 'thermo', 'every': 100},
                       {'target': 'file', 'type': 'cross', 'every': 1},
                       {'target': 'file', 'type': 'traj', 'every': 10,
                        'header': 'MD-Flux simulation. Step: {}'},
                       {'target': 'screen', 'type': 'thermo', 'every': 10}],
           'nve': [{'target': 'file', 'type': 'thermo', 'every': 100},
                   {'target': 'file', 'type': 'traj', 'every': 10,
                    'header': 'NVE simulation. Step: {}'},
                   {'target': 'screen', 'type': 'thermo', 'every': 10}]}


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


def create_simulation(settings):
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
    simulation_type = settings.get('type', 'nve').lower()
    sim = None
    required = {'nve': ['system', 'endcycle'],
                'md-flux': ['system', 'endcycle', 'integrator', 'interfaces',
                            'orderparameter']}
    if simulation_type in required:
        # just check if all the required settings were given:
        if not _check_settings(settings, required[simulation_type]):
            return None
    if simulation_type == 'nve':
        # set up a MD NVE simulation.
        intg = create_integrator(settings.get('integrator', None),
                                 simulation_type)
        sim = SimulationNVE(settings['system'], intg,
                            endcycle=settings['endcycle'],
                            startcycle=settings.get('startcycle', 0))
    elif simulation_type == 'md-flux':
        # set up a simulation for MD FLUX
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
    if sim is not None:
        if simulation_type in _OUTPUT:  # add defaults:
            for task in _OUTPUT[simulation_type]:
                sim.add_output(task)
        for task in settings.get('output', []):
            sim.add_output(task)
    return sim


def _create_output_task(task, system=None):
    """
    This method will create an object for a given output task.
    It will make use of some of the pre-define output possibilities
    defined in retis.inout

    Parameters
    ----------
    task : dict
        This dict describes the task.
    system : object
        The system we are describing. Needed for creating the
        trajectory writer.
    """
    writer = None
    if task['target'] == 'file':
        # we have to create different files for the different
        # outputs:
        if task['type'] == 'orderp':
            writer = OrderFile(task.get('filename', 'order.dat'),
                               mode='w',
                               oldfile=task.get('oldfile', 'overwrite'))
        elif task['type'] == 'thermo':
            writer = EnergyFile(task.get('filename', 'energy.dat'),
                                mode='w',
                                oldfile=task.get('oldfile', 'overwrite'))
        elif task['type'] == 'cross':
            writer = CrossFile(task.get('filename', 'cross.dat'),
                               mode='w',
                               oldfile=task.get('oldfile', 'overwrite'))
        elif task['type'] == 'traj':
            fmt = task.get('format', 'gro')
            default_file = 'traj.{}'.format(fmt)
            writer = create_traj_writer({'type': fmt,
                                         'file': task.get('filename',
                                                          default_file),
                                         'oldfile': 'overwrite'}, system)
        else:
            msg = 'Unknown type {} for target file'.format(task['type'])
            warnings.warn(msg)
            return False
        if writer is not None:
            task['filename'] = writer.filename
    elif task['target'] == 'screen':
        if task['type'] == 'thermo':
            writer = get_predefined_table('energies')
    else:
        msg = 'Unknown output target {}. Will not add task!'
        warnings.warn(msg.format(task['target']))
        return False
    if writer is not None:
        task['writer'] = writer
    return True


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
        The current step number of the simulation.

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
        # just check again since people might add without using the
        # add_task method of the Simulation object.
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


def _check_task(task):
    """
    This is a helper function to inspect a given task.
    It will check:
    1) If the task can be executed
    2) If the correct number of arguments are given
    3) If the default arguments are correct if given.

    Parameters
    ----------
    task : dict
        The task to investigate. The keys are:
        taks['func'] : this should be a callable function
        task['args'] : this should be a list with arguments (if needed)
        task['kwargs'] : this should be a dict with kwargs (if needed)

    Returns
    -------
    out : boolean
        False if task should not be added, True otherwise

    Note
    ----
    Tasks that will fail might still be returned as True. Here we
    only test if the task is executable and if the task has the correct
    arguments in task['args'] and task['kwargs']. False is only returned
    if the function is not executable or if the wrong number of arguments
    are given.
    """
    # Check 1)
    if not callable(task['func']):
        msg = 'Task {} cannot be executed. Not added!'.format(task['func'])
        warnings.warn(msg)
        return False
    # Check 2)
    arguments = inspect.getargspec(task['func'])
    if not arguments.defaults:
        args = arguments.args
        defaults = None
    else:
        defaults = arguments.args[-len(arguments.defaults):]
        args = [arg for arg in arguments.args if arg not in defaults]
    # remove self from args, this is passed implicitly to objects
    args = [arg for arg in args if arg is not 'self']
    # first test the required arguments:
    task_args = task.get('args', None)
    if task_args:
        # here we need to be carefull. The expected input is a list or
        # a tuple (at least a sequence of some sort). However, it can be
        # just a single variable. It this single variable happens to be
        # a string, len(task_args) will not be correct. Here we attempt
        # to correct this. TODO: Consider if this block is needed.
        try:
            # will fail in python 3
            isstring = isinstance(task_args, basestring)
        except NameError:
            isstring = isinstance(task_args, str)
        isiterab = isinstance(task_args, collections.Iterable)
        if isstring or not isiterab:
            task['args'] = [task_args]
            msg = ['Argument is expected to be a list or tuple',
                   'Corrected {} to {}'.format(task_args, task['args']),
                   'Please verify that this is correct!']
            warnings.warn('\n'.join(msg))
            task_args = task['args']
        ntask_args = len(task_args)
    try:
        ntask_args = len(task_args)
    except TypeError:
        ntask_args = 0
    if not len(args) == ntask_args:
        msg = ['Wrong number of arguments for task {}:'.format(task['func']),
               'Expected args: {}'.format(args),
               'Arguments found in task["args"]: {}'.format(task_args)]
        warnings.warn('\n'.join(msg))
        return False
    # Check 3)
    kwargs = task.get('kwargs', None)
    if kwargs:
        if defaults:
            extra = [key for key in kwargs if key not in defaults]
            if extra:
                msg = ['Task Keyword arguments: {}'.format(defaults)]
                msg += ['Attempting to pass extra: {}'.format(extra)]
                msg = '\n'.join(msg)
                warnings.warn(msg)
        else:
            msg = 'Passing keyword arguments to a non-keyword function {}!'
            warnings.warn(msg.format(task['func']))
    return True


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
        self.system = None
        self.task = []
        self.output_task = []
        self.first_step = True

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
        out : dict
            This dict contains the results of the defined tasks. Here, this
            dict is obtained as the return value from self.execute_tasks().

        Note
        ----
        This function will have ``side effects`` and update/change
        the state of the system and other variables that are not
        explicitly shown. This is intended. In order to see what actually
        is happening when running ``step()``, investigate the defined tasks
        in self.task.
        """
        if not self.first_step:
            self.cycle['step'] += 1
            self.cycle['stepno'] += 1
        results = self.execute_tasks(first=self.first_step)
        self.output(results, first=self.first_step)
        if self.first_step:
            self.first_step = False
        return results

    def execute_tasks(self, first=False):
        """
        This method will execute all the tasks in sequential order.

        Returns
        -------
        resuts : dict
            The results from the different tasks (if any).
        first : boolean
            This is just to do the initial tasks, i.e. tasks that should
            be done before the simulation starts.
        """
        results = {}
        for task in self.task:
            if not first or (task.get('first', False)):  # and first
                resi = _do_task(task, self.cycle['stepno'],
                                self.cycle['step'])
                label = task.get('result', None)
                if label:
                    results[label] = resi
        # also add the cycle number to results, this is just for
        # convenience:
        results['cycle'] = self.cycle
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
            A dict defining the task. See also `_do_tasks` for a more
            eleborate description of what this dict contains.
        position : int
            Can be used to placed the task at a specific position.

        Note
        ----
        Tasks that will fail might still added to the list of tasks. See
        the checks carried out in `_check_task`.

        See Also
        --------
        `_check_task` function for doing some simple checks before a task is
        added.
        """
        if not _check_task(task):
            return False
        else:
            if position is None:
                self.task.append(task)
            else:
                self.task.insert(position, task)
            return True

    def add_output(self, output):
        """
        The output tasks are added slightly different than the other tasks.
        This is since we need to create some objects here and possibly new
        files. We also have to possibility of someone just wanting to
        update a default output task, for instance change the requence of
        output etc.

        Parameters
        ----------
        output : dict
            This dict describes the output task.

        Returns
        -------
        out : boolean
            True if task was added, false otherwise
        """
        if _create_output_task(output, system=self.system):
            # check if we should update or add:
            for task in self.output_task:
                if output['target'] == 'file':
                    equ = True
                    for key in ['type', 'filename']:
                        equ = equ and task[key] == output[key]
                        if not equ:
                            break
                    if equ:
                        task.update(output)
                        return True
            # we did not update, just add:
            self.output_task.append(output)
            return True
        else:
            return False

    def output(self, results, first=False):
        """
        This method handles all the outputs that should be done. These
        are defined as tasks in self.output_task.

        Parameters
        ----------
        results : dict
            These are the results from the current simulation step.
        first : boolean
            This is just to determine if this is the first step or
            not. In some cases we might to do something special on the first
            output. For instance when writing to the screen, we typically
            want to output a table heading.

        Returns
        -------
        N/A
        """
        for task in self.output_task:
            if not task['type'] in results and task['type'] != 'traj':
                # the desired output was not calculated at this step for
                # some reason. This can for instance happen for the crossing
                # output which is calculated when a crossing occurs.
                continue
            every = task.get('every', None)
            at_step = task.get('at', None)
            exe_out = False
            step = self.cycle['step']
            if every:
                exe_out = self.cycle['stepno'] % every == 0
            if at_step:
                try:
                    exe_out = step in at_step
                except TypeError:
                    exe_out = step == at_step
            if exe_out:
                # ok, do writing
                if task['target'] == 'file':
                    if task['type'] == 'traj':
                        header = task['header'].format(step)
                        task['writer'].write(self.system, header=header)
                    else:
                        if task['type'] == 'cross':
                            task['writer'].write(results[task['type']])
                        else:
                            task['writer'].write(step, results[task['type']])
                elif task['target'] == 'screen':
                    # all these output tasks will be tables, just return the
                    # new row:
                    results[task['type']]['stepno'] = step
                    out = task['writer'].get_row(results[task['type']])
                    if first:
                        out = '\n'.join([task['writer'].get_header()] + [out])
                    print out

    def run(self):
        """
        This method can be used to run a simulation. The intended usage is
        for simulations where all tasks have been defined in the system
        object. Outputs are defined as separate tasks and are handled by
        `self.output(results)`.

        Note
        ----
        This method will simply run the tasks. In general this is probably
        too generic for the simulation you want. It is perhaps best to
        modify the `run` method of your simulation object to tailor the
        simulation more.

        Yields
        ------
        out : dict
            This dict contains the results from the simulation
        """
        # run the simulation :-)
        while not self.is_finished():
            yield self.step()


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
    SimulationNVE(Simulation)

    This class is used to define a NVE simulation with some additional
    additional tasks/calculations.
    """
    def __init__(self, system, integrator, endcycle=0, startcycle=0):
        """
        Initialization of a NVE simulation. Here we will set up the
        tasks that are to be performed in the simulation.

        Parameters
        ----------
        system : object of type System
            This is the system we are investigating
        integrator : object of type Integrator
            This is the integrator that is used to propagate the system
            in time.
        startcycle : int, optional.
            The cycle we start the simulation on, can be useful if
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
                       'args': [system],
                       'kwargs': {'dof': system.temperature['dof'],
                                  'dim': system.get_dim(),
                                  'volume': system.box.calculate_volume()},
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
            The cycle we start the simulation on, can be useful if
            restarting.
        endcycle : int, optional.
            This number represents the cycle number where the simulation
            should end.

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
        leftside, _ = check_crossing(self.cycle['step'], self.system,
                                     self.order_function,
                                     self.interfaces,
                                     self.leftside_prev)
        self.leftside_prev = leftside
        # also add a thermo task
        task_thermo = {'func': calculate_thermo,
                       'args': [system],
                       'kwargs': {'dof': system.temperature['dof'],
                                  'dim': system.get_dim(),
                                  'volume': system.box.calculate_volume()},
                       'first': True,
                       'result': 'thermo'}
        self.add_task(task_thermo)
        # add a task for calculating the order parameter
        task_order = {'func': self.order_function.__call__,
                      'args': [system],
                      'first': True,
                      'result': 'orderp'}
        self.add_task(task_order)

    def step(self):
        """
        Run a simulation step. Rather than using the tasks for the more
        general simulation, we here just execute what we need. Since we
        are integrating and checking the crossing at every step, these tasks
        are not in the self.tasks list. Other tasks are handled by this list.

        Returns
        -------
        out : dict
            This list contains the results of the defined tasks.
        """
        if not self.first_step:
            self.cycle['step'] += 1
            self.cycle['stepno'] += 1
            self.integrator.integration_step(self.system)
        # collect energy and order parameter, this is done at all steps
        results = {}
        system = self.system
        results['thermo'] = calculate_thermo(self.system)
        results['orderp'] = self.order_function(system)
        # do not check crossing at step 0
        if not self.first_step:
            leftside, cross = check_crossing(self.cycle['step'],
                                             self.system,
                                             results['orderp'][0],
                                             self.interfaces,
                                             self.leftside_prev)
            self.leftside_prev = leftside
            results['cross'] = cross
        # just output:
        self.output(results, first=self.first_step)
        if self.first_step:
            self.first_step = False
        return results
