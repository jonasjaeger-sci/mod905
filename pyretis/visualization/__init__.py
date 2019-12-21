# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""The sub-package with tools for visualizing simulation results for PyRETIS.

This package is intended for compiling data of a simulation into a compact file
standard (pickle), and displaying results from file in a custom GUI applet.
Included are compiler of simulation data and a custom built PyQt5 GUI applet
that loads pre-compiled data (or compiles when loading raw simulation data).
The applet allows for user-friendly and interactive plotting of combinations of
order parameter data of different interfaces and cycles of the simulation.

Package structure
~~~~~~~~~~~~~~~~~

Modules
~~~~~~~

__init__.py
    Imports from the other modules.

common.py (:py:mod:`pyretis.visualization.common`)
    Common functions and variables for the visualization. These functions
    are mainly intended for internal use and are not imported here.

orderparam_density.py (:py:mod:`pyretis.visualization.orderparam_density`)
    A module that handles the compiling of data to a single file.

plotting.py (:py:mod:`pyretis.visualization.plotting`)
    A module which contains some functions that are used to plot regression
    lines and interface planes, and generate surface plots.

resources_rc.py (:py:mod:`pyretis.visualization.resources_rc`)
    A module containing the resources, icons/logos for the PyRETIS GUI.

visualize.py (:py:mod:`pyretis.visualization.visualize`)
    A module that handles the loading and plotting of data from a compiled file
    or a simulation.

Sub-packages
~~~~~~~~~~~~

None

Important classes defined in this package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

CustomFigCanvas
    (:py:class:`pyretis.visualization.visualize.CustomFigCanvas`)
    A class for the custom figure shown in the VisualApp class PyQt5 applet.

DataObject
    (:py:class:`pyretis.visualization.visualize.DataObject`)
    A class that reads from simulation data, holds the data, and supplies the
    data to VisualApp for plotting.

DataSlave (:py:class:`pyretis.visualization.visualize.DataSlave`)
    QObject class definition that holds the PathDensity data.

PathDensity (:py:class:`pyretis.visualization.orderparam_density.PathDensity`)
    A class for reading, storing, and compiling simulation data.

PathVisualize
    (:py:class:`pyretis.visualization.orderparam_density.PathVisualize`)
    A class for loading data (compiled or not), and generating plots.

VisualApp (:py:class:`pyretis.visualization.visualize.VisualApp`)
    A QtWidget class that holds an user-defined figure.

VisualObject
    (:py:class:`pyretis.visualization.visualize.VisualObject`)
    A class that loads from pickle, holds and, supplies VisualApp with data for
    plotting.


Important methods defined in this package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

_grid_it_up (:py:func:`pyretis.visualization.plotting._grid_it_up`)
    Maps the x,y and z data to a numpy.meshgrid using scipy interpolation
    at a user defined resolution.

diff_matching(:py:func:`pyretis.visualization.common.diff_matching`)
    A function to get the indeces where to similar lists differ.

gen_surface(:py:func:`pyretis.visualization.plotting.gen_surface`)
    A function that generates a user-defined `surface` plot (2D/3D).

_grid_it_up(:py:func:`pyretis.visualization.plotting._grid_it_up`)
    A function that generates a [X,Y] numpy.meshgrid and [Z] grid-data
    for a given resolution.

plot_int_plane(:py:func:`pyretis.visualization.plotting.plot_int_plane`)
    A function that generates planes of the simulation interfaces for
    3D plots.

plot_regline(:py:func:`pyretis.visualization.plotting.plot_regline`)
    A function that generates a linear regression line of x and y data on
    a given matplotlib.axes object.

shift_data(:py:func:`pyretis.visualization.common.shift_data`)
    A function that shifts data values of a list by the median value.

try_data_shift(:py:func:`pyretis.visualization.common.try_data_shift`)
    A function that attempts a shift of the data values to increase linear
    correlation.
"""
from .common import (diff_matching, try_data_shift, shift_data)
from .orderparam_density import (PathDensity, PathVisualize)
from .plotting import (plot_regline,
                       _grid_it_up,
                       plot_int_plane,
                       gen_surface)
# Check if PyQt5 is installed
try:
    HAS_PYQT5 = True
    import PyQt5
    from . import resources_rc
    from .visualize import VisualApp
except ImportError:
    HAS_PYQT5 = False
