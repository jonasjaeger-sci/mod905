# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
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
from __future__ import absolute_import
from abc import ABCMeta, abstractmethod
import logging
import subprocess
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['ExternalScript']


class ExternalScript(metaclass=ABCMeta):
    """ExternalScript(metaclass=ABCMeta).

    This class defines the interface to external programs. This
    interface will define how we interact with the external programs
    and how we write input files for them and read output files.

    Attributes
    ----------
    description : string
        Short string which a description about the external
        script. This can for instance be what program we are
        interfacing.
    """

    def __init__(self, description):
        """Initialization of the script.

        Parameters
        ----------
        description : string
            Short string which a description about the external
            script. This can for instance be what program we are
            interfacing.
        """
        self.description = description

    @staticmethod
    @abstractmethod
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
        return

    @abstractmethod
    def write_configuration(self):
        """Write input configuration for external software."""
        return

    @abstractmethod
    def read_input(self):
        """Read input file for external software."""
        return

    @abstractmethod
    def write_input(self, outputfile, nsteps):
        """Write input file for external software.

        Here we will just update the number of steps to run.

        Parameters
        ----------
        outputfile : string
            The path of the file to write.
        nsteps : integer
            The number of steps to set in the file.
        """
        return

    @abstractmethod
    def read_output(self):
        """Generic method for reading output from external software."""
        return

    @staticmethod
    def execute_command(cmd, inputs=None):
        """Method that will execute a command.

        We are here executing a command and then waiting until it
        finishes.

        Parameters
        ----------
        cmd : list of strings
            The command to execute.
        inputs : string
            Possible input to give to the command.

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
        exe = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, shell=False)
        out = exe.communicate(input=inputs)
        if exe.returncode != 0:
            msg = out[1].decode('utf-8')
            logger.critical(msg)
            raise RuntimeError(msg)
        return out, exe.returncode

    def calculate_order_parameter(self, orderp, system, filename):
        """Calculate order parameter from configuration in a file.

        Parameters
        ----------
        orderp : object like `pyretis.orderparameter.OrderParameter`
            The object responsible for calculating the order parameter.
        system : object like `pyretis.core.system`
            The object the order parameter is acting on.
        filename : string
            The file with the configuration for which we want to
            calculate the order parameter.

        Returns
        -------
        out : float
            The calculated order parameter.
        """
        xyz, vel = self.read_configuration(filename)
        system.particles.pos = xyz
        system.particles.vel = vel
        return orderp.calculate(system)

    def __str__(self):
        """Return the string description of the integrator."""
        return self.description
