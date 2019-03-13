# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Definition of PyRETIS engines.

This module defines the base class for the engines.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

EngineBase (:py:class:`.EngineBase`)
    The base class for engines.
"""
from abc import ABCMeta, abstractmethod
import logging
import os
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
logger.addHandler(logging.NullHandler())


__all__ = ['EngineBase']


class EngineBase(metaclass=ABCMeta):
    """
    Abstract base class for engines.

    The engines perform molecular dynamics (or Monte Carlo) and they
    are assumed to act on a system. Typically they will integrate
    Newtons equation of motion in time for that system.

    Attributes
    ----------
    description : string
        Short string description of the engine. Used for printing
        information about the integrator.
    exe_dir : string
        A directory where the engine is going to be executed.
    engine_type : string or None
        Describe the type of engine as an "internal" or "external"
        engine. If this is undefined, this variable is set to None.
    needs_order : boolean
        Determines if the engine needs an internal order parameter
        or not. If not, it is assumed that the order parameter is
        calculated by the engine.

    """

    engine_type = None
    needs_order = True

    def __init__(self, description):
        """Just add the description."""
        self.description = description
        self._exe_dir = None

    @property
    def exe_dir(self):
        """Return the directory we are currently using."""
        return self._exe_dir

    @exe_dir.setter
    def exe_dir(self, exe_dir):
        """Set the directory for executing."""
        self._exe_dir = exe_dir
        if exe_dir is not None:
            logger.debug('Setting exe_dir to "%s"', exe_dir)
            if self.engine_type == 'external' and not os.path.isdir(exe_dir):
                logger.warning(('"Exe dir" for "%s" is set to "%s" which does'
                                ' not exist!'), self.description, exe_dir)

    @abstractmethod
    def integration_step(self, system):
        """Perform one time step of the integration."""
        return

    @staticmethod
    def add_to_path(path, phase_point, left, right):
        """
        Add a phase point and perform some checks.

        This method is intended to be used by the propagate methods.

        Parameters
        ----------
        path : object like :py:class:`.PathBase`
            The path to add to.
        phase_point : object like py:class:`.System`
            The phase point to add to the path.
        left : float
            The left interface.
        right : float
            The right interface.

        """
        status = 'Running propagate...'
        success = False
        stop = False
        add = path.append(phase_point)
        if not add:
            if path.length >= path.maxlen:
                status = 'Max. path length exceeded'
            else:  # pragma: no cover
                status = 'Could not add for unknown reason'
            success = False
            stop = True
        if path.phasepoints[-1].order[0] < left:
            status = 'Crossed left interface!'
            success = True
            stop = True
        elif path.phasepoints[-1].order[0] > right:
            status = 'Crossed right interface!'
            success = True
            stop = True
        if path.length == path.maxlen:
            status = 'Max. path length exceeded!'
            success = False
            stop = True
        return status, success, stop, add

    @abstractmethod
    def propagate(self, path, system, order_function, interfaces,
                  reverse=False):
        """Propagate equations of motion."""
        return

    @abstractmethod
    def modify_velocities(self, system, rgen, sigma_v=None, aimless=True,
                          momentum=False, rescale=None):
        """Modify the velocities of the current state.

        Parameters
        ----------
        system : object like :class:`.System`
            The system is used here since we need access to the particle
            list.
        rgen : object like :class:`.RandomGenerator`
            This is the random generator that will be used.
        sigma_v : numpy.array, optional
            These values can be used to set a standard deviation (one
            for each particle) for the generated velocities.
        aimless : boolean, optional
            Determines if we should do aimless shooting or not.
        momentum : boolean, optional
            If True, we reset the linear momentum to zero after generating.
        rescale : float, optional
            In some NVE simulations, we may wish to re-scale the energy to
            a fixed value. If `rescale` is a float > 0, we will re-scale
            the energy (after modification of the velocities) to match the
            given float.

        Returns
        -------
        dek : float
            The change in the kinetic energy.
        kin_new : float
            The new kinetic energy.

        """
        return

    @abstractmethod
    def calculate_order(self, order_function, system,
                        xyz=None, vel=None, box=None):
        """Obtain the order parameter."""
        return

    @abstractmethod
    def dump_phasepoint(self, phasepoint, deffnm=None):
        """Dump phase point to a file."""
        return

    @abstractmethod
    def kick_across_middle(self, system, order_function, rgen, middle,
                           tis_settings):
        """Force a phase point across the middle interface."""
        return

    @abstractmethod
    def clean_up(self):
        """Perform clean up after using the engine."""
        return

    @staticmethod
    def snapshot_to_system(system, snapshot):
        """Convert a snapshot to a system object."""
        system_copy = system.copy()
        system_copy.order = snapshot.get('order', None)
        particles = system_copy.particles
        particles.pos = snapshot.get('pos', None)
        particles.vel = snapshot.get('vel', None)
        particles.vpot = snapshot.get('vpot', None)
        particles.ekin = snapshot.get('ekin', None)
        for external in ('config', 'vel_rev', 'top'):
            if hasattr(particles, external) and external in snapshot:
                setattr(particles, external, snapshot[external])
        return system_copy

    @classmethod
    def can_use_order_function(cls, order_function):
        """Fail if the engine can't be used with an empty order parameter."""
        if order_function is None and cls.needs_order:
            raise ValueError(
                'No order parameter was defined, but the '
                'engine *does* require it.'
            )

    def __str__(self):
        """Return the string description of the integrator."""
        return self.description
