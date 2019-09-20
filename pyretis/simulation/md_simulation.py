# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Definitions of simulation objects for molecular dynamics simulations.

This module contains definitions of classes for performing molecular
dynamics simulations.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

SimulationNVE (:py:class:`.SimulationNVE`)
    Definition of a simple NVE simulation. The engine
    used for this simulation must have dynamics equal to NVE.

SimulationMD (:py:class:`.SimulationMD`)
    Definition of a simulation for running somply MD.

SimulationMDFlux (:py:class:`.SimulationMDFlux`)
    Definition of a simulation for determining the initial flux.
    This is used for calculating rates in TIS simulations.
"""
import logging
from pyretis.simulation.simulation import Simulation
from pyretis.core.particlefunctions import calculate_thermo
from pyretis.core.path import check_crossing
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
logger.addHandler(logging.NullHandler())


__all__ = [
    'SimulationMD',
    'SimulationNVE',
    'SimulationMDFlux'
]


class SimulationMD(Simulation):
    """A generic MD simulation.

    This class is used to define a simple MD simulation.

    Attributes
    ----------
    system : object like :py:class:`.System`
        This is the system the simulation will act on.
    engine : object like :py:class:`.EngineBase`
        The engine to use for integrating the equations of motion.
    order_function : object like :py:class:`.OrderParameter`
        A class that can be used to calculate an order parameter,
        if needed.

    """

    simulation_type = 'md'
    simulation_output = [
        {'type': 'energy', 'name': 'md-energy-file'},
        {'type': 'thermo-file', 'name': 'md-thermo-file'},
        {'type': 'traj-xyz', 'name': 'md-traj-file'},
        {'type': 'thermo-screen', 'name': 'md-thermo-screen'},
        {'type': 'order', 'name': 'md-order-file'},
    ]

    def __init__(self, system, engine, order_function=None,
                 steps=0, startcycle=0):
        """Initialise the MD simulation.

        Here we just add variables and do not do any other setup.

        Parameters
        ----------
        system : object like :py:class:`.System`
            This is the system we are investigating.
        engine : object like :py:class:`.EngineBase`
            This is the integrator that is used to propagate the system
            in time.
        order_function : object like :py:class:`.OrderParameter`, optional
            A class that can be used to calculate an order parameter,
            if needed.
        steps : int, optional
            The number of simulation steps to perform.
        startcycle : int, optional
            The cycle we start the simulation on.

        """
        super().__init__(steps=steps, startcycle=startcycle)
        self.system = system
        self.engine = engine
        self.order_function = order_function

    def run(self):
        """Run the MD simulation.

        Yields
        ------
        results : dict
            The results from a single step in the simulation.

        """
        nsteps = 1 + self.cycle['end'] - self.cycle['step']
        integ = self.engine.integrate(
            self.system,
            nsteps,
            order_function=self.order_function,
            thermo='full',
        )
        for step in integ:
            if not self.first_step:
                self.cycle['step'] += 1
                self.cycle['stepno'] += 1
            results = {'cycle': self.cycle.copy()}
            if self.first_step:
                self.first_step = False
            results.update(step)
            for task in self.output_tasks:
                task.output(results)
            self.write_restart()
            if self.soft_exit():
                yield results
                break
            yield results

    def __str__(self):
        """Return a string with info about the simulation."""
        msg = ['Generic MD simulation']
        nstep = self.cycle['end'] - self.cycle['start']
        msg += ['Number of steps to do: {}'.format(nstep)]
        msg += ['MD engine: {}'.format(self.engine)]
        msg += ['Time step: {}'.format(self.engine.timestep)]
        return '\n'.join(msg)


class SimulationNVE(SimulationMD):
    """A MD NVE simulation class.

    This class is used to define a NVE simulation. Compared with
    the :py:class:`.SimulationMD` we here require that the engine
    supports NVE dynamics.
    """

    simulation_type = 'md-nve'
    simulation_output = [
        {'type': 'energy', 'name': 'nve-energy-file'},
        {'type': 'thermo-file', 'name': 'nve-thermo-file'},
        {'type': 'traj-xyz', 'name': 'nve-traj-file'},
        {'type': 'thermo-screen', 'name': 'nve-thermo-screen'},
        {'type': 'order', 'name': 'nve-order-file'},
    ]

    def __init__(self, system, engine, order_function=None,
                 steps=0, startcycle=0):
        """Initialise the NVE simulation object.

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
        order_function : object like :py:class:`.OrderParameter`, optional
            A class that can be used to calculate an order parameter,
            if needed.
        steps : int, optional
            The number of simulation steps to perform.
        startcycle : int, optional
            The cycle we start the simulation on.

        """
        super().__init__(system, engine, order_function=order_function,
                         steps=steps, startcycle=startcycle)
        if self.engine.dynamics.lower() != 'nve':
            logger.warning(
                'Inconsistent MD integrator %s (%s) for NVE dynamics!',
                engine.__class__,
                engine.description
            )

    def step(self):
        """Run a single simulation step."""
        if self.first_step:
            self.system.potential_and_force()
            self.first_step = False
        else:
            self.cycle['step'] += 1
            self.cycle['stepno'] += 1
            self.engine.integration_step(self.system)
        results = {'cycle': self.cycle.copy(),
                   'thermo': calculate_thermo(self.system),
                   'system': self.system}
        if self.order_function:
            results['order'] = self.engine.calculate_order(
                self.order_function,
                self.system
            )
        return results

    def __str__(self):
        """Return a string with info about the simulation."""
        msg = ['NVE simulation']
        nstep = self.cycle['end'] - self.cycle['start']
        msg += ['Number of steps to do: {}'.format(nstep)]
        msg += ['MD engine: {}'.format(self.engine)]
        msg += ['Time step: {}'.format(self.engine.timestep)]
        return '\n'.join(msg)


class SimulationMDFlux(SimulationMD):
    """A simulation for obtaining the initial flux for TIS.

    This class is used to define a MD simulation where the goal is
    to calculate crossings in order to obtain the initial flux for a TIS
    calculation.

    Attributes
    ----------
    interfaces : list of floats
        These floats define the interfaces used in the crossing
        calculation.
    leftside_prev : list of booleans or None
        These are used to store the previous positions with respect
        to the interfaces.

    """

    simulation_type = 'md-flux'
    simulation_output = [
        {'type': 'energy', 'name': 'flux-energy-file'},
        {'type': 'traj-xyz', 'name': 'flux-traj-file'},
        {'type': 'thermo-screen', 'name': 'flux-thermo-screen'},
        {'type': 'order', 'name': 'flux-order-file'},
        {'type': 'cross', 'name': 'flux-cross-file'},
    ]

    def __init__(self, system, order_function, engine, interfaces,
                 steps=0, startcycle=0):
        """Initialise the MD-Flux simulation object.

        Parameters
        ----------
        system : object like :py:class:`.System`
            This is the system we are investigating
        order_function : object like :py:class:`.OrderParameter`
            The class used for calculating the order parameters.
        engine : object like :py:class:`.EngineBase`
            This is the integrator that is used to propagate the system
            in time.
        interfaces : list of floats
            These define the interfaces for which we will check the
            crossing(s).
        steps : int, optional
            The number of steps to perform.
        startcycle : int, optional
            The cycle we start the simulation on.

        """
        super().__init__(system, engine, order_function=order_function,
                         steps=steps, startcycle=startcycle)
        self.interfaces = interfaces
        # set up for initial crossing
        self.leftside_prev = None

    def run(self):
        """Run the MD simulation.

        Yields
        ------
        results : dict
            The results from a single step in the simulation.

        """
        nsteps = 1 + self.cycle['end'] - self.cycle['step']
        leftside = None
        integ = self.engine.integrate(
            self.system,
            nsteps,
            order_function=self.order_function,
            thermo='full',
        )
        for step in integ:
            results = {}
            if not self.first_step:
                self.cycle['step'] += 1
                self.cycle['stepno'] += 1
            else:
                self.first_step = False
            results['cycle'] = self.cycle
            if leftside:
                self.leftside_prev = leftside
            leftside, cross = check_crossing(self.cycle['step'],
                                             step['order'][0],
                                             self.interfaces,
                                             self.leftside_prev)
            results['cross'] = cross
            results.update(step)

            for task in self.output_tasks:
                task.output(results)
            self.write_restart()
            if self.soft_exit():
                yield results
                break
            yield results

    def __str__(self):
        """Return a string with info about the simulation."""
        msg = ['MD-flux simulation']
        nstep = self.cycle['end'] - self.cycle['start']
        msg += ['Number of steps to do: {}'.format(nstep)]
        msg += ['Dynamics engine: {}'.format(self.engine)]
        msg += ['Time step: {}'.format(self.engine.timestep)]
        return '\n'.join(msg)

    def restart_info(self):
        """Return restart info.

        Here we report the cycle number and the random
        number generator status.
        """
        info = super().restart_info()
        info['leftside_prev'] = self.leftside_prev
        return info

    def load_restart_info(self, info):
        """Load the restart information."""
        super().load_restart_info(info)
        self.leftside_prev = info['leftside_prev']
