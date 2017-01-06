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
