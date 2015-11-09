# -*- coding: utf-8 -*-
"""Methods for generating plots using matplotlib.

This module defines a class for using matplotlib and it also defines
some standard plots that are used in the analysis.

Important classes and functions
-------------------------------

- MplPlotter: A class for plotting with matplotlib.

- mpl_set_style: A method for setting the style for the plots, typically
  used here to load the _pyretis style_.
"""
import numpy as np
import os
import warnings
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.collections import LineCollection
# import styles for newer matplotlibs:
if matplotlib.__version__ < '1.4.0':
    HAS_STYLE = False
    warnings.warn('Using Matplotlib version < 1.4.0, please upgrade it!')
else:
    try:
        import matplotlib.style
        HAS_STYLE = True
    except ImportError:
        HAS_STYLE = False
# pylint: disable=E0611
from scipy.stats import gamma
# pylint: enable=E0611
from pyretis.inout.common import (create_backup, _ENERFILES, _ENERTITLE,
                                  _FLUXFILES, _ORDERFILES, _PATHFILES,
                                  _PATH_MATCH)


__all__ = ['MplPlotter']


# Define default style file:
_MPL_STYLE_FILE = os.sep.join([os.path.dirname(__file__), 'styles',
                               'pyretis.mplstyle'])


class MplPlotter(object):
    """
    Class MplPlotter(object).

    This class defines a plotter. A plotter is just a object
    that supports certain functions which conveniently can be called in
    different analysis output function. The Mplplotter will use matplotlib
    and can be used to create other plotters based on other tools, for
    instance gnuplot or Veusz, visvis or your favourite plotting tool.

    Attributes
    ----------
    style : string
        Defines what style to use for the plotting.
    out_fmt : string
        Selects format for output plots.
    """

    def __init__(self, out_fmt, style=None):
        """
        To initiate the plotting object. Here we only define the style.

        Parameters
        ----------
        style : string, optional
            This selects the style to use, it can be a file path or the
            string with the style name.
        """
        self.style = style
        mpl_set_style(self.style)
        fig = Figure()
        canvas = FigureCanvas(fig)
        supported = canvas.get_supported_filetypes()
        del fig
        del canvas
        if out_fmt not in supported:
            msg = ['Output format "{}" is not supported.'.format(out_fmt),
                   'Please try:']
            for key in supported:
                msg.append(key)
            raise ValueError(' '.join(msg))
        else:
            self.out_fmt = out_fmt

    def plot_flux(self, results):
        """Function to call ``mpl_plot_flux``."""
        return mpl_plot_flux(results, self.out_fmt)

    def plot_energy(self, results, energies, sim_settings=None):
        """Function to call ``mpl_plot_energy``."""
        return mpl_plot_energy(results, energies, self.out_fmt,
                               sim_settings=sim_settings)

    def plot_orderp(self, results, orderdata):
        """Function to just call ``mpl_plot_orderp``."""
        return mpl_plot_orderp(results, orderdata, self.out_fmt)

    def plot_path(self, path_ensemble, results, idetect):
        """Function to just ``call mpl_plot_path``."""
        return mpl_plot_path(path_ensemble, results, idetect, self.out_fmt)

    def plot_total_probability(self, path_ensembles, detect, matched):
        """Function to just call ``mpl_plot_matched``."""
        return mpl_plot_matched(path_ensembles, detect, matched, self.out_fmt)


def _mpl_read_style_file(filename):
    """
    Read style files for old versions of matplotlib.

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
                    warnings.warn(msg.format(key))


def mpl_set_style(style='pyretis'):
    """
    Set the plotting style for matplotlib.

    This will set up the plotting according to some given style.
    Styles can be given as string, for instance 'ggplot', 'bmh',
    'grayscale' (i.e. one of the styles in matplotlib.style.available) or
    as a file (full path is needed). The default pyretis style
    is stored in _MPL_STYLE_FILE and can be selected with 'pyretis'.
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
        msg = 'Cannot use styles, will load from file'
        warnings.warn(msg)
        _mpl_read_style_file(style)
    else:
        if style in matplotlib.style.available:
            matplotlib.style.use(style)
        else:  # assume this is just a file
            rcpar = matplotlib.rc_params_from_file(style)
            matplotlib.rcParams.update(rcpar)


