# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Definitions of simulation objects for path sampling simulations.

This module defines simulations for performing path sampling
simulations.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PathSimulation (:py:class:`.PathSimulation`)
    The base class for path simulations.

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
from pyretis.initiation import initiate_path_simulation
from pyretis.inout.simulationio import task_from_settings
from pyretis.inout.screen import print_to_screen
from pyretis.inout.common import make_dirs
from pyretis.inout.restart import write_path_ensemble_restart
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
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
        :py:func:`pyretis.core.tis.make_tis_step_ensemble` method
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
    simulation_type = 'generic-path'
    simulation_output = [
        {
            'type': 'pathensemble',
            'name': 'path-ensemble',
            'result': ('pathensemble-{}',),
        },
        {
            'type': 'path-order',
            'name': 'path-ensemble-order',
            'result': ('path-{}', 'status-{}'),
        },
        {
            'type': 'path-traj-{}',
            'name': 'path-ensemble-traj',
            'result': ('path-{}', 'status-{}', 'pathensemble-{}'),
        },
        {
            'type': 'path-energy',
            'name': 'path-ensemble-energy',
            'result': ('path-{}', 'status-{}'),
        },
    ]

    def __init__(self, system, order_function, engine, path_ensembles,
                 settings, rgen=None, steps=0, startcycle=0):
        """Initialise the path simulation object.

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
        settings : dict of dicts
            A dictionary with TIS and RETIS settings.
        steps : int, optional
            The number of simulation steps to perform.
        startcycle : int, optional
            The cycle we start the simulation on.

        """
        super().__init__(steps=steps, startcycle=startcycle)
        self.system = system
        self.system.potential_and_force()  # Check that we can get forces.
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
        if rgen is None:
            self.rgen = np.random.RandomState()
        else:
            self.rgen = rgen
        # Additional setup for shooting:
        if self.settings['tis']['sigma_v'] < 0.0:
            self.settings['tis']['aimless'] = True
            logger.debug('%s: aimless is True', self.name)
        else:
            logger.debug('Path simulation: Creating sigma_v.')
            sigv = (self.settings['tis']['sigma_v'] *
                    np.sqrt(system.particles.imass))
            logger.debug('Path simulation: sigma_v created and set.')
            self.settings['tis']['sigma_v'] = sigv
            self.settings['tis']['aimless'] = False
            logger.info('Path simulation: aimless is False')

    def restart_info(self):
        """Return restart info.

        The restart info for the path simulation includes the state of
        the random number generator(s).

        """
        info = {'cycle': self.cycle,
                'rgen': self.rgen.get_state(),
                'type': self.simulation_type}
        try:
            rgen = self.engine.rgen
            info['engine'] = {'rgen': rgen.get_state()}
        except AttributeError:
            pass
        return info

    def create_output_tasks(self, settings, progress=False):
        """Create output tasks for the simulation.

        This method will generate output tasks based on the tasks
        listed in :py:attr:`.simulation_output`.

        Parameters
        ----------
        settings : dict
            These are the simulation settings.
        progress : boolean
            For some simulations, the user may select to display a
            progress bar, we then need to disable the screen output.

        """
        logging.debug('Clearing output tasks & adding pre-defined ones')
        self.output_tasks = []
        for ensemble in self.path_ensembles:
            directory = ensemble.directory['path-ensemble']
            idx = ensemble.ensemble_number
            logger.info('Creating output directories for ensemble %s',
                        ensemble.ensemble_name)
            for dir_name in ensemble.directories():
                msg_dir = make_dirs(dir_name)
                logger.info('%s', msg_dir)
            for task_dict in self.simulation_output:
                task_dict_ens = task_dict.copy()
                if 'result' in task_dict_ens:
                    task_dict_ens['result'] = [
                        key.format(idx) for key in task_dict_ens['result']
                    ]
                task = task_from_settings(task_dict_ens, settings, directory,
                                          self.engine, progress)
                if task is not None:
                    logger.debug('Created output task:\n%s', task)
                    self.output_tasks.append(task)

    def write_restart(self, now=False):
        """Create a restart file.

        Parameters
        ----------
        now : boolean, optional
            If True, the output file will be written irrespective of the
            step number.

        """
        super().write_restart(now=now)
        if now or (self.restart_freq is not None and
                   self.cycle['stepno'] % self.restart_freq == 0):
            for ensemble in self.path_ensembles:
                write_path_ensemble_restart(ensemble)

    def initiate(self, settings):
        """Initialise the path simulation.

        Parameters
        ----------
        settings : dictionary
            The simulation settings.

        """
        init = initiate_path_simulation(self, settings)
        print_to_screen('')
        for accept, path, status, ensemble in init:
            print_to_screen(
                'Found initial path for {}:'.format(ensemble.ensemble_name),
                level='success' if accept else 'warning',
            )
            for line in str(path).split('\n'):
                print_to_screen('- {}'.format(line))
            logger.info('Found initial path for %s', ensemble.ensemble_name)
            logger.info('%s', path)
            print_to_screen('')
            idx = ensemble.ensemble_number
            ensemble_result = {
                'pathensemble-{}'.format(idx): ensemble,
                'path-{}'.format(idx): path,
                'status-{}'.format(idx): status,
                'cycle': self.cycle,
                'system': self.system,
            }
            # If we are doing a restart, we do not print out at the
            # "restart" step as we assume that this is already
            # outputted in the "previous" simulation (the one
            # we restart from):
            if settings['initial-path']['method'] != 'restart':
                for task in self.output_tasks:
                    task.output(ensemble_result)
                write_path_ensemble_restart(ensemble)
            if self.soft_exit():
                return False
        return True


