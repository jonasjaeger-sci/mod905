# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Definition of pyretis engines.

This module defines the base class for the engines.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

EngineBase (:py:class:`pyretis.engines.engine.EngineBase`)
    The base class for engines.
"""
from abc import ABCMeta, abstractmethod


__all__ = ['EngineBase']


class EngineBase(metaclass=ABCMeta):
    """Abstract base class for engines.

    The engines perform molecular dynamics (or Monte Carolo) and they
    are assumed to act on a system. Typically they will integrate
    Newtons equation of motion in time for that system.
    """

    @property
    @abstractmethod
    def engine_type(self):
        """Return information about engine type."""
        pass

    @abstractmethod
    def integration_step(self, system):
        """Perform one time step of the integration."""
        pass

    @staticmethod
    def add_to_path(phase_point, path, left, right):
        """Adds phase point and perform some checks.

        This method is intended to be used by the propagate methods.

        Parameters
        ----------
        phase_point : dict
            The phase_point to add.
        path : object like :py:class:`pyretis.core.path.PathBase`
            The path to add to.
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

    @staticmethod
    @abstractmethod
    def modify_velocities(system, rgen, sigma_v=None, aimless=True,
                          momentum=False, rescale=None):
        """Generate random velocities for a configuration."""
        pass

    @staticmethod
    @abstractmethod
    def calculate_order(order_function, system):
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