def mpl_savefig(canvas, outputfile):
    """
    Function to save matplotlib figures.

    It will save figures so that old ones are not overwritten.

    Parameters
    ----------
    canvas : object like `FigureCanvas` from `matplotlib.backends.backend_agg`
        This is the figure to be written to the file by
        using canvas.print_figure().
    outputfile : string
        This is the name of the output file to create.
    """
    msg = create_backup(outputfile)
    if msg:
        warnings.warn(msg)
    canvas.print_figure(outputfile)


def mpl_plot_in_chunks(axs, series, chunksize=20000):
    """
    Plot a series in chunks using matplotlib.

    When plotting 'large' datasets, matplotlib might give an
    'OverflowError: Allocated too many blocks' error.
    Here we avoid this error by plotting the data in chunks. We could
    also downsample the data, but this is perhaps something best left
    to the user.

    Parameters
    ----------
    axs : Axes object from matplotlib
        Where to do the plotting
    series : dict
        Represents the data to be plotted.
    chunksize : int
        This is the maximim size we will try to plot in one go.
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
    """
    Do the actual plotting in chunks for x-vs-y data.

    Parameters
    ----------
    axs : Axes object from matplotlib
        Where to do the plotting.
    series : dict
        Represents the data to be plotted.
    low : int, optional
        Lower index to start plotting. `low` can be negative.
    high : int, optional
        Index where to end the plotting, this index is not plotted. `high`
        is assumed to always be > 0 or None.
    color : string, optional
        A string representing the color to use.

    Returns
    -------
        handle : object of type matplotlib.lines.Line2D
            A handle forthe plotted line.
    """
    # pick out just a few keys - we want to limit what we change here:
    kwargs = {'linestyle': series.get('ls', '-'),
              'alpha': series.get('alpha', 1.0),
              'linewidth': series.get('lw', 2.0)}
    if color is not None:
        kwargs['color'] = color

    handle, = axs.plot(series['x'][low:high], series['y'][low:high],
                       **kwargs)
    return handle


def mpl_simple_plot(series, outputfile, fig_settings=None):
    """
    Plot simple time series data (i.e. x vs y data).

    Parameters
    ----------
    series : list of dicts
        `series[i]` is the dict which contain the data to be plotted.
    outputfile : string
        This is the name of the output file to create.
    fig_settings : dict
        This dict contains settings for the figure, keys are:
        xlabel : string, the label to use for the x-axis.
        ylabel : string, the label to use for the y-axis.
        title : string, title to use for the figure.
        yscale : string, to change the scale for the y-axis.
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
        axs.set_title(fig_settings['title'], fontsize='x-small', loc='left')
    if len(labels) == len(handles) and len(labels) >= 1:
        axs.legend(handles, labels, prop={'size': 'x-small'})
    if 'yscale' in fig_settings:
        axs.set_yscale(fig_settings['yscale'])
    mpl_savefig(canvas, outputfile)


def mpl_linecollection_gradient(axs, series):
    """
    Plot a line with a color gradient along the line.

    Parameters
    ----------
    axs : Axes object from matplotlib
        Where to do the plotting.
    series : dict
        Represents the data to be plotted.

    Returns
    -------
    handle : object of type matplotlib.collections.LineCollection
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
    """
    Plot a line gradient in chunks.

    Here we will plot lines with length equal to chunksize and color
    that line-chunk with one color. This method will be used when
    chunksize << length of the data to plot so that
    each chunksize will have approximately the same color.

    Paremters
    ---------
    axs : Axes object from matplotlib
        Where to do the plotting.
    series : dict
        Represents the data to be plotted.

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


