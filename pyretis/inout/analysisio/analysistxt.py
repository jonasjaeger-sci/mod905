# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""Functions and classes for text based output from the analysis.

This file contains functions and classes that handle text files for the
analysis input/output.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

txt_energy_output
    For writing the output from a energy analysis.

txt_flux_output
    For writing the output from a flux-analysis.

txt_orderp_output
    For writing the output from a order parameter analysis.

txt_path_output
    For writing the output from a path simulation.

txt_matched_probability
    For writing output with matched probabilities.
"""
import logging
import numpy as np
# pyretis imports:
from pyretis.inout.common import create_backup, name_file
from pyretis.inout.common import (ENERFILES, ENERTITLE, FLUXFILES,
                                  ORDERFILES, PATHFILES, PATH_MATCH)
from pyretis.inout.writers.txtinout import txt_save_columns
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['txt_energy_output', 'txt_flux_output',
           'txt_orderp_output', 'txt_path_output',
           'txt_matched_probability']


def txt_block_error(outputfile, title, error, backup=False):
    """Write the output from the error analysis to a text file.

    Parameters
    ----------
    outputfile : string
        This is the name of the output file to create.
    title : string
        This is a identifier/title to add to the header, e.g.
        'Ensemble: 001', 'Kinetic energy', etc.
    error : list
        This is the result from the error analysis.
    backup : boolean, optional
        Determines if we will do backup of old files or not.
    """
    header = '{0}, Rel.err: {1:9.6e}, Ncor: {2:9.6f}'
    header = header.format(title, error[4], error[6])
    txt_save_columns(outputfile, header, (error[0], error[3]), backup=backup)


def txt_histogram(outputfile, title, histograms, backup=False):
    """Write histograms to a text file.

    Parameters
    ----------
    outputfile : string
        This is the name of the output file to create.
    title : string
        A descriptive title to add to the header.
    histograms : tuple
        The histograms to store.
    backup : boolean, optional
        Determines if we will do backup of old files or not.
    """
    data = []
    header = [r'{}'.format(title)]
    for hist in histograms:
        header.append(r'avg: {0:6.2f}, std: {1:6.2f}'.format(hist[2][0],
                                                             hist[2][1]))
        data.append(hist[1])
        data.append(hist[0])
    headertxt = ', '.join(header)
    txt_save_columns(outputfile, headertxt, data, backup=backup)


def txt_flux_output(results, out_fmt='txt.gz', backup=False,
                    path=None):
    """Store the output from the flux analysis in text files.

    Parameters
    ----------
    results : dict
        This is the dict with the results from the flux analysis.
    out_fmt : string, optional
        This is the desired format to use for the graphs. If 'gz' is
        specified, the file will be written in compressed gzip format.
    backup : boolean, optional
        Determines if we will do backup of old files or not.
    path : string, optional
        Specify a directory for writing the files to.

    Returns
    -------
    outfiles : list of strings
        The output files created by this function.

    """
    outfiles = []
    # make running average plot and error plot:
    for i in range(len(results['flux'])):
        flux = results['flux'][i]
        runflux = results['runflux'][i]
        errflux = results['errflux'][i]
        outfile = name_file(FLUXFILES['runflux'].format(i + 1), out_fmt,
                            path=path)
        outfiles.append(outfile)
        # output running average:
        txt_save_columns(outfile, 'Time, running average',
                         (flux[:, 0], runflux), backup=backup)
        # output block-error results:
        outfile = name_file(FLUXFILES['block'].format(i + 1), out_fmt,
                            path=path)
        outfiles.append(outfile)
        txt_block_error(outfile, 'Block error for flux analysis',
                        errflux, backup=backup)
    return outfiles


def txt_orderp_output(results, orderdata, out_fmt='txt.gz', backup=False,
                      path=None):
    """Save the output from the order parameter analysis to text files.

    Parameters
    ----------
    results : dict
        Each item in `results` contains the results for the
        corresponding order parameter.
    orderdata : list of numpy.arrays
        This is the raw-data for the order parameter analysis
    out_fmt : string, optional
        This is the desired format to use for the graphs. If 'gz' is
        specified, the file will be written in compressed gzip format.
    backup : boolean, optional
        Determines if we will do backup of old files or not.
    path : string, optional
        Specify a directory for writing the files to.

    Returns
    -------
    outfiles : list
        The output files created by this function.

    Note
    ----
    We are here only outputting results for the first order parameter.
    I.e. other order parameters or velocities are not written here. This
    will be changed when the structure of the output order parameter
    file has been fixed. Also note that, if present, the first order
    parameter will be plotted against the second one - i.e. the second
    one will be assumed to represent the velocity here.
    """
    outfiles = []
    time = orderdata[0]
    # output running average:
    outfile = name_file(ORDERFILES['run_order'], out_fmt, path=path)
    txt_save_columns(outfile, 'Time, running average',
                     (time, results[0]['running']),
                     backup=backup)
    outfiles.append(outfile)

    # output block-error results:
    outfile = name_file(ORDERFILES['block'], out_fmt, path=path)
    txt_block_error(outfile, 'Block error for order param',
                    results[0]['blockerror'], backup=backup)
    outfiles.append(outfile)
    # output distributions:
    outfile = name_file(ORDERFILES['dist'], out_fmt, path=path)
    txt_histogram(outfile, 'Order parameter',
                  [results[0]['distribution']], backup=backup)
    outfiles.append(outfile)
    # output msd if it was calculated:
    if 'msd' in results[0]:
        msd = results[0]['msd']
        outfile = name_file(ORDERFILES['msd'], out_fmt, path=path)
        txt_save_columns(outfile, 'Time MSD Std',
                         (time[:len(msd)], msd[:, 0], msd[:, 1]),
                         backup=backup)
        outfiles.append(outfile)
        # TODO: time c/should here be multiplied with the correct dt
    return outfiles


def txt_energy_output(results, energies, out_fmt='txt.gz', backup=False,
                      path=None):
    """Save the output from the energy analysis to text files.

    Parameters
    ----------
    results : dict
        Each item in `results` contains the results for the
        corresponding energy. It is assumed to contains the keys
        'vpot', 'ekin', 'etot', 'ham', 'temp', 'elec'.
    energies : numpy.array
        This is the raw-data for the energy analysis.
    out_fmt : string, optional
        This is the desired format to use for the graphs. If 'gz' is
        specified, the file will be written in compressed gzip format.
    backup : boolean, optional
        Determines if we will do backup of old files or not.
    path : string, optional
        Specify a directory for writing the files to.

    Returns
    -------
    outfiles : list
        The output files created by this function.
    """
    outfiles = []
    time = energies['time']
    # 1) Store the running average:
    header = ['Running average of energy data: time']
    data = [time]
    for key in ['vpot', 'ekin', 'etot', 'ham', 'temp', 'ext']:
        if key in results:
            data.append(results[key]['running'])
            header.append(key)
    headertxt = ' '.join(header)
    outfile = name_file(ENERFILES['run_energies'], out_fmt, path=path)
    outfiles.append(outfile)
    txt_save_columns(outfile, headertxt, data, backup=backup)
    # 2) Save block error data:
    for key in ['vpot', 'ekin', 'etot', 'temp']:
        if key in results:
            outfile = name_file(ENERFILES['block'].format(key), out_fmt,
                                path=path)
            outfiles.append(outfile)
            txt_block_error(outfile, ENERTITLE[key],
                            results[key]['blockerror'], backup=backup)
    # 3) Save histograms:
    for key in ['vpot', 'ekin', 'etot', 'temp']:
        if key in results:
            outfile = name_file(ENERFILES['dist'].format(key), out_fmt,
                                path=path)
            outfiles.append(outfile)
            txt_histogram(outfile, r'Histogram for {}'.format(ENERTITLE[key]),
                          [results[key]['distribution']], backup=backup)
    return outfiles


def _txt_shoots_histogram(outputfile, histograms, scale, ensemble,
                          backup=False):
    """Write the histograms from the shoots analysis to a text file.

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
    backup : boolean, optional
        Determines if we will do backup of old files or not.
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
    headertxt = ', '.join(header)
    txt_save_columns(outputfile, headertxt, data, backup=backup)


