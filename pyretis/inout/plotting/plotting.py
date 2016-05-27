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
    that supports certain functions which conveniently can be called in
    different analysis output function. This plotter does not implement
    any functions, it's just here to make sure that the derived plotters
    implement these functions.

    Attributes
    ----------
    backup : boolean
        Determines if we overwrite old files or try yo back them up.
    plotter_type : string
        Defines a name for the plotter, in case we want to identify it.
    """

    def __init__(self, backup=True, plotter_type=None):
        """Initiate the plotting object.

        Parameters
        ----------
        backup : boolean
            Determines if we overwrite old files or not.
        plotter_type : string
            A name for the plotter.
        """
        self.plotter_type = plotter_type
        self.backup = backup in (True, 'yes', 'True')

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
