# -*- coding: utf-8 -*-
"""
system.py
"""
from __future__ import absolute_import
import numpy as np
import warnings
# from the retis package
from .units import CONSTANTS
from .particles import Particles
from .particlefunctions import calculate_kinetic_temperature

__all__ = ['System']


class System(object):
    """
    This class defines a generic system for simulation.

    Attributes
    ----------
    box : object of Box type (defined in retis.core.box)
        Defines the simulation box.
    temperature : dict
        the float temperature['set'] defines the set temperature of the
        simulation (if applicable)  and the derived float 1.0/(kB*T)
        which is stored in temperature['beta'].
        temperature['dof'] contains information about the degrees of
        freedom which is used when calculating the instantaneous temperature
        of the system.
    v_pot : float
        the potential energy of the system
    particles : obj from retis.core.particles
        Defines the particleslist which represents the particles and the
        properties of the particles (positions, velocities, forces etc.)
    forcefield : ForceField object from retis.forcefield
        Defines the force field to use and implements the actual force
        and potential calculation.
    units : string
        Units to use for the system/simulation. Should match the defined units
        in retis.core.units.
    """
    def __init__(self, units='eV/K', box=None, temperature=None):
        """
        Initialization of the system.

        Parameters
        ----------
        box : object of type Box
            This variable represents the simulation box. It is used to
            determine the number of dimensions
        temperature : float
            The (desired) temperature of the system, if applicable.
        units : string
            The system of units to use in the simulation box.

        Returns
        -------
        N/A, but sets derived variables:

        Note
        ----
        self.temperature is defined as a dictionary. This is just
        because it's convenient to include information about the
        degrees of freedom of the system here. In the future one could
        possibly have a more general temperature object, but it's not
        really needed right now.
        """
        self.box = box
        self.units = units
        self.temperature = {'set': temperature, 'dof': None}
        self.temperature['beta'] = self.calculate_beta()
        # intialize other variables:
        self.v_pot = 0.0
        self.particles = Particles(dim=self.get_dim())  # empty particle list
        self.forcefield = None

    def adjust_dof(self, dof):
        """
        This method adjusts the degrees of freedom we are going to
        neglect for the system.

        Parameters
        ----------
        dof : numpy.array
            The degrees of freedom to add.
        """
        if isinstance(dof, list):
            dof = np.array(dof)
        if self.temperature['dof'] is None:
            self.temperature['dof'] = dof
        else:
            self.temperature['dof'] += dof

    def get_boltzmann(self):
        """
        This function returns the value of Boltzmanns constant
        in the correct units for the system

        Returns
        -------
        Boltzmanns constant as a float
        """
        return CONSTANTS['kB'][self.units]

    def get_dim(self):
        """
        This function returns the dimensionality of the system.
        The value is obtained from the box. In other words,
        it is the box object that defines the dimensionality of
        the system.

        Returns
        -------
        integer, representing the number of dimensions
        """
        try:
            return self.box.dim
        except AttributeError:
            warnings.warn('Box dimensions not set, defaulting to 1!')
            return 1

    def calculate_beta(self, temperature=None):
        """
        Updates the temperature and beta for the system

        Parameters
        ----------
        temperature : float, optional
            The temperature of the syste. If the temperature
            is not given, self.temperature will be used.

        Returns
        -------
        out : float
            The calculated 1.0/(kB*T)
        """
        if temperature is None:
            if self.temperature['set'] is None:
                return None
            else:
                temperature = self.temperature['set']
        return 1.0 / (temperature * CONSTANTS['kB'][self.units])

    def add_particle(self, pos, vel=None, force=None,
                     mass=1.0, name='?', ptype='?'):
        """
        Adds a particle to the system.

        Parameters
        ----------
        pos : numpy.array,
            Position of the particle.
        vel : numpy.array, optional.
            Velocity of the particle. If not given np.zeros will be used.
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
        N/A, updates self.particles
        """
        dim = self.get_dim()
        if vel is None:
            vel = np.zeros(dim)
        if force is None:
            force = np.zeros(dim)
        self.particles.add_particle(pos, vel, force, mass=mass,
                                    name=name, ptype=ptype)

    def force(self):
        """
        Updates the forces by calling self._evaluate_potential_force()

        Returns
        -------
        out[1] : numpy.array.
            Forces on the particles. Note that self.particles.force will
            also be updated.
        out[2] : float.
            The virial. Note that self.particles.virial will also be updated.
        """
        force, virial = self._evaluate_potential_force(what='force')
        self.particles.force = force
        self.particles.virial = virial
        return self.particles.force, virial

    def potential(self):
        """
        Updates self.v_pot by calling self._evaluate_potential_force()

        Returns
        -------
        out : float.
            The potential energy, note self.v_pot is also updated.
        """
        self.v_pot = self._evaluate_potential_force(what='potential')
        return self.v_pot

    def potential_and_force(self):
        """
        Updates the potential energy in self.v_pot and the forces in
        self.particles.force by calling self._evaluate_potential_force()

        Returns
        -------
        out[1] : float
            The potential energy, note self.v_pot is also updated.
        out[2] : numpy.array.
            Forces on the particles. Note that self.particles.force will
            also be updated.
        out[3] : float.
            The virial. Note that self.particles.virial will also be updated.
        """
        v_pot, force, virial = self._evaluate_potential_force(what='both')
        self.v_pot = v_pot
        self.particles.force = force
        self.particles.virial = virial
        return v_pot, force, virial

    def evaluate_force(self, **kwargs):
        """
        Evaluate the forces

        Parameters
        ----------
        kwargs : dictionary with settings that can be used to override
            the information in self.particles. This is useful if one
            wants to evaluate the forces for a different configuration
            of the particles.

        Returns
        -------
        out[1] : numpy.array
            Forces on the particles.
        out[2] : float
            The virial.
        """
        return self._evaluate_potential_force(what='force', **kwargs)

    def evaluate_potential(self, **kwargs):
        """
        Evaluate the potential energy.

        Parameters
        ----------
        kwargs : dictionary with settings that can be used to override
            the information in self.particles. This is useful if one
            wants to evaluate the potential for a different configuration
            of the particles.

        Returns
        -------
        out : float
            The potential energy.
        """
        return self._evaluate_potential_force(what='potential', **kwargs)

    def evaluate_potential_and_force(self, **kwargs):
        """
        Evaluate the potential and/or the force

        Parameters
        ----------
        kwargs : dictionary with settings that can be used to override
            the information in self.particles. This is useful if one
            wants to evaluate the potential for a different configuration
            of the particles.

        Returns
        -------
        out[1] : float
            The potential energy.
        out[2] : numpy.array
            Forces on the particles.
        out[3] : float
            The virial.
        """
        return self._evaluate_potential_force(what='both', **kwargs)

    def _evaluate_potential_force(self, what='both', **kwargs):
        """
        Helper function to evaluate the potential or force
        or both.
        """
        args = {}
        args['pos'] = kwargs.get('pos', self.particles.pos)
        args['name'] = kwargs.get('name', self.particles.name)
        args['ptype'] = kwargs.get('ptype', self.particles.ptype)
        args['particles'] = kwargs.get('particles', self.particles)
        args['box'] = kwargs.get('box', self.box)
        if what == 'potential':
            return self.forcefield.evaluate_potential(**args)
        elif what == 'force':
            return self.forcefield.evaluate_force(**args)
        else:
            return self.forcefield.evaluate_potential_and_force(**args)

    def generate_velocities(self, rgen, momentum=True, temperature=None,
                            distribution='maxwell'):
        """
        This method will set the velocities of the particles
        according to the desired temperature. The temperature can
        be specified, or it can be taken from self.temperature['set'].

        Parameters
        ----------
        rgen : object of type RandomGenerator
            This is the random generator which handles the drawing of
            velocities
        momentum : boolean, optional
            Determines if the momentum should be reset.
        temperature : float, optional
            The desired temperature to set.
        distribution : str
            Selects a distribution for generating the velocities.

        Returns
        -------
        N/A but updates system.particles.vel
        """
        if temperature is None:
            temperature = self.temperature['set']
        dof = self.temperature['dof']
        if distribution == 'maxwell':
            rgen.generate_maxwellian_velocities(self.particles, temperature,
                                                dof, momentum=momentum)
        else:
            msg = 'Distribution "{}" not defined!'.format(distribution)
            warnings.warn(msg)

    def calculate_temperature(self):
        """
        Function to calculate the temperature of the current configuration
        of the system. It is included here for convenience since the dof's
        are easily accessible and it's a very common calculation to perform,
        even though it might be cleaner to include it as a particlefunction.

        Returns
        -------
        out : float
            The temperature of the system
        """
        dof = self.temperature['dof']
        _, temp, _ = calculate_kinetic_temperature(self.particles, dof=dof)
        return temp
