# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""Definition of the base class for the plotter.

This module just defines a base class for plotters. This is just to
ensure that all plotters at least implements some functions and that we
can make use of them.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Plotter
    A generic class for creating plots.
"""

__all__ = ['Plotter']


class Plotter(object):
    """Class Plotter(object).

    This class defines a plotter. A plotter is just a object
    that supports certain functions which can be called by analysis
    output functions. It should define certain plots and the
    ``Plotter`` class is an abstract class just to make sure that
    all plotters define the needed plots.

    Attributes
    ----------
    backup : boolean
        Determines if we overwrite old files or try to back them up.
    plotter_type : string
        Defines a name for the plotter, in case we want to identify it.
    out_dir : string, optional
        Defines an output directory for the plotter.
    """

    def __init__(self, backup=True, plotter_type=None, out_dir=None):
        """Initiate the plotting object.

        Parameters
        ----------
        backup : boolean, optional
            Determines if we overwrite old files or not.
        plotter_type : string, optional
            A name for the plotter.
        out_dir : string, optional
            A string which can be used to set an output directory
            for the plotter.
        """
        self.plotter_type = plotter_type
        self.backup = backup in (True, 'yes', 'True')
        self.out_dir = out_dir

    def plot_flux(self, results):
        """Function that plots flux results."""
        raise NotImplementedError()

    def plot_energy(self, results, energies):
        """Function that plots energy results."""
        raise NotImplementedError()

    def plot_orderp(self, results, orderdata):
        """Function that plots order parameter results."""
        raise NotImplementedError()

    def plot_path(self, path_ensemble, results, idetect):
        """Function that plots path ensemble results."""
        raise NotImplementedError()

    def plot_total_probability(self, path_ensembles, detect, matched):
        """Function that plots the overall probability for path ensembles."""
        raise NotImplementedError()

    def __str__(self):
        """Just print out the basic info."""
        return 'Plotter: {}'.format(self.plotter_type)
