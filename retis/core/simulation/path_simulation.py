# -*- coding: utf-8 -*-
"""Definitions of simulation objects."""
from __future__ import absolute_import
import numpy as np
from retis.core.simulation import Simulation
from retis.core.path import PathEnsemble
from retis.core.random_gen import RandomGenerator
from retis.core.tis import generate_initial_path_kick, make_tis_step


__all__ = ['SimulationTIS']


class SimulationTIS(Simulation):
    """
    SimulationTIS(Simulation)

    This class is used to define a TIS simulation where the goal is
    to calculate crossing probabilities.

    Attributes
    ----------
    system : object of type retis.core.system.System
        This is the system the simulation will act on.
    integrator : object of type Integrator.
        This is the integrator that is used to propagate the system
        in time.
    interfaces : list of floats
        These floats defines the interfaces used in the crossing calculation.
    orderparameter : function or object
        The defines how the order parameter should be calculated.
        This is either a function or a object of type
        `retis.core.orderparameter.OrderParameter`.
        It is assumed that the order_function can be called with a
        `retis.core.system.System` object as a parameter.
    tis_settings : dict
        This dict contain specific settings for the TIS simulation (shooting
        moves etc.).
    rgen : object of type RandomGenerator
        This is a random generator used for the generation of paths.
    path : object of type Path
        This is the current accepted path
    path_ensemble : object of type PathEnsemble
        This is used for storing results for the simulation.
    """
    def __init__(self, system, integrator, settings,
                 endcycle=0, startcycle=0):
        """
        Initialization of the TIS simulation.

        Parameters
        ----------
        system : object of type System.
            This is the system we are investigating
        integrator : object of type Integrator.
            This is the integrator that is used to propagate the system
            in time.
        settings : dict
            This dict contains the settings for the TIS simulation.

        Returns
        -------
        N/A
        """
        super(SimulationTIS, self).__init__(endcycle=endcycle,
                                            startcycle=startcycle)
        self.system = system
        self.system.potential_and_force()  # make sure forces are defined.
        self.integrator = integrator
        self.interfaces = settings['interfaces']
        self.tis_settings = settings['tis']
        self.orderparameter = settings['orderparameter']
        # check for shooting:
        if self.tis_settings['sigma_v'] < 0.0:
            self.tis_settings['sigma_v'] = None
            self.tis_settings['aimless'] = True
        else:
            self.tis_settings['sigma_v'] = (self.tis_settings['sigma_v'] *
                                            np.sqrt(system.particles.imass))
            self.tis_settings['aimless'] = False
        # create a random generator for TIS moved etc.:
        self.rgen = RandomGenerator(seed=self.tis_settings['seed'])
        self.path = None  # current path
        self.path_ensemble = PathEnsemble(settings.get('ensemble', '000'),
                                          self.interfaces)

    def _initialize_path(self):
        """
        This is a method to initialize the TIS simulation.
        It will select the initialization method based on the setting given
        in `self.tis_settings['initial_path']`.
        """
        path = None
        if self.tis_settings['initial_path'] == 'kick':
            path = generate_initial_path_kick(self.system,
                                              self.interfaces,
                                              self.integrator,
                                              self.rgen,
                                              self.orderparameter,
                                              self.tis_settings)
        else:
            raise ValueError('Unknown initialization method requested!')
        return path

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
        results = {}
        if self.first_step:
            initial_path = self._initialize_path()
            accept = True
            trial = None
            status = 'ACC'
            self.path = initial_path
            self.path_ensemble.add_path_data(initial_path, status,
                                             cycle=self.cycle['step'])
            self.first_step = False
            results['accept'] = accept
            results['trial'] = trial
            results['status'] = status
        else:
            self.cycle['step'] += 1
            self.cycle['stepno'] += 1
            accept, trial, status = make_tis_step(self.rgen,
                                                  self.system,
                                                  self.path,
                                                  self.orderparameter,
                                                  self.interfaces,
                                                  self.integrator,
                                                  self.tis_settings)
            self.path_ensemble.add_path_data(trial, status,
                                             cycle=self.cycle['step'])
            results['accept'] = accept
            results['trial'] = trial
            results['status'] = status
            if accept:
                self.path = trial
        results['path'] = self.path
        results['cycle'] = self.cycle
        results['pathensemble'] = self.path_ensemble
        self.output(results)
        return results

    def __str__(self):
        """Just a small function to return some info about the simulation"""
        msg = ['TIS simulation']
        nstep = self.cycle['end'] - self.cycle['start']
        msg += ['Number of steps to do: {}'.format(nstep)]
        msg += ['Integrator: {}'.format(self.integrator)]
        msg += ['Time step: {}'.format(self.integrator.delta_t)]
        msg += ['Interfaces {}'.format(self.interfaces)]
        return '\n'.join(msg)
