# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""Functions for generating plots using matplotlib.

This module defines a class for using matplotlib and it also defines
some standard plots that are used in the analysis.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

MplPlotter
    A class for plotting with matplotlib.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

mpl_set_style
    Method for setting the style for the plots, typically used here to
    load the *pyretis style*.
"""
# TODO: See if the plotting functions mpl_* can be moved into the object.
import os
import logging
import numpy as np
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.collections import LineCollection
# pyretis imports
from pyretis.inout.plotting.plotting import Plotter
from pyretis.inout.common import create_backup, name_file
from pyretis.inout.common import (ENERFILES, ENERTITLE, FLUXFILES,
                                  ORDERFILES, PATHFILES, PATH_MATCH)


logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())
# import styles for newer matplotlibs:
_STYLEFILE = 'pyretis.mplstyle'
if matplotlib.__version__ < '1.5.0':
    _STYLEFILE = 'pyretis-old.mplstyle'
if matplotlib.__version__ < '1.4.0':
    HAS_STYLE = False
    logger.warning('Using Matplotlib version < 1.4.0, please upgrade.')
else:
    try:
        import matplotlib.style
        HAS_STYLE = True
    except ImportError:
        HAS_STYLE = False


__all__ = ['MplPlotter']


# Define default style file:
_MPL_STYLE_FILE = os.sep.join([os.path.dirname(__file__), 'styles',
                               _STYLEFILE])
_TITLE_SETTINGS = {'loc': 'right'}


class MplPlotter(Plotter):
    """Class MplPlotter(Plotter).

    This class defines a plotter. A plotter is just a object that
    supports certain functions which conveniently can be called in
    different analysis output function. The `MplPlotter` will use
    matplotlib and it can be used to create other plotters based
    on other tools, for instance gnuplot or Veusz, visvis or your
    favorite plotting tool.

    Attributes
    ----------
    style : string
        Defines what style to use for the plotting.
    out_fmt : string
        Selects format for output plots.
    """

    def __init__(self, out_fmt, backup=False, style=None, out_dir=None):
        """Initiate the plotting object.

        Here we only define the style and check if the requested file
        format is something that we actually can handle.

        Parameters
        ----------
        out_fmt : string
            This is the format to use for the images.
        style : string, optional
            This selects the style to use, it can be a file path or the
            string with the style name.
        backup : boolean, optional
            Determines if we should overwrite or backup old files.
        out_dir : string, optional
            Determines if we should write the files to a particular
            directory.
        """
        super(MplPlotter, self).__init__(backup=backup,
                                         plotter_type='matplotlib',
                                         out_dir=out_dir)
        self.style = style
        mpl_set_style(self.style)
        # Check if the requested file format is something we can do:
        fig = Figure()
        canvas = FigureCanvas(fig)
        supported = canvas.get_supported_filetypes()
        if out_fmt not in supported:
            msg = ['Output format "{}" is not supported.'.format(out_fmt),
                   'Please try:']
            for key in supported:
                msg.append(key)
            raise ValueError(' '.join(msg))
        else:
            self.out_fmt = out_fmt
        del fig
        del canvas

    def _print_figures_to_file(self, canvas):
        """Function to save figures as files.

        This function will save figures to files. It will append a file
        format extension to the files when writing.

        Parameters
        ----------
        canvas : dict of objects like `FigureCanvas` from `matplotlib`.
            `canvas[key]` is assumed to define a figure which we will
            save to a file with a file name defined by `key` and the
            extension defined by `self.out_fmt`.

        Returns
        -------
        out : dict
            The files written.
        """
        outputfiles = {}
        for key in canvas:
            local_file = name_file(key, self.out_fmt, path=None)
            full_path = name_file(key, self.out_fmt, self.out_dir)
            outputfiles[key] = local_file
            mpl_savefig(canvas[key], full_path, self.backup)
        return outputfiles

    def plot_flux(self, results):
        """Function to plot flux results using `mpl_plot_flux`.

        The parameters for this method is described in `mpl_plot_flux`.

        Returns
        -------
        outputfile : list of dicts
            A list containing the files created for the flux and for
            the error in the flux.

        Note
        ----
        We return a list here. This is because we want to plot these
        figures in pairs.
        """
        canvas_run, canvas_err = mpl_plot_flux(results)
        # Restructure output files for reporting
        outputfiles = []
        for run, err in zip(canvas_run, canvas_err):
            local_run = name_file(run['name'], self.out_fmt, path=None)
            local_err = name_file(err['name'], self.out_fmt, path=None)
            full_run = name_file(run['name'], self.out_fmt, path=self.out_dir)
            full_err = name_file(err['name'], self.out_fmt, path=self.out_dir)
            mpl_savefig(run['canvas'], full_run, self.backup)
            mpl_savefig(err['canvas'], full_err, self.backup)
            outputfiles.append({'runflux': local_run,
                                'errflux': local_err})
        return outputfiles

    def plot_energy(self, results, energies):
        """Function to plot energy results using `mpl_plot_energy`.

        The parameters for this method is described in
        `mpl_plot_energy`.

        Returns
        -------
        out : dict
            This dict contains the files created by the plotting.
        """
        canvas = mpl_plot_energy(results, energies)
        return self._print_figures_to_file(canvas)

    def plot_orderp(self, results, orderdata):
        """Function to plot order parameter using `mpl_plot_orderp`.

        The parameters for this method is described in
        `mpl_plot_orderp`.

        Returns
        -------
        out : dict
            This dict contains the files created by the plotting.
        """
        canvas = mpl_plot_orderp(results, orderdata)
        return self._print_figures_to_file(canvas)

    def plot_path(self, path_ensemble, results, idetect):
        """Function to plot path results using `mpl_plot_path`.

        The parameters for this method is described in `mpl_plot_path`.

        Returns
        -------
        out : dict
            This dict contains the files created by the plotting.
        """
        canvas = mpl_plot_path(path_ensemble, results, idetect)
        return self._print_figures_to_file(canvas)

    def plot_total_probability(self, path_ensembles, detect, matched):
        """Function to plot matched probabilities with `mpl_plot_matched`

        The parameters for this method is described in
        `mpl_plot_matched`.

        Returns
        -------
        out : dict
            This dict contains the files created by the plotting.
        """
        canvas = mpl_plot_matched(path_ensembles, detect, matched)
        return self._print_figures_to_file(canvas)


def _mpl_read_style_file(filename):
    """Read style files for old versions of matplotlib.

    This function is just intended for old versions of matplotlib
    where we have to read parameters and set them ourselves.

    Parameters
    ----------
    filename : string
        This is the matplotlib rc file to open.

    Returns
    -------
    out : None
        Returns `None` but modifies `matplotlib.rcParams`.
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
                    matplotlib.rcParams[key] = value
                except KeyError:
                    msg = 'Unknown setting "{}". Please update matplotlib'
                    msg = msg.format(key)
                    logger.warning(msg)


