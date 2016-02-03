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

- CrossWriter: A writer of crossing data.

- EnergyWriter: A writer of energy data

- OrderWriter: A writer of order parameter data.

- PathEnsembleWriter: A writer of path ensemble data.

- PathEnsembleFile: A class which represent path ensembles in files.
  This class is useful for the analysis.

- TrajXYZ: A writer of trajectories in xyz-format.

- TrajGRO: A writer of trajectories in GROMACS gro-format.

- TxtTable: A generic table writer.

- ThermoTable: A specific table writer for energy output.

- PathTable: A specific table writer for path results.
"""
from __future__ import absolute_import
import logging
# pyretis imports
from .fileio import FileIO
from .pathfile import PathEnsembleWriter, PathEnsembleFile
from .traj import read_xyz_file, read_gromacs_file, TrajXYZ, TrajGRO
from .txtinout import txt_save_columns
from .tablewriter import TxtTable, ThermoTable, PathTable
from .writers import CrossWriter, EnergyWriter, OrderWriter
from pyretis.inout.settings.common import initiate_instance

logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


_CLASS_MAP = {'cross': {'class': CrossWriter},
              'order': {'class': OrderWriter},
              'energy': {'class': EnergyWriter},
              'trajgro': {'class': TrajGRO, 'args': [('units', 'lj')]},
              'trajxyz': {'class': TrajXYZ, 'args': [('units', 'lj')]},
              'pathensemble': {'class': PathEnsembleWriter,
                               'args': [('ensemble', '000'),
                                        ('interfaces', None)]},
              'thermotable': {'class': ThermoTable},
              'pathtable': {'class': PathTable}}


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
    try:
        if file_type == 'pathensemble':
            msg = 'Opening a path ensemble file. Experimental feature!'
            logger.warning(msg)
        return get_writer(file_type, settings=None)
    except KeyError:
        msg = 'Unknown file type {} requested. Ignored'.format(file_type)
        logger.error(msg)
        return None


def get_writer(writer_type, settings=None):
    """This method is intented as a factory method for writers.

    Parameters
    ----------
    writer_type : string
        This string defines the class we want to initiate
    settings : dict, optional
        Additional settings that might be required for the
        initialization of the class.
    """
    try:
        writer = _CLASS_MAP[writer_type]
        cls = writer['class']
        args = writer.get('args', None)
        kwargs = writer.get('kwargs', None)
        if args is not None:
            if settings is None:
                arg_val = [arg[1] for arg in args]
            else:
                arg_val = [settings.get(arg[0], arg[1]) for arg in args]
        else:
            arg_val = None
        if kwargs is not None:
            kwarg_val = {}
            if settings is not None:
                for key in kwargs:
                    kwarg_val[key] = settings.get(key, kwargs[key])
        else:
            kwarg_val = None
        return initiate_instance(cls, args=arg_val, kwargs=kwarg_val)
    except KeyError:
        msg = 'Ignored creating unknown writer "{}"!'.format(writer_type)
        logger.error(msg)
        return None
