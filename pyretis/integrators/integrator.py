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
import logging
from pyretis.core.particlefunctions import (calculate_kinetic_energy,
                                            reset_momentum)

logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['Integrator']


class Integrator(object):
    """Base class for integrators.

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
        path : object like `Path` from `pyretis.core.Path`
            This is the path we use to fill in phase-space point.
            We are here not returning a new path - this since we want
            to delegate the creation of the path (type) to the method
            that is running `propagate`.
        system : object like `System` from `pyretis.core.system`
            The system object gives the initial state for the
            integration. The initial state is stored and the system is
            reset to the initial state when the integration is done.
        orderp : object like `OrderParameter` from `pyretis.orderparameter`
            The object used for calculating the order parameter.
        interfaces : list of floats
            These interfaces define the stopping criterion.
        reverse : boolean
            If True, the system will be propagated backwards in time.
        """
        if reverse:
            status = 'Generating backward path...'
        else:
            status = 'Generating forward path...'
        logger.debug(status)
        success = False
        initial_system = system.particles.get_particle_state()
        system.potential_and_force()  # make sure forces are set
        left, _, right = interfaces
        for _ in range(path.maxlen):
            order = self.calculate_order(orderp, system)
            kin = calculate_kinetic_energy(system.particles)[0]
            phasepoint = {'order': order, 'pos': system.particles.pos,
                          'vel': system.particles.vel, 'vpot': system.v_pot,
                          'ekin': kin}
            add = path.append(phasepoint)
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
            if path.length == path.maxlen:
                # Next step will just exceed path length,
                # no need to actually do it
                #status = 'Max. path length exceeded'
                #success = False
                #break
                pass
            if reverse:
                system.particles.vel *= -1.0
                self.integration_step(system)
                system.particles.vel *= -1.0
            else:
                self.integration_step(system)
        system.particles.set_particle_state(initial_system)
        msg = 'Propagate done: "{}" (success: {})'.format(status, success)
        logger.debug(msg)
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
        system : object like :py:class:`core.system.System`
            System is used here since we need access to the particle
            list.
        rgen : object like :py:class:`core.random_gen.RandomGenerator`
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
            kin_old = rescale - system.v_pot
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

    @staticmethod
    def calculate_order(order_function, system):
        """Return the order parameter.

        This method is just to help calculating the order parameter
        in cases where only the integrator can do it! This creates
        a uniform behavior for both internal and external integrators.
        For internal integrators this is not useful in it self, since
        we could just call  `order.calculate(system)`. But for
        external integrators, we can not assume that the system is able
        to calculate the order parameter, this because the state of the
        system might be stored in a file which only the integrator knows
        how to read.

        Parameters
        ----------
        order_function : object like `OrderParameter`
            The object used for calculating the order parameter(s).
        system : object like `pyretis.core.system.System`
            The system containing the corrent positions and velocities.

        Returns
        -------
        out : list of floats
            The calculated order parameters
        """
        return order_function(system)

    def kick_across_middle(self, system, order_function, rgen, middle,
                           tis_settings):
        """Force a phase point across the middle interface.

        This is accomplished by repeatedly kicking the pahse point so
        that it crosses the middle interface.

        Parameters
        ----------
        system : object like :py:class:`.system.System`
            This is the system that contains the particles we are
            investigating
        order_function : object like :py:class:`OrderParameter`
            The object used for calculating the order parameter.
        rgen : object like :py:class:`.random_gen.RandomGenerator`
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
        curr = self.calculate_order(order_function, system)[0]
        while True:
            # save current state:
            previous = particles.get_particle_state()
            previous['order'] = curr
            # Modify velocities
            self.modify_velocities(system,
                                   rgen,
                                   sigma_v=None,
                                   aimless=True,
                                   momentum=tis_settings['zero_momentum'],
                                   rescale=tis_settings['rescale_energy'])
            # Integrate forward one step:
            self.integration_step(system)
            # Compare previous order parameter and the new one:
            prev = curr
            curr = self.calculate_order(order_function, system)[0]
            if (prev <= middle < curr) or (curr < middle <= prev):
                # have crossed middle interface, just stop the loop
                break
            elif (prev <= curr < middle) or (middle < curr <= prev):
                # are getting closer, keep the new point
                pass
            else:  # we did not get closer, fall back to previous point
                particles.set_particle_state(previous)
                curr = previous['order']
        return previous, particles.get_particle_state()

    def __str__(self):
        """Return the string description of the integrator."""
        return self.desc


