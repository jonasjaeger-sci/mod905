# -*- coding: utf-8 -*-

"""
integrators.py
"""
from __future__ import absolute_import
import numpy as np

__all__ = ['VelocityVerlet', 'Langevin']


class Integrator(object):
    """
    Integrator(object)

    This class defines an integrator. The integrator is assumed to
    act on a system as will typically need to execute the command
    to update the forces.

    Attributes
    ----------
    delta_t : float
        Time timesptep.
    desc : string
        Description of the integrator.
    dynamics : str
        A short string to represent the type of dynamics produced
        by the integrator (NVE, NVT, stochastic, ...).
    """

    def __init__(self, delta_t, desc='Generic integrator', dynamics=''):
        """
        Initialization of the integrator

        Parameters
        ----------
        delta_t : float
            The timestep for the integrator.
        """
        self.delta_t = delta_t
        self.desc = desc
        self.dynamics = dynamics

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

    def invert_dt(self):
        """
        This method is just intended to invert the time step for the
        integration

        Returns
        -------
        out : boolean
            True if time step is positive, False otherwise
        """
        self.delta_t *= -1.0
        return self.delta_t > 0.0

    def __call__(self, system):
        """
        This is just to allow calling Integrator(system).
        Here, we are just calling integration_step(system)

        Parameters
        ----------
        system : object of type system.

        Returns
        -------
        N/A, but will update the particles.
        """
        self.integration_step(system)

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
    def __init__(self, delta_t, desc='The verlet integrator'):
        """
        Initiates the Velocity Verlet integrator

        Parameters
        ----------
        delta_t : float
            The time step
        desc : string
            Description of the integrator
        """
        super(Verlet, self).__init__(delta_t, desc=desc, dynamics='NVE')
        self.half_idt = 0.5 / self.delta_t
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
        self.previous_pos = particles.pos - particles.vel * self.delta_t

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
        pos = 2.0 * particles.pos - self.previous_pos + acc * self.delta_t2
        particles.vel = (pos - self.previous_pos) * self.half_idt
        self.previous_pos, particles.pos = particles.pos, pos
        system.potential_and_force()


class VelocityVerlet(Integrator):
    """
    VelocityVerlet(Integrator)

    This class defines the velocity verlet integrator.

    Attributes
    ----------
    delta_t : float
        Time timestep.
    half_delta_t : float
        Half of timestep
    desc : string
        Description of the integrator.
    """
    def __init__(self, delta_t, desc='The velocity verlet integrator'):
        """
        Initiates the Velocity Verlet integrator

        Parameters
        ----------
        delta_t : float
            The time step.
        desc : string
            Description of the integrator.
        """
        super(VelocityVerlet, self).__init__(delta_t, desc=desc, dynamics='NVE')
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


