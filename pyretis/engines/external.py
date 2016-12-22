# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Definition of external integrators.

This module defines the external integrator. In addition
it defines a class for the execution script which is
sub-classed by all external scripts.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ExternalMDEngine
    The base class for external scripts. This defines the actual
    interface to external programs.
"""
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
    """Base class for interfacing external engines (programs).

    This class defines the interface to external programs. This
    interface will define how we interact with the external programs
    and how we write input files for them and read output files.

    Attributes
    ----------
    description : string
        Short string which a description about the external
        script. This can for instance be what program we are
        interfacing.
    timestep : float
        The time step used for the external engine.
    subcycles : integer
        The number of steps the external step is composed of. That is
        each external step is really composed of ``subcycles``
        number of iterations.
    ext_time : float
        The time to extend simulations by. It is equal to
        ``timestep * subcycles``.
    ext : string
        Extension for configuration files. It includes the
        extension separator ".".
    """

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
        self.description = description
        self.timestep = timestep
        self.subcycles = subcycles
        self.ext_time = self.timestep * self.subcycles
        self.exe_dir = None
        self.ext = '{}{}'.format(os.extsep, ext)

    @property
    def engine_type(self):
        """Just return the type for the engine."""
        return 'external'

    @staticmethod
    def read_configuration(filename):
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
        raise NotImplementedError

    @staticmethod
    def modify_input(sourcefile, outputfile, settings, delim='='):
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
    def execute_command(cmd, cwd=None, inputs=None):
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
        if inputs is None:
            cmd2 = ' '.join(cmd)
            msg = 'Executing "{}"'.format(cmd2)
            logger.info(msg)
        else:
            cmd2 = ' '.join(cmd)
            msg = 'Executing "{}" with input "{}"'.format(cmd2, inputs)
            logger.info(msg)
        exe = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               shell=False,
                               cwd=cwd)
        out = exe.communicate(input=inputs)
        if exe.returncode != 0:
            msg = out[1].decode('utf-8')
            logger.critical(msg)
            raise RuntimeError(msg)
        return out, exe.returncode

    @staticmethod
    def movefile(source, dest):
        """Move file from source to destination."""
        shutil.move(source, dest)

    @staticmethod
    def copyfile(source, dest):
        """Copy file from source to destination."""
        shutil.copyfile(source, dest)

    @staticmethod
    def removefile(filename):
        """Remove a given file if it exist."""
        if os.path.isfile(filename):
            os.remove(filename)

    def calculate_order(self, order_function, system):
        """Calculate order parameter from configuration in a file.

        Parameters
        ----------
        order_function : object like :py:class:`OrderParameter`
            The class used for calculating the order parameter.
        system : object like `pyretis.core.system`
            The object the order parameter is acting on.

        Returns
        -------
        out : float
            The calculated order parameter.
        """
        xyz, vel = self.read_configuration(system.particles.config[0])
        system.particles.pos = xyz
        if system.particles.vel_rev:
            system.particles.vel = -vel
        else:
            system.particles.vel = vel
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
        particles = system.particles
        initial_file = self.dump_frame(system)
        # Start with a "previous" file:
        prev_file = os.path.join(self.exe_dir, 'previous{}'.format(self.ext))
        self.copyfile(initial_file, prev_file)
        previous = particles.get_particle_state()
        previous['pos'] = (prev_file, None)
        particles.set_particle_state(previous)
        curr = self.calculate_order(order_function, system)[0]
        curr_file = os.path.join(self.exe_dir, 'current{}'.format(self.ext))
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
            out_files = self.integration_step(system, 'current', self.exe_dir)
            # Remove all out files, but not the config:
            for key, val in out_files.items():
                if key != 'conf':
                    filename = os.path.join(self.exe_dir, val)
                    self.removefile(filename)
            # Compare previous order parameter and the new one:
            prev = curr
            curr = self.calculate_order(order_function, system)[0]
            print(prev, curr, middle)
            if (prev <= middle < curr) or (curr < middle <= prev):
                # have crossed middle interface, just stop the loop
                break
            elif (prev <= curr < middle) or (middle < curr <= prev):
                # Getting closer, keep the new point
                print('Getting closer!')
                self.movefile(curr_file, prev_file)
                # Update file name after moving:
                particles.set_pos((prev_file, None))
            else:  # we did not get closer, fall back to previous point
                print('Did not get closer...')
                particles.set_particle_state(previous)
                curr = previous['order']
                filename = os.path.join(self.exe_dir, out_files['conf'])
                self.removefile(filename)
        return previous, particles.get_particle_state()

    def extract_frame(self, traj_file, idx, out_file):
        """Extract a frame from a .trr file.

        Parameters
        ----------
        traj_file : string
            The trajectory file to open.
        idx : integer
            The frame number we look for.
        out_file : string
            The file to dump to.
        """
        raise NotImplementedError

    def propagate(self, path, system, order_function, interfaces,
                  reverse=False):
        """Propagate the equations of motion with the external code."""
        raise NotImplementedError

    def integration_step(self, system, name, exe_dir):
        """Integrate the given system forward in time."""
        raise NotImplementedError

    def modify_velocities(self, system, rgen, sigma_v=None, aimless=True,
                          momentum=False, rescale=None):
        """Modify the velocities of the current state."""
        raise NotImplementedError

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
        We assume here that we won't be using the velocities in the
        configuration and we do not reverse the velocities.
        """
        pos_file, idx = config
        if idx is None:
            return pos_file
        else:
            out_file = os.path.join(self.exe_dir,
                                    '{}{}'.format(deffnm, self.ext))
            self.extract_frame(pos_file, idx, out_file)
            return out_file

    def dump_frame(self, system, deffnm='conf'):
        """Just dump the frame from a system object."""
        return self.dump_config(system.particles.config, deffnm=deffnm)

    def dump_phasepoint(self, phasepoint, deffnm='conf'):
        """Just dump the frame from a system object."""
        pos_file = self.dump_config(phasepoint['pos'], deffnm=deffnm)
        phasepoint['pos'] = (pos_file, None)

    def __str__(self):
        """Return the string description of the integrator."""
        return self.description
