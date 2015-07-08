# -*- coding: utf-8 -*-
"""
This library handles the input and output for pytismol.

Package structure
=================

Modules:

- analysisio.py: This is a module to output the analysis of (RE)TIS
  simulation. It defines functions for outputting to text files
  (using numpy.savetxt) or plotting files using pyplot.

- common.py: This module contains some common functions. These functions
  are mainly intended for internal use and are not currently imported
  here.

- __init__.py: Imports from the other modules and define some convenience
  functions for creating trajectory writers and text tables.

- plotting.py: This file defines some colors etc. for plotting. It
  also defines a function which can be used to load different plotting
  styles, among them the default pytismol style.

- report.py: Module for creating reports based on analysis. This module
  is responsible for creating the final output from the analysis of (RE)TIS
  simulations

- txtinout.py: Defines objects and some methods for text-based output.
  It defines the TxtTable object (table-like-format) intended to be
  written to the screen during a simulation or to a file.
  Futher it defines the more general FileWriter
  object and the trajectory-writers for storing trajectories in
  a 'standard' format, e.g. .xyz or .gro.

Folders:

- styles: This folder contains style files for matplotlib.

- templates: This folder contains templates for the report.
"""
from .analysisio import (mpl_output_analysis, mpl_total_probability,
                         txt_output_analysis, txt_total_probability)
from .plotting import set_plotting_style
from .report import generate_report
from .txtinout import WriteXYZ, WriteGromacs, FileWriter, TxtTable


def create_traj_writer(settings, system):
    """
    This is a method which will set up a trajectory writer object from
    the settings in a given dictionary.

    Parameters
    ----------
    settings : dict
        These are the settings (filename etc) to use for creating the
        trajectory writer
    system : object of type system
        This object is included since information about the units (and
        possibly the box) is needed.
    """
    if settings['type'] == 'xyz':
        trajwriter = WriteXYZ(settings['file'],
                              units=system.units)
    elif settings['type'] == 'gro':
        trajwriter = WriteGromacs(settings['file'],
                                  system.box,
                                  system.units)
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
                                'width': (10, 12), 'spacing': 2}}


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
    out : object of type TxtTable
    """
    settings = _DEFINED_TABLES.get(table.lower(), None)
    if settings is None:
        return None
    else:
        tab = TxtTable(settings['var'], width=settings['width'],
                       headers=settings['headers'],
                       spacing=settings['spacing'])
        return tab
