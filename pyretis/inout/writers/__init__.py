# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""This sub-package handle writers for pyretis data.

Writers are basically formatting the data created from pyretis.
The writers also have some additional functionality and can be used to
load data written by pyretis as well. This is used when analysing
the output from a pyretis simulation.

Package structure
-----------------

Modules
~~~~~~~

writers.py
    Module for defining the base writer and some simple derived writers
    (for crossing data, energy and order parameter data).

pathfile.py
    Module for handling path data and path-ensemble data.

traj.py
    Module for handling writing of trajectory data.

Important methods defined in this package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

get_writer
    Opens a file for reading given a file type and file name.

read_xyz_file
    Read snapshots from a xyz file.

read_gro_file
    Read snapshots from a gromacs GRO file.

Important classes defined in this package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

CrossWriter
    A writer of crossing data.

EnergyWriter
    A writer of energy data

OrderWriter
    A writer of order parameter data.

PathEnsembleWriter
    A writer of path ensemble data.

PathEnsembleFile
    A class which represent path ensembles in files. This class is
    intended for use in an analysis.

TrajXYZ
    A writer of trajectories in xyz-format.

TrajGRO
    A writer of trajectories in GROMACS gro-format.

TxtTable
    A generic table writer.

ThermoTable
    A specific table writer for energy output.

PathTable
    A specific table writer for path results.
"""
from __future__ import absolute_import
import logging
# pyretis imports
from pyretis.core.common import initiate_instance
from .fileio import FileIO
from .pathfile import PathEnsembleWriter, PathEnsembleFile
from .traj import read_xyz_file, read_gromacs_file, TrajXYZ, TrajGRO
from .txtinout import txt_save_columns
from .tablewriter import TxtTable, ThermoTable, PathTable
from .writers import CrossWriter, EnergyWriter, OrderWriter

logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


_CLASS_MAP = {'cross': CrossWriter,
              'order': OrderWriter,
              'energy': EnergyWriter,
              'trajgro': TrajGRO,
              'trajxyz': TrajXYZ,
              'pathensemble': PathEnsembleWriter,
              'thermotable': ThermoTable,
              'pathtable': PathTable}


def get_writer(file_type, settings=None):
    """Return a file object which can be used for loading files.

    This is a convenience function to return an instance of a `Writer`
    or derived classes so that we are ready to read data from that file.
    Usage is intended to be in cases when we just want to open a file
    easily. The returned object can then be used to read the file
    using `load(filename)`.

    Parameters
    ----------
    file_type : string
        The desired file type
    settings : dict
        A dict of settings we might need to pass for to the writer.
        This can for instance be the units for a trajectory writer.

    Returns
    -------
    out : object like `Writer` from `pyretis.inout.writers`
        An object which implements the `load(filename)` method.

    Examples
    --------
    >>> from pyretis.inout.writers import get_writer
    >>> crossfile = get_writer('cross')
    >>> print(crossfile)
    >>> for block in crossfile.load('cross.dat'):
    >>>     print(len(block['data']))
    """
    try:
        cls = _CLASS_MAP[file_type]
        if settings is None:
            return initiate_instance(cls, {})
        else:
            return initiate_instance(cls, settings)
    except KeyError:
        msg = 'Unknown file type {} requested. Ignored'.format(file_type)
        logger.error(msg)
        return None
