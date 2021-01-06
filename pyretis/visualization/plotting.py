# -*- coding: utf-8 -*-
# Copyright (c) 2021, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""This file contains common functions for the visualization.

It contains some functions that are used to plot regression lines
and interface planes, and generate surface plots.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

gen_surface (:py:func:`.gen_surface`)
    Generates a user-defined surface/contour/etc plot with colorbar in
    given matplotlib.figure and -.axes objects.

plot_int_plane(:py:func:`.plot_regline`)
    Generates interface planes for the current span of x-values, in a
    given matplotlib.axes-object.

plot_regline (:py:func:`.plot_regline`)
    Calculates the linear regression and correlation, plots a line for the
    regression in the given matplotlib.axes-object, with info in legend.

_grid_it_up (:py:func:`._grid_it_up`)
    Maps the x,y and z data to a numpy.meshgrid using scipy interpolation
    at a user defined resolution.
"""
# pylint: disable=C0103
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from scipy.interpolate import griddata as scgriddata
from scipy.stats import linregress as linreg


def plot_regline(ax, x, y):
    """Plot a regression line calculated from input data in the input subplot.

    Parameters
    ----------
    x, y : list
        Floats, coordinates of data regression lines
        are calculated from.
    ax : Matplotlib subplot, where reg.line is to be plotted.

    Returns/Updates
    ---------------
    Regression line with values.

    """
    xplot = np.linspace(min(x), max(x), 2)
    slope, intercept, r_value, _, _ = linreg(x, y)
    rtxt = 'y={0:.2f}x + {1:.2f}, $r^2$={2:.3f}'
    rline = ax.plot(xplot, slope*xplot + intercept, '-', c='black',
                    label=rtxt.format(slope, intercept, r_value**2))
    return rline


def plot_int_plane(ax, pos, ymin, ymax, zmin, zmax, visible=False):
    """Generate the interface planes for 3D visualization.

    Parameters
    ----------
    ax : The matplotlib.axes object where the planes will be plotted.
    pos : float
        The x-axis position of the interface plane.
    ymin, ymax, zmin, zmax : float
        The limits of the plane in the 3D canvas.
    visible : boolean, optional
        If True, shows interface planes.

    Returns
    -------
    plane : A 3D surface at x=pos, perpendicular to the x-axis.

    """
    yy, zz = np.linspace(ymin, ymax, 2), np.linspace(zmin, zmax, 2)
    yy, zz = np.meshgrid(yy, zz)
    point = np.array([pos, 0.0, 0.0])
    normal = np.array([1.0, 0.0, 0.0])
    d = -point.dot(normal)
    x = (-normal[2]*yy - normal[1]*zz - d) * 1./normal[0]
    plane = ax.plot_surface(x, yy, zz, color='grey',
                            alpha=0.30, visible=visible)
    return plane


def gen_surface(x, y, z, fig, ax, cbar_ax=None, dim=3, method='contour',
                res_x=400, res_y=400, colormap='viridis'):
    """Generate the chosen surface/contour/scatter plot.

    Parameters
    ----------
    x, y, z : list
        Coordinates of data points. (x,y) the chosen orderP pairs, and
        z is the chosen energy value of the two combinations.
    fig : Matplotlib object
        main canvas.
    ax : Matplotlib object
        axes of the plot.
    cbar_ax : Matplotlib object, optional
        plot colorbar.
    method : string, optional
        Method used for plotting data, default is contour lines.
    res_x, res_y : integer, optional
        Resolution of plot, either as N*N bins in 2D histogram
        (Density plot) or as gridpoints for interpolation of data
        (Surface and contour plots).
    colormap : string, optional
        Name of the colormap/color scheme to use when plotting.

    Returns
    -------
    surf : Matplotlib object
         The chosen surface/contour/plot object.
    cbar : Matplotlib object
         The chosen colorbar.

    """
    xmin, xmax = min(x), max(x)
    ymin, ymax = min(y), max(y)
    zmin, zmax = min(z), max(z)

    CMAP = plt.get_cmap(colormap)

    if not zmin == zmax:
        colors = [CMAP((z[i]-zmin)/(zmax-zmin)) for i in range(len(z))]
    else:
        colors = [CMAP(z[i]) for i in range(len(z))]

    # When scatter plots, use resolution to make size for dots.
    if method == 'scatter':
        scat_size = res_x / 100.0

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    if dim == 3:
        # 3d plot settings
        ax.set_zlim3d(zmin, zmax)
        ax.zaxis.set_ticklabels([])

    # Methods for plotting in 3D
    if method == 'scatter':
        if dim == 3:
            surf = ax.scatter(x, y, z, c=colors, s=scat_size, cmap=CMAP)
        else:
            surf = ax.scatter(x, y, c=colors, s=scat_size, cmap=CMAP)

        norm = mpl.colors.Normalize(vmin=zmin, vmax=zmax)
        cbar = fig.colorbar(
            mpl.cm.ScalarMappable(norm=norm, cmap=CMAP),
            cax=cbar_ax)
        return surf, cbar

    X, Y, Z = _grid_it_up(x, y, z, res_x=res_x, res_y=res_y)
    if method == 'surface':
        surf = ax.plot_surface(X, Y, Z, cmap=CMAP, vmin=zmin, vmax=zmax,
                               facecolor=colors, shade=True,
                               antialiased=False)
    elif method == 'contour':
        surf = ax.contour(X, Y, Z, cmap=CMAP)
    elif method == 'contourf':
        surf = ax.contourf(X, Y, Z, cmap=CMAP)
    cbar = fig.colorbar(surf, cax=cbar_ax)

    return surf, cbar


def _grid_it_up(x, y, z, res_x=200, res_y=200, fill='max'):
    """Map x, y and z data values to a numpy meshgrid by interpolation.

    Parameters
    ----------
    x, y, z : list
        Lists of data values.
    res_x, res_y : integer, optional
        Resolution (number of points in a axis range).
    fill : string, optional
        Criteria to color the un-explored regions.

    Returns
    -------
    X, Y, Z : list
        Numpy.arrays of mapped data.

    """
    # Convert 3 columns of data to grid for matplotlib"""
    xi = np.linspace(min(x), max(x), res_x)
    yi = np.linspace(min(y), max(y), res_y)
    X, Y = np.meshgrid(xi, yi)

    # Scipy griddata """ # Works
    if fill == 'max':
        fill_value = max(z)
    elif fill == 'min':
        fill_value = min(z)
    Z = scgriddata((x, y), np.array(z), (X, Y),
                   method='linear', fill_value=fill_value)
    # other options: 'linear'/'cubic'/'nearest'

    return X, Y, Z
