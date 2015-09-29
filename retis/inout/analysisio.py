# -*- coding: utf-8 -*-
"""
This files contains methods that will output results from the
path analysis and the energy analysis. It currently supports matplotlib
graphics and a simple txt-table format (i.e. a space-separated format).
For the path analysis it can also be used to output over-all matched
results.
"""
from __future__ import absolute_import
import warnings
import numpy as np
import os
# pylint: disable=E0611
from scipy.stats import gamma
# pylint: enable=E0611
from .plotting import (mpl_error_plot, mpl_line_gradient,
                       mpl_simple_plot, mpl_block_error)
from .common import create_backup
from .txtinout import txt_save_columns, txt_block_error, txt_histogram

__all__ = ['mpl_path_output', 'txt_path_output',
           'mpl_total_probability', 'txt_total_probability',
           'mpl_total_matched_probability', 'txt_total_matched_probability',
           'mpl_energy_output', 'txt_energy_output',
           'mpl_orderp_output', 'txt_orderp_output',
           'mpl_flux_output', 'txt_flux_output']


# hard-coded patters for path analysis output files:
_PATHFILES = {'pcross': os.extsep.join(['{}_pcross', '{}']),
              'prun': os.extsep.join(['{}_prun', '{}']),
              'perror': os.extsep.join(['{}_perror', '{}']),
              'pathlength': os.extsep.join(['{}_lpath', '{}']),
              'shoots': os.extsep.join(['{}_shoots', '{}']),
              'shoots-scaled': os.extsep.join(['{}_shoots_scale', '{}'])}
# hard-coded patters for energy analysis output files:
_ENERFILES = {'energies': os.extsep.join(['energies', '{}']),
              'run_energies': os.extsep.join(['runenergies', '{}']),
              'temperature': os.extsep.join(['temperature', '{}']),
              'run_temp': os.extsep.join(['runtemperature', '{}']),
              'block': os.extsep.join(['{}block', '{}']),
              'dist': os.extsep.join(['{}dist', '{}'])}
# hard-coded information for the energy terms:
_ENERTITLE = {'vpot': 'Potential energy',
              'ekin': 'Kinetic energy',
              'etot': 'Total energy',
              'ham': 'Hamilt. energy',
              'temp': 'Temperature',
              'elec': 'Energy (externally computed)'}
# order files:
_ORDERFILES = {'order': os.extsep.join(['orderp', '{}']),
               'ordervel': os.extsep.join(['orderpv', '{}']),
               'run_order': os.extsep.join(['runorderp', '{}']),
               'dist': os.extsep.join(['orderdist', '{}']),
               'block': os.extsep.join(['ordererror', '{}']),
               'msd': os.extsep.join(['ordermsd', '{}'])}
# hard-coded patters for flux analysis output files:
_FLUXFILES = {'runflux': os.extsep.join(['runflux_{}', '{}']),
              'block': os.extsep.join(['errflux_{}', '{}'])}


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


