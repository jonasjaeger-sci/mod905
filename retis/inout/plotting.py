# -*- coding: utf-8 -*-
"""
This file contains methods for creating plots.
Specifically it defines colors, colorschemes, the reading of styles
and some common plotting functions.

References
----------
.. [1] The colorblind_10 color scheme,
       https://jiffyclub.github.io/palettable/tableau/
.. [2] The deep color scheme, from the seaborn project
       http://stanford.edu/~mwaskom/software/seaborn/index.html
.. [3] The husl color scheme,
       http://www.husl-colors.org/
"""
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import os
import warnings
from .common import create_backup

__all__ = ['mpl_set_style']


# Custom named colors:
_COLORS = {'almost_black': '#262626'}
# Custom color-schemes. The default will be defined by the style file.
# The husl schemes are suited when many different colors are needed. They
# are hard-coded with different number of colors.
_COLOR_SCHEME = {'colorblind_10': ['#006BA4', '#FF800E', '#ABABAB', '#595959',
                                   '#5F9ED1', '#C85200', '#898989', '#A2C8EC',
                                   '#FFBC79', '#CFCFCF'],
                 'deep': ['#4C72B0', '#55A868', '#C44E52', '#8172B2',
                          '#CCB974', '#64B5CD'],
                 'husl_10': ['#f67088', '#db8831', '#ad9c31', '#77aa31',
                             '#33b07a', '#35aca4', '#38a8c5', '#6e9af4',
                             '#cc79f4', '#f565cc'],
                 'husl_15': ['#f67088', '#f37932', '#ca9131', '#ad9c31',
                             '#8ea531', '#4fb031', '#33b07a', '#34ad99',
                             '#36abae', '#38a8c5', '#3ba3ec', '#9491f4',
                             '#cc79f4', '#f45fe3', '#f569b7'],
                 'husl_20': ['#f67088', '#f7754f', '#db8831', '#c29431',
                             '#ad9c31', '#96a331', '#77aa31', '#31b23e',
                             '#33b07a', '#34ae92', '#35aca4', '#36abb3',
                             '#38a8c5', '#3aa5de', '#6e9af4', '#a38cf4',
                             '#cc79f4', '#f45bf1', '#f565cc', '#f66bad']}


# Define default style file:
_MPL_STYLE_FILE = os.sep.join([os.path.dirname(__file__), 'styles',
                               'pytismol.mplstyle'])


def _mpl_read_style_file(filename):
    """
    This function is just intended for old versions of matplotlib
    where we have to read parameters and set them ourselves.

    Parameters
    ----------
    filename : string
        This is the matplotlib rc file to open.

    Returns
    -------
    N/A but it modifies mpl.rcParams
    """
    with open(filename, 'r') as fileh:
        for lines in fileh:
            linesc = lines.strip().split('#')[0]
            loc = linesc.find(':')
            if loc != -1:
                key = linesc[:loc].strip()
                value = linesc[loc+1:].strip()
                if key.find('color') != -1:
                    value = '#{}'.format(value)
                try:
                    mpl.rcParams[key] = value
                except KeyError:
                    msg = 'Could not set {}. Please update matplotlib'
                    warnings.warn(msg.format(key))


def mpl_set_style(style='pytismol'):
    """
    This will set up the plotting according to some given style.
    Styles can be given as string, for instance 'ggplot', 'bmh',
    'grayscale' (i.e. one of the styles in plt.style.available) or
    as a file (full path is needed). The default pytismol style
    is stored in _MPL_STYLE_FILE and can be selected with 'pytismol'.
    Style equal to None is just the default matplotlib style.

    Parameters
    ----------
    style : string, optional
        This selects the style to use, it can be a file path or the
        string with the style name.
    """
    if style is None:
        return
    if style == 'pytismol':
        style = _MPL_STYLE_FILE
    if mpl.__version__ < '1.4.0':  # default to loading from file
        _mpl_read_style_file(style)
    else:
        if style in plt.style.available:
            plt.style.use(style)
        else:  # assume this is just a file
            rcpar = mpl.rc_params_from_file(style)
            mpl.rcParams.update(rcpar)


def mpl_savefig(fig, outputfile):
    """
    This is just a helper function to save matplotlib figures.
    It will save figures so that old ones are not overwritten.

    Parameters
    ----------
    fig : figure object from pyplot
        This is the figure to be written to the file.
        We simply use fig.savefig here.
    outputfile : string
        This is the name of the output file to create.

    Note
    ----
    If desirable pyplot/plt can be exchanged for FigureCanvans, i.e.:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    In this method, we then need to do have `mpl_savefig(canvas, outputfile)`
    and use canvas.print_figure(outputfile).
    In the plotting functions the figure is then created with a
    fig = Figure()
    canvas = FigureCanvas(fig)
    """
    msg = create_backup(outputfile)
    if msg:
        warnings.warn(msg)
    fig.savefig(outputfile)
    plt.close(fig)  # free up memory


