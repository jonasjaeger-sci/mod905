# -*- coding: utf-8 -*-
"""This sub-package handle writers for pyretis data.

Writers are basically formatting the data created from pyretis.
The writers also have some additional functionality and can be used to
load data written by pyretis as well. This is used when analysing
the output from a pyretis simulation.


Modules:

- writers.py: Module for defining the base writer and some simple derived
  writers (for crossing data, energy and order parameter data).

- pathfile.py: Module for handling path data and path-ensemble data.

- traj.py: Module for handling writing of trajectory data.

Important functions:

- get_file_object: Opens a file for reading given a file type and file name.

- read_xyz_file: Read snapshots from a xyz file.

- read_gro_file: Read snapshots from a gromacs GRO file.

Important classes:

- CrossFile: A writer of crossing data.

- EnergyFile: A writer of energy data

- OrderFile: A writer of order parameter data.

- PathEnsembleFile: A writer of path ensemble data.
"""
from __future__ import absolute_import
import logging
# pyretis imports
from .traj import read_xyz_file, read_gromacs_file, TrajXYZ, TrajGRO
from .writers import CrossFile, EnergyFile, OrderFile
from .pathfile import PathEnsembleFile
from .tablewriter import TxtTable, get_predefined_table
from .txtinout import txt_save_columns
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


def get_file_object(file_type):
    """Return a file object which can be used for loading files.

    This is a convenience function to return an instance of a `Writer` or
    derived classes so that we are ready to read data from that file. Usage is
    intended to be in cases when we just want to open a file easily. The
    returned object can then be used to read the file using `load(filename)`.

    Parameters
    ----------
    file_type : string
        The desired file type

    Returns
    -------
    out : object like `Writer` from `pyretis.inout.writers`
        An object which implements the `load(filename)` method.

    Examples
    --------
    >>> from pyretis.inout.writers import get_file_object
    >>> crossfile = get_file_object('cross')
    >>> print(crossfile)
    >>> for block in crossfile.load('cross.dat'):
    >>>     print(len(block['data']))
    """
    file_map = {'cross': CrossFile, 'order':  OrderFile,
                'energy': EnergyFile, 'pathensemble': PathEnsembleFile}
    try:
        file_class = file_map[file_type]
        if file_type == 'pathensemble':
            msg = 'Opening a path ensemble file. Experimental feature!'
            logger.warning(msg)
            return file_class('000', None, None)
        else:
            return file_class()
    except KeyError:
        msg = 'Unknown file type {} requested. Ignored'.format(file_type)
        logger.error(msg)
        return None
