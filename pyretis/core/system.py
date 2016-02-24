# -*- coding: utf-8 -*-
"""Definition of the system class.

The system object defines the system the simulation acts on. The system
object contains particles, a force field and a box.
"""
from __future__ import absolute_import
import logging
import numpy as np
# from the pyretis package
from pyretis.core.units import CONSTANTS
from pyretis.core.particles import Particles
from pyretis.core.particlefunctions import calculate_kinetic_temperature
from pyretis.core.random_gen import RandomGenerator
logging.getLogger(__name__).addHandler(logging.NullHandler())


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
        the potential energy of the system
    particles : object like `pyretis.core.particles.Particles`
        Defines the particle list which represents the particles and the
        properties of the particles (positions, velocities, forces etc.)
    forcefield : object like `ForceField` from `pyretis.forcefield`
        Defines the force field to use and implements the actual force
        and potential calculation.
    units : string
        Units to use for the system/simulation. Should match the defined
        units in `pyretis.core.units`.
    """

    def __init__(self, units='eV/K', box=None, temperature=None):
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
            logging.warning(msg)
            return 1

    def calculate_beta(self, temperature=None):
        r"""Return the so-called beta factor for the system.

        Beta is defined as :math:`\beta = 1/(k_\text{B} \times T`
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
                     mass=1.0, name='?', ptype='?'):
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
            Mass of the particle, default is 1.0
        name : string, optional.
            Name of the particle, default is '?'
        ptype : string, optional. Particle type.
            Particle type, default is '?'

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

    def force(self):
        """Update the forces by calling `self._evaluate_potential_force`.

        Returns
        -------
        out[1] : numpy.array.
            Forces on the particles. Note that `self.particles.force`
            will also be updated.
        out[2] : float.
            The virial. Note that `self.particles.virial` will be
            updated.
        """
        force, virial = self._evaluate_potential_force(what='force')
        self.particles.force = force
        self.particles.virial = virial
        return self.particles.force, virial

    def potential(self):
        """Update `self.v_pot` by calling `self._evaluate_potential_force()`.

        Returns
        -------
        out : float.
            The potential energy, note `self.v_pot` is also updated.
        """
        self.v_pot = self._evaluate_potential_force(what='potential')
        return self.v_pot

    def potential_and_force(self):
        """Update the potential energy and forces.

        The potential in `self.v_pot` and the forces in
        `self.particles.force` are here updated by calling
        `self._evaluate_potential_force()`.

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
        v_pot, force, virial = self._evaluate_potential_force(what='both')
        self.v_pot = v_pot
        self.particles.force = force
        self.particles.virial = virial
        return v_pot, force, virial

    def evaluate_force(self, **kwargs):
        """Evaluate the forces on the particles.

        Parameters
        ----------
        kwargs : dictionary
            Settings that can be used to override the information in
            `self.particles`. This is useful if one wants to evaluate
            the forces for a different configuration of the particles.

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
        return self._evaluate_potential_force(what='force', **kwargs)

    def evaluate_potential(self, **kwargs):
        """Evaluate the potential energy.

        Parameters
        ----------
        kwargs : dictionary
            Settings that can be used to override the information in
            `self.particles`. This is useful if one wants to evaluate
            the forces for a different configuration of the particles.

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
        return self._evaluate_potential_force(what='potential', **kwargs)

    def evaluate_potential_and_force(self, **kwargs):
        """Evaluate the potential and/or the force.

        Parameters
        ----------
        kwargs : dictionary
            Settings that can be used to override the information in
            `self.particles`. This is useful if one wants to evaluate
            the forces for a different configuration of the particles.

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
        return self._evaluate_potential_force(what='both', **kwargs)

    def _evaluate_potential_force(self, what='both', **kwargs):
        """Evaluate the potential or force or both.

        Parameters
        ----------
        what : string
            This selects what we are to evaluate. 'potential' selects
            the potential energy only, 'force' selects the force only
            and anything else will give both.
        kwargs : dict
            This dictionary can be used to override position, name,
            types, particles and/or box. Default values are taken from
            `self.box` or `self.particles`.
        """
        args = {'pos': kwargs.get('pos', self.particles.pos),
                'name': kwargs.get('name', self.particles.name),
                'ptype': kwargs.get('ptype', self.particles.ptype),
                'particles': kwargs.get('particles', self.particles),
                'box': kwargs.get('box', self.box)}
        # Here we allow for **args when calling the force field. This is
        # simply because we do not know what parameters we should
        # pass into the force field.
        if what == 'potential':
            return self.forcefield.evaluate_potential(**args)
        elif what == 'force':
            return self.forcefield.evaluate_force(**args)
        else:
            return self.forcefield.evaluate_potential_and_force(**args)

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
            logging.error(msg)

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