def txt_path_output(path_ensemble, results, idetect, out_fmt='txt.gz',
                    backup=False, path=None):
    """Output all the results obtained by the path analysis.

    Parameters
    ----------
    path_ensemble : object
        This is the path ensemble we have analysed.
    results : dict
        This dict contains the result from the analysis.
    idetect : float
        This is the interface used for the detection in the analysis.
    out_fmt : string, optional
        This is the desired format to use for the graphs. If 'gz' is
        specified, the file will be written in compressed gzip format.
    backup : boolean, optional
        Determines if we will do backup of old files or not.
    path : string, optional
        Specify a directory for writing the files to.

    Returns
    -------
    outfiles : list
        The output files created by this function.
    """
    ens = path_ensemble.ensemble_name  # identify the ensemble
    ens_simplified = path_ensemble.ensemble_name_simple
    outfiles = []
    if 'pcross' in results:
        # 1) Output pcross vs lambda:
        outfile = name_file(PATHFILES['pcross'].format(ens_simplified),
                            out_fmt, path=path)
        outfiles.append(outfile)
        txt_save_columns(outfile,
                         'Ensemble: {}, idetect: {}'.format(ens, idetect),
                         [results['pcross'][0], results['pcross'][1]],
                         backup=backup)
    if 'prun' in results:
        # 2) Output the running average of p:
        outfile = name_file(PATHFILES['prun'].format(ens_simplified),
                            out_fmt, path=path)
        outfiles.append(outfile)
        txt_save_columns(outfile, 'Ensemble: {}'.format(ens),
                         [results['prun']], backup=backup)
    if 'blockerror' in results:
        # 3) Block error results:
        outfile = name_file(PATHFILES['perror'].format(ens_simplified),
                            out_fmt, path=path)
        outfiles.append(outfile)
        txt_block_error(outfile, 'Ensemble: {0}'.format(ens),
                        results['blockerror'], backup=backup)
    # 3) Length histograms
    outfile = name_file(PATHFILES['pathlength'].format(ens_simplified),
                        out_fmt, path=path)
    outfiles.append(outfile)
    txt_histogram(outfile, 'Histograms for acc and all',
                  [results['pathlength'][0], results['pathlength'][1]],
                  backup=backup)
    # 4) Shoot histograms
    outfile = name_file(PATHFILES['shoots'].format(ens_simplified),
                        out_fmt, path=path)
    outfiles.append(outfile)
    _txt_shoots_histogram(outfile, results['shoots'][0],
                          results['shoots'][1], ens, backup=backup)
    return outfiles


