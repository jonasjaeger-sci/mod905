# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Definition of pyretis engines.

This module defines the base class for the engines.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

EngineBase (:py:class:`.EngineBase`)
    The base class for engines.
"""
from abc import ABCMeta, abstractmethod


__all__ = ['EngineBase']


class EngineBase(metaclass=ABCMeta):
    """Abstract base class for engines.

    The engines perform molecular dynamics (or Monte Carolo) and they
    are assumed to act on a system. Typically they will integrate
    Newtons equation of motion in time for that system.

    Attributes
    ----------
    description : string
        Short string description of the engine. Used for printing
        information about the integrator.
    """
    engine_type = None

    def __init__(self, description):
        """Just add the description."""
        self.description = description

    @abstractmethod
    def integration_step(self, system):
        """Perform one time step of the integration."""
        pass

    @staticmethod
    def add_to_path(path, phase_point, left, right):
        """Adds phase point and perform some checks.

        This method is intended to be used by the propagate methods.

        Parameters
        ----------
        path : object like :py:class:`.PathBase`
            The path to add to.
        phase_point : dict
            The phase_point to add.
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
            else:
                status = 'Could not add for unknown reason'
            success = False
            stop = True
        if path.ordermin[0] < left:
            status = 'Crossed left interface!'
            success = True
            stop = True
        elif path.ordermax[0] > right:
            status = 'Crossed right interface!'
            success = True
            stop = True
        if path.length == path.maxlen:
            status = 'Max. path length exceeded!'
            success = False
            stop = True
        return status, success, stop

    @abstractmethod
    def propagate(self, path, system, orderp, interfaces, reverse=False):
        """Propagate equations of motion."""
        pass

    @abstractmethod
    def modify_velocities(self, system, rgen, sigma_v=None, aimless=True,
                          momentum=False, rescale=None):
        """Modify the velocities of the current state.

        This method will modify the velocities of a time slice.

        Parameters
        ----------
        system : object like :class:`.System`
            System is used here since we need access to the particle
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
            In some NVE simulations, we may wish to rescale the energy to
            a fixed value. If `rescale` is a float > 0, we will rescale
            the energy (after modification of the velocities) to match the
            given float.

        Returns
        -------
        dek : float
            The change in the kinetic energy.
        kin_new : float
            The new kinetic energy.
        """
        pass

    @abstractmethod
    def calculate_order(self, order_function, system):
        """Obtain the order parameter."""
        pass

    @abstractmethod
    def dump_phasepoint(self, phasepoint, deffnm=None):
        """Dump phase point to a file"""
        pass

    @abstractmethod
    def kick_across_middle(self, system, order_function, rgen, middle,
                           tis_settings):
        """Force a phase point across the middle interface."""
        pass

    @abstractmethod
    def clean_up(self):
        """Perform clean up after using the engine."""
        pass

    def __str__(self):
        """Return the string description of the integrator."""
        return self.description
