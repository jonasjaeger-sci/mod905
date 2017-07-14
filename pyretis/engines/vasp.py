# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""A VASP external MD integrator interface.

This module defines a class for using VASP as an external engine.

Important classes defined here
------------------------------

VASPEngine
    A class responsible for interfacing VASP.
"""
import logging
import os
import shlex
import numpy as np
from pyretis.engines.external import ExternalMDEngine
from pyretis.core.units import CONVERT
#from pyretis.inout.setup.createsystem import guess_particle_mass
from pyretis.core.units import CONSTANTS
from pyretis.core.box import box_matrix_to_list
from pyretis.core.particlefunctions import kinetic_energy, kinetic_temperature
from pyretis.inout.writers.vaspio import (
    read_potcar_file,
    read_poscar_file,
    add_velocities,
    append_frame_to_traj,
    get_energy
)
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())

PERIODIC_TABLE = {'H': 1.007975, 'He': 4.002602, 'Li': 6.9675,
                  'Be': 9.0121831, 'B': 10.8135, 'C': 12.0106,
                  'N': 14.006855, 'O': 15.9994, 'F': 18.998403163,
                  'Ne': 20.1797, 'Na': 22.98976928, 'Mg': 24.3055,
                  'Al': 26.9815385, 'Si': 28.085, 'P': 30.973761998,
                  'S': 32.0675, 'Cl': 35.4515, 'Ar': 39.948,
                  'K': 39.0983, 'Ca': 40.078, 'Sc': 44.955908,
                  'Ti': 47.867, 'V': 50.9415, 'Cr': 51.9961,
                  'Mn': 54.938044, 'Fe': 55.845, 'Co': 58.933194,
                  'Ni': 58.6934, 'Cu': 63.546, 'Zn': 65.38,
                  'Ga': 69.723, 'Ge': 72.63, 'As': 74.921595,
                  'Se': 78.971, 'Br': 79.904, 'Kr': 83.798,
                  'Rb': 85.4678, 'Sr': 87.62, 'Y': 88.90584,
                  'Zr': 91.224, 'Nb': 92.90637, 'Mo': 95.95,
                  'Ru': 101.07, 'Rh': 102.9055, 'Pd': 106.42,
                  'Ag': 107.8682, 'Cd': 112.414, 'In': 114.818,
                  'Sn': 118.71, 'Sb': 121.76, 'Te': 127.6,
                  'I': 126.90447, 'Xe': 131.293, 'Cs': 132.90545196,
                  'Ba': 137.327, 'La': 138.90547, 'Ce': 140.116,
                  'Pr': 140.90766, 'Nd': 144.242, 'Sm': 150.36,
                  'Eu': 151.964, 'Gd': 157.25, 'Tb': 158.92535,
                  'Dy': 162.5, 'Ho': 164.93033, 'Er': 167.259,
                  'Tm': 168.93422, 'Yb': 173.045, 'Lu': 174.9668,
                  'Hf': 178.49, 'Ta': 180.94788, 'W': 183.84,
                  'Re': 186.207, 'Os': 190.23, 'Ir': 192.217,
                  'Pt': 195.084, 'Au': 196.966569, 'Hg': 200.592,
                  'Tl': 204.3835, 'Pb': 207.2, 'Bi': 208.9804,
                  'Th': 232.0377, 'Pa': 231.03588, 'U': 238.02891}


class VASPEngine(ExternalMDEngine):
    """A class for interfacing VASP.

    This class defines the interface to VASP.

    Attributes
    ----------
    vasp : string
        The command for executing vasp.
    input_path : string
        The directory where the input files are stored.
    timestep : float
        The time step used in the VASP MD simulation.
    subcycles : integer
        The number of steps each VASP run is composed of.
    """

    def __init__(self, vasp, input_path, timestep, subcycles):
        """Initiate the script.

        Parameters
        ----------
        vasp : string
            The vasp executable.
        input_path : string
            The absolute path to where the input files are stored.
        input_files : dict
            This dictionary contains the names of the input files.
        timestep : float
            The time step used in the vasp simulation.
        subcycles : integer
            The number of steps each vasp run is composed of.
        """
        super().__init__('VASP external engine', timestep, subcycles)
        # Store variables for vasp:
        self.vasp = shlex.split(vasp)
        logger.info('Command for execution of vasp: %s', ' '.join(self.vasp))
        # store input path:
        self.input_path = os.path.abspath(input_path)
        # store input files:
        self.input_files = {}
        for key in ('INCAR', 'KPOINTS', 'POSCAR', 'POTCAR'):
            self.input_files[key] = os.path.join(self.input_path, key)
            if not os.path.isfile(self.input_files[key]):
                msg = 'VASP engine could not find file "{}"!'.format(key)
                raise ValueError(msg)
            logger.debug('Input %s: %s', key, self.input_files[key])
        # rename for internal use:
        self.input_files['conf'] = self.input_files['POSCAR']

        settings = {'NSW': '{} ! MD steps/subcycles'.format(self.subcycles),
                    'POTIM': '{} ! time step in fs'.format(self.timestep)}

        self.input_files['input'] = os.path.join(self.input_path,
                                                 'INCAR.pyretis')
        self._modify_input(self.input_files['INCAR'],
                           self.input_files['input'], settings, delim='=')

        # For generation of velocities:
        self.boltzmann = CONSTANTS['kB']['eV/K']
        self.convert = 0.09822694808412166  # velocities to to A/fs
        masses, sigma_v, _ = self._setup_for_velocities()
        self.masses = masses
        self.sigma_v = sigma_v
        self.npart = len(self.masses)


    def _setup_for_velocities(self):
        """Helper method to do the setup needed for velocity generation."""
        logger.debug('Reading input temperature to VASP')
        input_settings = self._read_input_settings(self.input_files['input'])
        if 'TEBEG' not in input_settings:
            msg = ('Could not find "TEBEG" setting in VASP '
                   'input: "{}"').format(self.input_files['INCAR'])
            logger.error(msg)
            logger.info('Please add TEBEG setting in the VASP input')
            raise ValueError(msg)
        try:
            temperature = float(input_settings['TEBEG'].split('!')[0])
            logger.debug('Read TEBEG for VASP = %f', temperature)
        except ValueError:
            msg = ('Could not understand TEBEG temperature from VASP '
                   'input "{}"').format(self.input_files['INCAR'])
            logger.error(msg)
            logger.info('Please check TEBEG setting in the VASP input')
            raise ValueError(msg)
        logger.info('Reading VASP topology from %s and %s',
                    self.input_files['POTCAR'],
                    self.input_files['POSCAR'])
        atoms = read_potcar_file(self.input_files['POTCAR'])
        data, _, _ = read_poscar_file(self.input_files['POSCAR'])
        all_mass = []
        atom_names = []
        for i, (atom, natom) in enumerate(zip(atoms, data['natom'])):
            logger.info('\tFound atom: %s: %i', atom, natom)
            all_mass += [guess_particle_mass(i, atom, 'g/mol')] * natom
            atom_names += [atom] * natom
        masses = np.array(all_mass)
        masses.shape = (len(all_mass), 1)  # pyretis expects this!
        sigma_v = np.sqrt((temperature * self.boltzmann) / masses)
        return masses, sigma_v, atom_names

    def _run_vasp(self):
        """Method to execute VASP.

        Returns
        -------
        out : dict
            The files created by the run.
        """
        print('Running VASP')
        self.execute_command(self.vasp, cwd=self.exe_dir, inputs=None)
        out = {}
        for key in ('OUTCAR', 'vasprun.xml', 'stout', 'IBZKPT', 'CONTCAR',
                    'CHGCAR', 'CHG', 'WAVECAR', 'TMPCAR', 'EIGENVAL',
                    'DOSCAR', 'PROCAR', 'OSZICAR', 'PCDAT', 'XDATCAR',
                    'LOCPOT', 'ELFCAR', 'PROOUT', 'REPORT'):
            filename = os.path.join(self.exe_dir, key)
            if os.path.isfile(filename):
                out[key] = filename
        return out

    def _extract_frame(self, traj_file, idx, out_file):
        """Extract a frame from a trajectory file.

        This method is used by `self.dump_config` when we are
        dumping from a trajectory file. It is not used if we are
        dumping from a single config file.

        Parameters
        ----------
        traj_file : string
            The trajectory file to dump from.
        idx : integer
            The frame number we look for.
        out_file : string
            The file to dump to.
        """
        frame_idx = None
        read_frame = False
        found_frame = False
        with open(traj_file, 'r') as traj, open(out_file, 'w') as output:
            for lines in traj:
                if lines.find('# Frame') != -1:
                    frame_idx = int(lines.strip().split()[-1])
                    if read_frame:
                        # we have reached the next frame, stop reading
                        read_frame = False
                        break
                    else:
                        if frame_idx == idx:
                            found_frame = True
                            read_frame = True
                            continue
                if read_frame:
                    output.write(lines)
        if not found_frame:
            logger.warning('Frame no. %i not found in trajectory "%s"!', idx,
                           traj_file)
            # Remove the output file created, this is to ensure that
            # we fail at a later stage.
            self._removefile(out_file)
        return None

    def _propagate_from(self, name, path, system, order_function, interfaces,
                        reverse=False):
        """Propagate with VASP from the current system configuration.

        Here, we assume that this method is called after the propagate()
        has been called in the parent. The parent is then responsible
        for reversing the velocities and also for setting the initial
        state of the system.

        Parameters
        ----------
        name : string
            A name to use for the trajectory we are generating.
        path : object like :py:class:`pyretis.core.Path.PathBase`
            This is the path we use to fill in phase-space points.
            We are here not returning a new path - this since we want
            to delegate the creation of the path to the method
            that is running `propagate`.
        system : object like `System` from `pyretis.core.system`
            The system object gives the initial state for the
            integration. The initial state is stored and the system is
            reset to the initial state when the integration is done.
        order_function : object like `pyretis.orderparameter.OrderParameter`
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
        status = 'propagating with VASP (reverse = {})'.format(reverse)
        print('In {}: {}'.format(self.exe_dir, status))
        logger.debug(status)
        success = False
        left, _, right = interfaces
        # Dumping of the initial config were done by the parent, here
        # we will just the dumped file:
        initial_conf = system.particles.get_pos()[0]

        poscar = os.path.join(self.exe_dir, 'POSCAR')
        self._copyfile(initial_conf, poscar)
        # Set the positions to be just the POSCAR
        system.particles.set_pos((poscar, None))

        contcar = os.path.join(self.exe_dir, 'CONTCAR')
        oszicar = os.path.join(self.exe_dir, 'OSZICAR')
        traj_file = os.path.join(self.exe_dir, name)
        if os.path.isfile(traj_file):
            logger.warning('%s exist, it will be overwritten!', traj_file)
            self._removefile(traj_file)
        traj_file2 = os.path.join(self.exe_dir, name)
        if os.path.isfile(traj_file2):
            logger.warning('%s exist, it will be overwritten!', traj_file2)
            self._removefile(traj_file2)

        success = False
        left, _, right = interfaces
        # Add vasp input files:
        self.add_input_files(self.exe_dir)
        # Get INCAR file:
        incar = os.path.join(self.exe_dir, 'INCAR')
        self._copyfile(self.input_files['input'], incar)

        phase_point = system.particles.get_particle_state()
        # Just to be keep the same order as in the loop
        vpot = phase_point['vpot']
        ekin = phase_point['ekin']
        order = self.calculate_order(order_function, system)
        out_files = {}
        for i in range(path.maxlen):
            logger.debug('Current: %9.5g %9.5g %9.5g', left, order[0], right)
            # We first add the current phase point, and then we propagate.
            phase_point = {
                'order': order,
                'pos': (traj_file, i),
                'vel': reverse,
                'vpot': vpot,
                'ekin': ekin}
            status, success, stop = self.add_to_path(path, phase_point,
                                                     left, right)
            # Add it to the output trajectory file as well:
            append_frame_to_traj(poscar, traj_file, i)
            if stop:
                logger.debug('Ending propagate at %i. Reason: %s', i, status)
                break
            # Run vasp:
            out_files = self._run_vasp()
            # Move CONTCAR TO POSCAR
            self._movefile(contcar, poscar)
            # Update energies:
            energy = get_energy(oszicar)
            ekin = energy[0][-1]
            vpot = energy[1][-1]
            # Recalculate order parameter, not that we assume
            # that the order parameter is purely defined by the positions
            # and velocities in the current POSCAR:
            order = self.calculate_order(order_function, system)
        # We are done, remove the files we do not need anymore:
        remove = [val for _, val in out_files.items()]
        self._remove_files(self.exe_dir, remove)
        self._removefile(poscar)
        return success, status

    def step(self, system, name):
        """Perform a single step with vasp.

        Parameters
        ----------
        system : object like :py:class:`pyretis.core.system.System`
            The system we are integrating.
        name : string
            To name the output files from the vasp step.

        Returns
        -------
        out_files : dict
            The output files created by this step.
        """
        # Get initial config and store as POSCAR
        input_file = self.dump_frame(system)
        poscar = os.path.join(self.exe_dir, 'POSCAR')
        self._copyfile(input_file, poscar)
        # Get INCAR file:
        incar = os.path.join(self.exe_dir, 'INCAR')
        self._copyfile(self.input_files['input'], incar)
        # get KPOINTS, POTCAR:
        self.add_input_files(self.exe_dir)
        # Run (in self.exe_dir):
        out_files = self._run_vasp()
        # We now have the result in CONTCAR
        contcar = os.path.join(self.exe_dir, 'CONTCAR')
        # Store the frame after the step:
        config = os.path.join(self.exe_dir, '{}_POSCAR'.format(name))
        self._movefile(contcar, config)
        # Get kinetic energy:
        oszicar = os.path.join(self.exe_dir, 'OSZICAR')
        energy = get_energy(oszicar)
        ekin = energy[0][-1]
        vpot = energy[1][-1]
        remove = [val for _, val in out_files.items()]
        self._remove_files(self.exe_dir, remove)
        self._removefile(poscar)
        phase_point = {'pos': (config, None),
                       'vel': False, 'vpot': vpot, 'ekin': ekin}
        system.particles.set_particle_state(phase_point)
        return config

    def add_input_files(self, dirname):
        """Add required input files to a given directory.

        We will here only copy the KPOINTS and POTCAR files and we
        will only copy if they do not exist in the given directory.

        Parameters
        ----------
        dirname : string
            The full path to where we want to add the files.
        """
        for key in ('KPOINTS', 'POTCAR'):
            dest = os.path.join(dirname, key)
            if not os.path.isfile(dest):
                logger.debug('Adding input file "%s" to "%s"', key, dirname)
                self._copyfile(self.input_files[key], dest)

    @staticmethod
    def _read_configuration(filename):
        """Method to read vasp POSCAR/CONTCAR.

        This method is used when we calculate the order parameter.

        Parameters
        ----------
        filename : string
            The file to read the configuration from.

        Returns
        -------
        lengths : numpy.array
            The box-lengths
        xyz : numpy.array
            The positions.
        vel : numpy.array
            The velocities.
        """
        data, xyz, vel = read_poscar_file(filename)
        lengths = box_matrix_to_list(data['cell']) * data['scale']
        if not data['cartesian']:
            xyz_c = data['scale'] * np.dot(xyz, data['cell'])
            return lengths, xyz_c, vel
        else:
            # Just scale for cartesian
            scale = data['scale']
            return lengths, scale * xyz, vel

    @staticmethod
    def _reverse_velocities(filename, outfile):
        """Method to reverse velocity in a given snapshot.

        Parameters
        ----------
        filename : string
            The configuration to reverse velocities in.
        outfile : string
            The output file for storing the configuration with
            reversed velocities.
        """
        _, _, vel = read_poscar_file(filename)
        add_velocities(filename, outfile, -vel)

    def modify_velocities(self, system, rgen, sigma_v=None, aimless=True,
                          momentum=False, rescale=None):
        """Modify the velocities of the current state.

        This method will modify the velocities of a time slice.

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
        dek = None
        kin_old = None
        kin_new = None
        if rescale is not None and rescale is not False and rescale > 0:
            msgtxt = 'VASP engine does not support energy rescale!'
            logger.error(msgtxt)
            raise NotImplementedError(msgtxt)
        else:
            kin_old = system.particles.ekin
        if aimless:
            pos = self.dump_frame(system)
            phase_point = system.particles.get_particle_state()
            vel = rgen.normal(loc=0.0, scale=self.sigma_v,
                              size=(self.npart, 3))
            if momentum:
                vel -= np.sum(vel * self.masses, axis=0) / self.masses.sum()
            # Create a new file with the new velocities
            genvel = os.path.join(self.exe_dir, 'g_POSCAR')
            # Write velocities in units of A/fs:
            add_velocities(pos, genvel, vel * self.convert)
            # Update system to new phase point
            kin_new, kin_tens = kinetic_energy(vel, self.masses)
            _, temperature, _ = kinetic_temperature(vel, self.masses,
                                                    self.boltzmann,
                                                    kin_tensor=kin_tens)
            logger.debug('Generated velocities for corresponding to T = %f',
                         temperature)
            phase_point['pos'] = (genvel, None)
            phase_point['vel'] = False
            phase_point['ekin'] = kin_new
            # Note: We keep the potential energy
            system.particles.set_particle_state(phase_point)
        else:  # soft velocity change, add from Gaussian dist
            msgtxt = 'VASP engine only support aimless shooting!'
            logger.error(msgtxt)
            raise NotImplementedError(msgtxt)
        if kin_old is None or kin_new is None:
            dek = float('inf')
            logger.warning(('Kinetic energy not found for previous point.'
                            '\n(This happens when the initial configuration '
                            'does not contain energies.)'))
        else:
            dek = kin_new - kin_old
        return dek, kin_new


def guess_particle_mass(particle_no, particle_type, unit):
    """Method that will try to guess a particle mass from it's type.

    Parameters
    ----------
    particle_no : integer
    Just used to identify the particle number
    particle_type : string
    Used to identify the particle
    unit : string
    The system of units. This is used in case we try to get the
    mass from the periodic table where the units are in `g/mol`.
    """
    logger.info(('Mass not specified for particle no. %i\n'
                 'Will guess from particle type "%s"'), particle_no,
                 particle_type)
    mass = PERIODIC_TABLE.get(particle_type, None)
    if mass is None:
        particle_mass = 1.0
        logger.info(('-> Could not find mass. '
                     'Assuming %f (internal units)'), particle_mass)
    else:
        particle_mass = CONVERT['mass']['g/mol', unit] * mass
        logger.info(('-> Using a mass of %f g/mol '
                     '(%f in internal units)'), mass, particle_mass)
    return particle_mass