def mpl_path_output(path_ensemble, results, idetect, out_format='png'):
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
    out_format : string, optional
        This is the desired format to use for the graphs. Supported are
        png, pdf, svg, etc. (see the matplotlib documentation).

    Returns
    -------
    out : dict
        This dictionary contains the filenames of the figures that
        we wrote.
    """
    ens = path_ensemble.ensemble  # identify the ensemble
    outfiles = {}
    for key in _PATHFILES:
        outfiles[key] = _PATHFILES[key].format(ens, out_format)
    # first plot pcross vs lambda with the idetect surface
    series = [{'type': 'xy', 'x': results['pcross'][0],
               'y': results['pcross'][1]}]
    series.append({'type': 'vline', 'x': idetect, 'ls': '--', 'alpha': 0.8})
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
                                  'ylabel': 'Probability (running average)',
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


def mpl_total_probability(path_ensembles, detect, results, matched,
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


def mpl_total_matched_probability(detect, matched, outputfile):
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
    mpl_simple_plot(series, outputfile,
                    fig_settings={'xlabel': r'Order parameter ($\lambda$)',
                                  'ylabel': 'Probability',
                                  'title': 'Matched probability',
                                  'yscale': 'log'})


def mpl_energy_output(results, energies, simulation_settings=None,
                      out_format='png'):
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
    simulation_settings : dict, optional
        This is the simulation settings which are usefull for creating
        theoretical plots of distributions. It is assumed to contain
        the number of particles, the dimensionality
    out_format : string, optional
        This is the desired format to use for the graphs. Supported are
        png, pdf, svg, etc. (see the matplotlib documentation).

    Returns
    -------
    outfiles : dict
        The output files created by this method.
    """
    outfiles = {'energies': _ENERFILES['energies'].format(out_format),
                'run_energies': _ENERFILES['run_energies'].format(out_format),
                'temperature': _ENERFILES['temperature'].format(out_format),
                'run_temp': _ENERFILES['run_temp'].format(out_format)}
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
        series.append({'type': 'xy', 'x': time, 'y': results[key]['running'],
                       'label': _ENERTITLE[key]})
    mpl_simple_plot(series, outfiles['run_energies'],
                    fig_settings={'xlabel': 'Time', 'ylabel': 'Energy'})
    # plot temperature
    series = [{'type': 'xy', 'x': time, 'y': energies['temp']}]
    mpl_simple_plot(series, outfiles['temperature'],
                    fig_settings={'xlabel': 'Time', 'ylabel': 'Temperature'})
    # and running average for temperature
    series = [{'type': 'xy', 'x': time, 'y': results['temp']['running']}]
    mpl_simple_plot(series, outfiles['run_temp'],
                    fig_settings={'xlabel': 'Time', 'ylabel': 'Temperature',
                                  'title': 'Running average'})

    # plot block-error results:
    outfile = _ENERFILES['block'].format('{}', out_format)
    for key in ['vpot', 'ekin', 'etot', 'temp']:
        outfiles['{}block'.format(key)] = outfile.format(key)
        mpl_block_error(results[key]['blockerror'], _ENERTITLE[key],
                        outfiles['{}block'.format(key)])
    # plot distributions
    outfile = _ENERFILES['dist'].format('{}', out_format)
    for key in ['vpot', 'ekin', 'etot', 'temp']:
        dist = results[key]['distribution']
        series = [{'type': 'xy', 'x': dist[1], 'y': dist[0],
                   'label': _ENERTITLE[key]}]
        title = '{0}. Average: {1:9.6e}, std: {2:9.6f}'
        title = title.format(_ENERTITLE[key], dist[2][0], dist[2][1])
        if simulation_settings is not None and key in ['ekin', 'temp']:
            pos = np.linspace(min(0.0, dist[1].min()),
                              dist[1].max(), 1000)
            alp = (0.5 * simulation_settings['npart'] *
                   simulation_settings['dim'])
            if key == 'ekin':
                scale = 1.0 / simulation_settings['beta']
            elif key == 'temp':
                scale = simulation_settings['temp'] / alp
            series.append({'type': 'xy', 'x': pos,
                           'y': gamma.pdf(pos, alp, loc=0, scale=scale),
                           'label': 'Boltzmann distribution'})
        outfiles['{}dist'.format(key)] = outfile.format(key)
        mpl_simple_plot(series, outfiles['{}dist'.format(key)],
                        fig_settings={'title': title})
    return outfiles