def mpl_set_style(style='pyretis'):
    """Set the plotting style for matplotlib.

    This will set up the plotting according to some given style.
    Styles can be given as string, for instance 'ggplot', 'bmh',
    'grayscale' (i.e. one of the styles in `matplotlib.style.available`)
    or as a file (full path is needed). The default pyretis style
    is stored in `_MPL_STYLE_FILE` and can be selected with 'pyretis'.
    Style equal to None is just the default matplotlib style.

    Parameters
    ----------
    style : string, optional
        This selects the style to use, it can be a file path or the
        string with the style name.
    """
    if style is None:
        return
    if style == 'pyretis':
        style = _MPL_STYLE_FILE
    if not HAS_STYLE:  # default to loading from file
        msg = ('Your matplotlib installation cannot use styles!',
               'Will try to load style from file: "{}"'.format(style),
               'Please consider updating matplotlib.')
        msgtxt = '\n'.join(msg)
        logger.warning(msgtxt)
        _mpl_read_style_file(style)
    else:
        if style in matplotlib.style.available:
            msgtxt = 'Loading matplotlib style: {}'.format(style)
            logger.info(msgtxt)
            matplotlib.style.use(style)
        else:  # assume this is just a file
            msgtxt = 'Loading matplitlib style from file: {}'.format(style)
            logger.info(msgtxt)
            rcpar = matplotlib.rc_params_from_file(style)
            # TODO: For mpl version 1.5: use_default_template=False can be
            # added to matplotlib.rc_params_from_file().
            matplotlib.rcParams.update(rcpar)


def mpl_savefig(canvas, outputfile, backup=False):
    """Function to save matplotlib figures.

    It will save figures so that old ones are not overwritten.

    Parameters
    ----------
    canvas : object like `FigureCanvas` from `matplotlib.backends.backend_agg`
        This is the figure to be written to the file by
        using `canvas.print_figure()`.
    outputfile : string
        This is the name of the output file to create.
    backup : boolean
        This determines if we should try to back-up old versions of the
        figures.
    """
    if backup:
        msg = create_backup(outputfile)
        if msg:
            logger.warning(msg)
    canvas.print_figure(outputfile)


