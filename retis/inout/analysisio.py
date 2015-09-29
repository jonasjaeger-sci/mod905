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
from .common import (create_backup, _ENERFILES, _ENERTITLE, _FLUXFILES,
                     _ORDERFILES, _PATHFILES)
from .txtinout import txt_save_columns, txt_block_error, txt_histogram

__all__ = ['txt_path_output',
           'txt_total_probability',
           'txt_total_matched_probability',
           'txt_energy_output',
           'txt_orderp_output',
           'txt_flux_output']


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
