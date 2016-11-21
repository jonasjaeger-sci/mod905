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
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['ExternalScript']


class ExternalScript(object):
    """ExternalScript(object).

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

    __metaclass__ = ABCMeta  # Python2.

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

    @abstractmethod
    def execute_external(self):
        """Execute the external software."""
        return
    
    @abstractmethod
    def propagate(self):
        """Execute the external software until a condition is met."""
        return

    @abstractmethod
    def read_configuration(self):
        """Read output configuration from external software."""
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

        Parameters
        ----------
        outputfile : string
            The path of the file to write.
        nsteps : integer
            The number of steps to set.
        """
        return

    @abstractmethod
    def read_output(self):
        """Generic method for reading output from external software."""
        return

    def __str__(self):
        """Return the string description of the integrator."""
        return self.description