def mpl_orderp_output(results, orderdata, out_format='png'):
    """
    Plot the output from the order parameter analysis using matplotlib.

    Parameters
    ----------
    results : dict
        Each item in `results` contains the results for the corresponding
        order parameter.
    orderdata : dict of numpy.arrays
        This is the raw-data for the order parameter analysis
    out_format : string, optional
        This is the desired format to use for the graphs. Supported are
        png, pdf, svg, etc. (see the matplotlib documentation).

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
        outfiles[key] = _ORDERFILES[key].format(out_format)

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
        mpl_error_plot(series, outfiles['msd'], xlabel='Time', ylabel='MSD',
                       title=None)
    return outfiles


def mpl_flux_output(results, out_format='png'):
    """
    Plot the output from the flux analysis using matplotlib.

    Parameters
    ----------
    results : dict
        This is the dict with the results from the flux analysis.
    out_format : string, optional
        This is the desired format to use for the graphs. Supported are
        png, pdf, svg, etc. (see the matplotlib documentation).

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
        outfile = _FLUXFILES['runflux'].format(i + 1, out_format)
        outfiles['runflux'].append(outfile)
        series = [{'type': 'xy', 'x': flux[:, 0], 'y': runflux,
                   'label': 'Running average'}]
        title = 'Flux for interface no. {}'.format(i + 1)
        mpl_simple_plot(series, outfile,
                        fig_settings={'xlabel': 'Time',
                                      'ylabel': 'Flux / internal units',
                                      'title': title})
        outfile = _FLUXFILES['block'].format(i + 1, out_format)
        outfiles['block'].append(outfile)
        mpl_block_error(errflux, 'Flux interface no. {}'.format(i + 1),
                        outfile)
    return outfiles


def _txt_shoots_histogram(outputfile, histograms, scale, ensemble):
    """
    This method will write the histograms from the shoots analysis to a
    text file.

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
        This is the name of the output file to create.
    """
    data = []
    header = ['Ensemble: {0}'.format(ensemble)]
    for key in ['ACC', 'REJ', 'BWI', 'ALL']:
        try:
            mid = histograms[key][2]
            hist = histograms[key][0]
            hist_scale = hist * scale[key]
            data.append(mid)
            data.append(hist)
            data.append(hist_scale)
            header.append('{} (mid, hist, hist*scale)'.format(key))
        except KeyError:
            continue
    header = ', '.join(header)
    txt_save_columns(outputfile, header, *data)
    # *data is used here since empty histograms will not be
    # written to the output file.


def txt_path_output(path_ensemble, results, idetect, out_format='txt.gz'):
    """
    This method will output all the results obtained by the path analysis.

    Parameters
    ----------
    path_ensemble : object
        This is the path ensemble we have analysed.
    results : dict
        This dict contains the result from the analysis.
    idetect : float
        This is the interface used for the detection in the analysis.
    out_format : string, optional
        This is the desired format to use for the graphs. If 'gz' is specified,
        a gzipped file will be written
    """
    ens = path_ensemble.ensemble  # identify the ensemble
    outfiles = {}
    for key in _PATHFILES:
        outfiles[key] = _PATHFILES[key].format(ens, out_format)
    # 1) Output pcross vs lambda:
    txt_save_columns(outfiles['pcross'],
                     'Ensemble: {}, idetect: {}'.format(ens, idetect),
                     results['pcross'][0], results['pcross'][1])
    # 2) Output the running average of p:
    txt_save_columns(outfiles['prun'], 'Ensemble: {}'.format(ens),
                     results['prun'])
    # 3) Block error results:
    txt_block_error(outfiles['perror'], 'Ensemble: {0}'.format(ens),
                    results['blockerror'])
    # 3) Length histograms
    txt_histogram(outfiles['pathlength'], 'Histograms for acc and all',
                  results['pathlength'][0], results['pathlength'][1])
    # 4) Shoot histograms
    _txt_shoots_histogram(outfiles['shoots'], results['shoots'][0],
                          results['shoots'][1], ens)


