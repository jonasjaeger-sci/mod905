# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Example of using a integration routine implemented in FORTRAN."""
import logging
from pyretis.engines import MDEngine
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())
try:
    from vvintegrator import vvintegrator
except ImportError:
    MSG = ('Could not import external FORTRAN library.'
           '\nPlease compile with "make"!')
    logger.critical(MSG)
    raise ImportError(MSG)


__all__ = ['VelocityVerletF']


class VelocityVerletF(MDEngine):
    """VelocityVerletF(MDEngine).

    This class defines the Velocity Verlet integrator.

    Attributes
    ----------
    delta_t : float
        The time step.
    half_delta_t : float
        Half of timestep
    desc : string
        Description of the integrator.
    """

    def __init__(self, delta_t,
                 desc='The velocity verlet integrator (FORTRAN)'):
        """Initiate the Velocity Verlet integrator.

        Parameters
        ----------
        delta_t : float
            The time step.
        desc : string
            Description of the integrator.
        """
        super().__init__(delta_t, desc, dynamics='NVE')
        self.half_delta_t = self.delta_t * 0.5

    def integration_step(self, system):
        """Velocity Verlet integration, one time step.

        Parameters
        ----------
        system : object like :py:class:`.System`
            The system to integrate/act on. Assumed to have a particle
            list in `system.particles`.

        Returns
        -------
        out : None
            Does not return anything, but alters the state of the given
            `system`.
        """
        particles = system.particles
        particles.pos, particles.vel = vvintegrator.step1(
            particles.pos,
            particles.vel,
            particles.force,
            particles.imass,
            self.delta_t,
            self.half_delta_t
        )
        system.potential_and_force()
        particles.vel = vvintegrator.step2(
            particles.vel,
            particles.force,
            particles.imass,
            self.half_delta_t
        )
        return None
