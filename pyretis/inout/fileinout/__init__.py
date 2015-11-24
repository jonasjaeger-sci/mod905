# -*- coding: utf-8 -*-
"""This sub-package handle the input and output of pyretis files.

These files will store results/outputs from the simulation and
can be used to analyze a simulation.

Modules:

- crossfile.py: Module for handling crossing data.

- energyfile.py: Module for handling energy data.

- fileinout.py: Module for handling generic writing of data.

- orderfile.py: Module for handling order parameter data.

- pathfile.py: Module for handling path data and path-ensemble data.

- traj.py: Module for handling writing of trajectory data.

Important functions:

- create_traj_writer: A function to create a trajectory writer from given
  settings.

- get_file_object: Opens a file for reading given a file type and file name.

Important classes:

- FileWriter: A generic file writer class.

- CrossWriter: A writer of crossing data.

- EnergyFile: A writer of energy data

- OrderFile: A writer of order parameter data.

- PathFile: A writer for path data.

- PathEnembleFile : A writer of path ensemble data.
"""
from __future__ import absolute_import
import warnings
# pyretis imports
from .traj import create_traj_writer
from .fileinout import FileWriter
from .crossfile import CrossFile
from .energyfile import EnergyFile
from .orderfile import OrderFile
from .pathfile import PathFile, PathEnsembleFile


def get_file_object(file_type, file_name):
    """Open a file for reading using a file reader based on file type.

    This is a convenience function to return an instance of `FileWriter` or
    derived classes so that we are ready to read data from that file. Usage is
    indended to be in cases when we just want to open a file easily. The
    returned object can then be used to read the file using `load()`.

    Parameters
    ----------
    file_type : string
        The desired file type
    file_name : string
        The file to open
    ensemble : string
        In case we are opening a path ensemble, we can specify the which one.
    interfaces : list of floats
        In case we are opening a path ensemble we can specify the interfaces

    Returns
    -------
    out : object like `FileWriter` from `pyretis.inout.fileinout`

    Examples
    --------
    >>> from pyretis.inout.fileinout import get_file_object
    >>> crossfile = get_file_object('cross', 'cross.dat')
    >>> print(crossfile)
    >>> for block in crossfile.load():
    >>>     print(len(block['data']))
    """
    if file_type == 'cross':
        return CrossFile(file_name, mode='r')
    elif file_type == 'order':
        return OrderFile(file_name, mode='r')
    elif file_type == 'energy':
        return EnergyFile(file_name, mode='r')
    elif file_type == 'pathensemble':
        msg = 'Opening a path ensemble is not yet implemented completely!'
        warnings.warn(msg)
        return PathEnsembleFile(file_name, None, None, mode='r')
    elif file_type == 'path':
        return PathFile(file_name, mode='r')
    else:
        msg = 'Unknown file type {} requested. Aborting reading {}'
        msg = msg.format(file_type, file_name)
        warnings.warn(msg)
        return None
