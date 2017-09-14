# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Definition of external engines.

This module defines the base class for external MD engines.
This class is sub-classed by all other external MD engines.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ExternalMDEngine (:py:class:`.ExternalMDEngine`)
    The base class for external scripts. This defines the actual
    interface to external programs.
"""
from abc import abstractmethod
import re
import logging
import subprocess
import shutil
import os
from pyretis.inout.common import print_to_screen
from pyretis.engines.engine import EngineBase
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['ExternalMDEngine']


class ExternalMDEngine(EngineBase):
    """Base class for interfacing external MD engines.

    This class defines the interface to external programs. The
    interface will define how we interact with the external programs
    and how we write input files for them and read output files.
    New engines should inherit from this class and implement the
    following methods:

    * :py:meth:`ExternalMDEngine.step`
        A method for performing a MD step with the external
        engine. Note that the MD step can consist of a number
        of sub-cycles.
    * :py:meth:`ExternalMDEngine._read_configuration`
        For reading output (configurations) from the external engine.
        This is used for calculating the order parameter(s).
    * :py:meth:`ExternalMDEngine._reverse_velocities`
        For reversing velocities in a snapshot. This method
        will typically make use of the
        :py:meth:`ExternalMDEngine._read_configuration` method.
    * :py:meth:`ExternalMDEngine._extract_frame`
        For extracting a single frame from a trajectory.
    * :py:meth:`ExternalMDEngine._propagate_from`
        The method for propagating the equations of motion using
        the external engine.
    * :py:meth:`ExternalMDEngine.modify_velocities`
        The method used for generating random velocities for
        shooting points. Note that this method is defined in
        :py:meth:`.EngineBase.modify_velocities`.

    Attributes
    ----------
    description : string
        Short string which a description about the external
        script. This can for instance be what program we are
        interfacing. This is used for output of information to
        the user.
    timestep : float
        The time step used for the external engine.
    subcycles : integer
        The number of steps the external step is composed of. That is:
        each external step is really composed of ``subcycles`` number
        of iterations.
    """
    engine_type = 'external'

    def __init__(self, description, timestep, subcycles):
        """Initialisation of the external engine.

        Here we just set up some common properties which are useful
        for the execution.

        Parameters
        ----------
        description : string
            Short string which a description about the external
            script. This can for instance be what program we are
            interfacing.
        timestep : float
            The time step used in the simulation.
        subcycles : integer
            The number of sub-cycles each external integration step is
            composed of.
        """
        super().__init__(description)
        self.timestep = timestep
        self.subcycles = subcycles
        self._exe_dir = None

    @property
    def exe_dir(self):
        """Return the directory we are currently using."""
        return self._exe_dir

    @exe_dir.setter
    def exe_dir(self, exe_dir):
        """Set the current executable dir."""
        self._exe_dir = exe_dir
        logger.debug('Setting exe_dir to "%s"', exe_dir)
        if not os.path.isdir(exe_dir):
            logger.warning(('"Exe dir" for "%s" is set to "%s" which does '
                            'not exist!'), self.description, exe_dir)

    def integration_step(self, system):
        """Perform one time step of the integration.

        For external engines, it does not make much sense to run single
        steps unless we absolutely have to. We therefore just fail here.
        I.e. the external engines are not intended for performing pure
        MD simulations.

        If it's absolutely needed, there is a `self.step()` method
        which can be used, for instance in the initialisation.
        """
        msg = 'External engine does not support "integration_step()"!'
        logger.error(msg)
        raise NotImplementedError(msg)

    @abstractmethod
    def step(self, system, name):
        """Perform a single step with the external engine.

        Parameters
        ----------
        system : object like :py:class:`.System`
            The system we are integrating.
        name : string
            To name the output files from the external engine.

        Returns
        -------
        out : string
            The name of the output configuration, obtained after
            completing the step.

        """
        pass

    @abstractmethod
    def _read_configuration(self, filename):
        """Read output configuration from external software.

        Parameters
        ----------
        filename : string
            The file to open and read a configuration from.

        Returns
        -------
        out[0] : numpy.array
            The dimensions of the simulation box.
        out[1] : numpy.array
            The positions found in the given filename.
        out[2] : numpy.array
            The velocities found in the given filename.
        """
        pass

    @abstractmethod
    def _reverse_velocities(self, filename, outfile):
        """Reverse velocities in a given snapshot.

        Parameters
        ----------
        filename : string
            Input file with velocities.
        outfile : string
            File to write with reversed velocities.
        """
        pass

    @staticmethod
    def _modify_input(sourcefile, outputfile, settings, delim='='):
        """Modify input file for external software.

        Here we assume that the input file has a syntax consisting of
        ``keyword = setting``. We will only replace settings for
        the keywords we find in the file that is also inside the
        ``settings`` dictionary.

        Parameters
        ----------
        sourcefile : string
            The path of the file to use for creating the output.
        outputfile : string
            The path of the file to write.
        settings : dict
            A dictionary with settings to write.
        delim : string
            The delimiter used for separation keywords from settings
        """
        reg = re.compile(r'(.*?){}'.format(delim))
        written = set()
        with open(sourcefile, 'r') as infile, open(outputfile, 'w') as outfile:
            for line in infile:
                to_write = line
                key = reg.match(line)
                if key:
                    keyword = ''.join([key.group(1), delim])
                    keyword_strip = key.group(1).strip()
                    if keyword_strip in settings:
                        to_write = '{} {}\n'.format(keyword,
                                                    settings[keyword_strip])
                    written.add(keyword_strip)
                outfile.write(to_write)
            # Add settings not yet written:
            for key, value in settings.items():
                if key not in written:
                    outfile.write('{} {} {}\n'.format(key, delim, value))

    @staticmethod
    def _read_input_settings(sourcefile, delim='='):
        """Read input settings for simulation input files.,

        Here we assume that the input file has a syntax consisting of
        ``keyword = setting``, where ``=`` can be any string given
        in the input parameter ``delim``.

        Parameters
        ----------
        sourcefile : string
            The path of the file to use for creating the output.
        delim : string
            The delimiter used for separation keywords from settings

        Returns
        -------
        settings : dict of strings
            The settings found in the file.

        Note
        ----
        Important: We are here assuming that there will *ONLY* be one
        keyword per line.
        """
        reg = re.compile(r'(.*?){}'.format(delim))
        settings = {}
        with open(sourcefile, 'r') as infile:
            for line in infile:
                key = reg.match(line)
                if key:
                    keyword_strip = key.group(1).strip()
                    settings[keyword_strip] = line.split(delim)[1].strip()
        return settings

    def execute_command(self, cmd, cwd=None, inputs=None):
        """Method that will execute a command.

        We are here executing a command and then waiting until it
        finishes.

        Parameters
        ----------
        cmd : list of strings
            The command to execute.
        cwd : string or None
            The current working directory to set for the command.
        inputs : bytes or None
            Possible input to give to the command. This are not arguments
            but more akin to keystrokes etc. that the external command
            may take.

        Returns
        -------
        out : int
            The return code of the command.
        """
        cmd2 = ' '.join(cmd)
        logger.debug('Executing: %s', cmd2)
        if inputs is not None:
            logger.debug('With input: %s', inputs)

        out_name = 'stdout.txt'
        err_name = 'stderr.txt'

        if cwd:
            out_name = os.path.join(cwd, out_name)
            err_name = os.path.join(cwd, err_name)

        return_code = None

        with open(out_name, 'wb') as fout, open(err_name, 'wb') as ferr:
            exe = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=fout,
                stderr=ferr,
                shell=False,
                cwd=cwd
            )
            exe.communicate(input=inputs)
            # Note: communicate will wait until process terminates.
            return_code = exe.returncode
            if return_code != 0:
                logger.error('Execution of external program (%s) failed!',
                             self.description)
                logger.error('Attempted command: %s', cmd2)
                logger.error('Execution directory: %s', cwd)
                if inputs is not None:
                    logger.error('Input to external program was: %s', inputs)
                logger.error('Return code from external program: %i',
                             return_code)
                logger.error('STDOUT, see file: %s', out_name)
                logger.error('STDERR, see file: %s', err_name)
                msg = ('Execution of external program ({}) failed. '
                       'Return code: {}').format(self.description, return_code)
                raise RuntimeError(msg)
            else:
                self._removefile(out_name)
                self._removefile(err_name)
        return return_code

    @staticmethod
    def _movefile(source, dest):
        """Move file from source to destination."""
        logger.debug('Moving: %s -> %s', source, dest)
        shutil.move(source, dest)

    @staticmethod
    def _copyfile(source, dest):
        """Copy file from source to destination."""
        logger.debug('Copy: %s -> %s', source, dest)
        shutil.copyfile(source, dest)

    @staticmethod
    def _removefile(filename):
        """Remove a given file if it exist."""
        try:
            os.remove(filename)
            logger.debug('Removing: %s', filename)
        except OSError:
            logger.debug('Could not remove: %s', filename)

    def _remove_files(self, dirname, files):
        """Remove files from a directory.

        Parameters
        ----------
        dirname : string
            Where we are removing.
        files : list of strings
            A list with files to remove.
        """
        for thefile in files:
            self._removefile(os.path.join(dirname, thefile))

    def clean_up(self):
        """Will remove all files from the current directory."""
        dirname = self.exe_dir
        logger.debug('Running engine clean-up in "%s"', dirname)
        files = [item.name for item in os.scandir(dirname) if item.is_file()]
        self._remove_files(dirname, files)

    def calculate_order(self, order_function, system,
                        xyz=None, vel=None, box=None):
        """Calculate order parameter from configuration in a file.

        Note, if ``xyz``, ``vel`` or ``box`` are given, we will
        **NOT** read positions, velocity and box information from the
        current configuration file.

        Parameters
        ----------
        order_function : object like :py:class:`.OrderParameter`
            The class used for calculating the order parameter.
        system : object like :py:class:`.System`
            The object the order parameter is acting on.
        xyz : numpy.array, optional
            The positions to use, in case we have already read them
            somewhere else. We will then not attempt to read the again.
        vel : numpy.array, optional
            The velocities to use, in case we already have read them.
        box : numpy.array, optional
            The current box vectors, in case we already have read them.

        Returns
        -------
        out : list of floats
            The calculated order parameter(s).
        """
        if any((xyz is None, vel is None, box is None)):
            out = self._read_configuration(system.particles.config[0])
            box = out[0]
            xyz = out[1]
            vel = out[2]
        system.particles.pos = xyz
        if system.particles.vel_rev:
            if vel is not None:
                system.particles.vel = -1.0 * vel
        else:
            system.particles.vel = vel
        system.update_box(box)
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
            * `rescale_energy`: boolean, determines if energy is re-scaled.

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
        logger.info('Kicking with external integrator: %s', self.description)
        # We search for crossing with the middle interface and do this
        # by sequentially kicking the initial phase point
        # Let's get the starting point:
        initial_file = self.dump_frame(system)
        # Create a "previous file" for storing the state before a new kick
        prev_file = os.path.join(
            self.exe_dir,
            'p_{}'.format(os.path.basename(initial_file))
        )
        self._copyfile(initial_file, prev_file)
        # Update so that we use the prev_file
        system.particles.set_pos((prev_file, None))
        logger.info('Searching for crossing with: %9.6g', middle)
        print_to_screen('Searching for crossing with: {}'.format(middle))
        while True:
            print_to_screen('Kicking:')
            # Do kick from current state:
            self.modify_velocities(system,
                                   rgen,
                                   sigma_v=None,
                                   aimless=True,
                                   momentum=False,
                                   rescale=None)
            # Update order parameter in case it's velocity dependent:
            curr = self.calculate_order(order_function, system)[0]
            # Store the kicked configuration as the previous config.
            self._movefile(system.particles.get_pos()[0], prev_file)
            system.particles.set_pos((prev_file, None))
            previous = system.particles.get_particle_state()
            previous['order'] = curr
            # Update system by integrating forward:
            conf = self.step(system, 'gen_kick')
            curr_file = os.path.join(self.exe_dir, conf)
            # Compare previous order parameter and the new one:
            prev = curr
            curr = self.calculate_order(order_function, system)[0]
            txt = '{} -> {} | {}'.format(prev, curr, middle)
            if (prev <= middle < curr) or (curr < middle <= prev):
                logger.info('Crossed middle interface: %s', txt)
                print_to_screen('Crossed middle interface: {}'.format(txt),
                                level='info')
                # have crossed middle interface, just stop the loop
                break
            elif (prev <= curr < middle) or (middle < curr <= prev):
                # Getting closer, keep the new point
                logger.debug('Getting closer to middle: %s', txt)
                print_to_screen('-> Getting closer to middle: {}'.format(txt))
                self._movefile(curr_file, prev_file)
                # Update file name after moving:
                system.particles.set_pos((prev_file, None))
            else:  # we did not get closer, fall back to previous point
                logger.debug('Did not get closer to middle: %s', txt)
                print_to_screen(
                    '-> Did not get closer to middle: {}'.format(txt)
                )
                system.particles.set_particle_state(previous)
                curr = previous['order']
                self._removefile(curr_file)
        return previous, system.particles.get_particle_state()

    @abstractmethod
    def _extract_frame(self, traj_file, idx, out_file):
        """Extract a frame from a trajectory file.

        Parameters
        ----------
        traj_file : string
            The trajectory file to open.
        idx : integer
            The frame number we look for.
        out_file : string
            The file to dump to.
        """
        pass

    def propagate(self, path, system, order_function, interfaces,
                  reverse=False):
        """Propagate the equations of motion with the external code.

        This method will explicitly do the common set-up, before
        calling more specialised code for doing the actual propagation.

        Parameters
        ----------
        path : object like :py:class:`.PathBase`
            This is the path we use to fill in phase-space points.
            We are here not returning a new path - this since we want
            to delegate the creation of the path to the method
            that is running `propagate`.
        system : object like :py:class:`.System`
            The system object gives the initial state for the
            integration. The initial state is stored and the system is
            reset to the initial state when the integration is done.
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
        logger.debug('Running propagate with: "%s"', self.description)
        if reverse:
            logger.debug('Running backward in time.')
            name = 'trajB'
        else:
            logger.debug('Running forward in time.')
            name = 'trajF'
        logger.debug('Trajectory name: "%s"', name)

        initial_state = system.particles.get_particle_state()
        initial_file = self.dump_frame(system)
        logger.debug('Initial state: %s', initial_state)

        if reverse != initial_state['vel']:
            logger.debug('Reversing velocities in initial config.')
            basepath = os.path.dirname(initial_file)
            localfile = os.path.basename(initial_file)
            initial_conf = os.path.join(basepath, 'r_{}'.format(localfile))
            self._reverse_velocities(initial_file, initial_conf)
        else:
            initial_conf = initial_file

        # Update system to point to the configuration file:
        phase_point = {'pos': (initial_conf, None),
                       'vel': reverse,
                       'vpot': None,
                       'ekin': None}
        system.particles.set_particle_state(phase_point)
        # Propagate from this point:
        success, status = self._propagate_from(
            name,
            path,
            system,
            order_function,
            interfaces,
            reverse=reverse
        )
        # Reset system to initial state:
        system.particles.set_particle_state(initial_state)
        return success, status

    @abstractmethod
    def _propagate_from(self, name, path, system, order_function, interfaces,
                        reverse=False):
        """Method to run the actual propagation using the specific engine.

        This method is called after :py:meth:`.propagate`.

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
        pass

    def _name_output(self, basename):
        """Return the name of the output file."""
        return os.path.join(self.exe_dir, basename)

    def dump_config(self, config, deffnm='conf'):
        """Extract configuration frame from a system if needed.

        Parameters
        ----------
        config : tuple
            The configuration given as (filename, index).
        deffnm : string, optional
            The base name for the file we dump to.

        Returns
        -------
        out : string
            The file name we dumped to. If we did not in fact dump, this is
            because the system contains a single frame and we can use it
            directly. Then we return simply this file name.

        Note
        ----
        If the velocities should be reversed, this is handled elsewhere.
        """
        pos_file, idx = config
        out_file = os.path.join(self.exe_dir, self._name_output(deffnm))
        if idx is None:
            if pos_file != out_file:
                self._copyfile(pos_file, out_file)
        else:
            logger.debug('Config: %s', (config, ))
            self._extract_frame(pos_file, idx, out_file)
        return out_file

    def dump_frame(self, system, deffnm='conf'):
        """Just dump the frame from a system object."""
        return self.dump_config(system.particles.config, deffnm=deffnm)

    def dump_phasepoint(self, phasepoint, deffnm='conf'):
        """Just dump the frame from a system object."""
        pos_file = self.dump_config(phasepoint['pos'], deffnm=deffnm)
        phasepoint['pos'] = (pos_file, None)
