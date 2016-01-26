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

- read_xyz_file: Read snapshots from a xyz file.

- read_gro_file: Read snapshots from a gromacs GRO file.

Important classes:

- FileWriter: A generic file writer class.

- CrossWriter: A writer of crossing data.

- EnergyFile: A writer of energy data

- OrderFile: A writer of order parameter data.

- PathEnsembleFile : A writer of path ensemble data.
"""
from __future__ import absolute_import
import logging
# pyretis imports
from .traj import create_traj_writer, read_xyz_file, read_gromacs_file
from .fileinout import FileWriter
from .crossfile import CrossFile
from .energyfile import EnergyFile
from .orderfile import OrderFile
from .pathfile import PathEnsembleFile
logging.getLogger(__name__).addHandler(logging.NullHandler())


def get_file_object(file_type, file_name):
    """Open a file for reading using a file reader based on file type.

    This is a convenience function to return an instance of `FileWriter` or
    derived classes so that we are ready to read data from that file. Usage is
    intended to be in cases when we just want to open a file easily. The
    returned object can then be used to read the file using `load()`.

    Parameters
    ----------
    file_type : string
        The desired file type
    file_name : string
        The file to open

    Returns
    -------
    out : object like `FileWriter` from `pyretis.inout.fileio`

    Examples
    --------
    >>> from pyretis.inout.fileio import get_file_object
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
        msg = 'Opening a path ensemble is still an experimental feature!'
        logging.warning(msg)
        return PathEnsembleFile(file_name, None, None, mode='r')
    else:
        msg = 'Unknown file type {} requested. Aborting reading {}'
        msg = msg.format(file_type, file_name)
        logging.error(msg)
        return None