def txt_matched_probability(path_ensembles, detect, matched,
                            out_fmt='txt.gz', backup=False, path=None):
    """Output the matched probabilities to a text file.

    This function will output the matched probabilities for the
    different ensembles and also output the over-all matched
    probability.

    Parameters
    ----------
    path_ensembles : list of strings
        This is the names for the path ensembles we have calculated
        the probability for.
    detect : list of floats
        These are the detect interfaces used in the analysis.
    matched : dict
        This dict contains the results from the matching of the
        probabilities. We make use of `matched['overall-prob']` and
        `matched['matched-prob']` here.
    out_fmt : string
        Determines the output format for the text file. If 'gz' is used,
        the file will be written in compressed gzip format.
    backup : boolean
        If `backup` is False, we will overwrite files, otherwise we will
        backup.
    path : string, optional
        Specify a directory for writing the files to.


    Returns
    -------
    outfiles : list
        The files created by this function.
    """
    outfiles = []
    # start by creating the matched file, here we use a custom
    # file writer:
    outfile = name_file(PATH_MATCH['match'], out_fmt, path=path)
    if outfile.endswith('.gz'):
        outfile = outfile[:-3]
        msgtxt = ('Writing gzipped matched probabilities is not supported!\n'
                  'File will be written as text.')

        logger.warning(msgtxt)
    if backup:
        msgtxt = create_backup(outfile)
        if msgtxt:
            logger.warning(msgtxt)
    outfiles.append(outfile)
    with open(outfile, 'wb') as fhandle:
        for prob, ens, idet in zip(matched['matched-prob'],
                                   path_ensembles, detect):
            header = 'Ensemble: {}, idetect: {}'.format(ens, idet)
            np.savetxt(fhandle, prob, header=header)
    # output the over-all matched probability:
    outfile = name_file(PATH_MATCH['total'], out_fmt, path=path)
    outfiles.append(outfile)
    interf = ' , '.join([str(idet) for idet in detect])
    header = 'Total matched probability. Interfaces: {}'
    txt_save_columns(outfile, header.format(interf),
                     (matched['overall-prob'][:, 0],
                      matched['overall-prob'][:, 1]),
                     backup=backup)
    return outfiles
