# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Definition of external integrators.

This module defines the external integrator. In addition
it defines a class for the execution script which is
sub-classed by all external scripts.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ExternalScript
    The base class for external scripts. This defines the actual
    interface to external programs.
"""
import re
import logging
import subprocess
import shutil
import os
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['ExternalScript']


class ExternalScript(object):
    """Base class for interfacing external programs.

    This class defines the interface to external programs. This
    interface will define how we interact with the external programs
    and how we write input files for them and read output files.

    Attributes
    ----------
    description : string
        Short string which a description about the external
        script. This can for instance be what program we are
        interfacing.
    time_step : float
        The time step used in the GROMACS MD simulation.
    subcycles : integer
        The number of steps each GROMACS MD run is composed of.
    ext_time : float
        The time to extend simulations by. It is equal to
        ``time_step * subcycles``. 
    """

    _int_type = 'external'

    def __init__(self, description, exe, time_step, subcycles):
        """Initialization of the script.

        Parameters
        ----------
        description : string
            Short string which a description about the external
            script. This can for instance be what program we are
            interfacing.
        time_step : float
            The time step used in the GROMACS MD simulation.
        subcycles : integer
            The number of steps each GROMACS MD run is composed of.
        """
        self.description = description
        self.exe = exe
        self.time_step = time_step
        self.subcycles = subcycles
        self.ext_time = self.time_step * self.subcycles
        self.exe_dir = None

    @property
    def int_type(self):
        """Just return the type for the integrator."""
        return type(self)._int_type

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
            msg = 'Executing "{}"'.format(cmd)
            logger.info(msg)
        else:
            msg = 'Executing "{}" with input "{}"'.format(cmd, inputs)
            logger.info(msg)
        # print(' '.join(cmd))
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
        print('moving {} -> {}'.format(source, dest))
        shutil.move(source, dest)

    @staticmethod
    def copyfile(source, dest):
        """Copy file from source to destination."""
        print('copying {} -> {}'.format(source, dest))
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

    def __str__(self):
        """Return the string description of the integrator."""
        return self.description
