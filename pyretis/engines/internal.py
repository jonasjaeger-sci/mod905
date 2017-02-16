# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Definition of numerical MD integrators.

These integrators are representations of engines for performing
molecular dynamics. Typically they will propagate Newtons
equations of motion in time numerically.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

MDEngine (:py:class:`.MDEngine`)
    Base class for internal MDEngines.

Verlet (:py:class:`.Verlet`)
    A Verlet MD integrator.

VelocityVerlet (:py:class:`.VelocityVerlet`)
    A Velocity Verlet MD integrator.

Langevin (:py:class:`.Langevin`)
    A Langevin MD integrator.
"""
import logging
import numpy as np
from pyretis.engines.engine import EngineBase
from pyretis.core.random_gen import create_random_generator
from pyretis.core.particlefunctions import (calculate_kinetic_energy,
                                            reset_momentum)


logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['MDEngine', 'Verlet', 'VelocityVerlet', 'Langevin']


class MDEngine(EngineBase):
    """Base class for internal MD integrators.

    This class defines an internal MD integrator. This class of
    integrators work with the positions and velocities of the system
    object directly. Further, we make use of the system object in
    order to update forces etc.

    Attributes
    ----------
    delta_t : float
        Time step for the integration.
    description : string
        Description of the MD integrator.
    dynamics : str
        A short string to represent the type of dynamics produced
        by the integrator (NVE, NVT, stochastic, ...).
    """
    engine_type = 'internal'

    def __init__(self, timestep, description, dynamics=None):
        """Initialization of the integrator.

        Parameters
        ----------
        timestep : float
            The time step for the integrator in internal units.
        """
        super().__init__(description)
        self.delta_t = timestep
        self.dynamics = dynamics

    def integration_step(self, system):
        """Perform one time step of the integration.

        Parameters
        ----------
        system : object like :py:class:`.System`
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

    def propagate(self, path, system, orderp, interfaces, reverse=False):
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
        path : object like :py:class:`.PathBase`
            This is the path we use to fill in phase-space points.
            We are here not returning a new path - this since we want
            to delegate the creation of the path (type) to the method
            that is running `propagate`.
        system : object like :py:class:`.System`
            The system object gives the initial state for the
            integration. The initial state is stored and the system is
            reset to the initial state when the integration is done.
        orderp : object like :py:class:`.OrderParameter`
            The object used for calculating the order parameter.
        interfaces : list of floats
            These interfaces define the stopping criterion.
        reverse : boolean
            If True, the system will be propagated backwards in time.

        Returns
        -------
        success : boolean
            This is True if we generated an acceptable path.
        status : string
            A text description of the current status of the propagation.
        """
        status = 'Propagate w/internal engine'
        logger.debug(status)
        success = False
        initial_system = system.particles.get_particle_state()
        system.potential_and_force()  # make sure forces are set
        left, _, right = interfaces
        for i in range(path.maxlen):
            order = self.calculate_order(orderp, system)
            kin = calculate_kinetic_energy(system.particles)[0]
            phasepoint = {'order': order,
                          'pos': system.particles.pos,
                          'vel': system.particles.vel,
                          'vpot': system.particles.vpot,
                          'ekin': kin}
            status, success, stop = self.add_to_path(path, phasepoint,
                                                     left, right)
            if stop:
                logger.debug('Stopping propagate at step: %i ', i)
                break
            if reverse:
                system.particles.vel *= -1.0
                self.integration_step(system)
                system.particles.vel *= -1.0
            else:
                self.integration_step(system)
        # Reset to initial config:
        system.particles.set_particle_state(initial_system)
        logger.debug('Propagate done: "%s" (success: %s)', status, success)
        return success, status

    @staticmethod
    def modify_velocities(system, rgen, sigma_v=None, aimless=True,
                          momentum=False, rescale=None):
        """Modify the velocities of the current state.

        This method will modify the velocities of a time slice.
        And it is part of the integrator since it, conceptually,
        fits here:  we are acting on the system and modifying it.

        Parameters
        ----------
        system : object like :py:class:`.System`
            System is used here since we need access to the particle
            list.
        rgen : object like :py:class:`.RandomGenerator`
            This is the random generator that will be used.
        sigma_v : numpy.array, optional
            These values can be used to set a standard deviation (one
            for each particle) for the generated velocities.
        aimless : boolean, optional
            Determines if we should do aimless shooting or not.
        momentum : boolean, optional
            If True, we reset the linear momentum to zero after generating.
        rescale : float, optional
            In some NVE simulations, we may wish to rescale the energy to
            a fixed value. If `rescale` is a float > 0, we will rescale
            the energy (after modification of the velocities) to match the
            given float.

        Returns
        -------
        dek : float
            The change in the kinetic energy.
        kin_new : float
            The new kinetic energy.
        """
        particles = system.particles
        if rescale is not None and rescale is not False and rescale > 0:
            kin_old = rescale - particles.vpot
        else:
            kin_old = calculate_kinetic_energy(particles)[0]
        if aimless:
            vel, _ = rgen.draw_maxwellian_velocities(system)
            particles.vel = vel
        else:  # soft velocity change, add from Gaussian dist
            dvel, _ = rgen.draw_maxwellian_velocities(system, sigma_v=sigma_v)
            particles.vel = particles.vel + dvel
        if momentum:
            reset_momentum(particles)
        if rescale:
            system.rescale_velocities(rescale)
        kin_new = calculate_kinetic_energy(particles)[0]
        dek = kin_new - kin_old
        return dek, kin_new

    def __call__(self, system):
        """To allow calling `MDEngine(system)`.

        Here, we are just calling `self.integration_step(system)`.

        Parameters
        ----------
        system : object like :py:class:`.System`
            The system we are integrating.

        Returns
        -------
        out : None
            Does not return anything, but will update the particles.
        """
        return self.integration_step(system)

    @staticmethod
    def calculate_order(order_function, system):
        """Return the order parameter.

        This method is just to help calculating the order parameter
        in cases where only the engine can do it! This creates
        a uniform behavior for both internal and external engines.
        For internal engine this may not be so useful in it self, since
        we could just call `order.calculate(system)`. But for external
        engines, we can not assume that the system is able
        to calculate the order parameter, this because the state of the
        system might be stored in a file which only the engine knows
        how to read.

        Parameters
        ----------
        order_function : object like :py:class:`.OrderParameter`
            The object used for calculating the order parameter(s).
        system : object like :py:class:`.System`
            The system containing the corrent positions and velocities.

        Returns
        -------
        out : list of floats
            The calculated order parameters
        """
        return order_function.calculate_all(system)

    def kick_across_middle(self, system, order_function, rgen, middle,
                           tis_settings):
        """Force a phase point across the middle interface.

        This is accomplished by repeatedly kicking the pahse point so
        that it crosses the middle interface.

        Parameters
        ----------
        system : object like :py:class:`.System`
            This is the system that contains the particles we are
            investigating
        order_function : object like :py:class:`.OrderParameter`
            The object used for calculating the order parameter.
        rgen : object like :py:class:`.RandomGenerator`
            This is the random generator that will be used.
        middle : float
            This is the value for the middle interface.
        tis_settings : dict
            This dictionary contains settings for TIS. Explicitly used here:

            * `zero_momentum`: boolean, determines if the momentum is zeroed
            * `rescale_energy`: boolean, determines if energy is rescaled.

        Returns
        -------
        out[0] : dict
            This dict contains the phase-point just before the interface.
            It is obtained by calling the `get_particle_state()` of the
            particles object.
        out[1] : dict
            This dict contains the phase-point just after the interface.
            It is obtained by calling the `get_particle_state()` of the
            particles object.

        Note
        ----
        This function will update the system state so that the
        `system.particles.get_particle_state() == out[1]`.
        This is more convenient for the following usage in the
        `generate_initial_path_kick` function.
        """
        # We search for crossing with the middle interface and do this
        # by sequentially kicking the initial phase point:
        previous = None
        particles = system.particles
        system.potential_and_force()  # make sure forces are set
        curr = self.calculate_order(order_function, system)[0]
        while True:
            # save current state:
            previous = particles.get_particle_state()
            # Modify velocities
            self.modify_velocities(system,
                                   rgen,
                                   sigma_v=None,
                                   aimless=True,
                                   momentum=tis_settings['zero_momentum'],
                                   rescale=tis_settings['rescale_energy'])
            # Update order parameter in case it is velocity dependent:
            curr = self.calculate_order(order_function, system)[0]
            previous['order'] = curr
            # Store modified velocities
            previous['vel'] = system.particles.get_vel()
            # Integrate forward one step:
            self.integration_step(system)
            # Compare previous order parameter and the new one:
            prev = curr
            curr = self.calculate_order(order_function, system)[0]
            if (prev <= middle < curr) or (curr < middle <= prev):
                # have crossed middle interface, just stop the loop
                logger.info('Crossing found: %9.6f %9.6f ', prev, curr)
                break
            elif (prev <= curr < middle) or (middle < curr <= prev):
                # We are getting closer, keep the new point
                pass
            else:  # we did not get closer, fall back to previous point
                particles.set_particle_state(previous)
                curr = previous['order']
        return previous, particles.get_particle_state()

    def dump_phasepoint(self, phasepoint, deffnm=None):
        """This method is just for compatibility with external integrators."""
        pass

    def clean_up(self):
        """Clean up after using the engine.

        Currently this is only included for compatibility with external
        integrators.
        """
        pass


class Verlet(MDEngine):
    """The Verlet MD integrator.

    This class defines the Verlet MD integrator.

    Attributes
    ----------
    delta_t : float
        The integrator time step.
    half_idt : float
        Half of inverse time step: `0.5 / delta_t`
    delta_t2 : float
        Squared time step: `delta_t**2`
    """

    def __init__(self, timestep):
        """Initiate the Verlet MD integrator.

        Parameters
        ----------
        timestep : float
            The time step in internal units.
        """
        super().__init__(timestep, 'Verlet MD integrator', dynamics='NVE')
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
        system : object like :py:class:`.System`
            The system to integrate/act on. Assumed to have a particle
            list in ``system.particles``.

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


class VelocityVerlet(MDEngine):
    """The Velocity Verlet MD integrator.

    This class defines the Velocity Verlet integrator.

    Attributes
    ----------
    half_delta_t : float
        Half of timestep.
    """

    def __init__(self, timestep):
        """Initiate the Velocity Verlet integrator.

        Parameters
        ----------
        timestep : float
            The time step in internal units.
        """
        super().__init__(timestep, 'Velocity Verlet MD integrator',
                         dynamics='NVE')
        self.half_delta_t = self.delta_t * 0.5

    def integration_step(self, system):
        """Velocity Verlet integration, one time step.

        Parameters
        ----------
        system : object like :py:class:`.System`
            The system to integrate/act on. Assumed to have a particle
            list in ``system.particles``.

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


