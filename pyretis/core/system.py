# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""Module defining the system class


Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

System
    A class representing a system. A system object defines the system
    the simulation acts and contains information about particles,
    force fields etc.
"""
from __future__ import absolute_import
import logging
import numpy as np
# from the pyretis package
from pyretis.core.units import CONSTANTS
from pyretis.core.particles import Particles
from pyretis.core.particlefunctions import (calculate_kinetic_temperature,
                                            calculate_kinetic_energy)
from pyretis.core.random_gen import RandomGenerator
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['System']


class System(object):
    """This class defines a generic system for simulation.

    Attributes
    ----------
    box : object like `Box` from `pyretis.core.box`
        Defines the simulation box.
    temperature : dict
        This dictionary contains information on the temperature. The
        following information is stored:

        * `set`: The set temperature, ``T``, (if any).
        * `beta`: The derived property ``1.0/(k_B*T)``.
        * `dof`: Information about the degrees of freedom for the
          system.
    v_pot : float
        The potential energy of the system.
    particles : object like `pyretis.core.particles.Particles`
        Defines the particle list which represents the particles and the
        properties of the particles (positions, velocities, forces etc.)
    post_setup : list of tuples
        This list contain extra functions that should be called when
        preparing to run a simulation. This is typically functions that
        should only be called after the system is fully set up. The
        tuples should correspond to ('function', args) where
        such that ``system.function(*args)`` can be called.
    forcefield : object like `ForceField` from `pyretis.forcefield`
        Defines the force field to use and implements the actual force
        and potential calculation.
    order_function : object like `OrderParameter` from `.orderparameter`
        Defines the an order parameter to use for the system. See
        :py:mod:`pyretis.core.orderparameter` for the definition
        of order parameters.
    units : string
        Units to use for the system/simulation. Should match the defined
        units in :py:mod:`pyretis.core.units`.
    """

    def __init__(self, units='lj', box=None, temperature=None):
        """Initialization of the system.

        Parameters
        ----------
        box : object like `Box` from `pyretis.core.box`
            This variable represents the simulation box. It is used to
            determine the number of dimensions
        temperature : float
            The (desired) temperature of the system, if applicable.
        units : string
            The system of units to use in the simulation box.
        energy : float, optional
            In case we want to fix the total energy of the system to
            a given value.

        Note
        ----
        `self.temperature` is defined as a dictionary. This is just
        because it's convenient to include information about the
        degrees of freedom of the system here. In the future one could
        possibly have a more general temperature object.
        """
        self.units = units
        self.temperature = {'set': temperature, 'dof': None}
        self.temperature['beta'] = self.calculate_beta()
        self.box = box
        self._adjust_dof_according_to_box()
        # initialize other variables:
        self.v_pot = 0.0  # TODO: Consider making v_pot a particle attrib.!
        self.particles = Particles(dim=self.get_dim())  # empty particle list
        self.forcefield = None
        self.order_function = None
        self.orderp = None
        self.post_setup = []

    def adjust_dof(self, dof):
        """Adjust the degrees of freedom to neglect in the system.

        Parameters
        ----------
        dof : numpy.array
            The degrees of freedom to neglect, in addition to the ones
            we already have neglected.
        """
        if self.temperature['dof'] is None:
            self.temperature['dof'] = np.array(dof)
        else:
            self.temperature['dof'] += np.array(dof)

    def _adjust_dof_according_to_box(self):
        """Adjust the dof's according to the box connected to the system.

        For each 'True' in the periodic settings of the box, we subtract
        one degree of freedom for that dimension.
        """
        try:
            dof = []
            all_false = True
            for peri in self.box.periodic:
                dof.append(1 if peri else 0)
                all_false = all_false and not peri
            # If all items in self.box.periodic are false, then we
            # will not bother setting the dof to just zeros
            if not all_false:
                self.adjust_dof(dof)
            return True
        except AttributeError:
            return False

    def get_boltzmann(self):
        """Return the Boltzmann constant in correct units for the system.

        Returns
        -------
        out : float
            The Boltzmann constant.
        """
        return CONSTANTS['kB'][self.units]

    def get_dim(self):
        """Return the dimensionality of the system.

        The value is obtained from the box. In other words,
        it is the box object that defines the dimensionality of
        the system.

        Returns
        -------
        out : integer
            The number of dimensions of the system.
        """
        try:
            return self.box.dim
        except AttributeError:
            msg = 'Box dimensions are not set. Setting dimensions to "1"'
            logger.warning(msg)
            return 1

    def calculate_beta(self, temperature=None):
        r"""Return the so-called beta factor for the system.

        Beta is defined as :math:`\beta = 1/(k_\text{B} \times T)`
        where :math:`k_\text{B}` is the Boltzmann constant and the
        temperature `T` is either specified in the parameters or assumed
        equal to the set temperature of the system.

        Parameters
        ----------
        temperature : float, optional
            The temperature of the system. If the temperature
            is not given, `self.temperature` will be used.

        Returns
        -------
        out : float
            The calculated beta factor, or None if no temperature data
            is available.
        """
        if temperature is None:
            if self.temperature['set'] is None:
                return None
            else:
                temperature = self.temperature['set']
        return 1.0 / (temperature * CONSTANTS['kB'][self.units])

    def add_particle(self, pos, vel=None, force=None,
                     mass=1.0, name='?', ptype=0):
        """Add a particle to the system.

        Parameters
        ----------
        pos : numpy.array,
            Position of the particle.
        vel : numpy.array, optional.
            Velocity of the particle. If not given numpy.zeros will be
            used.
        force : numpy.array, optional.
            Force on the particle. If not given np.zeros will be used.
        mass : float, optional.
            Mass of the particle, default is 1.0.
        name : string, optional.
            Name of the particle, default is '?'.
        ptype : integer, optional. Particle type.
            Particle type, default is 0.

        Returns
        -------
        out : None
            Does not return anything, but updates `system.particles`.
        """
        dim = self.get_dim()
        if vel is None:
            vel = np.zeros(dim)
        if force is None:
            force = np.zeros(dim)
        self.particles.add_particle(pos, vel, force, mass=mass,
                                    name=name, ptype=ptype)

    def calculate_order(self):
        """Calculates and updates the order parameter"""
        if self.order_function:
            order = self.order_function.__call__(self)
            # TODO: Maybe consider if we should create a new object that
            # is a composition of system, orderparameter and force field,
            # i.e. newobject.system, newobject.orderparameter, newobject.ff
            # etc. Then we could do newobject.calculate_order() which does
            # self.orderparameter(self.system, self.forcefield) for instance...
            self.orderp = order
        return self.orderp

    def force(self):
        """Update the forces and virial

        The update is done by calling `self._evaluate_potential_force`.

        Returns
        -------
        out[1] : numpy.array.
            Forces on the particles. Note that `self.particles.force`
            will also be updated.
        out[2] : float.
            The virial. Note that `self.particles.virial` will be
            updated.
        """
        force, virial = self.forcefield.evaluate_force(self)
        self.particles.force = force
        self.particles.virial = virial
        return self.particles.force, virial

    def potential(self):
        """Update the potential energy in `self.v_pot`.

        Returns
        -------
        out : float.
            The potential energy, note `self.v_pot` is also updated.
        """
        self.v_pot = self.forcefield.evaluate_potential(self)
        return self.v_pot

    def potential_and_force(self):
        """Update the potential energy and forces.

        The potential in `self.v_pot` and the forces in
        `self.particles.force` are here updated by calling
        `forcefield.evaluate_potential_force()`.

        Returns
        -------
        out[1] : float
            The potential energy, note self.v_pot is also updated.
        out[2] : numpy.array.
            Forces on the particles. Note that self.particles.force will
            also be updated.
        out[3] : float.
            The virial. Note that `self.particles.virial` will also be
            updated.
        """
        pot, force, viri = self.forcefield.evaluate_potential_and_force(self)
        self.v_pot = pot
        self.particles.force = force
        self.particles.virial = viri
        return pot, force, viri

    def evaluate_force(self):
        """Evaluate the forces on the particles.

        Returns
        -------
        out[1] : numpy.array
            Forces on the particles.
        out[2] : float
            The virial.

        Note
        ----
        This function will not update the forces, just calculate them.
        Use `self.force` to update the forces.
        """
        return self.forcefield.evaluate_force(self)

    def evaluate_potential(self):
        """Evaluate the potential energy.

        Returns
        -------
        out : float
            The potential energy.

        Note
        ----
        This function will not update `self.v_pot` but it will just
        return it's value for the (possibly given) configuration.
        The function `self.potential` can be used to update `self.v_pot`.
        """
        return self.forcefield.evaluate_potential(self)

    def evaluate_potential_and_force(self):
        """Evaluate the potential and/or the force.

        Returns
        -------
        out[1] : float
            The potential energy.
        out[2] : numpy.array
            Forces on the particles.
        out[3] : float
            The virial.

        Note
        ----
        This function will not update the forces on the particles nor
        `self.v_pot`. To update these, call `self.potential_and_force`.
        """
        return self.forcefield.evaluate_potential_and_force(self)

    def generate_velocities(self, rgen=None, seed=0, momentum=True,
                            temperature=None, distribution='maxwell'):
        """Set velocities for the particles according to a given temperature.

        The temperature can be specified, or it can be taken from
        `self.temperature['set']`.

        Parameters
        ----------
        rgen : object like `RandomGenerator` from `.random_gen`.
            This is the random generator which handles the drawing of
            velocities. If not given, a `RandomGenerator` object will
            be created with a given `seed` (see below).
        seed : int, optional
            Seed for the `RandomGenerator` in case `rgen` is not given.
        momentum : boolean, optional
            Determines if the momentum should be reset.
        temperature : float, optional
            The desired temperature to set.
        distribution : str
            Selects a distribution for generating the velocities.

        Returns
        -------
        out : None
            Does not return anything, but updates
            `system.particles.vel`.
        """
        if rgen is None:
            rgen = RandomGenerator(seed=seed)
        if temperature is None:
            temperature = self.temperature['set']
        dof = self.temperature['dof']
        if distribution.lower() == 'maxwell':
            rgen.generate_maxwellian_velocities(self.particles,
                                                CONSTANTS['kB'][self.units],
                                                temperature,
                                                dof, momentum=momentum)
        else:
            msg = 'Distribution "{}" not defined! Velocities not set!'
            msg = msg.format(distribution)
            logger.error(msg)

    def calculate_temperature(self):
        """Calculate the temperature of the system.

        It is included here for convenience since the degrees of freedom
        are easily accessible and it's a very common calculation to
        perform, even though it might be cleaner to include it as a
        particle function.

        Returns
        -------
        out : float
            The temperature of the system
        """
        dof = self.temperature['dof']
        _, temp, _ = calculate_kinetic_temperature(self.particles,
                                                   CONSTANTS['kB'][self.units],
                                                   dof=dof)
        return temp

    def extra_setup(self):
        """Perform extra set-up for the system.

        The extra set-up will typically be tasks that can only
        be performed after the system is fully set-up, for instance
        after the force field is properly defined.
        """
        for func_name, args in self.post_setup:
            func = getattr(self, func_name, None)
            if func is not None:
                func(*args)

    def rescale_velocities(self, energy):
        """Rescale the kinetic energy to a given total energy.

        Parameters
        ----------
        energy : float
            The desired energy.

        Returns
        -------
        None, but updates the velocities of the particles.
        """
        vpot = self.potential()
        ekin, _ = calculate_kinetic_energy(self.particles)
        ekin_new = energy - vpot
        if ekin_new < 0:
            msg = ('Can not rescale velocities. '
                   'Target: {}, Pot = {}'.format(energy, vpot))
            logger.warning(msg)
        else:
            alpha = np.sqrt(ekin_new / ekin)
            self.particles.vel = self.particles.vel * alpha
