# -*- coding: utf-8 -*-
"""Definitions of simulation objects for path sampling simulations.

This module defines simulations for performing path sampling simulations.

Important classes and functions
-------------------------------

- SimulationTIS: Definition of a TIS simulation.
"""
from __future__ import absolute_import
import numpy as np
from pyretis.core.simulation.simulation import Simulation
from pyretis.core.simulation.common import check_settings
from pyretis.core.path import PathEnsemble
from pyretis.core.integrators import create_integrator
from pyretis.core.random_gen import RandomGenerator
from pyretis.core.tis import (generate_initial_path_kick,
                              make_tis_step_ensemble)


__all__ = ['SimulationTIS']

# define settings for known simulations:
_KNOWN_SIM = {'tis': {'required': [], 'output': []}}

_KNOWN_SIM['tis']['required'] = ['endcycle', 'tis', 'integrator',
                                 'interfaces']
_KNOWN_SIM['tis']['output'] = [{'type': 'pathensemble', 'target': 'file',
                                'when': {'every': 10},
                                'filename': 'pathensemble.dat'},
                               {'type': 'trialpath', 'target': 'file',
                                'when': {'every': 10},
                                'filename': 'paths.dat'}]


def create_path_simulation(settings, system, sim_type):
    """Create a path simulation from the given settings.

    This is a helper function that will do some checks and set up one of the
    path simulations defined in this module based on the given settings.

    Parameters
    ----------
    settings : dict
        This dictionary contains the settings for the simulation.
    system : object like `System` from `pyretis.core.system`
        This is the system for which the simulation will run.
    sim_type : string
        This defines the simulation type we are to set up. Note that
        simulation type is also given in `settings['type']`. It is also
        given here since we typically call this function after checking the
        type.

    Returns
    -------
    out[0] : object like `Simulation` from `pyretis.core.simulation`.
        This object will correspond to the selected simulation type.
    out[1] : list of dicts
        The default outputs for the given simulation.

    Note
    ----
    We are duplicating code here - the checking of required settings is
    identical to the checking in other simulation creaters, for instance
    the `create_md_simulation` in `pyretis.core.simulation.md_simulation`.
    This is just in case someone wants to add some magic that amends missing
    settings.
    """
    simulation = None
    required = check_settings(settings, _KNOWN_SIM[sim_type]['required'])[0]
    if not required:
        raise ValueError('Please update settings!')
    if sim_type == 'tis':
        intg = create_integrator(settings['integrator'], sim_type)
        simulation = SimulationTIS(system, intg, settings,
                                   endcycle=settings['endcycle'],
                                   startcycle=settings.get('startcycle', 0))
    else:
        msg = 'Unknown path simulation: {}'.format(sim_type)
        raise ValueError(msg)
    return simulation, _KNOWN_SIM[sim_type]['output']


class SimulationTIS(Simulation):
    """
    SimulationTIS(Simulation).

    This class is used to define a TIS simulation where the goal is
    to calculate crossing probabilities.

    Attributes
    ----------
    system : object like `System` from `pyretis.core.system`
        This is the system the simulation will act on.
    integrator : object like `Integrator` from `pyretis.core.integrators`
        This is the integrator that is used to propagate the system
        in time.
    interfaces : list of floats
        These floats defines the interfaces used in the crossing calculation.
    orderparameter : function or object
        The defines how the order parameter should be calculated.
        This is either a function or a object like `OrderParameter` from
        `pyretis.core.orderparameter`.
        It is assumed that the order_function can be called with a object like
        `pyretis.core.system.System` as a parameter.
    tis_settings : dict
        This dict contain specific settings for the TIS simulation (shooting
        moves etc.).
    rgen : object like `RandomGenerator` from `pyretis.core.random_gen`
        This is a random generator used for the generation of paths.
    path_ensemble : object like `PathEnsemble` from `pyretis.core.path`
        This is used for storing results for the simulation.
    """

    def __init__(self, system, integrator, settings,
                 endcycle=0, startcycle=0):
        """
        Initialization of the TIS simulation.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`
            This is the system we are investigating
        integrator : object like `Integrator` from `pyretis.core.integrators`
            This is the integrator that is used to propagate the system
            in time.
        settings : dict
            This dict contains the settings for the TIS simulation.
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
        self.path_ensemble = PathEnsemble(settings.get('ensemble', '[0^+]'),
                                          self.interfaces)

    def _initialize_path(self):
        """
        Initialize the TIS simulation.

        It will select the initialization method based on the setting given
        in `self.tis_settings['initial_path']`.
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
            raise ValueError('Unknown initialization method requested!')
        return path

    def step(self):
        """
        Perform a simulation step.

        Rather than using the tasks for the more general simulation, we here
        just execute what we need. Since we are integrating and checking the
        crossing at every step, these tasks are not in the self.tasks list.
        Other tasks are handled by this list.

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
            self.path_ensemble.add_path_data(initial_path, status,
                                             cycle=self.cycle['step'])
            self.first_step = False
            results['accept'] = accept
            results['trialpath'] = trial
            results['status'] = status
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
        self.output(results)
        return results

    def __str__(self):
        """Just a small function to return some info about the simulation."""
        msg = ['TIS simulation']
        nstep = self.cycle['end'] - self.cycle['start']
        msg += ['Number of steps to do: {}'.format(nstep)]
        msg += ['Integrator: {}'.format(self.integrator)]
        msg += ['Time step: {}'.format(self.integrator.delta_t)]
        msg += ['Interfaces {}'.format(self.interfaces)]
        return '\n'.join(msg)
