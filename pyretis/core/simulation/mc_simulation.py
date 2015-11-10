# -*- coding: utf-8 -*-
"""Definition of simulation objects for Monte Carlo simulations

This module defines some classes and functions for performing
Monte Carlo simulations.

Important classes and functions
-------------------------------

- UmbrellaWindowSimulation: Defines a simulation for performing umbrella
  window simulations. Several umbrella window simulations can be joined
  to perform a umbrella simulation.

"""
from __future__ import absolute_import
import numpy as np
import warnings
from pyretis.core.montecarlo import max_displace_step
from pyretis.core.simulation.simulation import Simulation
from pyretis.core.simulation.common import check_settings
from pyretis.core.random_gen import RandomGenerator

__all__ = ['UmbrellaWindowSimulation', 'create_mc_simulation']


_REQUIRED = {'umbrellawindow': ['umbrella', 'over', 'rgen', 'seed',
                                'maxdx', 'mincycle']}


def create_mc_simulation(settings, system, sim_type):
    """Create a MC simulation from the given settings.

    This is a helper function that will do some checks and set up one
    of the MC simulations defined in this module based on the given settings.

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
    out : object like `Simulation` from `pyretis.core.simulation`.
        This object will correspond to the selected simulation type.

    Note
    ----
    We are duplicating code here - the checking of required settings is
    identical to the checking in other simulation creators, for instance
    the `create_path_simulation` in `pyretis.core.simulation.path_simulation`.
    This is just in case someone wants to add some magic that amends missing
    settings.
    """
    simulation = None
    required, not_found = check_settings(settings, _REQUIRED[sim_type])
    if sim_type == 'umbrellawindow':
        if 'seed' in not_found or 'rgen' in not_found:
            # one or both of these keywords were present
            # things are OK if there is no other missing
            not_found = set(not_found) - set(['seed', 'rgen'])
            required = len(not_found) == 0
    if not required:
        warnings.warn('Settings not found: {}'.format(not_found))
        raise ValueError('Please update settings')
    if sim_type == 'umbrellawindow':
        try:
            rgen = settings['rgen']
        except KeyError:
            rgen = RandomGenerator(seed=settings.get('seed', 0))
        simulation = UmbrellaWindowSimulation(system,
                                              settings['umbrella'],
                                              settings['over'],
                                              rgen,
                                              settings['maxdx'],
                                              mincycle=settings['mincycle'])
    else:
        msg = 'Unknown MC simulation: {}'.format(sim_type)
        raise ValueError(msg)
    return simulation


def mc_task(rgen, system, maxdx):
    """Function to perform Monte Carlo moves.

    Will update positions and potential energy as needed.

    Parameters
    ----------
    rgen : object like `pyretis.core.random_gen.RandomGenerator`
        This object is used for generating random numbers.
    system : object like `System` from `pyretis.core.system`
        The system we act on.
    maxdx : float
        Maximum displacement step for the Monte Carlo move.
    """
    accepted_r, _, trial_r, v_trial, status = max_displace_step(rgen, system,
                                                                maxdx)
    if status:
        system.particles.pos = accepted_r
        system.v_pot = v_trial
    return accepted_r, v_trial, trial_r, status


class UmbrellaWindowSimulation(Simulation):
    """This class defines a Umbrella simulation.

    The Umbrella simulation is a special case of
    the simulation class with settings to simplify the
    execution of the umbrella simulation.

    Attributes
    ----------
    system : object like `System` from `pyretis.core.system`
        The system to act on.
    umbrella : list = [float, float]
        The umbrella window.
    overlap : float
        The positions that must be crossed before the simulation is done.
    startcycle : int
        The current simulation cycle.
    mincycle : int
        The MINIMUM number of cycles to perform.
    rgen : object like `pyretis.core.random_gen.RandomGenerator`
        Object to use for random number generation.
    maxdx : float
        Maximum allowed displacement in the Monte Carlo step.
    """

    def __init__(self, system, umbrella, overlap, rgen, maxdx,
                 mincycle=0, startcycle=0):
        """Initialization of a umbrella simulation.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`
            The system to act on.
        umbrella : list, [float, float]
            The umbrella window to consider.
        overlap : float
            The position we have to cross before the simulation is done.
        rgen : object like `pyretis.core.random_gen.RandomGenerator`
            Object to use for random number generation.
        cycle : int, optional.
            The current simulation cycle.
        maxcycle : int, optional.
            The MINIMUM number of cycles to perform. Note that in the
            base `Simulation` class this is the MAXIMUM number of
            cycles to perform. The meaning is redefined by redefining
            the `self.simulation_finished` method.
        """
        super(UmbrellaWindowSimulation, self).__init__(endcycle=mincycle,
                                                       startcycle=startcycle)
        self.umbrella = umbrella
        self.overlap = overlap
        self.rgen = rgen
        self.system = system
        self.maxdx = maxdx
        task_monte_carlo = {'func': mc_task,
                            'args': [self.rgen, self.system, self.maxdx],
                            'result': 'displace_step'}
        self.add_task(task_monte_carlo)
        self.first_step = False

    def is_finished(self):
        """Check if simulation is done.

        In the umbrella simulation, the simulation is finished when we
        cycle is larger than maxcycle and all particles have
        crossed self.overlap.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`
            Used to check if current position(s) satisfy the ending criterion.

        Returns
        -------
        out : boolean
            True if simulation is finished, False otherwise.
        """
        return (self.cycle['step'] > self.cycle['end'] and
                np.all(self.system.particles.pos > self.overlap))

    def __str__(self):
        """Just a small function to return some info about the simulation."""
        msg = ['Umbrella window simulation']
        msg += ['Umbrella: {}, Overlap: {}.'.format(self.umbrella,
                                                    self.overlap)]
        msg += ['Minimum number of cycles: {}'.format(self.cycle['end'])]
        return '\n'.join(msg)