def mpl_simple_plot(series, outputfile, fig_settings=None):
    """
    This method will plot time series data.

    Parameters
    ----------
    series : list of tuples
        `series[i]` is the tuple which will be plotted. It is assumed
        to be on the form (x-values, y-values, legend)
    outputfile : string
        This is the name of the output file to create.
    fig_settings : dict
        This dict contains settings for the figure, keys are:
        xlabel : string, the label to use for the x-axis.
        ylabel : string, the label to use for the y-axis.
        title : string, title to use for the figure.
        yscale : string, to change the scale for the y-axis.
    """
    fig = plt.figure()
    axs = fig.add_subplot(111)
    handles = []
    labels = []
    for seri in series:
        handle = None
        if seri['type'] == 'xy':
            if 'x' in seri:
                handle, = axs.plot(seri['x'], seri['y'],
                                   ls=seri.get('ls', '-'),
                                   alpha=seri.get('alpha', 1.0),
                                   lw=seri.get('lw', 2.0))
            else:
                handle, = axs.plot(seri['y'],
                                   ls=seri.get('ls', '-'),
                                   alpha=seri.get('alpha', 1.0),
                                   lw=seri.get('lw', 2.0))
        elif seri['type'] == 'vline':
            handle = axs.axvline(x=seri['x'], ls=seri.get('ls', '-'),
                                 alpha=seri.get('alpha', 1.0),
                                 lw=seri.get('lw', 2.0))
        elif seri['type'] == 'hline':
            handle = axs.axhline(y=seri['y'], ls=seri.get('ls', '-'),
                                 alpha=seri.get('alpha', 1.0),
                                 lw=seri.get('lw', 2.0))
        legend = seri.get('label', None)
        if legend is not None and handle is not None:
            handles.append(handle)
            labels.append(legend)
    if 'xlabel' in fig_settings:
        axs.set_xlabel(fig_settings['xlabel'])
    if 'ylabel' in fig_settings:
        axs.set_ylabel(fig_settings['ylabel'])
    if 'title' in fig_settings:
        axs.set_title(fig_settings['title'], fontsize='x-small', loc='left')
    if len(labels) == len(handles) and len(labels) >= 1:
        axs.legend(handles, labels, prop={'size': 'x-small'})
    if 'yscale' in fig_settings:
        axs.set_yscale(fig_settings['yscale'])
    mpl_savefig(fig, outputfile)


def mpl_line_gradient(series, outputfile, xlabel='Time', ylabel='Value',
                      title=None):
    """
    This method will plot time series data and color the lines with
    a gradient according to 'time'

    Parameters
    ----------
    series : list of tuples
        `series[i]` is the tuple which will be plotted. It is assumed
        to be on the form (x-values, y-values, legend)
    outputfile : string
        This is the name of the output file to create.
    xlabel : string, optional
        The label to use for the x-axis.
    ylabel : string, optional
        The label to use for the y-axis.
    title : string, optional
        Title to use for the plot.
    """
    fig = plt.figure()
    axs = fig.add_subplot(111)
    handles = []
    labels = []
    for seri in series:
        points = np.array([seri[0], seri[1]]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        linec = LineCollection(segments, array=np.linspace(0, 1, len(seri[0])),
                               norm=mpl.colors.Normalize(vmin=0, vmax=1))
        try:
            add_legend = seri[2] is not None
        except IndexError:
            add_legend = False
        handle = axs.add_collection(linec)
        if add_legend:
            handles.append(handle)
            labels.append(seri[2])
    axs.autoscale_view()
    if xlabel is not None:
        axs.set_xlabel(xlabel)
    if ylabel is not None:
        axs.set_ylabel(ylabel)
    if title is not None:
        axs.set_title(title, fontsize='x-small', loc='left')
    if len(labels) == len(handles) and len(labels) >= 1:
        axs.legend(handles, labels, prop={'size': 'x-small'})
    mpl_savefig(fig, outputfile)


def mpl_error_plot(series, outputfile, xlabel='Time', ylabel='Value',
                   title=None):
    """
    This method will plot time series data.

    Parameters
    ----------
    series : list of tuples
        `series[i]` is the tuple which will be plotted. It is assumed
        to be on the form (x-values, y-values, y-error, legend)
    outputfile : string
        This is the name of the output file to create.
    xlabel : string, optional
        The label to use for the x-axis.
    ylabel : string, optional
        The label to use for the y-axis.
    title : string, optional
        Title to use for the plot.
    """
    fig = plt.figure()
    axs = fig.add_subplot(111)
    handles = []
    labels = []
    for seri in series:
        try:
            add_legend = seri[3] is not None
        except IndexError:
            add_legend = False
        handle, = axs.plot(seri[0], seri[1])
        axs.fill_between(seri[0], seri[1] + seri[2],
                         seri[1] - seri[2],
                         facecolor=handle.get_color(), alpha=0.3)
        if add_legend:
            handles.append(handle)
            labels.append(seri[3])
    if xlabel is not None:
        axs.set_xlabel(xlabel)
    if ylabel is not None:
        axs.set_ylabel(ylabel)
    if title is not None:
        axs.set_title(title, fontsize='x-small', loc='left')
    if len(labels) == len(handles) and len(labels) >= 1:
        axs.legend(handles, labels, prop={'size': 'x-small'})
    mpl_savefig(fig, outputfile)


def mpl_block_error(error, title, outputfile):
    """
    This will plot the output from a error analysis; the error
    as a function of the block length.

    Parameters
    ----------
    error : list
        This list contains the result from the error analysis.
    title : string
        String to add to the title to the plot. In addition,
        the relative error and the correlation length will be written
        in the title.
    outputfile : string
        This is the name of the output file to create.
    """
    fig = plt.figure()
    axs = fig.add_subplot(111)
    axs.axhline(y=error[4], alpha=0.8, ls='--')
    axs.plot(error[0], error[3])
    axs.set_xlabel('Block length')
    axs.set_ylabel('Estimated error')
    titl = '{0}: Rel.err: {1:9.6e} Ncor: {2:9.6f}'
    titl = titl.format(title, error[4], error[6])
    axs.set_title(titl, fontsize='x-small', loc='left')
    mpl_savefig(fig, outputfile)