def mpl_line_gradient(series, outputfile, fig_settings):
    """
    Plot time series and color the line with a color gradient.

    This method will plot time series data and color the lines with
    a gradient according to 'time'

    Parameters
    ----------
    series : list of dicts
        `series[i]` is the dict which contain the data to be plotted.
    outputfile : string
        This is the name of the output file to create.
    fig_settings : dict
        This dict contains settings for the figure, keys are:
        xlabel : string, the label to use for the x-axis.
        ylabel : string, the label to use for the y-axis.
        title : string, title to use for the figure.
        yscale : string, to change the scale for the y-axis.

    Notes
    -----
    This method is based on the matplotlib example from:
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
        axs.set_title(fig_settings['title'], fontsize='x-small', loc='left')
    if len(labels) == len(handles) and len(labels) >= 1:
        axs.legend(handles, labels, prop={'size': 'x-small'})
    mpl_savefig(canvas, outputfile)


def mpl_error_plot(series, outputfile, xlabel='Time', ylabel='Value',
                   title=None):
    """
    Plot series with error values.

    The error values will be displayed as a filled region.

    Parameters
    ----------
    series : list of tuples
        `series[i]` is the tuple which will be plotted. It is assumed
        to be on the form (x-values, y-values, y-error, legend).
    outputfile : string
        This is the name of the output file to create.
    xlabel : string, optional
        The label to use for the x-axis.
    ylabel : string, optional
        The label to use for the y-axis.
    title : string, optional
        Title to use for the plot.
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
    if xlabel is not None:
        axs.set_xlabel(xlabel)
    if ylabel is not None:
        axs.set_ylabel(ylabel)
    if title is not None:
        axs.set_title(title, fontsize='x-small', loc='left')
    if len(labels) == len(handles) and len(labels) >= 1:
        axs.legend(handles, labels, prop={'size': 'x-small'})
    mpl_savefig(canvas, outputfile)


def mpl_block_error(error, title, outputfile):
    """
    Plot results from a block error analysis.

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
    fig = Figure()
    canvas = FigureCanvas(fig)
    axs = fig.add_subplot(111)
    axs.axhline(y=error[4], alpha=0.8, ls='--')
    axs.plot(error[0], error[3])
    axs.set_xlabel('Block length')
    axs.set_ylabel('Estimated error')
    titl = '{0}: Rel.err: {1:9.6e} Ncor: {2:9.6f}'
    titl = titl.format(title, error[4], error[6])
    axs.set_title(titl, fontsize='x-small', loc='left')
    mpl_savefig(canvas, outputfile)


def _mpl_shoots_histogram(histograms, scale, ensemble, outputfile,
                          outputfile_scale):
    """
    Plot the histograms from the shoots analysis.

    Parameters
    ----------
    histograms : list
        These are the histograms obtained in the shoots analysis.
    scale : dict
        These are the scale factors for normalizing the histograms
        obtained in the shoots analysis.
    ensemble : string
        This is the ensemble identifier, e.g. 001, 002, etc.
    outputfile : string
        This is the name of the output file to create. This will be
        the unscaled plot.
    outputfile_scale : string
        This is the name of the output file to create. This will be
        the scaled plot.
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
    mpl_simple_plot(series,
                    outputfile,
                    fig_settings={'title': 'Ensemble: {0}'.format(ensemble)})
    mpl_simple_plot(series_scale,
                    outputfile_scale,
                    fig_settings={'title': 'Ensemble: {0}'.format(ensemble)})