class Langevin(Integrator):
    """
    Langevin(Integrator)

    This class defines a Langevin integrator.

    Attributes
    ----------
    rgen : object of type RandomGenerator
        This is the class that handles generation of random numbers
    gamma : float
        The friction parameter
    high_friction : boolan
        Determines if we are in the high_friction limit and should
        do the overdamped version
    init_params : boolean
        If true, we will initiate parameters for the Langevin integrator when
        integrate_step is invoked.
    param_high : dict
        This contains the parameters for the high friction limit. Here
        we integrate the equations of motion according to:
        r(t + dt) = r(t) + dt * f(t)/m*gamma + dr
        param_high['sigma'] : float
            standard deviation for the positions, used when drawing dr
        param_high['bddt'] : numpy.array
            Equal to dt*gamma/masses, since the masses is an numpy.array
            this will have the same shape.
    param_iner : dict
        This dict contains the parameters for the non-high friction limit
        We integrate the equations of motion according to:
        r(t + dt) = r(t) + c1 * dt * v(t) + c2*dt*dt*a(t) + dr
        v(r + dt) = c0 * v(t) + (c1-c2)*dt*a(t) + c2*dt*a(t+dt) + dv
        param_iner['c0'] : float
            Corresponds to c0 in the equation above.
        param_iner['a1'] : float
            Correcponds to c1*dt in the equation above.
        param_iner['a2'] : numpy.array
            Corresponds to c2*dt*dt/mass in the equation above.
            Here we divide by the masses in order to use the forces rather
            than the acceleration a. Since the masses might be different for
            different particles, this will result in a numpy.array with shape
            equal to the shape of the masses.
        param_iner['b1'] : numpy.array
            Corresponds to (c1-c2)*dt/mass in the equation above.
            Here we also divide by the masses, resulting in a numpy.array
        param_iner['b2'] : numpy.array
            Corresponds to c2*dt/mass in the equation above.
            Here we also divide by the masses, resulting in a numpy.array
        param_iner['mean'] : numpy.array (2,)
            The means for the bivariate gaussian distribution
        param_iner['cov'] : numpy.array (2,2)
            This array contains the covariance for the bivariate gaussian
            distribution param_iner['mean'] and param_iner['cov'] are used
            as parameters when drawing dr and dv from the bivariate
            distribution.

    Note
    ----
    Currently, we are using a multinormal distribution from numpy.
    Consider replacing this one as it seems somewhat slow.
    """
    def __init__(self, delta_t, gamma, rgen, high_friction=False,
                 desc='Langevin integrator'):
        """
        Initiates the Langevin integrator. Actually, it is very convenient to
        set some variables for the different particles. To have a
        uniform init for the different integrators, we postpone this. This
        initialization can be done later by calling explicitly the function
        _init_parameters(self, system) or it will be called the first time
        integration_step is invoked.

        Parameters
        ----------
        delta_t : float
            The time step.
        gamma : float
            The gamma parameter for the Langevin integrator
        rgen : object of type RandomGenerator
            This is the class that will handle random number generation
            for us.
        desc : string
            Description of the integrator.
        param_high : dict
            Parameters for the high friction limit.
        param_iner : dict
            Parameters for the non-high friction limit.
        """
        super(Langevin, self).__init__(delta_t, desc=desc, dynamics='stochastic')
        self.gamma = gamma
        self.high_friction = high_friction
        self.rgen = rgen
        self.param_high = {'sigma': None, 'bddt': None}
        self.param_iner = {'c0': None, 'a1': None, 'a2': None,
                           'b1': None, 'b2': None, 'mean': None, 'cov': None}
        self.init_params = True

    def _init_parameters(self, system):
        """
        Extra initialization of the Langevin integrator.

        Parameters
        ----------
        system : object
            The system to integrate/act on. Assumed to have a particle list
            in system.particles.
        """
        beta = system.temperature['beta']
        imasses = system.particles.imass
        if self.high_friction:
            self.param_high['sigma'] = np.sqrt(2.0 * self.delta_t *
                                               imasses/(beta * self.gamma))
            self.param_high['bddt'] = self.delta_t * imasses / self.gamma
        else:
            gammadt = self.gamma * self.delta_t
            exp_gdt = np.exp(-gammadt)
            if self.gamma > 0.0:
                c_0 = exp_gdt
                c_1 = (1.0 - c_0) / gammadt
                c_2 = (1.0 - c_1) / gammadt
            else:
                c_0, c_1, c_2 = 1.0, 1.0, 0.5

            self.param_iner['c0'] = c_0
            self.param_iner['a1'] = c_1 * self.delta_t
            self.param_iner['a2'] = c_2 * self.delta_t**2 * imasses
            self.param_iner['b1'] = (c_1 - c_2) * self.delta_t * imasses
            self.param_iner['b2'] = c_2 * self.delta_t * imasses

            self.param_iner['mean'] = []
            self.param_iner['cov'] = []
            self.param_iner['cho'] = []

            for imass in imasses:
                sig_ri = (self.delta_t * imass / (beta * self.gamma)) \
                         * (2. - (3. - 4.*exp_gdt + exp_gdt**2) / gammadt)
                sig_ri = np.sqrt(sig_ri)
                sig_vi = np.sqrt((1.0 - exp_gdt**2) * imass / beta)
                cov_rvi = (imass/(beta * self.gamma)) * (1.0 - exp_gdt)**2
                cov_matrix = np.zeros((2, 2))
                cov_matrix[0, 0] = sig_ri**2
                cov_matrix[1, 1] = sig_vi**2
                cov_matrix[0, 1] = cov_rvi
                cov_matrix[1, 0] = cov_rvi
                self.param_iner['cov'].append(cov_matrix)
                self.param_iner['cho'].append(np.linalg.cholesky(cov_matrix))
                self.param_iner['mean'].append(np.zeros(2))
                # NOTE: Can be simplified - mean is always just zero...

    def integration_step(self, system):
        """
        Langevin integration, one time step.

        Parameters
        ----------
        system : object
            The system to integrate/act on. Assumed to have a particle list
            in system.particles.
        """
        if self.init_params:
            self._init_parameters(system)
            self.init_params = False
        if self.high_friction:
            self.integration_step_overdamped(system)
        else:
            self.integration_step_inertia(system)

    def integration_step_overdamped(self, system):
        """
        Overdamped Langevin integration, one time step

        Parameters
        ----------
        system : object
            The system to integrate/act on. Assumed to have a particle list
            in system.particles.
        """
        particles = system.particles
        rands = self.rgen.normal(loc=0.0, scale=self.param_high['sigma'],
                                 size=particles.vel.shape)
        particles.pos += self.param_high['bddt'] * particles.force + rands
        particles.vel = rands

    def integration_step_inertia(self, system):
        """
        Langevin integration, one time step

        Parameters
        ----------
        system : object
            The system to integrate/act on. Assumed to have a particle list
            in system.particles.
        """
        particles = system.particles
        ndim = system.get_dim()
        pos_rand = np.zeros(particles.pos.shape)
        vel_rand = np.zeros(particles.vel.shape)
        if self.gamma > 0.0:
            mean, cov = self.param_iner['mean'], self.param_iner['cov']
            cho = self.param_iner['cho']
            for i, (meani, covi, choi) in enumerate(zip(mean, cov, cho)):
                randxv = self.rgen.multivariate_normal(meani, covi, cho=choi,
                                                       size=ndim)
                # special case for just a single particle:
                if system.particles.npart == 1:
                    pos_rand = randxv[:, 0]
                    vel_rand = randxv[:, 1]
                else:
                    pos_rand[i] = randxv[:, 0]
                    vel_rand[i] = randxv[:, 1]

        particles.pos += self.param_iner['a1'] * particles.vel +\
                         self.param_iner['a2'] * particles.force + pos_rand

        vel2 = self.param_iner['c0'] * particles.vel +\
               self.param_iner['b1'] * particles.force + vel_rand

        system.force()  # update forces

        particles.vel = vel2 + self.param_iner['b2'] * particles.force
