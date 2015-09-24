# -*- coding: utf-8 -*-
"""
This files contains methods that will output results from the
path analysis and the energy analysis. It currently supports matplotlib
graphics and a simple txt-table format (i.e. a space-separated format).
For the path analysis it can also be used to output over-all matched
results.
"""
from __future__ import absolute_import
from matplotlib import pyplot as plt
import warnings
import numpy as np
import os
# pylint: disable=E0611
from scipy.stats import gamma
# pylint: enable=E0611
from .plotting import (mpl_error_plot, mpl_line_gradient, mpl_savefig,
                       mpl_simple_plot)
from .common import create_backup
from .txtinout import txt_save_columns

__all__ = ['mpl_path_output', 'txt_path_output',
           'mpl_total_probability', 'txt_total_probability',
           'mpl_total_matched_probability', 'txt_total_matched_probability',
           'mpl_energy_output', 'txt_energy_output',
           'mpl_orderp_output', 'txt_orderp_output']


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
_ENERTITLE = {'pot': 'Potential energy',
              'kin': 'Kinetic energy',
              'tot': 'Total energy',
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


def _mpl_pcross_lambda(lamb, pcross, idetect, ensemble, outputfile):
    """
    This method will plot the crossing probability as a
    function of the order parameter using matplotlib.

    Parameters
    ----------
    lamb : numpy.array
        These are the values for the order parameter
    pcross : numpy.array
        These are the values for the crossing probability
    idetect : float
        This is the interface used for the detection.
    ensemble : string
        This is the ensemble identifier, e.g. 001, 002, etc.
    outputfile : string
        This is the name of the output file to create.
    """
    fig = plt.figure()
    axs = fig.add_subplot(111)
    axs.plot(lamb, pcross)
    axs.axvline(x=idetect, ls='--', alpha=0.8)
    axs.set_xlabel(r'Order parameter ($\lambda$)')
    axs.set_ylabel('Probability')
    titl = 'Ensemble: {0}'.format(ensemble)
    axs.set_title(titl, fontsize='x-small', loc='left')
    mpl_savefig(fig, outputfile)


def _mpl_p_running_average(prun, ensemble, outputfile):
    """
    This method will create the plot of the running average of
    the probability as a function of cycle number.

    Parameters
    ----------
    prun : numpy.array
        The running average of the probability.
    ensemble : string
        This is the ensemble identifier, e.g. 001, 002, etc.
    outputfile : string
        This is the name of the output file to create.
    """
    fig = plt.figure()
    axs = fig.add_subplot(111)
    axs.axhline(y=prun[-1], ls='--', alpha=0.8)
    axs.plot(prun)
    axs.set_xlabel('Cycle number')
    axs.set_ylabel('Probability (running average)')
    titl = 'Ensemble: {0}'.format(ensemble)
    axs.set_title(titl, fontsize='x-small', loc='left')
    mpl_savefig(fig, outputfile)


def _mpl_block_error(error, title, outputfile):
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


def _mpl_length_histogram(hist1, hist2, ensemble, outputfile):
    """
    This will plot the distribution of lengths

    Parameters
    ----------
    hist1 : list
        This is the histogram of accepted paths
    hist2 : list
        This is the histogram for all paths.
    ensemble : string
        This is the ensemble identifier, e.g. 001, 002, etc.
    outputfile : string
        This is the name of the output file to create.
    """
    fig = plt.figure()
    axs = fig.add_subplot(111)
    labfmt = r'{0}: {1:6.2f} $\pm$  {2:6.2f}'
    lab1 = labfmt.format('Accepted', hist1[2][0], hist1[2][1])
    lab2 = labfmt.format('All', hist2[2][0], hist2[2][1])
    axs.plot(hist1[1], hist1[0], lw=2, label=lab1)
    axs.plot(hist2[1], hist2[0], lw=2, label=lab2)
    axs.set_xlabel('MD steps')
    axs.set_ylabel('Frequency')
    titl = 'Ensemble: {0}'.format(ensemble)
    axs.set_title(titl, fontsize='x-small', loc='left')
    axs.legend(prop={'size': 'x-small'})
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
    fig = plt.figure()
    axs = fig.add_subplot(111)
    fig_scale = plt.figure()
    axs_scale = fig_scale.add_subplot(111)
    for key in ['ACC', 'REJ', 'BWI', 'ALL']:
        try:
            mid = histograms[key][2]
            hist = histograms[key][0]
            axs.plot(mid, hist, lw=2, ls='-', label='{}'.format(key),
                     alpha=0.8)
            hist *= scale[key]
            axs_scale.plot(mid, hist, lw=2, ls='-', label='{}'.format(key),
                           alpha=0.8)
        except KeyError:
            continue
    titl = 'Ensemble: {0}'.format(ensemble)
    axs.set_title(titl, fontsize='x-small', loc='left')
    axs.legend(prop={'size': 'x-small'})
    axs_scale.set_title(titl, fontsize='x-small', loc='left')
    axs_scale.legend(prop={'size': 'x-small'})
    mpl_savefig(fig, outputfile)
    mpl_savefig(fig_scale, outputfile_scale)


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
    _mpl_pcross_lambda(results['pcross'][0], results['pcross'][1], idetect,
                       ens, outfiles['pcross'])
    _mpl_p_running_average(results['prun'], ens, outfiles['prun'])
    _mpl_block_error(results['blockerror'], 'Ensemble: {0}'.format(ens),
                     outfiles['perror'])
    _mpl_length_histogram(results['pathlength'][0], results['pathlength'][1],
                          ens, outfiles['pathlength'])
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
    fig = plt.figure()
    axs = fig.add_subplot(111)
    for idetect in detect:
        axs.axvline(x=idetect, ls='--', alpha=0.8)
    for result, prob, path_e in zip(results, matched, path_ensembles):
        axs.plot(result['pcross'][0], prob, lw=3, label=path_e.ensemble)
    axs.set_yscale('log')
    axs.legend(prop={'size': 'small'})
    axs.set_xlabel(r'Order parameter ($\lambda$)')
    axs.set_ylabel('Probability')
    titl = 'Matched probabilities'
    axs.set_title(titl, fontsize='x-small', loc='left')
    mpl_savefig(fig, outputfile)


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
    fig = plt.figure()
    axs = fig.add_subplot(111)
    for idetect in detect:
        axs.axvline(x=idetect, ls='--', alpha=0.8)
    axs.plot(matched[:, 0], matched[:, 1], lw=3)
    axs.set_yscale('log')
    axs.set_xlabel(r'Order parameter ($\lambda$)')
    axs.set_ylabel('Probability')
    titl = 'Matched probability'
    axs.set_title(titl, fontsize='x-small', loc='left')
    mpl_savefig(fig, outputfile)


def mpl_energy_output(results, energies, simulation_settings=None,
                      out_format='png'):
    """
    Save the output from the energy analysis to text files.

    Parameters
    ----------
    results : dict
        Each item in `results` contains the results for the corresponding
        energy. It is assumed to contains the keys 'pot', 'kin', 'tot',
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
    for key in ['pot', 'kin', 'tot', 'ham']:
        series.append((time, energies[key],
                       _ENERTITLE[key]))
    mpl_simple_plot(series, outfiles['energies'],
                    xlabel='Time', ylabel='Energy', title=None)
    # make running average plot of the energies as function of time
    series = []
    for key in ['pot', 'kin', 'tot', 'ham']:
        series.append((time, results[key]['running'], _ENERTITLE[key]))
    mpl_simple_plot(series, outfiles['run_energies'],
                    xlabel='Time', ylabel='Energy', title=None)
    # plot temperature
    series = [(time, energies['temp'], None)]
    mpl_simple_plot(series, outfiles['temperature'],
                    xlabel='Time', ylabel='Temperature', title=None)
    # and running average for temperature
    series = [(time, results['temp']['running'], None)]
    mpl_simple_plot(series, outfiles['run_temp'],
                    xlabel='Time', ylabel='Temperature',
                    title='Running average')

    # plot block-error results:
    outfile = _ENERFILES['block'].format('{}', out_format)
    for key in ['pot', 'kin', 'tot', 'temp']:
        outfiles['{}block'.format(key)] = outfile.format(key)
        _mpl_block_error(results[key]['blockerror'], _ENERTITLE[key],
                         outfiles['{}block'.format(key)])
    # plot distributions
    outfile = _ENERFILES['dist'].format('{}', out_format)
    for key in ['pot', 'kin', 'tot', 'temp']:
        dist = results[key]['distribution']
        series = [(dist[1], dist[0], _ENERTITLE[key])]
        title = '{0}. Average: {1:9.6e}, std: {2:9.6f}'
        title = title.format(_ENERTITLE[key], dist[2][0], dist[2][1])
        if simulation_settings is not None and key in ['kin', 'temp']:
            pos = np.linspace(min(0.0, dist[1].min()),
                              dist[1].max(), 1000)
            alp = (0.5 * simulation_settings['npart'] *
                   simulation_settings['dim'])
            if key == 'kin':
                scale = 1.0 / simulation_settings['beta']
            elif key == 'temp':
                scale = simulation_settings['temp'] / alp
            series.append((pos, gamma.pdf(pos, alp, loc=0, scale=scale),
                           'Boltzmann distribution'))
        outfiles['{}dist'.format(key)] = outfile.format(key)
        mpl_simple_plot(series, outfiles['{}dist'.format(key)],
                        xlabel=None, ylabel=None, title=title)
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
    series = [(time, orderdata['data'][1])]
    mpl_simple_plot(series, outfiles['order'],
                    xlabel='Time', ylabel='Order parameter', title=None)
    # make running average plot of the energies as function of time
    series = [(time, results[0]['running'], 'Running average')]
    mpl_simple_plot(series, outfiles['run_order'],
                    xlabel='Time', ylabel='Order parameter', title=None)

    # plot block-error results:
    _mpl_block_error(results[0]['blockerror'], 'Order parameter',
                     outfiles['block'])
    # plot distributions
    dist = results[0]['distribution']
    series = [(dist[1], dist[0])]
    title = '{0}. Average: {1:9.6e}, std: {2:9.6f}'
    title = title.format('Order parameter', dist[2][0], dist[2][1])
    mpl_simple_plot(series, outfiles['dist'],
                    xlabel=None, ylabel=None, title=title)

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
        series = [(flux[:, 0], runflux, 'Running average')]
        mpl_simple_plot(series, outfile,
                        xlabel='Time', ylabel='Flux / internal units',
                        title='Flux for interface no. {}'.format(i + 1))
        outfile = _FLUXFILES['block'].format(i + 1, out_format)
        outfiles['block'].append(outfile)
        _mpl_block_error(errflux, 'Flux interface no. {}'.format(i + 1),
                         outfile)
    return outfiles


def _txt_block_error(outputfile, title, error):
    """
    This will write the output from the error analysis, to a text file.

    Parameters
    ----------
    outputfile : string
        This is the name of the output file to create.
    title : string
        This is a identifier/title to add to the header, e.g. 'Ensemble: 001',
        'Kinetic energy', etc.
    error : list
        This is the result from the error analysis
    """
    header = '{0}, Rel.err: {1:9.6e}, Ncor: {2:9.6f}'
    header = header.format(title, error[4], error[6])
    txt_save_columns(outputfile, header, error[0], error[3])


def _txt_histogram(outputfile, title, *histograms):
    """
    This will output the distribution of lengths to a text file.

    Parameters
    ----------
    outputfile : string
        This is the name of the output file to create.
    title : string
        A descriptive title to add to the header.
    histograms : tuple
        The histograms to store.
    """
    data = []
    header = [r'{}'.format(title)]
    for hist in histograms:
        header.append(r'avg: {0:6.2f}, std: {1:6.2f}'.format(hist[2][0],
                                                             hist[2][1]))
        data.append(hist[1])
        data.append(hist[0])
    header = ', '.join(header)
    txt_save_columns(outputfile, header, *data)
    # *data is used here since we want to be flexible and write any number
    # of histograms to the file.


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
    _txt_block_error(outfiles['perror'], 'Ensemble: {0}'.format(ens),
                     results['blockerror'])
    # 3) Length histograms
    _txt_histogram(outfiles['pathlength'], 'Histograms for acc and all',
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
        energy. It is assumed to contains the keys 'pot', 'kin', 'tot',
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
                     results['pot']['running'], results['kin']['running'],
                     results['tot']['running'], results['ham']['running'],
                     results['temp']['running'], results['ext']['running'])
    # 2) Save block error data:
    outfile = _ENERFILES['block'].format('{}', out_format)
    for key in ['pot', 'kin', 'tot', 'temp']:
        outfiles['{}block'.format(key)] = outfile.format(key)
        _txt_block_error(outfiles['{}block'.format(key)], _ENERTITLE[key],
                         results[key]['blockerror'])
    # 3) Save histograms:
    outfile = _ENERFILES['dist'].format('{}', out_format)
    for key in ['pot', 'kin', 'tot', 'temp']:
        outfiles['{}dist'.format(key)] = outfile.format(key)
        _txt_histogram(outfiles['{}dist'.format(key)],
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
    # output running average:
    txt_save_columns(outfiles['run_order'],
                     'Time, running average',
                     time, results[0]['running'])

    # plot block-error results:
    _txt_block_error(outfiles['block'], 'Block error for order param',
                     results[0]['blockerror'])
    # plot distributions
    _txt_histogram(outfiles['dist'], 'Order parameter',
                   results[0]['distribution'])
    # output msd if it was calculated:
    if 'msd' in results[0]:
        msd = results[0]['msd']
        txt_save_columns(outfiles['msd'], 'Time MSD Std',
                         time[:len(msd)], msd[:, 0], msd[:, 1])
        # TODO: time should here be multiplied with the correct dt
    return outfiles
