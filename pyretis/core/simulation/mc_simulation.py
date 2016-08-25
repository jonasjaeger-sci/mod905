# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""Definition of simulation objects for Monte Carlo simulations.

This module defines some classes and functions for performing
Monte Carlo simulations.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

UmbrellaWindowSimulation
    Defines a simulation for performing umbrella window simulations.
    Several umbrella window simulations can be joined to perform a
    umbrella simulation.
"""
from __future__ import absolute_import
import numpy as np
from pyretis.core.montecarlo import max_displace_step
from pyretis.core.simulation.simulation import Simulation


__all__ = ['UmbrellaWindowSimulation']


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
        The positions that must be crossed before the simulation is
        done.
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
        maxdx : float
            Defines the maximum movement allowed in the Monte Carlo
            moves.
        mincycle : int, optional.
            The *MINIMUM* number of cycles to perform. Note that in the
            base `Simulation` class this is the *MAXIMUM* number of
            cycles to perform. The meaning is redefined in this class
            by overriding `self.simulation_finished`.
        startcycle : int, optional.
            The current simulation cycle, i.e. where we start.
        """
        super(UmbrellaWindowSimulation, self).__init__(steps=mincycle,
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

        Returns
        -------
        out : boolean
            True if simulation is finished, False otherwise.
        """
        return (self.cycle['step'] > self.cycle['end'] and
                np.all(self.system.particles.pos > self.overlap))

    def __str__(self):
        """Return some info about the simulation as a string."""
        msg = ['Umbrella window simulation']
        msg += ['Umbrella: {}, Overlap: {}.'.format(self.umbrella,
                                                    self.overlap)]
        msg += ['Minimum number of cycles: {}'.format(self.cycle['end'])]
        return '\n'.join(msg)
