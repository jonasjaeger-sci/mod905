# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Definitions of simulation objects for path sampling simulations.

This module defines simulations for performing path sampling
simulations.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

SimulationSingleTIS
    Definition of a TIS simulation for a single path ensemble.

SimulationRETIS
    Definition of a RETIS simulation.
"""
from __future__ import absolute_import
import logging
import numpy as np
from pyretis.core.simulation.simulation import Simulation
from pyretis.core.tis import (make_tis_step_ensemble,
                              initiate_path_ensemble)
from pyretis.core.retis import make_retis_step
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['SimulationSingleTIS', 'SimulationRETIS']


class SimulationSingleTIS(Simulation):
    """SimulationSingleTIS(Simulation).

    This class is used to define a TIS simulation where the goal is
    to calculate crossing probabilities for a single path ensemble.

    Attributes
    ----------
    integrator : object like `Integrator` from `pyretis.integrators`
        This is the integrator that is used to propagate the system
        in time.
    interfaces : list of floats
        These floats defines the interfaces used in the crossing
        calculation.
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

    def __init__(self, system, integrator, path_ensemble, rgen,
                 tis_settings, steps=0, startcycle=0):
        """Initialization of the TIS simulation.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`
            This is the system we are investigating.
        integrator : object like `Integrator` from `pyretis.integrators`
            This is the integrator that is used to propagate the system
            in time.
        path_ensemble : object like `PathEnsemble` from `pyretis.core.path`.
            This is used for storing results for the simulation. It
            is also used for defining the interfaces for this
            simulation.
        rgen : object like `RandomGenerator`.
            This is the random generator to use in the simulation.
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
        super(SimulationSingleTIS, self).__init__(steps=steps,
                                                  startcycle=startcycle)
        self.system = system
        self.rgen = rgen
        self.system.potential_and_force()  # make sure forces are defined.
        self.integrator = integrator
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

    def step(self):
        """Perform a TIS simulation step.

        Returns
        -------
        out : dict
            This list contains the results of the defined tasks.
        """
        results = {}
        if self.first_step:
            initiate_path_ensemble(self.path_ensemble,
                                   self.system,
                                   self.integrator,
                                   self.rgen,
                                   self.tis_settings,
                                   self.cycle['step'])
            trial = self.path_ensemble.last_path
            status = 'ACC'
            accept = True
            self.first_step = False
        else:
            self.cycle['step'] += 1
            self.cycle['stepno'] += 1
            accept, trial, status = make_tis_step_ensemble(self.path_ensemble,
                                                           self.system,
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


class SimulationRETIS(Simulation):
    """SimulationRETIS(Simulation).

    This class is used to define a RETIS simulation where the goal is
    to calculate crossing probabilities for a several path ensembles.

    Attributes
    ----------
    """

    def __init__(self, system, integrator, path_ensembles, rgen,
                 tis_settings, retis_settings, steps=0, startcycle=0):
        """Initialization of the RETIS simulation.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`
            This is the system we are investigating.
        integrator : object like `Integrator` from `pyretis.integrators`
            This is the integrator that is used to propagate the system
            in time.
        path_ensembles : list of objects like `PathEnsemble`.
            This is used for storing results for the different path
            ensembles.
        rgen : object like `RandomGenerator`.
            This object is the random generator to use in the simulation.
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
        retis_settings : dict
            This dict contains RETIS specific settings, in particular:

            * `swapfreq`: The frequency for swapping moves.
            * `relative_shoots`: If we should do relative shooting for
              the ensembles.
            * `nullmoves`: Should we perform nullmoves.
            * `swapsimul`: Should we just swap a single pair or several
              pairs.
        steps : int, optional.
            The number of simulation steps to perform.
        startcycle : int, optional.
            The cycle we start the simulation on, can be useful if
            restarting.
        steps : int, optional.
            The number of simulation steps to perform.
        startcycle : int, optional.
            The cycle we start the simulation on, can be useful if
            restarting.
        """
        super(SimulationRETIS, self).__init__(steps=steps,
                                              startcycle=startcycle)
        self.system = system
        self.system.potential_and_force()  # make sure forces are defined.
        self.integrator = integrator
        self.path_ensembles = path_ensembles
        self.settings = {'tis': tis_settings, 'retis': retis_settings}
        self.rgen = rgen
        # check for shooting:
        local_tis = self.settings['tis']
        if local_tis['sigma_v'] < 0.0:
            local_tis['aimless'] = True
        else:
            local_tis['sigma_v'] = (local_tis['sigma_v'] *
                                    np.sqrt(system.particles.imass))
            local_tis['aimless'] = False

    def initiate_ensemble(self, ensemble):
        """Method to initiate a given ensemble.

        This method is mainly here for convenience. Sometimes we
        might want to do more stuff around the initiation - output
        to the user and so on. This method will just do the
        initialization.

        Parameters
        ----------
        ensemble : object like `PathEnsemble`
            The ensemble to initiate.

        Returns
        -------
        out : object like `Path`
            The initial path created.
        """
        msg = 'Initiating path in {}'.format(ensemble.ensemble_name)
        logger.info(msg)
        initiate_path_ensemble(ensemble,
                               self.system,
                               self.integrator,
                               self.rgen,
                               self.settings['tis'],
                               self.cycle['step'])
        return ensemble.last_path

    def step(self):
        """Perform a RETIS simulation step.

        Returns
        -------
        out : dict
            This list contains the results of the defined tasks.
        """
        results = {}
        if self.first_step:
            for ensemble in self.path_ensembles:
                msg = 'Initiating path in {}'.format(ensemble.ensemble_name)
                logger.info(msg)
                initiate_path_ensemble(ensemble,
                                       self.system,
                                       self.integrator,
                                       self.rgen,
                                       self.settings['tis'],
                                       self.cycle['step'])
            self.first_step = False
        else:
            self.cycle['step'] += 1
            self.cycle['stepno'] += 1
            retis_step = make_retis_step(self.path_ensembles,
                                         self.system,
                                         self.integrator,
                                         self.rgen,
                                         self.settings,
                                         self.cycle['step'])
            results['retis'] = retis_step
        results['cycle'] = self.cycle
        return results

    def __str__(self):
        """Just a small function to return some info about the simulation."""
        msg = ['RETIS simulation']
        msg += ['Path ensembles:']
        for ensemble in self.path_ensembles:
            msgtxt = '{}: Interfaces: {}'.format(ensemble.ensemble_name,
                                                 ensemble.interfaces)
            msg += [msgtxt]
        nstep = self.cycle['end'] - self.cycle['start']
        msg += ['Number of steps to do: {}'.format(nstep)]
        return '\n'.join(msg)
