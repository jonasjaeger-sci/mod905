# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""Definition of numerical integrators.

These integrators are typically used to integrate and propagate
Newtons equations of motion in time, the dynamics in molecular dynamics.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Integrator (:py:class:`pyretis.core.integrators.Integrator`)
    The base class for integrators

Verlet (:py:class:`pyretis.core.integrators.Verlet`)
    A Verlet integrator

VelocityVerlet (:py:class:`pyretis.core.integrators.VelocityVerlet`)
    A Velocity Verlet integrator

Langevin (:py:class:`pyretis.core.integrators.Langevin`)
    A Langevin integrator

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

integrator_factory (:py:func:`pyretis.core.integrators.integrator_factory`)
    Method for setting up and creating an integrator from
    simulation settings.
"""
from __future__ import absolute_import
import logging
import numpy as np
from pyretis.core.common import generic_factory
from pyretis.core.random_gen import RandomGenerator
from pyretis.core.particlefunctions import calculate_thermo_path
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['Integrator', 'Verlet', 'VelocityVerlet', 'Langevin',
           'integrator_factory']


def integrator_factory(settings):
    """Create an integrator according to the given integrator settings.

    This function is included as a convenient way of setting up and
    selecting a integrator. It will return the selected integrator.

    Parameters
    ----------
    settings : dict
        This defines how we set up and select the integrator.

    Returns
    -------
    out : object like `Integrator`.
        This object represents the integrator and will be one of the
        classes defined in `pyretis.core.integrators`.
    """
    integrator_map = {'velocityverlet': {'cls': VelocityVerlet},
                      'verlet': {'cls': Verlet},
                      'langevin': {'cls': Langevin}}
    return generic_factory(settings, integrator_map, name='integrator')


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
            to delegte the creation of the path (type) to the method
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
        status = 'Generating path...'
        logger.debug(status)
        success = False
        initial_system = system.particles.get_phase_point()
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
        msg = 'Propagate done: "{}" (success: {}'.format(status, success)
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


class Verlet(Integrator):
    """Verlet(Integrator).

    This class defines the Verlet integrator.

    Attributes
    ----------
    delta_t : float
        The integrator time step.
    half_idt : float
        Half of inverse time step: `0.5 / delta_t`
    delta_t2 : float
        Squared time step: `delta_t**2`
    """

    def __init__(self, timestep, desc='The verlet integrator'):
        """Initiate the Verlet integrator.

        Parameters
        ----------
        timestep : float
            The time step in internal units.
        desc : string
            Description of the integrator
        """
        super(Verlet, self).__init__(timestep, desc=desc, dynamics='NVE')
        self.half_idt = 0.5 / self.delta_t
        self.delta_t2 = self.delta_t**2
        self.previous_pos = None

    def set_initial_positions(self, particles):
        """Initiate the positions for the Verlet integration.

        Parameters
        ----------
        particles : object
            The initial configuration. Positions and velocities are
            required.
        """
        self.previous_pos = particles.pos - particles.vel * self.delta_t

    def integration_step(self, system):
        """Perform one Verlet integration step.

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
        acc = particles.force * particles.imass
        pos = 2.0 * particles.pos - self.previous_pos + acc * self.delta_t2
        particles.vel = (pos - self.previous_pos) * self.half_idt
        self.previous_pos, particles.pos = particles.pos, pos
        system.potential_and_force()
        return None


