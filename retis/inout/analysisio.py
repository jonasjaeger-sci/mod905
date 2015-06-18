# -*- coding: utf-8 -*-
"""
This file contains methods that will output
the results from the path analysis.
"""
from __future__ import absolute_import
from .inout import create_backup
from matplotlib import pyplot as plt
import warnings
import numpy as np


__all__ = ['mpl_output_analysis', 'txt_output_analysis']


# hard-coded patters for output files:
_OUTFILES = {'pcross': '{}_pcross.{}',
             'prun': '{}_prun.{}',
             'blockerror': '{}_perror.{}',
             'pathlength': '{}_lpath.{}',
             'shoots': '{}_shoots.{}',
             'shoots-scaled': '{}_shoots_scale.{}'}


def _mpl_savefig(fig, outputfile):
    """
    This is just a helper function to save matplotlib figures.
    It will save figures so that old ones are not overwritten.

    Parameters
    ----------
    fig : figure object from pyploy
        This is the figure to be written to the file.
        We simply use fig.savefig here.
    outputfile : string
        This is the name of the output file to create.
    """
    msg = create_backup(outputfile)
    if msg:
        warnings.warn(msg)
    fig.savefig(outputfile)


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
    _mpl_savefig(fig, outputfile)


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
    _mpl_savefig(fig, outputfile)


def _mpl_p_block_error(error, ensemble, outputfile):
    """
    This will plot the output from the error analysis, that is
    error as a function of the block length.

    Parameters
    ----------
    error : list
        This is the result from the error analysis
    ensemble : string
        This is the ensemble identifier, e.g. 001, 002, etc.
    outputfile : string
        This is the name of the output file to create.
    """
    fig = plt.figure()
    axs = fig.add_subplot(111)
    axs.axhline(y=error[4], alpha=0.8, ls='--')
    axs.plot(error[0], error[3])
    axs.set_xlabel('Block length')
    axs.set_ylabel('Estimated error')
    titl = 'Ensemble: {0}: Rel.err: {1:9.6e} Ncor: {2:9.6f}'
    titl = titl.format(ensemble, error[4], error[6])
    axs.set_title(titl, fontsize='x-small', loc='left')
    _mpl_savefig(fig, outputfile)


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
    _mpl_savefig(fig, outputfile)


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
    _mpl_savefig(fig, outputfile)
    _mpl_savefig(fig_scale, outputfile_scale)


def mpl_output_analysis(path_ensemble, results, idetect, mpl_format='png'):
    """
    This method will output all the figures from the results obtained
    by the path analysis.

    Parameters
    ----------
    path_ensemble : object
        This is the path ensemble we have analysed.
    results : dict
        This dict contains the result from the analysis.
    idetect : float
        This is the interface used for the detection in the analysis.
    mpl_format : string, optional
        This is the desired format to use for the graphs. Supported are
        png, pdf, svg, etc. (see the matplotlib documentation).
    """
    ens = path_ensemble.ensemble  # identify the ensemble
    outfiles = {}
    for key in _OUTFILES:
        outfiles[key] = _OUTFILES[key].format(ens, mpl_format)
    _mpl_pcross_lambda(results['pcross'][0], results['pcross'][1], idetect,
                       ens, outfiles['pcross'])
    _mpl_p_running_average(results['prun'], ens, outfiles['prun'])
    _mpl_p_block_error(results['blockerror'], ens, outfiles['blockerror'])
    _mpl_length_histogram(results['pathlength'][0], results['pathlength'][1],
                          ens, outfiles['pathlength'])
    _mpl_shoots_histogram(results['shoots'][0], results['shoots'][1], ens,
                          outfiles['shoots'], outfiles['shoots-scaled'])


