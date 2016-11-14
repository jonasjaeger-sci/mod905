# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""Definition of numerical integrators.

These integrators are typically used to integrate and propagate
Newtons equations of motion in time, the dynamics in molecular dynamics.
"""
from __future__ import absolute_import
import logging
import numpy as np
from pyretis.integrators import Integrator
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


class VVIntegrator(Integrator):
    """VVIntegrator(Integrator).

    This class defines the Velocity Verlet integrator.

    Attributes
    ----------
    delta_t : float
        The time step.
    half_delta_t : float
        Half of timestep.
    desc : string
        Description of the integrator.
    """

    def __init__(self, timestep, desc='The velocity verlet integrator'):
        """Initiate the Velocity Verlet integrator.

        Parameters
        ----------
        timestep : float
            The time step in internal units.
        desc : string
            Description of the integrator.
        """
        super(VVIntegrator, self).__init__(timestep, desc=desc,
                                           dynamics='NVE')
        self.half_delta_t = self.delta_t * 0.5

    def integration_step(self, system):
        """Velocity Verlet integration, one time step.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`
            The system to integrate/act on. Assumed to have a particle
            list in `system.particles`.

        Returns
        -------
        out : None
            Does not return anything, but alters the state of the given
            `system`.
        """
        particles = system.particles
        imass = particles.imass
        particles.vel += self.half_delta_t * particles.force * imass
        particles.pos += self.delta_t * particles.vel
        system.potential_and_force()
        particles.vel += self.half_delta_t * particles.force * imass
        return None

class Euler(Integrator):
    """Euler(Integrator).

    This class defines the Euler integrator.

    Attributes
    ----------
    delta_t : float
        The time step.
    half_delta_t : float
        Half of timestep.
    desc : string
        Description of the integrator.
    """

    def __init__(self, timestep, desc='The Euler integrator'):
        """Initiate the Euler integrator.

        Parameters
        ----------
        timestep : float
            The time step in internal units.
        desc : string
            Description of the integrator.
        """
        super(Euler, self).__init__(timestep, desc=desc,
                                    dynamics='NVE?')
        self.half_delta_tsq = 0.5 * self.delta_t**2

    def integration_step(self, system):
        """Euler integration, one time step.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`
            The system to integrate/act on. Assumed to have a particle
            list in `system.particles`.

        Returns
        -------
        out : None
            Does not return anything, but alters the state of the given
            `system`.
        """
        particles = system.particles
        imass = particles.imass
        # update positions and velocities
        particles.pos += (self.delta_t * particles.vel +
                          self.half_delta_tsq * particles.force * imass)
        particles.vel += self.delta_t * particles.force * imass
        # update forces
        system.potential_and_force()
        return None
