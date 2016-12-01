# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Definition of numerical integrators.

This module defines the base class for integrators.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Integrator (:py:class:`pyretis.integrators.Integrator`)
    The base class for integrators
"""
from __future__ import absolute_import
import logging
from pyretis.core.particlefunctions import calculate_thermo_path
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['Integrator']


class Integrator(object):
    """Integrator(object).

    This class defines an integrator. The integrator is assumed to
    act on a system as will typically need to execute the command
    to update the forces.

    Attributes
    ----------
    delta_t : float
        Time step for the integration.
    desc : string
        Description of the integrator.
    dynamics : str
        A short string to represent the type of dynamics produced
        by the integrator (NVE, NVT, stochastic, ...).
    """

    def __init__(self, timestep, desc='Generic integrator', dynamics=''):
        """Initialization of the integrator.

        Parameters
        ----------
        timestep : float
            The time step for the integrator in internal units.
        """
        self.delta_t = timestep
        self.desc = desc
        self.dynamics = dynamics

    def integration_step(self, system):
        """Perform one time step of the integration.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`
            The system we are acting on.

        Returns
        -------
        out : None
            Does not return anything, in derived classes it will
            typically update the given `System`.
        """
        raise NotImplementedError

    def invert_dt(self):
        """Invert the time step for the integration.

        Returns
        -------
        out : boolean
            True if time step is positive, False otherwise.
        """
        self.delta_t *= -1.0
        return self.delta_t > 0.0

    def propagate(self, path, system, interfaces,
                  reverse=False, thermo=False):
        """Generate a path by integrating until a criterion is met.

        This function will generate a path by calling the function
        specifying the integration step repeatedly. The integration is
        carried out until the order parameter has passed the specified
        interfaces or if we have integrated for more than a specified
        maximum number of steps. The given system defines the initial
        state and the system is reset to it's initial state when this
        method is done.

        Parameters
        ----------
        path : object like `Path` from `pyretis.core.Path`.
            This is the path we use to fill in phase-space point.
            We are here not returning a new path - this since we want
            to delegate the creation of the path (type) to the method
            that is running `propagate`.
        system : object like `System` from `pyretis.core.system`.
            The system object gives the initial state for the
            integration. The initial state is stored and the system is
            reset to the initial state when the integration is done.
        interfaces : list of floats.
            These interfaces define the stopping criterion.
        reverse : boolean
            If True, the system will be propagated backwards in time.
        thermo : boolean
            If True, we will do some extra calculation of energies.
        """
        if reverse:
            status = 'Generating backward path...'
        else:
            status = 'Generating forward path...'
        logger.debug(status)
        success = False
        initial_system = system.particles.get_phase_point()
        system.potential_and_force()  # make sure forces are set
        left, _, right = interfaces
        while True:
            orderp = system.calculate_order()
            energy = calculate_thermo_path(system) if thermo else None
            add = path.append(orderp,
                              system.particles.pos,
                              system.particles.vel,
                              energy)
            if not add:
                if path.length >= path.maxlen:
                    status = 'Max. path length exceeded'
                else:
                    status = 'Could not add for unknown reason'
                success = False
                break
            if path.ordermin[0] < left:
                status = 'Crossed left interface!'
                success = True
                break
            elif path.ordermax[0] > right:
                status = 'Crossed right interface!'
                success = True
                break
            if reverse:
                system.particles.vel *= -1.0
                self(system)
                system.particles.vel *= -1.0
            else:
                self(system)
        system.particles.set_phase_point(initial_system)
        msg = 'Propagate done: "{}" (success: {})'.format(status, success)
        logger.debug(msg)
        return success, status

    def __call__(self, system):
        """To allow calling `Integrator(system)`.

        Here, we are just calling `self.integration_step(system)`.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`
            The system we are integrating.

        Returns
        -------
        out : None
            Does not return anything, but will update the particles.
        """
        return self.integration_step(system)

    def __str__(self):
        """Return the string description of the integrator."""
        return self.desc
