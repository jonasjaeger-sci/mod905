# -*- coding: utf-8 -*-
"""
This library handles the input and output for pyretis.

This package is intended for creating various forms of output
from the pyretis program. It include writers for simple text based
output and plotters for creating figures. Figures and the text results
can be combined into reports, which can be templated.

Package structure
=================

Modules
-------

- analysisio.py: This is a module to output the analysis of (RE)TIS
  simulation.

- common.py: This module contains some common functions. These functions
  are mainly intended for internal use and are not currently imported
  here.

- __init__.py: Imports from the other modules and define some convenience
  functions for creating trajectory writers and text tables.

- fileinout.py: Module for handling writing and reading of crossing,
  energy, order parameter and path ensemble data.

- mpl_plotting.py: Module which defines plotting using matplotlib.

- plotting.py: This file defines some colors etc. for plotting. It
  also defines a function which can be used to load different plotting
  objects.

- report.py: Module for creating reports based on analysis. This module
  is responsible for creating the final output from the analysis of (RE)TIS
  simulations

- traj.py: Module for handling writing and reading of trajectories.

- txtinout.py: Defines objects and some methods for text-based output.
  It defines the TxtTable object (table-like-format) intended to be
  written to the screen during a simulation or to a file.
  Futher it defines the more general FileWriter object, which is used by
  other file writers (as in traj.py and fileinout.py).

Important classes and functions
-------------------------------

- WriteGromacs & WriteXYZ: Classes for writing coordinates.

- CrossFile, EnergyFile, OrderFile: Classes for writing crossing data
  (for initial the flux), energy data and order parameter data.

- PathEnembleFile: A writer of path ensemble data.

- generate_report: A function to generate reports from analysis output(s).

- create_traj_writer: A function to create a trajectory writer from given
  settings.

- get_predefined_table: A function to get an object which can be used to
  pretty-print tables to the screen/file during a simulation.

Folders
-------

- styles: This folder contains style files for matplotlib.

- templates: This folder contains templates for the report.
"""
from .txtinout import TxtTable, FileWriter
from .traj import WriteGromacs, WriteXYZ
from .fileinout import CrossFile, EnergyFile, OrderFile, PathEnsembleFile
from .report import generate_report_md, generate_report_tis


def create_traj_writer(filename, filefmt, oldfile, system):
    """
    This is a method which will set up a trajectory writer object from
    the settings in a given dictionary.

    Parameters
    ----------
    filename : string
        Name of file to create
    filefmt : string
        Format of file, 'xyz' for xyz, 'gro' for gromacs.
    oldfile : string
        How to deal with backups of old files with the same name.
    system : object like `System` from `pyretis.core.system`
        This object is included since information about the units (and
        possibly the box) is needed.
    """
    if filefmt == 'xyz':
        trajwriter = WriteXYZ(filename,
                              system,
                              oldfile=oldfile)
    elif filefmt == 'gro':
        trajwriter = WriteGromacs(filename,
                                  system,
                                  oldfile=oldfile)
    else:
        trajwriter = None
    return trajwriter

# define some table which may be usefull. These tables
# can be selected using the get_predefined_tables method defined below
_DEFINED_TABLES = {'energies': {'title': 'Energy output',
                                'var': ['stepno', 'temp', 'vpot',
                                        'ekin', 'etot', 'press'],
                                'headers': ['Step', 'Temp', 'Pot',
                                            'Kin', 'Tot', 'Press'],
                                'width': (10, 12), 'spacing': 2,
                                'row_fmt': ['{:> 10d}'] + 5 * ['{:> 12.6g}']}}


def get_predefined_table(table):
    """
    This method will just set up and return some predefined tables which
    are used often. It simply initiate TxtTable with some predefined
    settings.

    Parameters
    ----------
    table : string
        This should match one of the defined tables in _DEFINED_TABLES

    Returns
    -------
    out : object of type `TxtTable` from `pyretis.inout.txtinout`
        This is the text table that can be used for output.
    """
    settings = _DEFINED_TABLES.get(table.lower(), None)
    if settings is None:
        return None
    else:
        tab = TxtTable(settings['var'], width=settings['width'],
                       headers=settings['headers'],
                       spacing=settings['spacing'])
        if 'row_fmt' in settings:  # override the row-format:
            tab.row_fmt = (' ') * settings['spacing']
            tab.row_fmt = tab.row_fmt.join(settings['row_fmt'])
        return tab