def mpl_plot_path(path_ensemble, results, idetect, out_fmt):
    """
    Plot all figures from the path analysis.

    Parameters
    ----------
    path_ensemble : object like `PathEnsemble` from `pyretis.core.path`
        This is the path ensemble we have analysed.
    results : dict
        This dict contains the result from the analysis.
    idetect : float
        This is the interface used for the detection in the analysis.
    out_fmt : string
        This is the desired output format for the plots.

    Returns
    -------
    out : dict
        This dictionary contains the filenames of the figures that
        we wrote.
    """
    ens = path_ensemble.ensemble  # identify the ensemble
    outfiles = {}
    for key in _PATHFILES:
        outfiles[key] = _PATHFILES[key].format(ens, out_fmt)
    # first plot pcross vs lambda with the idetect surface
    series = [{'type': 'xy', 'x': results['pcross'][0],
               'y': results['pcross'][1]}]
    series.append({'type': 'vline', 'x': idetect, 'ls': '--',
                   'alpha': 0.8})
    mpl_simple_plot(series,
                    outfiles['pcross'],
                    fig_settings={'xlabel': r'Order parameter ($\lambda$)',
                                  'ylabel': 'Probability',
                                  'title': 'Ensemble: {0}'.format(ens)})
    # next plot running pcross:
    series = [{'type': 'xy', 'x': results['cycle'],
               'y': results['prun']}]
    series.append({'type': 'hline', 'y': results['prun'][-1],
                   'ls': '--', 'alpha': 0.8})
    mpl_simple_plot(series,
                    outfiles['prun'],
                    fig_settings={'xlabel': 'Cycle number',
                                  'ylabel': 'Probability (running avg.)',
                                  'title': 'Ensemble: {0}'.format(ens)})
    # plot results of block-error analysis:
    mpl_block_error(results['blockerror'], 'Ensemble: {0}'.format(ens),
                    outfiles['perror'])
    # plot length-histogram:
    hist1 = results['pathlength'][0]
    hist2 = results['pathlength'][1]
    labfmt = r'{0}: {1:6.2f} $\pm$  {2:6.2f}'
    lab1 = labfmt.format('Accepted', hist1[2][0], hist1[2][1])
    lab2 = labfmt.format('All', hist2[2][0], hist2[2][1])
    series = [{'type': 'xy', 'x': hist1[1], 'y': hist1[0],
               'label': lab1}]
    series.append({'type': 'xy', 'x': hist2[1], 'y': hist2[0],
                   'label': lab2})
    mpl_simple_plot(series,
                    outfiles['pathlength'],
                    fig_settings={'xlabel': 'No. of MD steps',
                                  'ylabel': 'Frequency',
                                  'title': 'Ensemble: {0}'.format(ens)})
    _mpl_shoots_histogram(results['shoots'][0], results['shoots'][1], ens,
                          outfiles['shoots'], outfiles['shoots-scaled'])
    return outfiles


def mpl_plot_orderp(results, orderdata, out_fmt):
    """
    Plot the output from the order parameter analysis using matplotlib.

    Parameters
    ----------
    results : dict
        Each item in `results` contains the results for the corresponding
        order parameter.
    orderdata : list of numpy.arrays
        This is the raw-data for the order parameter analysis
    out_fmt : string
        This is the desired output format for the plots.

    Returns
    -------
    outfiles : dict
        The output files created by this method.

    Note
    ----
    We are here only outputting results for the first order parameter.
    I.e. other order parameters or velocities are not written here. This
    will be changed when the structure of the output order parameter file
    has been fixed. Also note that, if present, the first order parameter
    will be plotted agains the second one - i.e. the second one will be
    assumed to represent the velocity here.
    """
    outfiles = {}
    for key in _ORDERFILES:
        outfiles[key] = _ORDERFILES[key].format(out_fmt)

    time = orderdata[0]
    series = [{'type': 'xy', 'x': time, 'y': orderdata[1]}]
    mpl_simple_plot(series, outfiles['order'],
                    fig_settings={'xlabel': 'Time',
                                  'ylabel': 'Order parameter'})
    # make running average plot of the energies as function of time
    series = [{'type': 'xy', 'x': time, 'y': results[0]['running'],
               'label': 'Running average'}]
    mpl_simple_plot(series, outfiles['run_order'],
                    fig_settings={'xlabel': 'Time',
                                  'ylabel': 'Order parameter'})

    # plot block-error results:
    mpl_block_error(results[0]['blockerror'], 'Order parameter',
                    outfiles['block'])
    # plot distributions
    dist = results[0]['distribution']
    series = [{'type': 'xy', 'x': dist[1], 'y': dist[0]}]
    title = '{0}. Average: {1:9.6e}, std: {2:9.6f}'
    title = title.format('Order parameter', dist[2][0], dist[2][1])
    mpl_simple_plot(series, outfiles['dist'],
                    fig_settings={'title': title})
    # also try a orderp vs ordervel plot:
    if len(orderdata) >= 3:
        series = [{'type': 'xyc', 'x': orderdata[1], 'y': orderdata[2]}]
        fig_settings = {'xlabel': r'$\lambda$',
                        'ylabel': r'$\dot{\lambda}$',
                        'title': 'Order parameter vs velocity'}
        mpl_line_gradient(series, outfiles['ordervel'],
                          fig_settings=fig_settings)
    # output msd if it was calculated:
    if 'msd' in results[0]:
        msd = results[0]['msd']
        series = [(np.arange(len(msd)), msd[:, 0], msd[:, 1])]
        mpl_error_plot(series, outfiles['msd'], xlabel='Time',
                       ylabel='MSD', title=None)
    return outfiles