def txt_total_probability(path_ensembles, detect, results, matched,
                          outputfile):
    """
    This method will output the overall matched probabilities.

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
    msg = create_backup(outputfile)
    if msg:
        warnings.warn(msg)
    with open(outputfile, 'w') as fhandle:
        for i, path_e in enumerate(path_ensembles):
            header = 'Ensemble: {}, idetect: {}'.format(path_e.ensemble,
                                                        detect[i])
            mat = np.zeros((len(matched[i]), 2))
            mat[:, 0] = results[i]['pcross'][0]
            mat[:, 1] = matched[i]
            np.savetxt(fhandle, mat, header=header)


def txt_total_matched_probability(detect, matched, outputfile):
    """
    This method will output the overall matched probability.

    Parameters
    ----------
    detect : list of floats
        These are the detect interfaces used in the analysis.
    matched : numpy.array
        The matched probability.
    outputfile : string
        This is the name of the output file to create.
    """
    header = 'Total matched probability. Interfaces: {}'
    interf = ' , '.join([str(idet) for idet in detect])
    header = header.format(interf)
    txt_save_columns(outputfile, header, matched[:, 0], matched[:, 1])


def txt_energy_output(results, energies, out_format='txt.gz'):
    """
    Save the output from the energy analysis to text files.

    Parameters
    ----------
    results : dict
        Each item in `results` contains the results for the corresponding
        energy. It is assumed to contains the keys 'vpot', 'ekin', 'etot',
        'ham', 'temp', 'elec'
    energies : numpy.array
        This is the raw-data for the energy analysis
    out_format : string, optional
        This is the desired format to use for the graphs. If 'gz' is specified,
        a gzipped file will be written

    Returns
    -------
    outfiles : dict
        The output files created by this method.
    """
    outfiles = {'run_energies': _ENERFILES['run_energies'].format(out_format),
                'temperature': _ENERFILES['temperature'].format(out_format),
                'run_temp': _ENERFILES['run_temp'].format(out_format)}
    time = energies['time']
    # 1) Store the running average:
    header = 'Running average of energy data'
    txt_save_columns(outfiles['run_energies'], header, time,
                     results['vpot']['running'], results['ekin']['running'],
                     results['etot']['running'], results['ham']['running'],
                     results['temp']['running'], results['ext']['running'])
    # 2) Save block error data:
    outfile = _ENERFILES['block'].format('{}', out_format)
    for key in ['vpot', 'ekin', 'etot', 'temp']:
        outfiles['{}block'.format(key)] = outfile.format(key)
        txt_block_error(outfiles['{}block'.format(key)], _ENERTITLE[key],
                        results[key]['blockerror'])
    # 3) Save histograms:
    outfile = _ENERFILES['dist'].format('{}', out_format)
    for key in ['vpot', 'ekin', 'etot', 'temp']:
        outfiles['{}dist'.format(key)] = outfile.format(key)
        txt_histogram(outfiles['{}dist'.format(key)],
                      r'Histogram for {}'.format(_ENERTITLE[key]),
                      results[key]['distribution'])
    return outfiles


def txt_orderp_output(results, orderdata, out_format='txt.gz'):
    """
    Save the output from the order parameter analysis to text files.

    Parameters
    ----------
    results : dict
        Each item in `results` contains the results for the corresponding
        order parameter.
    orderdata : dict of numpy.arrays
        This is the raw-data for the order parameter analysis
    out_format : string, optional
        This is the desired format to use for the graphs. If 'gz' is specified,
        a gzipped file will be written

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
        outfiles[key] = _ORDERFILES[key].format(out_format)

    time = orderdata['data'][0]
    # output running average:
    txt_save_columns(outfiles['run_order'],
                     'Time, running average',
                     time, results[0]['running'])

    # output block-error results:
    txt_block_error(outfiles['block'], 'Block error for order param',
                    results[0]['blockerror'])
    # output distributions:
    txt_histogram(outfiles['dist'], 'Order parameter',
                  results[0]['distribution'])
    # output msd if it was calculated:
    if 'msd' in results[0]:
        msd = results[0]['msd']
        txt_save_columns(outfiles['msd'], 'Time MSD Std',
                         time[:len(msd)], msd[:, 0], msd[:, 1])
        # TODO: time should here be multiplied with the correct dt
    return outfiles


def txt_flux_output(results, out_format='txt.gz'):
    """
    Store the output from the flux analysis in text files.

    Parameters
    ----------
    results : dict
        This is the dict with the results from the flux analysis.
    out_format : string, optional
        This is the desired format to use for the graphs. If 'gz' is specified,
        a gzipped file will be written

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
        outfile = _FLUXFILES['runflux'].format(i + 1, out_format)
        outfiles['runflux'].append(outfile)
        # output running average:
        txt_save_columns(outfile, 'Time, running average',
                         flux[:, 0], runflux)
        # output block-error results:
        outfile = _FLUXFILES['block'].format(i + 1, out_format)
        outfiles['block'].append(outfile)
        txt_block_error(outfile, 'Block error for flux analysis',
                        errflux)
    return outfiles