def mpl_plot_in_chunks(axs, series, chunksize=20000):
    """Plot a series in chunks using matplotlib.

    When plotting 'large' datasets, matplotlib might give an
    'OverflowError: Allocated too many blocks' error.
    Here we avoid this error by plotting the data in chunks. We could
    also down sample the data, but this is perhaps something best left
    to the user.

    Parameters
    ----------
    axs : Axes object from matplotlib
        Where to do the plotting
    series : dict
        Represents the data to be plotted.
    chunksize : int
        This is the maximum size we will try to plot in one go.
    """
    color = None
    line = None
    leny = len(series['y'])
    if leny > chunksize:
        nchunk, rest = divmod(leny, chunksize)
        for i in range(nchunk):
            low = i * chunksize
            high = low + chunksize
            line = _mpl_plot_xy_chunk(axs, series, low=low, high=high,
                                      color=color)
            color = line.get_color()
        if rest > 0:
            line = _mpl_plot_xy_chunk(axs, series, low=-(rest+1), high=None,
                                      color=color)
    else:
        line = _mpl_plot_xy_chunk(axs, series)
    return line


def _mpl_plot_xy_chunk(axs, series, low=0, high=None, color=None):
    """Do the actual plotting in chunks for ``x`` vs ``y`` data.

    Parameters
    ----------
    axs : Axes object from matplotlib
        Where to do the plotting.
    series : dict
        Represents the data to be plotted.
    low : int, optional
        Lower index to start plotting. `low` can be negative.
    high : int, optional
        Index where to end the plotting, this index is not plotted.
        `high` is assumed to always be > 0 or None.
    color : string, optional
        A string representing the color to use.

    Returns
    -------
    handle : object like `matplotlib.lines.Line2D`.
        A handle for the plotted line.
    """
    # pick out just a few keys - we want to limit what we change here:
    kwargs = {'linestyle': series.get('ls', '-'),
              'alpha': series.get('alpha', 1.0),
              'linewidth': series.get('lw', 2.0)}
    if color is not None:
        kwargs['color'] = color
    else:
        try:  # try to set color if it's specified
            kwargs['color'] = series['color']
        except KeyError:
            pass

    handle, = axs.plot(series['x'][low:high], series['y'][low:high],
                       **kwargs)
    return handle


def mpl_simple_plot(series, fig_settings=None):
    """Plot simple time series data (i.e. ``x`` vs ``y`` data).

    Parameters
    ----------
    series : list of dicts
        `series[i]` is the dict which contain the data to be plotted.
    fig_settings : dict
        This dict contains settings for the figure, keys are:

        * `xlabel`: string, the label to use for the x-axis.
        * `ylabel`: string, the label to use for the y-axis.
        * `title`: string, title to use for the figure.
        * `yscale`: string, to change the scale for the y-axis.

    Returns
    -------
    out : object like `FigureCanvas` from `matplotlib.backends.backend_agg`.
        This is the figure we create here.
    """
    fig = Figure()
    canvas = FigureCanvas(fig)
    axs = fig.add_subplot(111)
    handles = []
    labels = []
    for seri in series:
        handle = None
        if seri['type'] == 'xy':
            handle = mpl_plot_in_chunks(axs, seri)
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
        axs.set_title(fig_settings['title'], **_TITLE_SETTINGS)
    if len(labels) == len(handles) and len(labels) >= 1:
        ncol, rest = divmod(len(labels), 10)
        if rest > 0:
            ncol += 1
        axs.legend(handles, labels, ncol=ncol)
    if 'yscale' in fig_settings:
        axs.set_yscale(fig_settings['yscale'])
    return canvas