def mpl_plot_energy(results, energies, out_fmt, sim_settings=None):
    """
    Plot the output from the energy analysis using matplotlib.

    Parameters
    ----------
    results : dict
        Each item in `results` contains the results for the corresponding
        energy. It is assumed to contains the keys 'vpot', 'ekin', 'etot',
        'ham', 'temp', 'elec'
    energies : dict of numpy.arrays
        This is the raw-data for the energy analysis
    out_fmt : string
        This is the desired output format for the plots.
    sim_settings : dict, optional
        This is the simulation settings which are usefull for creating
        theoretical plots of distributions. It is assumed to contain
        the number of particles, the dimensionality

    Returns
    -------
    outfiles : dict
        The output files created by this method.
    """
    outfiles = {'energies': _ENERFILES['energies'].format(out_fmt),
                'run_energies': _ENERFILES['run_energies'].format(out_fmt),
                'temperature': _ENERFILES['temperature'].format(out_fmt),
                'run_temp': _ENERFILES['run_temp'].format(out_fmt)}
    time = energies['time']
    # make time series plot of the energies
    series = []
    for key in ['vpot', 'ekin', 'etot', 'ham']:
        if key not in energies:
            continue
        series.append({'type': 'xy', 'x': time, 'y': energies[key],
                       'label': _ENERTITLE[key]})
    mpl_simple_plot(series, outfiles['energies'],
                    fig_settings={'xlabel': 'Time', 'ylabel': 'Energy'})
    # make running average plot of the energies as function of time
    series = []
    for key in ['vpot', 'ekin', 'etot', 'ham']:
        if key not in results:
            continue
        series.append({'type': 'xy', 'x': time,
                       'y': results[key]['running'],
                       'label': _ENERTITLE[key]})
    mpl_simple_plot(series, outfiles['run_energies'],
                    fig_settings={'xlabel': 'Time', 'ylabel': 'Energy'})
    # plot temperature
    series = [{'type': 'xy', 'x': time, 'y': energies['temp']}]
    mpl_simple_plot(series, outfiles['temperature'],
                    fig_settings={'xlabel': 'Time',
                                  'ylabel': 'Temperature'})
    # and running average for temperature
    series = [{'type': 'xy', 'x': time, 'y': results['temp']['running']}]
    mpl_simple_plot(series, outfiles['run_temp'],
                    fig_settings={'xlabel': 'Time',
                                  'ylabel': 'Temperature',
                                  'title': 'Running average'})
    # plot block-error results:
    outfile = _ENERFILES['block'].format('{}', out_fmt)
    for key in ['vpot', 'ekin', 'etot', 'temp']:
        if key not in results:
            continue
        outfiles['{}block'.format(key)] = outfile.format(key)
        mpl_block_error(results[key]['blockerror'], _ENERTITLE[key],
                        outfiles['{}block'.format(key)])
    # plot distributions
    outfile = _ENERFILES['dist'].format('{}', out_fmt)
    for key in ['vpot', 'ekin', 'etot', 'temp']:
        if key not in results:
            continue
        dist = results[key]['distribution']
        series = [{'type': 'xy', 'x': dist[1], 'y': dist[0],
                   'label': _ENERTITLE[key]}]
        title = '{0}. Average: {1:9.6e}, std: {2:9.6f}'
        title = title.format(_ENERTITLE[key], dist[2][0], dist[2][1])
        if sim_settings is not None and key in ['ekin', 'temp']:
            pos = np.linspace(min(0.0, dist[1].min()),
                              dist[1].max(), 1000)
            alp = (0.5 * sim_settings['npart'] *
                   sim_settings['dim'])
            if key == 'ekin':
                scale = 1.0 / sim_settings['beta']
            elif key == 'temp':
                scale = sim_settings['temperature'] / alp
            series.append({'type': 'xy', 'x': pos,
                           'y': gamma.pdf(pos, alp, loc=0, scale=scale),
                           'label': 'Boltzmann distribution'})
        outfiles['{}dist'.format(key)] = outfile.format(key)
        mpl_simple_plot(series, outfiles['{}dist'.format(key)],
                        fig_settings={'title': title})
    return outfiles