class SimulationSingleTIS(PathSimulation):
    """A single TIS simulation.

    This class is used to define a TIS simulation where the goal is
    to calculate crossing probabilities for a single path ensemble.

    Attributes
    ----------
    path_ensemble : object like :py:class:`.PathEnsemble`
        This is used for storing results for the simulation.
        Note that we also have the :py:attr:`.path_ensembles`
        attribute defined by the parent class. The attribute
        :py:attr:`.path_ensemble` used here, is meant to reflect
        that this class is intended for simulating a single ensemble
        only.

    """

    required_settings = ('tis',)
    name = 'Single TIS simulation'
    simulation_type = 'tis'
    simulation_output = PathSimulation.simulation_output + [
        {
            'type': 'pathensemble-screen',
            'name': 'path-ensemble-screen',
            'result': ('pathensemble-{}',),
        },
    ]

    def __init__(self, system, order_function, engine, path_ensemble,
                 settings, rgen=None, steps=0, startcycle=0):
        """Initialise the TIS simulation object.

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
            The cycle we start the simulation on.

        """
        super().__init__(
            system,
            order_function,
            engine,
            (path_ensemble,),
            settings,
            rgen=rgen,
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
        for ensemble in self.path_ensembles:
            idx = ensemble.ensemble_number
            accept, trial, status = make_tis_step_ensemble(
                self.path_ensemble,
                self.order_function,
                self.engine,
                self.rgen,
                self.settings['tis'],
                self.cycle['step'],
            )
            results['cycle'] = self.cycle
            results['accept-{}'.format(idx)] = accept
            results['path-{}'.format(idx)] = trial
            results['status-{}'.format(idx)] = status
            results['pathensemble-{}'.format(idx)] = ensemble
        return results

    def __str__(self):
        """Just a small function to return some info about the simulation."""
        msg = ['TIS simulation']
        msg += ['Path ensemble: {}'.format(self.path_ensemble.ensemble_number)]
        msg += ['Interfaces: {}'.format(self.path_ensemble.interfaces)]
        nstep = self.cycle['end'] - self.cycle['start']
        msg += ['Number of steps to do: {}'.format(nstep)]
        msg += ['Engine: {}'.format(self.engine)]
        return '\n'.join(msg)


class SimulationRETIS(PathSimulation):
    """A RETIS simulation.

    This class is used to define a RETIS simulation where the goal is
    to calculate crossing probabilities for several path ensembles.

    The attributes are documented in the parent class, please see:
    :py:class:`.PathSimulation`.
    """

    required_settings = ('tis', 'retis')
    name = 'RETIS simulation'
    simulation_type = 'retis'
    simulation_output = PathSimulation.simulation_output + [
        {
            'type': 'pathensemble-retis-screen',
            'name': 'path-ensemble-retis-screen',
            'result': ('pathensemble-{}',),
        },
    ]

    def __init__(self, system, order_function, engine, path_ensembles,
                 settings, rgen=None, steps=0, startcycle=0):
        """Initialise the RETIS simulation object.

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
            The cycle we start the simulation on.

        """
        super().__init__(
            system,
            order_function,
            engine,
            path_ensembles,
            settings,
            rgen=rgen,
            steps=steps,
            startcycle=startcycle
        )

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
            self.order_function,
            self.engine,
            self.rgen,
            self.settings,
            self.cycle['step'],
        )
        for res in retis_step:
            idx = res['ensemble']
            results['move-{}'.format(idx)] = res['retis-move']
            results['status-{}'.format(idx)] = res['status']
            results['path-{}'.format(idx)] = res['trial']
            results['accept-{}'.format(idx)] = res['accept']
            results['all-{}'.format(idx)] = res
            results['pathensemble-{}'.format(idx)] = self.path_ensembles[idx]
        results['system'] = self.system  # TODO: IS THIS REALLY NEEDED HERE?
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
