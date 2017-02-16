# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Definition of external engines.

This module defines the base class for external MD engines.
This class is subclassed by all other external MD engines.

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
        of subcycles.
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
    ext : string
        Extension for configuration files.
    """
    engine_type = 'external'

    def __init__(self, description, timestep, subcycles, ext):
        """Initialization of the external engine.

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
            The number of steps each external interation run is
            composed of.
        ext : string
            The file extension for configuration files.
        """
        super().__init__(description)
        self.timestep = timestep
        self.subcycles = subcycles
        self._exe_dir = None
        self.ext = '{}{}'.format(os.extsep, ext)

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
        which can be used, for instance in the initialization.
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

    @staticmethod
    @abstractmethod
    def _read_configuration(filename):
        """Read output configuration from external software.

        Parameters
        ----------
        filename : string
            The file to open and read a configuration from.

        Returns
        -------
        xyz : numpy.array
            The positions found in the given filename.
        vel : numpy.array
            The velocities found in the given filename.
        """
        pass

    @staticmethod
    @abstractmethod
    def _reverse_velocities(filename, outfile):
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

        Here we assume that the input file has a syntax consiting of
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
                outfile.write(to_write)

    @staticmethod
    def _read_input_settings(sourcefile, delim='='):
        """Read input settings for simulation input files.,

        Here we assume that the input file has a syntax consiting of
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
        inputs : string or None
            Possible input to give to the command. This are not arguments
            but more akin to keystrokes etc. that the external command
            may take.

        Returns
        -------
        out[0] : tuple of strings
            The output (stdout, stderr) from the command.
        out[1] : int
            The return code of the command.
        """
        cmd2 = ' '.join(cmd)
        logger.debug('Executing: %s', cmd2)
        if inputs is not None:
            logger.debug('With input: %s', inputs)
        exe = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               shell=False,
                               cwd=cwd)
        out = exe.communicate(input=inputs)
        # Note: communicate will wait untill process terminates.
        return_code = exe.returncode
        if return_code != 0:
            stdout, stderr = out[0], out[1]
            logger.error('Execution of external program (%s) failed!',
                         self.description)
            logger.error('Attempted command: "%s"', cmd2)
            logger.error('Execution directory: "%s"', cwd)
            if inputs is not None:
                logger.error('Input to external program was: "%s"', inputs)
            logger.error('Return code from external program %i', return_code)
            logger.error('STDOUT: %s', stdout.decode('utf-8'))
            logger.error('STDERR: %s', stderr.decode('utf-8'))
            msg = ('Execution of external program "{}" failed. '
                   'Return code: {}').format(self.description, return_code)
            raise RuntimeError(msg)
        return out, exe.returncode

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
        if os.path.isfile(filename):
            logger.debug('Removing: %s', filename)
            os.remove(filename)

    def _remove_files(self, dirname, files):
        """Remove files from a directory.

        Parameters
        ----------
        dirname : string
            Where we are removing.
        file_names : list of strings
            A list with files to remove.
        """
        for thefile in files:
            self._removefile(os.path.join(dirname, thefile))

    def clean_up(self):
        """Remove all files from a given directory.

        Parameters
        ----------
        dirname : string
            The directory to remove files from.
        """
        dirname = self.exe_dir
        logger.debug('Running engine clean-up in "%s"', dirname)
        files = [item.name for item in os.scandir(dirname) if item.is_file()]
        self._remove_files(dirname, files)

    def calculate_order(self, order_function, system):
        """Calculate order parameter from configuration in a file.

        Parameters
        ----------
        order_function : object like :py:class:`.OrderParameter`
            The class used for calculating the order parameter.
        system : object like :py:class:`.System`
            The object the order parameter is acting on.

        Returns
        -------
        out : float
            The calculated order parameter.
        """
        xyz, vel = self._read_configuration(system.particles.config[0])
        system.particles.pos = xyz
        if system.particles.vel_rev:
            system.particles.vel = -vel
        else:
            system.particles.vel = vel
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
        print('Searching for crossing with: {}'.format(middle))
        while True:
            print('Kicking...')
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
                print('Crossed middle interface: {}'.format(txt))
                # have crossed middle interface, just stop the loop
                break
            elif (prev <= curr < middle) or (middle < curr <= prev):
                # Getting closer, keep the new point
                logger.debug('Getting closer to middle: %s', txt)
                print('Getting closer to middle: {}'.format(txt))
                self._movefile(curr_file, prev_file)
                # Update file name after moving:
                system.particles.set_pos((prev_file, None))
            else:  # we did not get closer, fall back to previous point
                logger.debug('Did not get closer to middle: %s', txt)
                print('Did not get closer to middle: {}'.format(txt))
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
        calling more specialized code for doing the actual propagation.

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

        # Update system to be at the configuration file:
        phase_point = {'pos': (initial_conf, None),
                       'vel': reverse,
                       'vpot': None,
                       'ekin': None}
        system.particles.set_particle_state(phase_point)
        # Perform propagate from this point
        success, status = self._propagate_from(
            name,
            path,
            system,
            order_function,
            interfaces,
            reverse=reverse)
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
        if idx is None:
            # Note, this does not create a new file.
            return pos_file
        else:
            out_file = os.path.join(self.exe_dir,
                                    '{}{}'.format(deffnm, self.ext))
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
