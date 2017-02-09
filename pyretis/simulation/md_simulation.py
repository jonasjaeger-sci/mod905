# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Definitions of simulation objects for molecular dynamics simulations.

This module contains definitions of classes for performing molecular
dynamics simulations.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

SimulationNVE (:py:class:`.SimulationNVE`)
    Definition of a simple NVE simulation. The engine
    used for this simulation must have dynamics equal to NVE.

SimulationMDFlux (:py:class:`.SimulationMDFlux`)
    Definition of a simulation for determining the initial flux.
    This is used for calculating rates in TIS simulations.
"""
from __future__ import absolute_import
import logging
from pyretis.simulation.simulation import Simulation
from pyretis.core.particlefunctions import calculate_thermo
from pyretis.core.path import check_crossing
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['SimulationNVE', 'SimulationMDFlux']


class SimulationNVE(Simulation):
    """A MD NVE simulation class.

    This class is used to define a NVE simulation with some additional
    additional tasks/calculations.

    Attributes
    ----------
    system : object like :py:class:`.System`
        This is the system the simulation will act on.
    engine : object like :py:class:`.EngineBase`
        The engine to use for integrating the equations of motion.
        The engine must have engine.dynamics == 'NVE' in order
        for it to be usable in this simulation.
    """

    def __init__(self, system, engine, steps=0, startcycle=0):
        """Initialization of a NVE simulation.

        Here we will set up the tasks that are to be performed in the
        simulation, such as the integration and thermodynamics
        calculation(s).

        Parameters
        ----------
        system : object like :py:class:`.System`
            This is the system we are investigating.
        engine : object like :py:class:`.EngineBase`
            This is the integrator that is used to propagate the system
            in time.
        steps : int, optional
            The number of simulation steps to perform.
        startcycle : int, optional
            The cycle we start the simulation on, can be useful if
            restarting.
        """
        super().__init__(steps=steps, startcycle=startcycle)
        self.system = system
        self.system.potential_and_force()  # make sure forces are defined.
        self.engine = engine
        if self.engine.dynamics.lower() != 'nve':
            msg = 'Inconsistent MD integrator {} for NVE dynamics!'
            msg = msg.format(engine.description)
            logger.warning(msg)
        task_integrate = {'func': self.engine.integration_step,
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
        """Return a string with info about the simulation."""
        msg = ['NVE simulation']
        nstep = self.cycle['end'] - self.cycle['start']
        msg += ['Number of steps to do: {}'.format(nstep)]
        msg += ['MD engine: {}'.format(self.engine)]
        msg += ['Time step: {}'.format(self.engine.delta_t)]
        return '\n'.join(msg)


class SimulationMDFlux(Simulation):
    """A simulation for obtaining the initial flux for TIS.

    This class is used to define a MD simulation where the goal is
    to calculate crossings in order to obtain the initial flux for a TIS
    calculation.

    Attributes
    ----------
    system : object like :py:class:`.System`
        This is the system the simulation will act on.
    engine : object like :py:class:`.EngineBase`
        This is the integrator that is used to propagate the system
        in time.
    interfaces : list of floats
        These floats defines the interfaces used in the crossing
        calculation.
    leftside_prev : list of booleans
        These are used to store the previous positions with respect
        to the interfaces.
    """

    def __init__(self, system, orderp, engine, interfaces,
                 steps=0, startcycle=0):
        """Initialization of the MD-Flux simulation.

        Parameters
        ----------
        system : object like :py:class:`.System`
            This is the system we are investigating
        orderp : object like :py:class:`.OrderParameter`
            The class used for calculating the order parameters.
        engine : object like :py:class:`.EngineBase`
            This is the integrator that is used to propagate the system
            in time.
        interfaces : list of floats
            These defines the interfaces for which we will check the
            crossing(s).
        steps : int, optional
            The number of steps to perform.
        startcycle : int, optional
            The cycle we start the simulation on, can be useful if
            restarting.
        """
        super().__init__(steps=steps, startcycle=startcycle)
        self.system = system
        self.system.potential_and_force()  # make sure forces are defined.
        self.orderp = orderp
        self.engine = engine
        self.interfaces = interfaces
        # set up for initial crossing
        self.leftside_prev = None
        leftside, _ = check_crossing(
            self.cycle['step'],
            self.engine.calculate_order(self.orderp, self.system)[0],
            self.interfaces,
            self.leftside_prev)
        self.leftside_prev = leftside

    def step(self):
        """Run a simulation step.

        Rather than using the tasks for the more general simulation, we
        here just executing what we need.

        Returns
        -------
        out : dict
            This list contains the results of the defined tasks.
        """
        if not self.first_step:
            self.cycle['step'] += 1
            self.cycle['stepno'] += 1
            self.engine.integration_step(self.system)
        # collect energy and order parameter, this is done at all steps
        results = {'cycle': self.cycle,
                   'thermo': calculate_thermo(self.system),
                   'order': self.engine.calculate_order(self.orderp,
                                                        self.system),
                   'system': self.system}
        # do not check crossing at step 0
        if not self.first_step:
            leftside, cross = check_crossing(self.cycle['step'],
                                             results['order'][0],
                                             self.interfaces,
                                             self.leftside_prev)
            self.leftside_prev = leftside
            results['cross'] = cross
        if self.first_step:
            self.first_step = False
        return results

    def __str__(self):
        """Return a string with info about the simulation."""
        msg = ['MD-flux simulation']
        nstep = self.cycle['end'] - self.cycle['start']
        msg += ['Number of steps to do: {}'.format(nstep)]
        msg += ['Dynamics engine: {}'.format(self.engine)]
        msg += ['Time step: {}'.format(self.engine.delta_t)]
        return '\n'.join(msg)