class VelocityVerlet(Integrator):
    """VelocityVerlet(Integrator).

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
        super(VelocityVerlet, self).__init__(timestep, desc=desc,
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


class Langevin(Integrator):
    """Langevin(Integrator).

    This class defines a Langevin integrator.

    Attributes
    ----------
    rgen : object like `RandomGenerator` from `pyretis.core.random_gen`
        This is the class that handles generation of random numbers.
    gamma : float
        The friction parameter.
    high_friction : boolean
        Determines if we are in the high friction limit and should
        do the over-damped version.
    init_params : boolean
        If true, we will initiate parameters for the Langevin
        integrator when `integrate_step` is invoked.
    param_high : dict
        This contains the parameters for the high friction limit. Here
        we integrate the equations of motion according to:
        ``r(t + dt) = r(t) + dt * f(t)/m*gamma + dr``.
        The items in the dict are:

        * `sigma` : float
          standard deviation for the positions, used when drawing dr
        * `bddt` : numpy.array
          Equal to ``dt*gamma/masses``, since the masses is a
          numpy.array this will have the same shape.
    param_iner : dict
        This dict contains the parameters for the non-high friction
        limit where we integrate the equations of motion according to:
        ``r(t + dt) = r(t) + c1 * dt * v(t) + c2*dt*dt*a(t) + dr``
        and
        ``v(r + dt) = c0 * v(t) + (c1-c2)*dt*a(t) + c2*dt*a(t+dt) + dv``.
        The dict contains:

        * `c0` : float
          Corresponds to ``c0`` in the equation above.
        * `a1` : float
          Corresponds to ``c1*dt`` in the equation above.
        * `a2` : numpy.array
          Corresponds to ``c2*dt*dt/mass`` in the equation above.
          Here we divide by the masses in order to use the forces rather
          than the acceleration. Since the masses might be different for
          different particles, this will result in a numpy.array with
          shape equal to the shape of the masses.
        * `b1` : numpy.array
          Corresponds to ``(c1-c2)*dt/mass`` in the equation above.
          Here we also divide by the masses, resulting in a numpy.array.
        * `b2` : numpy.array
          Corresponds to ``c2*dt/mass`` in the equation above.
          Here we also divide by the masses, resulting in a numpy.array.
        * `mean` : numpy.array (2,)
          The means for the bivariate Gaussian distribution.
        * `cov` : numpy.array (2,2)
          This array contains the covariance for the bivariate Gaussian
          distribution. `param_iner['mean']` and `param_iner['cov']` are
          used as parameters when drawing ``dr`` and ``dv`` from the
          bivariate distribution.

    Note
    ----
    Currently, we are using a multi-normal distribution from numpy.
    Consider replacing this one as it seems somewhat slow.
    """

    def __init__(self, timestep, gamma, rgen=None, seed=0, high_friction=False,
                 desc='Langevin integrator'):
        """Initiate the Langevin integrator.

        Actually, it is very convenient to set some variables for the
        different particles. However, to have a uniform initialization
        for the different integrators, we postpone this.
        This initialization can be done later by calling explicitly the
        function `self._init_parameters(system)` or it will be called
        the first time `self.integration_step` is invoked.

        Parameters
        ----------
        timestep : float
            The time step in internal units.
        gamma : float
            The gamma parameter for the Langevin integrator
        rgen : object like `RandomGenerator` from `.random_gen`.
            This is the class that will handle the random number
            generation for us. If not given, a `RandomGenerator` will
            be created here.
        seed : integer, optional.
            A seed which can be used if a `RandomGenerator` is to be
            created here.
        high_friction : boolean
            Determines if we are in the high_friction limit and should
            do the over-damped version.
        desc : string
            Description of the integrator.
        """
        super(Langevin, self).__init__(timestep, desc=desc,
                                       dynamics='stochastic')
        self.gamma = gamma
        self.high_friction = high_friction
        if rgen is None:
            msg = ['Langevin Integrator: Initiated new random generator']
            msg += ['Seed was set to: {}'.format(seed)]
            msgtxt = '\n'.join(msg)
            logger.debug(msgtxt)
            self.rgen = RandomGenerator(seed=seed)
        else:
            self.rgen = rgen
        self.param_high = {'sigma': None, 'bddt': None}
        self.param_iner = {'c0': None, 'a1': None, 'a2': None,
                           'b1': None, 'b2': None, 'mean': None, 'cov': None}
        self.init_params = True

    def _init_parameters(self, system):
        """Extra initialization of the Langevin integrator.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`
            The system to integrate/act on. Assumed to have a particle
            list in `system.particles`.

        Returns
        -------
        out : None
            Does not return anything, but updates `self.param`.
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
                sig_ri2 = ((self.delta_t * imass[0] / (beta * self.gamma)) *
                           (2. - (3. - 4.*exp_gdt + exp_gdt**2) / gammadt))
                sig_vi2 = ((1.0 - exp_gdt**2) * imass[0] / beta)
                cov_rvi = (imass[0]/(beta * self.gamma)) * (1.0 - exp_gdt)**2
                cov_matrix = np.array([[sig_ri2, cov_rvi],
                                       [cov_rvi, sig_vi2]])
                self.param_iner['cov'].append(cov_matrix)
                self.param_iner['cho'].append(np.linalg.cholesky(cov_matrix))
                self.param_iner['mean'].append(np.zeros(2))
                # NOTE: Can be simplified - mean is always just zero...

    def integration_step(self, system):
        """Langevin integration, one time step.

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
        if self.init_params:
            self._init_parameters(system)
            self.init_params = False
        if self.high_friction:
            return self.integration_step_overdamped(system)
        else:
            return self.integration_step_inertia(system)

    def integration_step_overdamped(self, system):
        """Over damped Langevin integration, one time step.

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
        system.force()  # update forces
        particles = system.particles
        rands = self.rgen.normal(loc=0.0, scale=self.param_high['sigma'],
                                 size=particles.vel.shape)
        particles.pos += self.param_high['bddt'] * particles.force + rands
        particles.vel = rands
        system.potential()
        return None

    def integration_step_inertia(self, system):
        """Langevin integration, one time step.

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
        ndim = system.get_dim()
        pos_rand = np.zeros(particles.pos.shape)
        vel_rand = np.zeros(particles.vel.shape)
        if self.gamma > 0.0:
            mean, cov = self.param_iner['mean'], self.param_iner['cov']
            cho = self.param_iner['cho']
            for i, (meani, covi, choi) in enumerate(zip(mean, cov, cho)):
                randxv = self.rgen.multivariate_normal(meani, covi, cho=choi,
                                                       size=ndim)
                pos_rand[i] = randxv[:, 0]
                vel_rand[i] = randxv[:, 1]
        particles.pos += (self.param_iner['a1'] * particles.vel +
                          self.param_iner['a2'] * particles.force + pos_rand)

        vel2 = (self.param_iner['c0'] * particles.vel +
                self.param_iner['b1'] * particles.force + vel_rand)

        system.force()  # update forces

        particles.vel = vel2 + self.param_iner['b2'] * particles.force

        system.potential()
        return None
