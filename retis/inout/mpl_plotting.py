# -*- coding: utf-8 -*-
"""
This file contains methods for generating plots using matplotlib.
It also defines some standard plots that are done in the analysis.
"""
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
# pylint: disable=E0611
from scipy.stats import gamma
# pylint: enable=E0611
import os
import warnings
from .common import (create_backup, _ENERFILES, _ENERTITLE, _FLUXFILES,
                     _ORDERFILES, _PATHFILES)


__all__ = ['MplPlotter']


# Define default style file:
_MPL_STYLE_FILE = os.sep.join([os.path.dirname(__file__), 'styles',
                               'pytismol.mplstyle'])


class MplPlotter(object):
    """
    Class MplPlotter(object)

    This class defines a plotter. A plotter is just a object
    that supports certain functions which conveniently can be called in
    different analysis output function. The Mplplotter will use matplotlib
    and can be used to create other plotters based on other tools, for
    instance gnuplot or Veusz, visvis or your favourite plotting tool.

    Attributes
    ----------

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
        _mpl_set_style(self.style)
        fig = plt.figure()
        supported = fig.canvas.get_supported_filetypes()
        plt.close(fig)
        if out_fmt not in supported:
            msg = ['Output format {} is not supported.'.format(out_fmt),
                   'Please try:']
            for key in supported:
                msg.append(key)
            raise ValueError(msg)
        else:
            self.out_fmt = out_fmt

    def plot_flux(self, results):
        """
        Plot the output from the flux analysis using matplotlib.

        Parameters
        ----------
        results : dict
            This is the dict with the results from the flux analysis.

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
            outfile = _FLUXFILES['runflux'].format(i + 1, self.out_fmt)
            outfiles['runflux'].append(outfile)
            series = [{'type': 'xy', 'x': flux[:, 0], 'y': runflux,
                       'label': 'Running average'}]
            title = 'Flux for interface no. {}'.format(i + 1)
            mpl_simple_plot(series, outfile,
                            fig_settings={'xlabel': 'Time',
                                          'ylabel': 'Flux / internal units',
                                          'title': title})
            outfile = _FLUXFILES['block'].format(i + 1, self.out_fmt)
            outfiles['block'].append(outfile)
            mpl_block_error(errflux, 'Flux interface no. {}'.format(i + 1),
                            outfile)
        return outfiles

    def plot_energy(self, results, energies, sim_settings=None):
        """
        Save the output from the energy analysis to text files.

        Parameters
        ----------
        results : dict
            Each item in `results` contains the results for the corresponding
            energy. It is assumed to contains the keys 'vpot', 'ekin', 'etot',
            'ham', 'temp', 'elec'
        energies : dict of numpy.arrays
            This is the raw-data for the energy analysis
        sim_settings : dict, optional
            This is the simulation settings which are usefull for creating
            theoretical plots of distributions. It is assumed to contain
            the number of particles, the dimensionality

        Returns
        -------
        outfiles : dict
            The output files created by this method.
        """
        out_fmt = self.out_fmt
        outfiles = {'energies': _ENERFILES['energies'].format(out_fmt),
                    'run_energies': _ENERFILES['run_energies'].format(out_fmt),
                    'temperature': _ENERFILES['temperature'].format(out_fmt),
                    'run_temp': _ENERFILES['run_temp'].format(out_fmt)}
        time = energies['time']
        # make time series plot of the energies
        series = []
        for key in ['vpot', 'ekin', 'etot', 'ham']:
            series.append({'type': 'xy', 'x': time, 'y': energies[key],
                           'label': _ENERTITLE[key]})
        mpl_simple_plot(series, outfiles['energies'],
                        fig_settings={'xlabel': 'Time', 'ylabel': 'Energy'})
        # make running average plot of the energies as function of time
        series = []
        for key in ['vpot', 'ekin', 'etot', 'ham']:
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
            outfiles['{}block'.format(key)] = outfile.format(key)
            mpl_block_error(results[key]['blockerror'], _ENERTITLE[key],
                            outfiles['{}block'.format(key)])
        # plot distributions
        outfile = _ENERFILES['dist'].format('{}', out_fmt)
        for key in ['vpot', 'ekin', 'etot', 'temp']:
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
                    scale = sim_settings['temp'] / alp
                series.append({'type': 'xy', 'x': pos,
                               'y': gamma.pdf(pos, alp, loc=0, scale=scale),
                               'label': 'Boltzmann distribution'})
            outfiles['{}dist'.format(key)] = outfile.format(key)
            mpl_simple_plot(series, outfiles['{}dist'.format(key)],
                            fig_settings={'title': title})
        return outfiles

    def plot_orderp(self, results, orderdata):
        """
        Plot the output from the order parameter analysis using matplotlib.

        Parameters
        ----------
        results : dict
            Each item in `results` contains the results for the corresponding
            order parameter.
        orderdata : dict of numpy.arrays
            This is the raw-data for the order parameter analysis

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
            outfiles[key] = _ORDERFILES[key].format(self.out_fmt)

        time = orderdata['data'][0]
        series = [{'type': 'xy', 'x': time, 'y': orderdata['data'][1]}]
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
        if len(orderdata['data']) >= 3:
            series = [(orderdata['data'][1], orderdata['data'][2])]
            mpl_line_gradient(series, outfiles['ordervel'],
                              xlabel=r'$\lambda$', ylabel=r'$\dot{\lambda}$',
                              title='Order parameter vs velocity')
        # output msd if it was calculated:
        if 'msd' in results[0]:
            msd = results[0]['msd']
            series = [(np.arange(len(msd)), msd[:, 0], msd[:, 1])]
            mpl_error_plot(series, outfiles['msd'], xlabel='Time',
                           ylabel='MSD', title=None)
        return outfiles

    def plot_path(self, path_ensemble, results, idetect):
        """
        This method will output all the figures from the results obtained
        by the path analysis.

        Parameters
        ----------
        path_ensemble : object of type PathEnsemble
            This is the path ensemble we have analysed.
        results : dict
            This dict contains the result from the analysis.
        idetect : float
            This is the interface used for the detection in the analysis.

        Returns
        -------
        out : dict
            This dictionary contains the filenames of the figures that
            we wrote.
        """
        ens = path_ensemble.ensemble  # identify the ensemble
        outfiles = {}
        for key in _PATHFILES:
            outfiles[key] = _PATHFILES[key].format(ens, self.out_fmt)
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
        series = [{'type': 'xy', 'y': results['prun']}]
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
                        fig_settings={'xlabel': 'MD steps',
                                      'ylabel': 'Frequency',
                                      'title': 'Ensemble: {0}'.format(ens)})
        _mpl_shoots_histogram(results['shoots'][0], results['shoots'][1], ens,
                              outfiles['shoots'], outfiles['shoots-scaled'])
        return outfiles

    @staticmethod
    def plot_total_probability(path_ensembles, detect, results, matched,
                               outputfile):
        """
        This method will plot the overall matched probabilities for the
        different ensembles.

        Parameters
        ----------
        path_ensembles : list of PathEnsemble objects
            This is the path ensembles we have analysed.
        results : list of dicts
            This dict contains the results from the analysis.
        detect : list of floats
            These are the detect interfaces used in the analysis.
        matched : list of numpy.arrays
            These are the matched/scaled probabilities
        outputfile : string
            This is the name of the output file to create.
        """
        series = []
        for idetect in detect:
            series.append({'type': 'vline', 'x': idetect,
                           'ls': '--', 'alpha': 0.8})
        for result, prob, path_e in zip(results, matched, path_ensembles):
            series.append({'type': 'xy', 'x': result['pcross'][0], 'y': prob,
                           'lw': 3, 'label': path_e.ensemble})
        mpl_simple_plot(series, outputfile,
                        fig_settings={'xlabel': r'Order parameter ($\lambda$)',
                                      'ylabel': 'Probability',
                                      'title': 'Matched probabilities',
                                      'yscale': 'log'})

    @staticmethod
    def plot_total_matched_probability(detect, matched, outputfile):
        """
        This method will plot the overall matched probability only.

        Parameters
        ----------
        detect : list of floats
            These are the detect interfaces used in the analysis.
        matched : numpy.array
            The matched probability.
        outputfile : string
            This is the name of the output file to create.
        """
        series = []
        for idetect in detect:
            series.append({'type': 'vline', 'x': idetect,
                           'ls': '--', 'alpha': 0.8})
        series.append({'type': 'xy', 'x': matched[:, 0],
                       'y': matched[:, 1], 'lw': 3})
        fig_setts = {'xlabel': r'Order parameter ($\lambda$)',
                     'ylabel': 'Probability',
                     'title': 'Matched probability',
                     'yscale': 'log'}
        mpl_simple_plot(series, outputfile,
                        fig_settings=fig_setts)


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


def _mpl_set_style(style='pytismol'):
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


def _mpl_shoots_histogram(histograms, scale, ensemble, outputfile,
                          outputfile_scale):
    """
    This method will plot the histograms from the shoots analysis.

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