def mpl_linecollection_gradient(axs, series):
    """Plot a line with a color gradient along the line.

    The line is split into segments and each segment is colored
    according to it's "location" along the line. By "location" we here
    mean the order of the segments.

    Parameters
    ----------
    axs : Axes object from matplotlib
        Where to do the plotting.
    series : dict
        Represents the data to be plotted.

    Returns
    -------
    handle : object of like `matplotlib.collections.LineCollection`.
        A handle for the plotted line.
    """
    # pick out just a few keys - we want to limit what we change here:
    kwargs = {'linestyle': series.get('ls', '-'),
              'alpha': series.get('alpha', 1.0),
              'linewidth': series.get('lw', 2.0)}
    points = np.array([series['x'], series['y']]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    values = np.linspace(0, 1, len(series['x']))
    linec = LineCollection(segments, array=values,
                           norm=matplotlib.colors.Normalize(vmin=0, vmax=1),
                           **kwargs)
    handle = axs.add_collection(linec)
    return handle


def mpl_chunks_gradient(axs, series, chunksize=20000):
    """Plot a line gradient in chunks.

    Here we will plot a line in chunks and color each chunk with one
    color. This function can be used as an alternative to
    `mpl_linecollection_gradient` when the number of points to plot is
    very large. Typically the chunk size here will be small compared to
    the size of the data to be plotted, so that each chunk, if plotted
    with `mpl_linecollection_gradient`, would have approximately the
    same color anyway.

    Parameters
    ---------
    axs : Axes object from matplotlib
        Where to do the plotting.
    series : dict
        Represents the data to be plotted.
    chunksize : int
        This is the maximum size (number of points) we will try to plot
        in one go.

    Returns
    -------
    handle : object of type matplotlib.lines.Line2D
        A handle for the plotted line.

    Note
    ----
    Color maps in matplotlib will typically have 256 colors. The number
    of different colors we can get is currently limited to 256.
    """
    kwargs = {'linestyle': series.get('ls', '-'),
              'alpha': series.get('alpha', 1.0),
              'linewidth': series.get('lw', 2.0)}
    line = None
    lenx = len(series['x'])
    nchunk, rest = divmod(lenx, chunksize)
    cnorm = matplotlib.colors.Normalize(vmin=0, vmax=nchunk+1)
    color_map = matplotlib.cm.ScalarMappable(norm=cnorm)
    for i in range(nchunk):
        low = i * chunksize
        high = low + chunksize
        line, = axs.plot(series['x'][low:high], series['y'][low:high],
                         **kwargs)
        line.set_color(color_map.to_rgba(i))
    if rest > 0:
        last = rest + 1
        line, = axs.plot(series['x'][-last:], series['y'][-last:],
                         **kwargs)
        line.set_color(color_map.to_rgba(nchunk))
    return line


def mpl_line_gradient(series, fig_settings):
    """Plot time series and color the line with a color gradient.

    This function will plot time series data and color the lines with
    a gradient according to 'time'

    Parameters
    ----------
    series : list of dicts
        `series[i]` is the dict which contain the data to be plotted.
    fig_settings : dict
        This dict contains settings for the figure, keys are:

        * `xlabel`: string, the label to use for the x-axis.
        * `ylabel`: string, the label to use for the y-axis.
        * `title`: string, title to use for the figure.
        * `yscale`: string, to change the scale for the y-axis.

    Returns
    -------
    out : object like `FigureCanvas` from `matplotlib.backends.backend_agg`.
        This is the figure we create here.

    Notes
    -----
    This function is based on the matplotlib example from:
    http://matplotlib.org/examples/pylab_examples/multicolored_line.html
    """
    fig = Figure()
    canvas = FigureCanvas(fig)
    axs = fig.add_subplot(111)
    handles = []
    labels = []
    for seri in series:
        lenx = len(seri['x'])
        if lenx >= 10**6:  # plot in chunks
            handle = mpl_chunks_gradient(axs, seri)
        else:  # just plot it all
            handle = mpl_linecollection_gradient(axs, seri)
        legend = seri.get('label', None)
        if legend is not None and handle is not None:
            handles.append(handle)
            labels.append(legend)
    axs.autoscale_view()
    if 'xlabel' in fig_settings:
        axs.set_xlabel(fig_settings['xlabel'])
    if 'ylabel' in fig_settings:
        axs.set_ylabel(fig_settings['ylabel'])
    if 'title' in fig_settings:
        axs.set_title(fig_settings['title'], **_TITLE_SETTINGS)
    if len(labels) == len(handles) and len(labels) >= 1:
        axs.legend(handles, labels)
    return canvas


def mpl_error_plot(series, fig_settings):
    """Plot series with error values.

    This will plot a series with error values displayed as a filled
    region.

    Parameters
    ----------
    series : list of tuples
        `series[i]` is the tuple which will be plotted. It is assumed
        to be on the form (x-values, y-values, y-error, legend).
    fig_settings : dict
        This dict contains settings for the figure, keys are:

        * `xlabel`: string, the label to use for the x-axis.
        * `ylabel`: string, the label to use for the y-axis.
        * `title`: string, title to use for the figure.

    Returns
    -------
    out : object like `FigureCanvas` from `matplotlib.backends.backend_agg`.
        This is the figure we create here.
    """
    fig = Figure()
    canvas = FigureCanvas(fig)
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
    if 'xlabel' in fig_settings:
        axs.set_xlabel(fig_settings['xlabel'])
    if 'ylabel' in fig_settings:
        axs.set_ylabel(fig_settings['ylabel'])
    if 'title' in fig_settings:
        axs.set_title(fig_settings['title'], **_TITLE_SETTINGS)
    if len(labels) == len(handles) and len(labels) >= 1:
        axs.legend(handles, labels)
    return canvas


def _mpl_shoots_histogram(histograms, scale, ensemble):
    """Plot the histograms from the shoots analysis.

    Parameters
    ----------
    histograms : list
        These are the histograms obtained in the shoots analysis.
    scale : dict
        These are the scale factors for normalizing the histograms
        obtained in the shoots analysis.
    ensemble : string
        This is the ensemble identifier, e.g. 001, 002, etc.

    Returns
    -------
    out[0] : object like `FigureCanvas` from `matplotlib`.
        This is the unscaled histogram.
    out[1] : object like `FigureCanvas` from `matplotlib`.
        This is the scaled histogram.
    """
    series = []
    series_scale = []
    for key in ['ACC', 'REJ', 'BWI', 'ALL']:
        try:
            mid = histograms[key][2]
            hist = histograms[key][0]
            series.append({'type': 'xy', 'x': mid, 'y': hist,
                           'label': '{}'.format(key), 'alpha': 0.8})
            series_scale.append({'type': 'xy', 'x': mid, 'y': hist*scale[key],
                                 'label': '{}'.format(key), 'alpha': 0.8})
        except KeyError:
            continue
    title = r'Ensemble ${0}$'.format(ensemble)
    canvas = mpl_simple_plot(series, fig_settings={'title': title})
    canvas_scale = mpl_simple_plot(series_scale, fig_settings={'title': title})
    return canvas, canvas_scale


def mpl_plot_path(path_ensemble, results, idetect):
    """Plot all figures from the path analysis.

    Parameters
    ----------
    path_ensemble : object like `PathEnsemble` from `pyretis.core.path`
        This is the path ensemble we have analyzed.
    results : dict
        This dict contains the result from the analysis.
    idetect : float
        This is the interface used for the detection in the analysis.

    Returns
    -------
    canvas : dict
        This dictionary contains the different canvases we have
        created
    """
    ens = path_ensemble.ensemble_name
    ens_simplified = path_ensemble.ensemble_name_simple
    canvas = {}
    out = {}
    for key in PATHFILES:
        out[key] = PATHFILES[key].format(ens_simplified)
    if 'pcross' in results:
        # First plot `pcross` vs `lambda` with the `idetect` surface:
        series = [{'type': 'xy', 'x': results['pcross'][0],
                   'y': results['pcross'][1]}]
        series.append({'type': 'vline', 'x': idetect, 'ls': '--',
                       'alpha': 0.8})
        figset = {'xlabel': r'Order parameter ($\lambda$)',
                  'ylabel': 'Probability',
                  'title': r'Ensemble ${0}$'.format(ens)}
        canvas[out['pcross']] = mpl_simple_plot(series, fig_settings=figset)
    if 'prun' in results:
        # Next plot running ` pcross`:
        series = [{'type': 'xy', 'x': results['cycle'],
                   'y': results['prun']}]
        series.append({'type': 'hline', 'y': results['prun'][-1],
                       'ls': '--', 'alpha': 0.8})
        figset = {'xlabel': 'Cycle number',
                  'ylabel': 'Probability (running avg.)',
                  'title': r'Ensemble ${0}$'.format(ens)}
        canvas[out['prun']] = mpl_simple_plot(series, fig_settings=figset)
    if 'blockerror' in results:
        # Plot results of block-error analysis:
        series = [{'type': 'xy', 'x': results['blockerror'][0],
                   'y': results['blockerror'][3]}]
        series.append({'type': 'hline', 'y': results['blockerror'][4],
                       'ls': '--', 'alpha': 0.8})
        title = r'Ensemble ${0}$: Rel. err.: {1:9.6e}, Ncor: {2:9.6f}'
        figset = {'xlabel': 'Block length', 'ylabel': 'Estimated error',
                  'title': title.format(ens, results['blockerror'][4],
                                        results['blockerror'][6])}
        canvas[out['perror']] = mpl_simple_plot(series, fig_settings=figset)
    if 'lengtherror' in results:
        # Plot results of length-error analysis:
        series = [{'type': 'xy', 'x': results['lengtherror'][0],
                   'y': results['lengtherror'][3]}]
        series.append({'type': 'hline', 'y': results['lengtherror'][4],
                       'ls': '--', 'alpha': 0.8})
        title = r'Ensemble ${0}$: Rel. err.: {1:9.6e}, Ncor: {2:9.6f}'
        figset = {'xlabel': 'Block length', 'ylabel': 'Estimated error',
                  'title': title.format(ens, results['lengtherror'][4],
                                        results['lengtherror'][6])}
        canvas[out['lengtherror']] = mpl_simple_plot(series, fig_settings=figset)

    # Plot length-histogram:
    labfmt = r'{0}: {1:6.2f} $\pm$  {2:6.2f}'
    series = [{'type': 'xy', 'x': results['pathlength'][0][1],
               'y': results['pathlength'][0][0],
               'label': labfmt.format('Accepted',
                                      results['pathlength'][0][2][0],
                                      results['pathlength'][0][2][1])}]
    series.append({'type': 'xy', 'x': results['pathlength'][1][1],
                   'y': results['pathlength'][1][0],
                   'label': labfmt.format('All',
                                          results['pathlength'][1][2][0],
                                          results['pathlength'][1][2][1])})
    figset = {'xlabel': 'No. of MD steps', 'ylabel': 'Frequency',
              'title': r'Ensemble ${0}$'.format(ens)}
    canvas[out['pathlength']] = mpl_simple_plot(series, fig_settings=figset)
    # Plot shoots-histogram
    can_tmp = _mpl_shoots_histogram(results['shoots'][0],
                                    results['shoots'][1], ens)
    canvas[out['shoots']] = can_tmp[0]
    canvas[out['shoots_scaled']] = can_tmp[1]
    return canvas


def mpl_plot_orderp(results, orderdata):
    """Plot the output from the order parameter analysis using matplotlib.

    Parameters
    ----------
    results : dict
        Each item in `results` contains the results for the
        corresponding order parameter.
    orderdata : list of numpy.arrays
        This is the raw-data for the order parameter analysis

    Returns
    -------
    canvas : dict
        The different plots created by this function.

    Note
    ----
    We are here only outputting results for the first order parameter.
    I.e. other order parameters or velocities are not written here. This
    will be changed when the structure of the output order parameter
    file has been fixed. Also note that, if present, the first order
    parameter will be plotted against the second one - i.e. the second
    one will be assumed to represent the velocity here.
    """
    canvas = {}
    time = orderdata[0]
    series = [{'type': 'xy', 'x': time, 'y': orderdata[1]}]
    figset = {'xlabel': 'Time', 'ylabel': 'Order parameter'}
    canvas[ORDERFILES['order']] = mpl_simple_plot(series, fig_settings=figset)
    # make running average plot of the energies as function of time
    series = [{'type': 'xy', 'x': time, 'y': results[0]['running'],
               'label': 'Running average'}]
    canvas[ORDERFILES['run_order']] = mpl_simple_plot(series,
                                                      fig_settings=figset)
    # plot block-error results:
    block = results[0]['blockerror']
    series = [{'type': 'xy', 'x': block[0], 'y': block[3]}]
    series.append({'type': 'hline', 'y': block[4],
                   'ls': '--', 'alpha': 0.8})
    title = 'Order parameter. Rel. err.: {0:9.6e}, Ncor: {1:9.6f}'
    figset = {'xlabel': 'Block length',
              'ylabel': 'Estimated error',
              'title': title.format(block[4], block[6])}
    canvas[ORDERFILES['block']] = mpl_simple_plot(series, fig_settings=figset)
    # plot distributions
    dist = results[0]['distribution']
    series = [{'type': 'xy', 'x': dist[1], 'y': dist[0]}]
    title = '{0}. Average: {1:9.6e}, std: {2:9.6f}'
    title = title.format('Order parameter', dist[2][0], dist[2][1])
    figset = {'title': title}
    canvas[ORDERFILES['dist']] = mpl_simple_plot(series,
                                                 fig_settings=figset)
    # also try a orderp vs ordervel plot:
    if len(orderdata) >= 3:
        series = [{'type': 'xyc', 'x': orderdata[1], 'y': orderdata[2]}]
        figset = {'xlabel': r'$\lambda$',
                  'ylabel': r'$\dot{\lambda}$',
                  'title': 'Order parameter vs velocity'}
        plot = ORDERFILES['ordervel']
        canvas[plot] = mpl_line_gradient(series, fig_settings=figset)
    # output msd if it was calculated:
    if 'msd' in results[0]:
        msd = results[0]['msd']
        series = [(np.arange(len(msd)), msd[:, 0], msd[:, 1])]
        figset = {'xlabel': 'Time', 'ylabel': 'MSD'}
        canvas[ORDERFILES['msd']] = mpl_error_plot(series,
                                                   fig_settings=figset)
    return canvas


def mpl_plot_energy(results, energies):
    r"""Plot the output from the energy analysis using matplotlib.

    Parameters
    ----------
    results : dict
        Each item in `results` contains the results for the
        corresponding energy. It is assumed to contains the keys
        'vpot', 'ekin', 'etot', 'ham', 'temp', 'elec'.
    energies : dict of numpy.arrays
        This is the raw-data for the energy analysis.

    Returns
    -------
    canvas : dict
        The output figures created by this function.
    """
    canvas = {}
    time = energies['time']
    # make time series plot of the energies
    series = []
    for key in ['vpot', 'ekin', 'etot', 'ham']:
        if key not in energies:
            continue
        series.append({'type': 'xy', 'x': time, 'y': energies[key],
                       'label': ENERTITLE[key]})
    figset = {'xlabel': 'Time', 'ylabel': 'Energy'}
    canvas[ENERFILES['energies']] = mpl_simple_plot(series,
                                                    fig_settings=figset)
    # make running average plot of the energies as function of time
    series = []
    for key in ['vpot', 'ekin', 'etot', 'ham']:
        if key not in results:
            continue
        series.append({'type': 'xy', 'x': time,
                       'y': results[key]['running'],
                       'label': ENERTITLE[key]})
    canvas[ENERFILES['run_energies']] = mpl_simple_plot(series,
                                                        fig_settings=figset)
    # plot temperature
    series = [{'type': 'xy', 'x': time, 'y': energies['temp']}]
    figset = {'xlabel': 'Time', 'ylabel': 'Temperature'}
    canvas[ENERFILES['temperature']] = mpl_simple_plot(series,
                                                       fig_settings=figset)
    # and running average for temperature
    series = [{'type': 'xy', 'x': time, 'y': results['temp']['running']}]
    figset = {'xlabel': 'Time',
              'ylabel': 'Temperature',
              'title': 'Running average'}
    canvas[ENERFILES['run_temp']] = mpl_simple_plot(series,
                                                    fig_settings=figset)
    # plot block-error results:
    title = r'{0}: Rel. err.: {1:9.6e}, Ncor: {2:9.6f}'
    for key in ['vpot', 'ekin', 'etot', 'temp']:
        if key not in results:
            continue
        plot = ENERFILES['block'].format(key)
        block = results[key]['blockerror']
        series = [{'type': 'xy', 'x': block[0], 'y': block[3]}]
        series.append({'type': 'hline', 'y': block[4],
                       'ls': '--', 'alpha': 0.8})
        figset = {'xlabel': 'Block length',
                  'ylabel': 'Estimated error',
                  'title': title.format(ENERTITLE[key], block[4], block[6])}
        canvas[plot] = mpl_simple_plot(series, fig_settings=figset)
    # plot distributions
    for key in ['vpot', 'ekin', 'etot', 'temp']:
        if key not in results:
            continue
        dist = results[key]['distribution']
        series = [{'type': 'xy', 'x': dist[1], 'y': dist[0],
                   'label': ENERTITLE[key]}]
        title = '{0}. Average: {1:9.6e}, std: {2:9.6f}'
        title = title.format(ENERTITLE[key], dist[2][0], dist[2][1])
        if 'boltzmann-dist' in results[key]:
            series.append({'type': 'xy',
                           'x': results[key]['boltzmann-dist'][1],
                           'y': results[key]['boltzmann-dist'][0],
                           'label': 'Boltzmann distribution'})
        plot = ENERFILES['dist'].format(key)
        canvas[plot] = mpl_simple_plot(series, fig_settings={'title': title})
    return canvas


def mpl_plot_flux(results):
    """Plot the output from the flux analysis using matplotlib.

    Parameters
    ----------
    results : dict
        This is the dict with the results from the flux analysis.

    Returns
    -------
    out[0] : list of dicts
        The output figures created by this function for running
        averages. `out[0][i]['name']` is the name of the figure and
        `out[0][i]['canvas']` is the corresponding canvas object.
    out[1] : list of dicts
        The output figures created by this function for block errors.
        `out[0][i]['name']` is the name of the figure and
        `out[0][i]['canvas']` is the corresponding canvas object.
    """
    canvas_run = []
    canvas_err = []
    for i in range(len(results['flux'])):
        # Plot running average:
        flux = results['flux'][i]
        runflux = results['runflux'][i]
        series = [{'type': 'xy', 'x': flux[:, 0], 'y': runflux,
                   'label': 'Running average'}]
        title = 'Flux for interface no. {}'.format(i + 1)
        figset = {'xlabel': 'Time',
                  'ylabel': 'Flux / internal units',
                  'title': title}
        canvas = mpl_simple_plot(series, fig_settings=figset)
        canvas_run.append({'name': FLUXFILES['runflux'].format(i + 1),
                           'canvas': canvas})
        # Plot error results:
        errflux = results['errflux'][i]
        title = r'Block error: {0}: Rel. err.: {1:9.6e}, Ncor: {2:9.6f}'
        series = [{'type': 'xy', 'x': errflux[0], 'y': errflux[3]},
                  {'type': 'hline', 'y': errflux[4], 'ls': '--',
                   'alpha': 0.8}]
        figset = {'xlabel': 'Block length',
                  'ylabel': 'Estimated error',
                  'title': title.format(i + 1, errflux[4], errflux[6])}
        canvas = mpl_simple_plot(series, fig_settings=figset)
        canvas_err.append({'name': FLUXFILES['block'].format(i + 1),
                           'canvas': canvas})
    return canvas_run, canvas_err


def mpl_plot_matched(path_ensembles, detect, matched):
    """Plot matched probabilities using matplotlib.

    This function will plot the matched probabilities for the different
    ensembles and also make a plot with just the over-all matched
    probability.

    Parameters
    ----------
    path_ensembles : list of strings.
        This is the name of the path ensembles we have calculated
        the probability for.
    detect : list of floats
        These are the detect interfaces used in the analysis.
    matched : dict
        This dict contains the results from the matching of the
        probabilities. `matched['overall-prob']` and
        `matched['matched-prob']` are used here.

    Returns
    -------
    canvas : dict
        The output figures created by this function.
    """
    canvas = {}
    # First plot the matched probabilities for each ensemble:
    series = []
    for idetect in detect:
        series.append({'type': 'vline', 'x': idetect,
                       'ls': '--', 'alpha': 0.8, 'lw': 1})

    # Matplotlib changed some rc params, this is to be compatible with more
    # versions:
    if 'axes.prop_cycle' in matplotlib.rcParams:
        ckey = 'axes.prop_cycle'
    else:
        ckey = 'axes.color_cycle'
    # Check if we need to have more colors:
    if len(matplotlib.rcParams[ckey]) < len(path_ensembles):
        logger.warning('Overriding color cycle')
        colors = matplotlib.cm.Set1(np.linspace(0, 1, len(path_ensembles)))
    else:
        colors = None

    new_series = {'type': 'xy',
                  'x': matched['overall-prob'][:, 0],
                  'y': matched['overall-prob'][:, 1],
                  'alpha': 0.8,
                  'lw': 9, 'label': 'Over-all', 'color': '#262626'}
    series.append(new_series)
    for i, (prob, path_e) in enumerate(zip(matched['matched-prob'],
                                           path_ensembles)):
        new_series = {'type': 'xy', 'x': prob[:, 0], 'y': prob[:, 1], 'lw': 3,
                      'label': '${}$'.format(path_e)}
        if colors is not None:
            new_series['color'] = colors[i]
        series.append(new_series)

    figset = {'xlabel': r'Order parameter ($\lambda$)',
              'ylabel': 'Probability',
              'title': 'Matched probabilities',
              'yscale': 'log'}
    canvas[PATH_MATCH['total']] = mpl_simple_plot(series,
                                                  fig_settings=figset)
    # Also make a plot with the overall matched probability:
    series = []
    for idetect in detect:
        series.append({'type': 'vline', 'x': idetect,
                       'ls': '--', 'alpha': 0.8, 'lw': 1})
    series.append({'type': 'xy',
                   'x': matched['overall-prob'][:, 0],
                   'y': matched['overall-prob'][:, 1],
                   'lw': 3})
    figset = {'xlabel': r'Order parameter ($\lambda$)',
              'ylabel': 'Probability',
              'title': 'Matched probability',
              'yscale': 'log'}
    canvas[PATH_MATCH['match']] = mpl_simple_plot(series,
                                                  fig_settings=figset)
    return canvas
