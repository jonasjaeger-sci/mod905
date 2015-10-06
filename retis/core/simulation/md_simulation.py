# -*- coding: utf-8 -*-
"""Definitions of simulation objects."""
from __future__ import absolute_import
from .simulation import Simulation
from retis.core.particlefunctions import calculate_thermo


__all__ = ['SimulationNVE']


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
        """Just a small function to return some info about the simulation"""
        msg = ['NVE simulation']
        nstep = self.cycle['end'] - self.cycle['start']
        msg += ['Number of steps to do: {}'.format(nstep)]
        msg += ['Integrator: {}'.format(self.integrator)]
        msg += ['Time step: {}'.format(self.integrator.delta_t)]
        return '\n'.join(msg)
