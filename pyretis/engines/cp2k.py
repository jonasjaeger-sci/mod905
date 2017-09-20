# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""A CP2K external MD integrator interface.

This module defines a class for using CP2K as an external engine.

Important classes defined here
------------------------------

CP2KEngine (:py:class:`.CP2KEngine`)
    A class responsible for interfacing CP2K.
"""
import logging
import os
import re
import shlex
from pyretis.engines.external import ExternalMDEngine
from pyretis.core.random_gen import create_random_generator
from pyretis.inout.writers.xyzio import (
    read_xyz_file,
    write_xyz_trajectory,
    convert_snapshot
)
from pyretis.inout.writers.cp2kio import (
    update_cp2k_input,
    read_cp2k_restart,
    read_cp2k_box,
    read_cp2k_energy,
)
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


OUTPUT_FILES = {
    'energy': '{}-1.ener',
    'restart': '{}-1.restart',
    'pos': '{}-pos-1.xyz',
    'vel': '{}-vel-1.xyz',
    'wfn': '{}-RESTART.wfn',
    'wfn-bak': '{}-RESTART.wfn.bak-'
}


REGEXP_BACKUP = re.compile(r'\.bak-\d$')


def write_for_step_vel(infile, outfile, timestep, subcycles, posfile, vel,
                       name='md_step', print_freq=None):
    """Create input file for a single step.

    Note, the single step actually consist of a number of subcycles.
    But from PyRETIS' point of view, this is a single step.
    Further, we here assume that we start from a given xyz file and
    we also explicitly give the velocities here.

    Parameters
    ----------
    infile : string
        The input template to use.
    outfile : string
        The file to create.
    timestep : float
        The time-step to use for the simulation.
    subcycles : integer
        The number of sub-cycles to perform.
    posfile : string
        The (base)name for the input file to read positions from.
    vel : numpy.array
        The velocities to set in the input.
    name : string
        A name given to the CP2K project.
    print_freq : integer, optional
        How often we should print to the trajectory file.
    """
    if print_freq is None:
        print_freq = subcycles
    to_update = {
        'GLOBAL': {
            'data': ['PROJECT {}'.format(name),
                     'RUN_TYPE MD',
                     'PRINT_LEVEL LOW'],
            'replace': True,
        },
        'MOTION->MD':  {
            'data': {'STEPS': subcycles,
                     'TIMESTEP': timestep}
        },
        'MOTION->PRINT->RESTART': {
            'data': ['BACKUP_COPIES 0'],
            'replace': True,
        },
        'MOTION->PRINT->RESTART->EACH': {
            'data': {'MD': print_freq}
        },
        'MOTION->PRINT->VELOCITIES->EACH': {
            'data': {'MD': print_freq}
        },
        'MOTION->PRINT->TRAJECTORY->EACH': {
            'data': {'MD': print_freq}
        },
        'FORCE_EVAL->SUBSYS->TOPOLOGY': {
            'data': {'COORD_FILE_NAME': posfile,
                     'COORD_FILE_FORMAT': 'xyz'}
        },
        'FORCE_EVAL->SUBSYS->VELOCITY': {
            'data': [],
            'replace': True,
        },
        'FORCE_EVAL->DFT->SCF->PRINT->RESTART': {
            'data': ['BACKUP_COPIES 0'],
            'replace': True,
        },
    }
    for veli in vel:
        to_update['FORCE_EVAL->SUBSYS->VELOCITY']['data'].append(
            '{} {} {}'.format(*veli)
        )
    remove = [
        'EXT_RESTART',
        'FORCE_EVAL->SUBSYS->COORD'
    ]
    update_cp2k_input(infile, outfile, update=to_update, remove=remove)


def write_for_continue(infile, outfile, timestep, subcycles,
                       name='md_continue'):
    """Create input file for a single step.

    Note, the single step actually consist of a number of sub-cycles.
    But from PyRETIS' point of view, this is a single step.
    Here, we make use of restart files named ``previous.restart``
    and ``previous.wfn`` to continue a run.

    Parameters
    ----------
    infile : string
        The input template to use.
    outfile : string
        The file to create.
    timestep : float
        The time-step to use for the simulation.
    subcycles : integer
        The number of sub-cycles to perform.
    name : string
        A name given to the CP2K project.
    """
    to_update = {
        'GLOBAL': {
            'data': ['PROJECT {}'.format(name),
                     'RUN_TYPE MD',
                     'PRINT_LEVEL LOW'],
            'replace': True,
        },
        'MOTION->MD':  {
            'data': {'STEPS': subcycles,
                     'TIMESTEP': timestep}
        },
        'MOTION->PRINT->RESTART': {
            'data': ['BACKUP_COPIES 0'],
            'replace': True,
        },
        'MOTION->PRINT->RESTART->EACH': {
            'data': {'MD': subcycles}
        },
        'MOTION->PRINT->VELOCITIES->EACH': {
            'data': {'MD': subcycles}
        },
        'MOTION->PRINT->TRAJECTORY->EACH': {
            'data': {'MD': subcycles}
        },
        'EXT_RESTART': {
            'data': ['RESTART_VEL',
                     'RESTART_POS',
                     'RESTART_FILE_NAME previous.restart'],
            'replace': True
        },
        'FORCE_EVAL->DFT': {
            'data': {'WFN_RESTART_FILE_NAME': 'previous.wfn'},
        },
        'FORCE_EVAL->DFT->SCF->PRINT->RESTART': {
            'data': ['BACKUP_COPIES 0'],
            'replace': True,
        },
    }
    remove = [
        'FORCE_EVAL->SUBSYS->TOPOLOGY',
        'FORCE_EVAL->SUBSYS->VELOCITY',
        'FORCE_EVAL->SUBSYS->COORD'
        'FORCE_EVAL->DFT->RESTART_FILE_NAME',
    ]
    update_cp2k_input(infile, outfile, update=to_update, remove=remove)


def write_for_genvel(infile, outfile, posfile, seed, name='genvel'):
    """Create input file for velocity generation.

    Parameters
    ----------
    infile : string
        The input template to use.
    outfile : string
        The file to create.
    posfile : string
        The (base)name for the input file to read positions from.
    seed : integer
        A seed for generating velocities.
    name : string
        A name given to the CP2K project.
    """
    to_update = {
        'GLOBAL': {
            'data': ['PROJECT {}'.format(name),
                     'SEED {}'.format(seed),
                     'RUN_TYPE MD',
                     'PRINT_LEVEL LOW'],
            'replace': True,
        },
        'FORCE_EVAL->DFT->SCF': {
            'data': {'SCF_GUESS': 'ATOMIC'}
        },
        'MOTION->MD':  {
            'data': {'STEPS': 1,
                     'TIMESTEP': 0}
        },
        'MOTION->PRINT->RESTART': {
            'data': ['BACKUP_COPIES 0'],
            'replace': True,
        },
        'MOTION->PRINT->RESTART->EACH': {
            'data': {'MD': 1}
        },
        'MOTION->PRINT->VELOCITIES->EACH': {
            'data': {'MD': 1}
        },
        'MOTION->PRINT->TRAJECTORY->EACH': {
            'data': {'MD': 1}
        },
        'FORCE_EVAL->SUBSYS->TOPOLOGY': {
            'data': {'COORD_FILE_NAME': posfile,
                     'COORD_FILE_FORMAT': 'xyz'}
        },
        'FORCE_EVAL->DFT->SCF->PRINT->RESTART': {
            'data': ['BACKUP_COPIES 0'],
            'replace': True,
        },
    }
    remove = [
        'EXT_RESTART',
        'FORCE_EVAL->SUBSYS->VELOCITY',
        'FORCE_EVAL->DFT->RESTART_FILE_NAME',
    ]
    update_cp2k_input(infile, outfile, update=to_update, remove=remove)


class CP2KEngine(ExternalMDEngine):
    """A class for interfacing CP2K.

    This class defines the interface to CP2K.

    Attributes
    ----------
    cp2k : string
        The command for executing CP2K.
    input_path : string
        The directory where the input files are stored.
    timestep : float
        The time step used in the CP2K MD simulation.
    subcycles : integer
        The number of steps each CP2K run is composed of.
    rgen : object like :py:class:`.RandomGenerator`
        An object we use to set seeds for velocity generation.
    """

    def __init__(self, cp2k, input_path, timestep, subcycles, extra_files,
                 seed=0):
        """Initiate the CP2K engine.

        Parameters
        ----------
        cp2k : string
            The CP2K executable.
        input_path : string
            The path to where the input files are stored.
        timestep : float
            The time step used in the CP2K simulation.
        subcycles : integer
            The number of steps each CP2K run is composed of.
        extra_files : list
            List of extra files which may be required to run CP2K.
        seed : integer
            A seed for the random number generator.
        """
        super().__init__('CP2K external engine', timestep,
                         subcycles)
        self.rgen = create_random_generator({'seed': seed})
        self.ext = 'xyz'
        self.cp2k = shlex.split(cp2k)
        logger.info('Command for execution of CP2K: %s', ' '.join(self.cp2k))
        # store input path:
        self.input_path = os.path.abspath(input_path)
        # store input files:
        self.input_files = {}
        for key, fname in zip(('conf', 'template'),
                              ('initial.xyz', 'cp2k.inp')):
            self.input_files[key] = os.path.join(self.input_path, fname)
            if not os.path.isfile(self.input_files[key]):
                msg = 'CP2K engine could not find file "{}"!'.format(fname)
                raise ValueError(msg)
            logger.debug('Input %s: %s', key, self.input_files[key])
        self.extra_files = []
        if extra_files is not None:
            for key in extra_files:
                fname = os.path.join(self.input_path, key)
                if not os.path.isfile(fname):
                    logger.critical('Extra CP2K input file "%s" not found!',
                                    fname)
                else:
                    self.extra_files.append(fname)

    def run_cp2k(self, input_file, proj_name):
        """Method to execute CP2K.

        Returns
        -------
        out : dict
            The files created by the run.
        """
        cmd = self.cp2k + ['-i', input_file]
        logger.debug('Executing CP2K %s: %s', proj_name, input_file)
        self.execute_command(cmd, cwd=self.exe_dir, inputs=None)
        out = {}
        for key, name in OUTPUT_FILES.items():
            out[key] = os.path.join(self.exe_dir, name.format(proj_name))
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
        for i, snapshot in enumerate(read_xyz_file(traj_file)):
            if i == idx:
                box, xyz, vel, names = convert_snapshot(snapshot)
                if os.path.isfile(out_file):
                    logger.warning('CP2K will overwrite %s', out_file)
                write_xyz_trajectory(out_file, xyz, vel, names, box,
                                     append=False)
                return
        logger.error('CP2K could not extract index %i from %s!',
                     idx, out_file)

    def _name_output(self, basename):
        """Return the name of the output file."""
        out_file = '{}.{}'.format(basename, self.ext)
        return os.path.join(self.exe_dir, out_file)

    def _propagate_from(self, name, path, system, order_function, interfaces,
                        reverse=False):
        """Propagate with CP2K from the current system configuration.

        Here, we assume that this method is called after the propagate()
        has been called in the parent. The parent is then responsible
        for reversing the velocities and also for setting the initial
        state of the system.

        Parameters
        ----------
        name : string
            A name to use for the trajectory we are generating.
        path : object like :py:class:`.PathBase`
            This is the path we use to fill in phase-space points.
        system : object like :py:class:`.System`
            The system object gives the initial state.
        order_function : object like :py:class:`.OrderParameter`
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
        status = 'propagating with CP2K (reverse = {})'.format(reverse)
        logger.debug(status)
        success = False
        left, _, right = interfaces
        logger.debug('Adding input files for CP2K')
        # First, copy the required input files:
        self.add_input_files(self.exe_dir)
        # Get positions and velocities from the input file.
        initial_conf = system.particles.get_pos()[0]
        box, xyz, vel, atoms = self._read_configuration(initial_conf)
        if box is None:
            box, _ = read_cp2k_box(self.input_files['template'])
        # Add CP2K input for a single step:
        step_input = os.path.join(self.exe_dir, 'step.inp')
        write_for_step_vel(self.input_files['template'], step_input,
                           self.timestep, self.subcycles,
                           os.path.basename(initial_conf),
                           vel, name=name)
        # And create the input file for continuing:
        continue_input = os.path.join(self.exe_dir, 'continue.inp')
        write_for_continue(self.input_files['template'], continue_input,
                           self.timestep, self.subcycles, name=name)
        # Get the order parameter before the run:
        order = self.calculate_order(order_function, system,
                                     xyz=xyz, vel=vel, box=box)
        traj_file = os.path.join(self.exe_dir, '{}.{}'.format(name, self.ext))
        # Run the first step:
        out_files = self.run_cp2k('step.inp', name)
        restart_file = os.path.join(self.exe_dir, out_files['restart'])
        prestart_file = os.path.join(self.exe_dir, 'previous.restart')
        wave_file = os.path.join(self.exe_dir, out_files['wfn'])
        pwave_file = os.path.join(self.exe_dir, 'previous.wfn')
        # Note: Order is calculated at the END of each iteration!
        i = 0
        # Write the config so we have a non-empty file:
        write_xyz_trajectory(traj_file, xyz, vel, atoms, box, step=i,
                             append=False)
        for i in range(path.maxlen):
            print('At step {}, order = {}'.format(i, order))
            phase_point = {'order': order,
                           'pos': (traj_file, i),
                           'vel': reverse,
                           'vpot': None,
                           'ekin': None}
            status, success, stop, add = self.add_to_path(path, phase_point,
                                                          left, right)
            if add and i > 0:
                # Write the previous configuration:
                write_xyz_trajectory(traj_file, xyz, vel, atoms, box,
                                     step=i)
            if stop:
                logger.debug('CP2K propagation ended at %i. Reason: %s',
                             i, status)
                break
            if i == 0:
                pass
            elif i > 0:
                self._movefile(restart_file, prestart_file)
                self._movefile(wave_file, pwave_file)
                if i < path.maxlen - 1:
                    out_files = self.run_cp2k('continue.inp', name)
            self._remove_files(self.exe_dir,
                               self._find_backup_files(self.exe_dir))
            # Read config after the step
            if i < path.maxlen - 1:
                atoms, xyz, vel, box, _ = read_cp2k_restart(restart_file)
                order = self.calculate_order(order_function, system,
                                             xyz=xyz, vel=vel, box=box)
        energy_file = out_files['energy']
        energy = read_cp2k_energy(energy_file)
        end = (i + 1) * self.subcycles
        path.ekin = energy[0][:end:self.subcycles]
        path.vpot = energy[1][:end:self.subcycles]
        for _, files in out_files.items():
            self._removefile(files)
        self._removefile(prestart_file)
        self._removefile(pwave_file)
        self._removefile(continue_input)
        self._removefile(step_input)
        return success, status

    def step(self, system, name):
        """Perform a single step with CP2K.

        Parameters
        ----------
        system : object like :py:class:`.System`
            The system we are integrating.
        name : string
            To name the output files from the CP2K step.

        Returns
        -------
        out : string
            The name of the output configuration, obtained after
            completing the step.
        """
        initial_conf = self.dump_frame(system)
        # Save as a single snapshot file
        phase_point = {'pos': (initial_conf, None), 'vel': False,
                       'vpot': None, 'ekin': None}
        system.particles.set_particle_state(phase_point)
        # Prepare input files etc.:
        self.add_input_files(self.exe_dir)
        box, xyz, vel, atoms = self._read_configuration(initial_conf)
        if box is None:
            box, _ = read_cp2k_box(self.input_files['template'])
        # Add CP2K input for a single step:
        step_input = os.path.join(self.exe_dir, 'step.inp')
        write_for_step_vel(self.input_files['template'], step_input,
                           self.timestep, self.subcycles,
                           os.path.basename(initial_conf),
                           vel, name=name)

        # Execute single step CP2K...
        logger.debug('Executing CP2K')
        out_files = self.run_cp2k('step.inp', name)
        energy = read_cp2k_energy(out_files['energy'])
        # Get the output configuration:
        atoms, xyz, vel, box, _ = read_cp2k_restart(out_files['restart'])
        conf_out = os.path.join(self.exe_dir, '{}.{}'.format(name, self.ext))
        write_xyz_trajectory(conf_out, xyz, vel, atoms, box, append=False)
        phase_point = {'pos': (conf_out, None),
                       'vel': False,
                       'vpot': energy[1][-1],
                       'ekin': energy[0][-1]}
        system.particles.set_particle_state(phase_point)
        logger.debug('Removing CP2K output after single step.')
        # Remove run-files etc:
        for _, files in out_files.items():
            self._removefile(files)
        self._remove_files(
            self.exe_dir,
            self._find_backup_files(self.exe_dir)
        )
        return conf_out

    def add_input_files(self, dirname):
        """Add required input files to a given directory.

        Parameters
        ----------
        dirname : string
            The full path to where we want to add the files.
        """
        for files in self.extra_files:
            basename = os.path.basename(files)
            dest = os.path.join(dirname, basename)
            if not os.path.isfile(dest):
                logger.debug('Adding input file "%s" to "%s"',
                             basename, dirname)
                self._copyfile(files, dest)

    @staticmethod
    def _find_backup_files(dirname):
        """Return backup-files in the given directory."""
        out = []
        for entry in os.scandir(dirname):
            if entry.is_file():
                match = REGEXP_BACKUP.search(entry.name)
                if match is not None:
                    out.append(entry.name)
        return out

    @staticmethod
    def _read_configuration(filename):
        """Method to read CP2K output configuration.

        This method is used when we calculate the order parameter.

        Parameters
        ----------
        filename : string
            The file to read the configuration from.

        Returns
        -------
        box : numpy.array
            The box dimensions if we mange to read it.
        xyz : numpy.array
            The positions.
        vel : numpy.array
            The velocities.
        names : list of strings
            The atom names found in the file.
        """
        xyz, vel, box, names = None, None, None, None
        for snapshot in read_xyz_file(filename):
            box, xyz, vel, names = convert_snapshot(snapshot)
            break  # stop after the first snapshot
        return box, xyz, vel, names

    def _reverse_velocities(self, filename, outfile):
        """Method to reverse velocity in a given snapshot.

        Parameters
        ----------
        filename : string
            The configuration to reverse velocities in.
        outfile : string
            The output file for storing the configuration with
            reversed velocities.
        """
        box, xyz, vel, names = self._read_configuration(filename)
        write_xyz_trajectory(outfile, xyz, -1.0*vel, names, box, append=False)
        return None

    def _prepare_shooting_point(self, input_file):
        """Create initial configuration for a shooting move.

        This creates a new initial configuration with random velocities.

        Parameters
        ----------
        input_file : string
            The input configuration to generate velocities for.

        Returns
        -------
        output_file : string
            The name of the file created.
        energy : dict
            The energy terms read from the GROMACS .edr file.
        """
        box, xyz, vel, atoms = self._read_configuration(input_file)
        if box is None:
            box, _ = read_cp2k_box(self.input_files['template'])
        input_config = os.path.join(self.exe_dir, 'genvel_input.xyz')
        write_xyz_trajectory(input_config, xyz, vel, atoms, box, append=False)
        # Create input file for CP2K:
        run_file = os.path.join(self.exe_dir, 'run.inp')
        write_for_genvel(self.input_files['template'],
                         run_file,
                         'genvel_input.xyz',
                         self.rgen.random_integers(1, 999999999),
                         name='genvel')
        # Prepare to run it:
        self.add_input_files(self.exe_dir)
        out_files = self.run_cp2k(run_file, 'genvel')
        energy = read_cp2k_energy(out_files['energy'])
        # Get the output configuration:
        atoms, xyz, vel, box, _ = read_cp2k_restart(out_files['restart'])
        conf_out = os.path.join(self.exe_dir,
                                '{}.{}'.format('genvel', self.ext))
        write_xyz_trajectory(conf_out, xyz, vel, atoms, box, append=False)
        # Remove run-files etc:
        for _, files in out_files.items():
            self._removefile(files)
        self._remove_files(
            self.exe_dir,
            self._find_backup_files(self.exe_dir)
        )
        return conf_out, energy

    def modify_velocities(self, system, rgen, sigma_v=None, aimless=True,
                          momentum=False, rescale=None):
        """Modify the velocities of the current state.

        This method will modify the velocities of a time slice.

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
            In some NVE simulations, we may wish to re-scale the energy to
            a fixed value. If `rescale` is a float > 0, we will re-scale
            the energy (after modification of the velocities) to match the
            given float.

        Returns
        -------
        dek : float
            The change in the kinetic energy.
        kin_new : float
            The new kinetic energy.
        """
        dek, kin_old, kin_new = None, None, None
        if rescale is not None and rescale is not False and rescale > 0:
            msgtxt = 'CP2K engine does not support energy re-scale.'
            logger.error(msgtxt)
            raise NotImplementedError(msgtxt)
        else:
            kin_old = system.particles.ekin
        if aimless:
            pos = self.dump_frame(system)
            posvel, energy = self._prepare_shooting_point(pos)
            kin_new = energy[0][-1]
            phase_point = {'pos': (posvel, None), 'vel': False,
                           'ekin': kin_new,
                           'vpot': energy[1][-1]}
            system.particles.set_particle_state(phase_point)
        else:  # soft velocity change, add from Gaussian dist
            msgtxt = 'CP2K engine only support aimless shooting!'
            logger.error(msgtxt)
            raise NotImplementedError(msgtxt)
        if momentum:
            pass
        if kin_old is None or kin_new is None:
            dek = float('inf')
            logger.warning(('Kinetic energy not found for previous point.'
                            '\n(This happens when the initial configuration '
                            'does not contain energies.)'))
        else:
            dek = kin_new - kin_old
        return dek, kin_new
