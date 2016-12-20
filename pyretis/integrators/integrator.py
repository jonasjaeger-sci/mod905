# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Definition of numerical integrators.

This module defines the base class for integrators.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

IntegratorBase (:py:class:`pyretis.integrators.IntegratorBase`)
    The base class for integrators.
"""
from abc import ABCMeta, abstractmethod
import logging

logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['IntegratorBase']


class IntegratorBase(metaclass=ABCMeta):
    """Abstract base class for integrators.

    The integrators perform molecular dynamics and they are assumed to
    act on a system and integrate Newtons equation of motion in time.
    """

    @property
    @abstractmethod
    def int_type(self):
        """Return information about integrator type."""
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
