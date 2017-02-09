# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Definitions of simulation objects for path sampling simulations.

This module defines simulations for performing path sampling
simulations.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

SimulationSingleTIS (:py:class:`.SimulationSingleTIS`)
    Definition of a TIS simulation for a single path ensemble.

SimulationRETIS (:py:class:`.SimulationRETIS`)
    Definition of a RETIS simulation.
"""
import logging
import numpy as np
from pyretis.simulation.simulation import Simulation
from pyretis.core.tis import make_tis_step_ensemble
from pyretis.core.retis import make_retis_step
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['PathSimulation', 'SimulationSingleTIS', 'SimulationRETIS']


class PathSimulation(Simulation):
    """A base class for TIS/RETIS simulations.

    Attributes
    ----------
    engine : object like :py:class:`.EngineBase`
        This is the integrator that is used to propagate the system
        in time.
    path_ensembles : list of objects like :py:class:`.PathEnsemble`
        This is used for storing results for the different path
        ensembles.
    rgen : object like :py:class:`.RandomGenerator`
        This is a random generator used for the generation of paths.
    system : object like :py:class:`.System`
        This is the system the simulation will act on.
    settings : dict
        A dictionary with TIS and RETIS settings. We expect that
        we can find ``settings['tis']`` and possibly
        ``settings['retis']``. For ``settings['tis']`` we further
        expect to find the keys:

        * `aimless`: Determines if we should do aimless shooting
          (True) or not (False).
        * `sigma_v`: Scale used for non-aimless shooting.
        * `seed`: A integer seed for the random generator used for
          the path ensemble we are simulating here.

        Note that the
        :py:meth:`pyretis.core.tis.make_tis_step_ensemble` method
        will make use of additional keys from ``settings['tis']``.
        Please see this method for further details. For the
        ``settings['retis']`` we expect to find the following keys:

        * `swapfreq`: The frequency for swapping moves.
        * `relative_shoots`: If we should do relative shooting for
          the ensembles.
        * `nullmoves`: Should we perform null moves.
        * `swapsimul`: Should we just swap a single pair or several
          pairs.
    required_settings : tuple of strings
        This is just a list of the settings that the simulation
        requires. Here it is used as a check to see that we have
        all we need to set up the simulation.
    """

    required_settings = ('tis',)
    name = 'Generic path simulation'

    def __init__(self, system, order_function, engine, path_ensembles, rgen,
                 settings, steps=0, startcycle=0):
        """Initialization of the path simulation class.

        Parameters
        ----------
        system : object like :py:class:`.System`
            This is the system we are investigating.
        order_fucntion : object like :py:class:`.OrderParameter`
            The object used for calculating the order parameter.
        engine : object like :py:class:`.EngineBase`
            This is the integrator that is used to propagate the system
            in time.
        path_ensembles : list of objects like :py:class:`.PathEnsemble`
            This is used for storing results for the different path
            ensembles.
        rgen : object like :py:class:`.RandomGenerator`
            This object is the random generator to use in the simulation.
        settings : dict of dicts
            A dictionary with TIS and RETIS settings.
        steps : int, optional
            The number of simulation steps to perform.
        startcycle : int, optional
            The cycle we start the simulation on, can be useful if
            restarting.
        """
        super().__init__(steps=steps, startcycle=startcycle)
        self.system = system
        self.system.potential_and_force()  # check that we can get forces.
        self.order_function = order_function
        self.engine = engine
        self.path_ensembles = path_ensembles
        self.settings = {}
        for key in self.required_settings:
            if key not in settings:
                logtxt = 'Missing required setting "{}" for simulation "{}"'
                logtxt = logtxt.format(key, self.name)
                logger.error(logtxt)
                raise ValueError(logtxt)
            else:
                self.settings[key] = settings[key]
        self.rgen = rgen
        # Additional setup for shooting:
        if self.settings['tis']['sigma_v'] < 0.0:
            self.settings['tis']['aimless'] = True
            logger.info('%s: aimless is True', self.name)
        else:
            logger.debug('Path simulation: Creating sigma_v.')
            sigv = (self.settings['tis']['sigma_v'] *
                    np.sqrt(system.particles.imass))
            logger.debug('Path simulation: sigma_v created and set.')
            self.settings['tis']['sigma_v'] = sigv
            self.settings['tis']['aimless'] = False
            logger.info('Path simulation: aimless is False')


class SimulationSingleTIS(PathSimulation):
    """A single TIS simulation.

    This class is used to define a TIS simulation where the goal is
    to calculate crossing probabilities for a single path ensemble.

    Attributes
    ----------
    path_ensemble : object like :py:class:`.PathEnsemble`
        This is used for storing results for the simulation.
        Note that we also have the ``path_ensembles`` attribute
        defined by the parent class. For ideological reasons we
        also like to have a ``path_ensemble`` attribute since this
        class is intended for simulating a single TIS ensemble only.
    """

    required_settings = ('tis',)
    name = 'Single TIS simulation'

    def __init__(self, system, order_function, engine, path_ensemble, rgen,
                 settings, steps=0, startcycle=0):
        """Initialization of the TIS simulation.

        Parameters
        ----------
        system : object like :py:class:`.System`
            This is the system we are investigating.
        order_function : object like :py:class:`.OrderParameter`
            The object used for calculating the order parameter.
        engine : object like :py:class:`.EngineBase`
            This is the integrator that is used to propagate the system
            in time.
        path_ensemble : object like :py:class:`.PathEnsemble`
            This is used for storing results for the simulation. It
            is also used for defining the interfaces for this
            simulation.
        rgen : object like :py:class:`.RandomGenerator`
            This is the random generator to use in the simulation.
        settings : dict
            This dict contains settings for the simulation.
        steps : int, optional
            The number of simulation steps to perform.
        startcycle : int, optional
            The cycle we start the simulation on, can be useful if
            restarting.
        """
        path_ensembles = (path_ensemble,)  # Just for the base class
        super().__init__(
            system,
            order_function,
            engine,
            path_ensembles,
            rgen,
            settings,
            steps=steps,
            startcycle=startcycle)
        self.path_ensemble = path_ensemble

    def step(self):
        """Perform a TIS simulation step.

        Returns
        -------
        out : dict
            This list contains the results of the TIS step.
        """
        results = {}
        self.cycle['step'] += 1
        self.cycle['stepno'] += 1
        accept, trial, status = make_tis_step_ensemble(
            self.path_ensemble,
            self.system,
            self.order_function,
            self.engine,
            self.rgen,
            self.settings['tis'],
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
        msg += ['Interfaces: {}'.format(self.path_ensemble.interfaces)]
        nstep = self.cycle['end'] - self.cycle['start']
        msg += ['Number of steps to do: {}'.format(nstep)]
        msg += ['Engine: {}'.format(self.engine)]
        return '\n'.join(msg)


class SimulationRETIS(PathSimulation):
    """A RETIS simulation.

    This class is used to define a RETIS simulation where the goal is
    to calculate crossing probabilities for a several path ensembles.

    The attributes are documented in the parent class, please see:
    py:class:`.PathSimulation`.
    """

    required_settings = ('tis', 'retis')
    name = 'RETIS simulation'

    def __init__(self, system, order_function, engine, path_ensembles, rgen,
                 settings, steps=0, startcycle=0):
        """Initialization of the RETIS simulation.

        Parameters
        ----------
        system : object like :py:class:`.System`
            This is the system we are investigating.
        order_function : object like :py:class:`.OrderParameter`
            The object used for calculating the order parameter.
        engine : object like :py:class:`.EngineBase`
            This is the integrator that is used to propagate the system
            in time.
        path_ensembles : list of objects like :py:class:`.PathEnsemble`
            This is used for storing results for the different path
            ensembles.
        rgen : object like :py:class:`.RandomGenerator`
            This object is the random generator to use in the simulation.
        settings : dict
            A dictionary with settings for TIS and RETIS.
        steps : int, optional
            The number of simulation steps to perform.
        startcycle : int, optional
            The cycle we start the simulation on, can be useful if
            restarting.
        steps : int, optional
            The number of simulation steps to perform.
        startcycle : int, optional
            The cycle we start the simulation on, can be useful if
            restarting.
        """
        super().__init__(
            system,
            order_function,
            engine,
            path_ensembles,
            rgen,
            settings,
            steps=steps,
            startcycle=startcycle)

    def step(self):
        """Perform a RETIS simulation step.

        Returns
        -------
        out : dict
            This list contains the results of the defined tasks.
        """
        results = {}
        self.cycle['step'] += 1
        self.cycle['stepno'] += 1
        msgtxt = 'RETIS step. Cycle {}'.format(self.cycle['stepno'])
        logger.info(msgtxt)
        retis_step = make_retis_step(
            self.path_ensembles,
            self.system,
            self.order_function,
            self.engine,
            self.rgen,
            self.settings,
            self.cycle['step'])
        results['retis'] = retis_step
        results['system'] = self.system
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
