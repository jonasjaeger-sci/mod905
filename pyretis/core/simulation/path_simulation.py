# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""Definitions of simulation objects for path sampling simulations.

This module defines simulations for performing path sampling
simulations.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

SimulationTIS
    Definition of a TIS simulation.
"""
from __future__ import absolute_import
import logging
import numpy as np
from pyretis.core.simulation.simulation import Simulation
from pyretis.core.random_gen import RandomGenerator
from pyretis.core.tis import (generate_initial_path_kick,
                              make_tis_step_ensemble)
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['SimulationTIS']


class SimulationTIS(Simulation):
    """SimulationTIS(Simulation).

    This class is used to define a TIS simulation where the goal is
    to calculate crossing probabilities.

    Attributes
    ----------
    integrator : object like `Integrator` from `pyretis.core.integrators`
        This is the integrator that is used to propagate the system
        in time.
    interfaces : list of floats
        These floats defines the interfaces used in the crossing
        calculation.
    orderparameter : function or object
        The defines how the order parameter should be calculated.
        This is either a function or a object like `OrderParameter` from
        `pyretis.core.orderparameter`.
        It is assumed that the order_function can be called with an
        object like `pyretis.core.system.System` as a parameter.
    path_ensemble : object like `PathEnsemble` from `pyretis.core.path`
        This is used for storing results for the simulation.
    rgen : object like `RandomGenerator` from `pyretis.core.random_gen`
        This is a random generator used for the generation of paths.
    system : object like `System` from `pyretis.core.system`
        This is the system the simulation will act on.
    tis_settings : dict
        This dict contain specific settings for the TIS simulation
        (shooting moves etc.).
    """

    def __init__(self, system, integrator, orderparameter, path_ensemble,
                 tis_settings, steps=0, startcycle=0):
        """Initialization of the TIS simulation.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`
            This is the system we are investigating
        integrator : object like `Integrator` from `pyretis.core.integrators`
            This is the integrator that is used to propagate the system
            in time.
        orderparameter : function or object like `OrderParameter`
            This function is used to calculate the order parameter.
            It is assumed to be called as ``orderparameter(system)``
            and to return at least two values where the first one
            is the scalar order parameter
        path_ensemble : object like `PathEnsemble` from `pyretis.core.path`.
            This is used for storing results for the simulation. It
            is also used for defining the interfaces for this
            simulation.
        tis_settings : dict
            This dict contains TIS specific settings, in particular we
            expect that the following keys are defined:

            * `aimless`: Determines if we should do aimless shooting
              (True) or not (False).
            * `sigma_v`: Values used for non-aimless shooting.
            * `initial_path`: A string which defines the method used
              for obtaining the initial path.
            * `seed`: A integer seed for the random generator used for
              the path ensemble we are simulating here.

            Note that the `make_tis_step_ensemble` method will make
            use of additional keys from `tis_settings`. Please see
            this method for further details.
        steps : int, optional.
            The number of simulation steps to perform.
        startcycle : int, optional.
            The cycle we start the simulation on, can be useful if
            restarting.
        """
        super(SimulationTIS, self).__init__(steps=steps,
                                            startcycle=startcycle)
        self.system = system
        self.system.potential_and_force()  # make sure forces are defined.
        self.integrator = integrator
        self.orderparameter = orderparameter
        self.path_ensemble = path_ensemble
        self.interfaces = path_ensemble.interfaces
        self.tis_settings = tis_settings
        # check for shooting:
        if self.tis_settings['sigma_v'] < 0.0:
            self.tis_settings['aimless'] = True
        else:
            self.tis_settings['sigma_v'] = (self.tis_settings['sigma_v'] *
                                            np.sqrt(system.particles.imass))
            self.tis_settings['aimless'] = False
        # create a random generator for TIS moves etc.:
        self.rgen = RandomGenerator(seed=self.tis_settings['seed'])

    def _initialize_path(self):
        """Initialize the path for the TIS simulation.

        It will select the initialization method based on the setting
        given in `self.tis_settings['initial_path']`.
        """
        path = None
        if self.tis_settings['initial_path'] == 'kick':
            path = generate_initial_path_kick(self.system,
                                              self.interfaces,
                                              self.orderparameter,
                                              self.integrator,
                                              self.rgen,
                                              self.tis_settings)
        else:
            msg = ('Unknown initialization method ',
                   "{}".format(self.tis_settings['initial_path']),
                   ' requested!')
            logger.error(msg)
            raise ValueError(msg)
        return path

    def step(self):
        """Perform a simulation step.

        Rather than using the tasks for the more general simulation, we
        here just execute what we need. Since we are integrating and
        checking the crossing at every step, these tasks are not in
        the `self.tasks` list. Other tasks are handled by this list.

        Returns
        -------
        out : dict
            This list contains the results of the defined tasks.
        """
        results = {}
        if self.first_step:
            initial_path = self._initialize_path()
            accept = True
            trial = initial_path
            status = 'ACC'
            self.path_ensemble.add_path_data(initial_path, status,
                                             cycle=self.cycle['step'])
            self.first_step = False
        else:
            self.cycle['step'] += 1
            self.cycle['stepno'] += 1
            accept, trial, status = make_tis_step_ensemble(self.path_ensemble,
                                                           self.system,
                                                           self.orderparameter,
                                                           self.integrator,
                                                           self.rgen,
                                                           self.tis_settings,
                                                           self.cycle['step'])
        results['accept'] = accept
        results['trialpath'] = trial
        results['status'] = status
        results['cycle'] = self.cycle
        results['pathensemble'] = self.path_ensemble
        return results

    def __str__(self):
        """Just a small function to return some info about the simulation."""
        msg = ['TIS simulation']
        msg += ['Path ensemble: {}'.format(self.path_ensemble.ensemble)]
        msg += ['Interfaces: {}'.format(self.interfaces)]
        nstep = self.cycle['end'] - self.cycle['start']
        msg += ['Number of steps to do: {}'.format(nstep)]
        msg += ['Integrator: {}'.format(self.integrator)]
        msg += ['Time step: {}'.format(self.integrator.delta_t)]
        return '\n'.join(msg)