def _txt_save_columns(outputfile, header, *variables):
    """
    This will save the different variables to a text file using
    numpy's savetxt. Note that the variables are assumed to be numpy.arrays of
    equal shape. Note that the outputfile may also be a zipped gz file.

    Parameters
    ----------
    outputfile : string
        This is the name of the output file to create.
    header : string
        String that will be written at the beginning of the file.
    variables : tuple of numpy.arrays
        These are the variables that will be save to the text file
    """
    msg = create_backup(outputfile)
    if msg:
        warnings.warn(msg)
    nvar = len(variables)
    mat = np.zeros((len(variables[0]), nvar))
    for i, vari in enumerate(variables):
        try:
            mat[:, i] = vari
        except ValueError:
            msg = 'Could not align variables, skipping (writing zeros)'
            warnings.warn(msg)
    np.savetxt(outputfile, mat, header=header)


def _txt_pcross_lambda(lamb, pcross, idetect, ensemble, outputfile):
    """
    This method save the output for the crossing probability as a simple
    text file.

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
    header = 'Ensemble: {}, idetect: {}'.format(ensemble, idetect)
    _txt_save_columns(outputfile, header, lamb, pcross)


def _txt_p_running_average(prun, ensemble, outputfile):
    """
    This method will write the running average of the probability
    to a text file.

    Parameters
    ----------
    prun : numpy.array
        The running average of the probability.
    ensemble : string
        This is the ensemble identifier, e.g. 001, 002, etc.
    outputfile : string
        This is the name of the output file to create.
    """
    header = 'Ensemble: {}'.format(ensemble)
    _txt_save_columns(outputfile, header, prun)


def _txt_p_block_error(error, ensemble, outputfile):
    """
    This will write the output from the error analysis, to a text file.

    Parameters
    ----------
    error : list
        This is the result from the error analysis
    ensemble : string
        This is the ensemble identifier, e.g. 001, 002, etc.
    outputfile : string
        This is the name of the output file to create.
    """
    header = 'Ensemble: {0}, Rel.err: {1:9.6e}, Ncor: {2:9.6f}'
    header = header.format(ensemble, error[4], error[6])
    _txt_save_columns(outputfile, header, error[0], error[3])


def _txt_length_histogram(hist1, hist2, ensemble, outputfile):
    """
    This will output the distribution of lengths to a text file.

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
    header = r'Ensemble: {0}, <acc>: {1:6.2f}, s(acc): {2:6.2f}, ' \
             r'<all>: {3:6.2f}, s(all): {4:6.2f}'
    header = header.format(ensemble, hist1[2][0], hist1[2][1],
                           hist2[2][0], hist2[2][1])
    _txt_save_columns(outputfile, header, hist1[1], hist1[0],
                      hist2[1], hist2[0])


def _txt_shoots_histogram(histograms, scale, ensemble, outputfile):
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
            header.append(', {}'.format(key))
        except KeyError:
            continue
    header = ''.join(header)
    _txt_save_columns(outputfile, header, *data)


def txt_output_analysis(path_ensemble, results, idetect, txt_format='txt.gz'):
    """
    This method will output all the figures from the results obtained
    by the path analysis.

    Parameters
    ----------
    path_ensemble : object
        This is the path ensemble we have analysed.
    results : dict
        This dict contains the result from the analysis.
    idetect : float
        This is the interface used for the detection in the analysis.
    txt_format : string, optional
        This is the desired format to use for the graphs. If 'gz' is specified,
        a gzipped file will be written
    """
    ens = path_ensemble.ensemble  # identify the ensemble
    outfiles = {}
    for key in _OUTFILES:
        outfiles[key] = _OUTFILES[key].format(ens, txt_format)
    _txt_pcross_lambda(results['pcross'][0], results['pcross'][1], idetect,
                       ens, outfiles['pcross'])
    _txt_p_running_average(results['prun'], ens, outfiles['prun'])
    _txt_p_block_error(results['blockerror'], ens, outfiles['blockerror'])
    _txt_length_histogram(results['pathlength'][0], results['pathlength'][1],
                          ens, outfiles['pathlength'])
    _txt_shoots_histogram(results['shoots'][0], results['shoots'][1], ens,
                          outfiles['shoots'])
