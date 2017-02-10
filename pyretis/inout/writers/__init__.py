# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""This sub-package handle writers for pyretis data.

Writers are basically formatting the data created from pyretis.
The writers also have some additional functionality and can be used to
load data written by pyretis as well. This is used when analysing
the output from a pyretis simulation.

Package structure
-----------------

Modules
~~~~~~~

fileio.py (:py:mod:`pyretis.inout.writers.fileio`)
    Module defining a class for handling writing of files.

gromacsio.py (:py:mod:`pyretis.inout.writers.gromacsio`)
    Module defining some io methods for use with GROMACS.

__init__.py
    This file.

pathfile.py (:py:mod:`pyretis.inout.writers.pathfile`)
    Module for handling path data and path-ensemble data.

tablewriter.py (:py:mod:`pyretis.inout.writers.tablewriter`)
    Module defining generic methods for creating text tables.

txtinout.py (:py:mod:`pyretis.inout.writers.txtinout`)
    Module defining some text based output.

writers.py (:py:mod:`pyretis.inout.writers.writers`)
    Module for defining the base writer and some simple derived writers
    (for crossing data, energy and order parameter data).

xyzio.py (:py:mod:`pyretis.inout.writers.xyzio`)
    Module for handling writing of trajectory data in XYZ format.

Important methods defined in this package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

get_writer (:py:func:`.get_writer`)
    Opens a file for reading given a file type and file name.

Important classes defined in this package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

CrossWriter (:py:class:`.CrossWriter`)
    A writer of crossing data.

EnergyWriter (:py:class:`.EnergyWriter`)
    A writer of energy data

EnergyPathWriter (:py:class:`.EnergyPathWriter`)
    A class for writing out energy data for paths.

OrderWriter (:py:class:`.OrderWriter`)
    A writer of order parameter data.

OrderPathWriter (:py:class:`.OrderPathWriter`)
    A class for writing out order parameter data for paths.

TrajWriter (:py:class:`.TrajWriter`)
    Generic class for writing trajectory output.

PathExtWriter (:py:class:`.PathExtWriter`)
    A class for writing external paths to file.

PathEnsembleWriter (:py:class:`.PathEnsembleWriter`)
    A writer of path ensemble data.

PathEnsembleFile (:py:class:`.PathEnsembleFile`)
    A class which represent path ensembles in files. This class is
    intended for use in an analysis.

XYZWriter (:py:class:`.XYZWriter`)
    A writer of trajectories in XYZ format.

PathXYZWriter (:py:class:`.PathXYZWriter`)
    A writer of path data to a file in XYZ format.

GROWriter (:py:class:`.GROWriter`)
    A writer of trajectories in GROMACS GRO format.

PathGROWriter (:py:class:`.PathGROWriter`)
    A writer of trajectories in GROMACS GRO format.

TxtTable (:py:class:`.TxtTable`)
    A generic table writer.

ThermoTable (:py:class:`.ThermoTable`)
    A specific table writer for energy output.

PathTable (:py:class:`.PathTable`)
    A specific table writer for path results.
"""
import logging
# pyretis imports
from pyretis.core.common import initiate_instance
from .fileio import FileIO
from .pathfile import PathEnsembleWriter, PathEnsembleFile
from .gromacsio import GROWriter, PathGROWriter
from .xyzio import XYZWriter, PathXYZWriter
from .tablewriter import TxtTable, ThermoTable, PathTable
from .writers import (CrossWriter,
                      EnergyWriter, EnergyPathWriter,
                      OrderWriter, OrderPathWriter,
                      TrajWriter, PathExtWriter)

logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


_CLASS_MAP = {'cross': CrossWriter,
              'order': OrderWriter,
              'energy': EnergyWriter,
              'trajgro': GROWriter,
              'trajxyz': XYZWriter,
              'pathensemble': PathEnsembleWriter,
              'thermotable': ThermoTable,
              'pathtable': PathTable,
              'pathorder': OrderPathWriter,
              'pathenergy': EnergyPathWriter,
              'pathtrajxyz': PathXYZWriter,
              'pathtrajgro': PathGROWriter,
              'pathtrajext': PathExtWriter}


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
    out : object like :py:class:`.Writer`
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