def mpl_plot_flux(results, out_fmt):
    """
    Plot the output from the flux analysis using matplotlib.

    Parameters
    ----------
    results : dict
        This is the dict with the results from the flux analysis.
    out_fmt : string
        This is the desired output format for the plots.

    Returns
    -------
    outfiles : dict
        The output files created by this method.
    """
    outfiles = {}
    for key in _FLUXFILES:
        outfiles[key] = []
    # make running average plot and error plot:
    for i in range(len(results['flux'])):
        flux = results['flux'][i]
        runflux = results['runflux'][i]
        errflux = results['errflux'][i]
        outfile = _FLUXFILES['runflux'].format(i + 1, out_fmt)
        outfiles['runflux'].append(outfile)
        series = [{'type': 'xy', 'x': flux[:, 0], 'y': runflux,
                   'label': 'Running average'}]
        title = 'Flux for interface no. {}'.format(i + 1)
        mpl_simple_plot(series, outfile,
                        fig_settings={'xlabel': 'Time',
                                      'ylabel': 'Flux / internal units',
                                      'title': title})
        outfile = _FLUXFILES['block'].format(i + 1, out_fmt)
        outfiles['block'].append(outfile)
        mpl_block_error(errflux, 'Flux interface no. {}'.format(i + 1),
                        outfile)
    return outfiles


def mpl_plot_matched(path_ensembles, detect, matched, out_fmt):
    """
    Plot matched probabilities using matplotlib.

    This method will plot the overall matched probabilities for the
    different ensembles and a plot with just the over-all matched
    probability.

    Parameters
    ----------
    path_ensembles : list of PathEnsemble objects
        This is the path ensembles we have analysed.
    detect : list of floats
        These are the detect interfaces used in the analysis.
    matched : dict
        This dict contains the results from the matching of the probabilities.
        `matched['overall-prob']` and `matched['matched-prob']` are used here.
    outputfile : string
        This is the name of the output file to create.
    out_fmt : string
        This is the desired output format for the plots.

    Returns
    -------
    outfiles : dict
        The output files created by this method.
    """
    outfiles = {}
    for key in _PATH_MATCH:
        outfiles[key] = _PATH_MATCH[key].format(out_fmt)

    # first plot the matched probabilities for each ensemble:
    series = []
    for idetect in detect:
        series.append({'type': 'vline', 'x': idetect,
                       'ls': '--', 'alpha': 0.8})
    for prob, path_e in zip(matched['matched-prob'], path_ensembles):
        series.append({'type': 'xy',
                       'x': prob[:, 0],
                       'y': prob[:, 1],
                       'lw': 3, 'label': path_e.ensemble})
    mpl_simple_plot(series, outfiles['total'],
                    fig_settings={'xlabel': r'Order parameter ($\lambda$)',
                                  'ylabel': 'Probability',
                                  'title': 'Matched probabilities',
                                  'yscale': 'log'})
    # also make a plot with the overall matched probability:
    series = []
    for idetect in detect:
        series.append({'type': 'vline', 'x': idetect,
                       'ls': '--', 'alpha': 0.8})
    series.append({'type': 'xy',
                   'x': matched['overall-prob'][:, 0],
                   'y': matched['overall-prob'][:, 1],
                   'lw': 3})
    fig_setts = {'xlabel': r'Order parameter ($\lambda$)',
                 'ylabel': 'Probability',
                 'title': 'Matched probability',
                 'yscale': 'log'}
    mpl_simple_plot(series, outfiles['match'],
                    fig_settings=fig_setts)
    return outfiles
