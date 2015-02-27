# -*- coding: utf-8 -*-

"""
integrators.py
"""

__all__ = ['VelocityVerlet']


class Integrator(object):
    """
    Integrator(object)

    This class defines an integrator. The integrator is assumed to
    act on a system as will typically need to execute the command
    to update the forces.

    Attributes
    ----------
    delta_t : float, time timesptep.
    desc : string, description of the integrator.
    """

    def __init__(self, delta_t, desc='Generic integrator'):
        """
        Initialization of the integrator

        Parameters
        ----------
        delta_t : float
            The timestep for the integrator.
        """
        self.delta_t = delta_t
        self.desc = desc

    def integration_step(self, system):
        """
        This method performs one time step of the integration.

        Parameters
        ----------
        system : object.
            The system we are acting on.

        Returns
        -------
        N/A, but will update the particles
        """
        pass

    def __str__(self):
        """
        This method just returns the string description of the
        integrator.
        """
        return self.desc


class Verlet(Integrator):
    """
    Verlet(Integrator)
    This class defines the verlet integrator.

    Attributes
    ----------
    delta_t : float
        The integrator timestep.
    half_idt : float
        Half of inverse timestep: `0.5/delta_t`
    delta_t2 : float
        Squared timestep: `delta_t*delta_t`
    """
    def __init__(self, delta_t, desc='The velocity verlet integrator'):
        """
        Initiates the Velocity Verlet integrator

        Parameters
        ----------
        delta_t : float
            The time step
        desc : string
            Description of the integrator
        """
        super(Verlet, self).__init__(delta_t, desc=desc)
        self.half_idt = 0.5/self.delta_t
        self.delta_t2 = self.delta_t**2
        self.previous_pos = None

    def set_initial_positions(self, particles):
        """
        Initiate the positions for the Verlet integration

        Parameters
        ----------
        particles : object
            The initial configuration. Positions and velocities are required.
        """
        self.previous_pos = particles.pos - particles.vel*self.delta_t

    def integration_step(self, system):
        """
        Performes one Verlet integration step.

        Parameters
        ----------
        system : object
            The system to integrate/act on. Assumed to have a particle list
            in system.particles.
        """
        particles = system.particles
        acc = particles.force * particles.imass
        pos = 2.0*particles.pos - self.previous_pos + acc*self.delta_t2
        particles.vel = (pos - self.previous_pos) * self.half_idt
        self.previous_pos, particles.pos = particles.pos, pos
        system.potential_and_force()


class VelocityVerlet(Integrator):
    """
    VelocityVerlet(Integrator)

    This class defines the velocity verlet integrator.

    Attributes
    ----------
    delta_t : float, time timestep.
    half_delta_t : float, half of timestep
    desc : string, description of the integrator.
    """
    def __init__(self, delta_t, desc='The velocity verlet integrator'):
        """
        Initiates the Velocity Verlet integrator

        Parameters
        ----------
        delta_t : float
            Tthe time step.
        desc : string
            Description of the integrator.
        """
        super(VelocityVerlet, self).__init__(delta_t, desc=desc)
        self.half_delta_t = self.delta_t * 0.5

    def integration_step(self, system):
        """
        Verlocity verlet integration, one time step.

        Parameters
        ----------
        system : object
            The system to integrate/act on. Assumed to have a particle list
            in system.particles.
        """
        particles = system.particles
        imass = particles.imass
        particles.vel += self.half_delta_t * particles.force * imass
        particles.pos += self.delta_t * particles.vel
        system.potential_and_force()
        particles.vel += self.half_delta_t * particles.force * imass
