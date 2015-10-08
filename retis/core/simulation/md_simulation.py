# -*- coding: utf-8 -*-
"""Definitions of simulation objects."""
from __future__ import absolute_import
from retis.core.simulation import Simulation
from retis.core.particlefunctions import calculate_thermo
from retis.core.path import check_crossing
import warnings


__all__ = ['SimulationNVE', 'SimulationMDFlux']


class SimulationNVE(Simulation):
    """
    SimulationNVE(Simulation)

    This class is used to define a NVE simulation with some additional
    additional tasks/calculations.

    Attributes
    ----------
    system : object of type retis.core.system.System
        This is the system the simulation will act on.
    integrator : object of type retis.core.integrator.Integrator
        This integrator defines how to propagate the system in time.
        The integrator must have integrator.dynamics == 'NVE' in order
        for it to be usable in this simulation.
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
        # task_thermo is set up to execute at all steps
        # add propagation task:
        self.add_task(task_integrate)
        # add task_thermo:
        self.add_task(task_thermo)

    def __str__(self):
        """Return info about the simulation"""
        msg = ['NVE simulation']
        nstep = self.cycle['end'] - self.cycle['start']
        msg += ['Number of steps to do: {}'.format(nstep)]
        msg += ['Integrator: {}'.format(self.integrator)]
        msg += ['Time step: {}'.format(self.integrator.delta_t)]
        return '\n'.join(msg)


class SimulationMDFlux(Simulation):
    """
    SimulationMDFlux(Simulation)

    This class is used to define a MD simulation where the goal is
    to calculate crossings.

    Attributes
    ----------
    system : object of type System from retis.core.system.
        This is the system the simulation will act on.
    integrator : object of type Integrator.
        This is the integrator that is used to propagate the system
        in time.
    interfaces : list of floats
        These floats defines the interfaces used in the crossing calculation.
    order_function : function or object
        The defines how the order parameter should be calculated.
        This is either a function or a object of type `OrderParameter`
        as defined in `retis.core.orderparameter`.
        It is assumed that the order_function can be called with a
        System object as a parameter (typically: self.system).
    leftside_prev : list of booleans
        These are used to store the previous positions with respect
        to the interfaces.
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
        super(SimulationMDFlux, self).__init__(endcycle=endcycle,
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

    def step(self):
        """
        Run a simulation step. Rather than using the tasks for the more
        general simulation, we here just execute what we need.
        The output tasks are handled by the routines for the base Simulation
        object.

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
        results['cycle'] = self.cycle
        results['thermo'] = calculate_thermo(self.system)
        results['orderp'] = self.order_function(self.system)
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
        self.output(results)
        if self.first_step:
            self.first_step = False
        return results

    def __str__(self):
        """Return info about the simulation"""
        msg = ['MD-flux simulation']
        nstep = self.cycle['end'] - self.cycle['start']
        msg += ['Number of steps to do: {}'.format(nstep)]
        msg += ['Integrator: {}'.format(self.integrator)]
        msg += ['Time step: {}'.format(self.integrator.delta_t)]
        return '\n'.join(msg)
