# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Definition of numerical integrators.

These integrators are typically used to integrate and propagate
Newtons equations of motion in time, the dynamics in molecular dynamics.
"""
import logging
import numpy as np
from pyretis.engines import MDEngine
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


class VVIntegrator(MDEngine):
    """VVIntegrator(MDEngine).

    This class defines the Velocity Verlet integrator.

    Attributes
    ----------
    delta_t : float
        The time step.
    half_delta_t : float
        Half of timestep.
    description : string
        Description of the integrator.
    """

    def __init__(self, timestep,
                 description='The velocity verlet integrator'):
        """Initiate the Velocity Verlet integrator.

        Parameters
        ----------
        timestep : float
            The time step in internal units.
        description : string
            Description of the integrator.
        """
        super().__init__(timestep, description, dynamics='NVE')
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

class Euler(MDEngine):
    """Euler(MDEngine).

    This class defines the Euler integrator.

    Attributes
    ----------
    delta_t : float
        The time step.
    half_delta_t : float
        Half of timestep.
    description : string
        Description of the integrator.
    """

    def __init__(self, timestep, description='The Euler integrator'):
        """Initiate the Euler integrator.

        Parameters
        ----------
        timestep : float
            The time step in internal units.
        descriotion : string
            Description of the integrator.
        """
        super().__init__(timestep, description, dynamics='NVE?')
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