class Langevin(MDEngine):
    """The Langevin MD integrator.

    This class defines a Langevin integrator.

    Attributes
    ----------
    rgen : object like :py:class:`.RandomGenerator`
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

    def __init__(self, timestep, gamma, rgen=None, seed=0,
                 high_friction=False):
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
        rgen : string
            This string can be used to pick a particular random
            generator, which is useful for testing.
        seed : integer, optional
            A seed for the random generator.
        high_friction : boolean
            Determines if we are in the high_friction limit and should
            do the over-damped version.
        """
        super().__init__(timestep, 'Langevin MD integrator',
                         dynamics='stochastic')
        self.gamma = gamma
        self.high_friction = high_friction
        rgen_settings = {'seed': seed, 'rgen': rgen}
        self.rgen = create_random_generator(rgen_settings)
        self.param_high = {'sigma': None, 'bddt': None}
        self.param_iner = {'c0': None, 'a1': None, 'a2': None,
                           'b1': None, 'b2': None, 'mean': None, 'cov': None}
        self.init_params = True

    def _init_parameters(self, system):
        """Extra initialization of the Langevin integrator.

        Parameters
        ----------
        system : object like :py:class:`.System`
            The system to integrate/act on. Assumed to have a particle
            list in ``system.particles``.

        Returns
        -------
        out : None
            Does not return anything, but updates ``self.param``.
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
        system : object like :py:class:`.System`
            The system to integrate/act on. Assumed to have a particle
            list in ``system.particles``.

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
        system : object like :py:class:`.System`
            The system to integrate/act on. Assumed to have a particle
            list in ``system.particles``.

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
        system : object like :py:class:`.System`
            The system to integrate/act on. Assumed to have a particle
            list in ``system.particles``.

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
