# -*- coding: utf-8 -*-
"""
This file contains methods for analysis of path ensembles as defined
in the object PathEnsemble in retis.core.path
"""
from __future__ import absolute_import
import numpy as np
from .analysis import running_average, block_error
from .histogram import histogram
import warnings


__all__ = ['analyse_path_ensemble', 'match_probabilities']


def _get_successfull(path_ensemble, idetect):
    """
    This is a helper function to build the data of accepted paths.
    In the PathEmsemble object all paths are stored, both accepted
    and rejected and the PathEnsemble.get_accepted() is used here to
    iterate over accepted paths. Successfull paths are defined as paths
    which are able to reach the interface specified with idetect. For
    each accepted path, this function will give a value of 1 if the path
    was successfull and 0 otherwise.

    Parameters
    ----------
    path_ensemble : object of type `retis.core.path.PathEnsemble`.
        This is the PathEnsemble we will analyse
    idetect : float
        This is the interface used for detecting if a path is usccessfull
        or not.

    Returns
    -------
    out : numpy.array
        out[i] = 1 if path no. i is successfull 0 otherwise.
    """
    data = []
    for path in path_ensemble.get_accepted():
        value = 1 if path['ordermax'][0] > idetect else 0
        data.append(value)
    data = np.array(data)
    return data


def _running_pcross(path_ensemble, idetect, data=None):
    """
    Function to create a running average of the crossing probability
    as function of the cycle number. Note that the accepted paths are used
    to create an array which is then averaged. This could possibly
    be replaced by a simple on-the-fly calculation of the running average,
    as detailed in: http://en.wikipedia.org/wiki/Moving_average

    Parameters
    ----------
    path_ensemble : object of type retis.core.path.PathEnsemble
        This is the PathEnsemble we will analyse
    idetect : float
        This is the interface used for detecting if a path is usccessfull
        or not. I
    data : numpy.array
        This is the data created by _get_successfull(path_ensemble)
        If this function has been executed, the result can be re-used here
        by specifying data. If not, it will be generated.

    Returns
    -------
    out[0] : numpy.array
        The running average of the crossing probability
    out[1] : numpy.array
        The original data, can be used further in other analysis methods.

    See Also
    --------
    _get_successfull
    """
    if data is None:
        data = _get_successfull(path_ensemble, idetect)
    return running_average(data), data


def _pcross_lambda(path_ensemble, ngrid=1000):
    """
    This function will calculate the crossing probability for an ensemble as
    a function of the value of the order parameter.

    Parameters
    ----------
    path_ensemble : object of type retis.core.path.PathEnsemble
        This is the PathEnsemble we will analyse
    ngrid : int
        This is the number of grid points

    Returns
    -------
    out[0] : numpy.array
        The crossing probability
    out[1] : numpy.array
        The order parameters

    See Also
    --------
    _pcross_lambda_cumulative

    Notes
    -----
    This routine could perhaps be made shorter by making use of
    numpy.digitize etc.
    """
    # first, get the boundaries and order parameters of the
    # accepted paths
    orderparam = []
    ordermax = None
    for path in path_ensemble.get_accepted():
        orderp = path['ordermax'][0]
        if ordermax is None or orderp > ordermax:
            ordermax = orderp
        orderparam.append(orderp)
    orderparam = np.array(orderparam)
    # next create the ``cumulative histogram'':
    ordermax = min(ordermax, max(path_ensemble.interfaces))
    ordermin = path_ensemble.interfaces[1]
    pcross, lamb = _pcross_lambda_cumulative(orderparam, ordermin, ordermax,
                                             ngrid)
    return pcross, lamb


def _pcross_lambda_cumulative(orderparam, ordermin, ordermax, ngrid,
                              weights=None):
    """
    This is a helper function for obtaining the crossing probability
    as a function of the order parameter. It will do the actual calculation
    of the crossing probability as a function of order parameter.

    It is split off from ``pcross_lambda`` since the analysis is intented
    to be backwards compatible with the output/results from the old
    tismol FORTRAN program.

    Parameters
    ----------
    orderparam : numpy.array
        Array containing the order parameters
    ordermin : float
        Minimum allowed order parameter
    ordermax : float
        Maximum allowed order parameter
    ngrid : int
        This is the number of grid points
    weights : numpy.array, optional
        The weight of each order parameter. This is used in order to
        count a specific order parameter more than once. If not given, the
        values in `orderparam` will be weighted equally.
    """
    lamb = np.linspace(ordermin, ordermax, ngrid)
    pcross = np.zeros(ngrid)
    delta_l = lamb[1] - lamb[0]
    sumw = 0.0
    for i, orderp in enumerate(orderparam):
        idx = np.floor((orderp - ordermin) / delta_l)
        idx = int(idx) + 1
        # +1: idx is here defined so that lamb[idx-1] <= orderp < lamb[idx]
        # further this lambda will contribute up to and including lamb[idx]
        # this is accomplished by the idx+1 when summing weights below
        if weights is None:
            weight = 1
        else:
            weight = weights[i]
        sumw += weight
        if idx >= ngrid:
            pcross += weight
        elif idx < 0:
            pass
        else:
            pcross[:idx + 1] += weight  # +1 to include up to idx
    pcross /= sumw  # normalization
    return pcross, lamb


def _pcross_error(path_ensemble, idetect, maxblock=5000, blockskip=1,
                  data=None):
    """
    This function will run the block error analysis for the
    path ensemble.

    Parameters
    ----------
    path_ensemble : object of type ``retis.core.path.PathEnsemble``.
        This is the path ensemble we will analyse
    maxblock : int
        The maximum block length to consider
    blockskip = int
        Intervall between blocks. Blocks are created as 1, 1+blockskip, ...
        up to maxblock.
    data : numpy.array
        This is the data created by ``_get_successfull``.
        If this function has been executed, the result can be re-used here
        by specifying data. If not, it will be generated.
    idetect : float
        This is the interface used for detecting if a path is usccessfull
        or not.

    See Also
    --------
    _get_successfull
    """
    if data is None:
        data = _get_successfull(path_ensemble, idetect)

    blen, bavg, berr, berr_avg = block_error(data, maxblock=maxblock,
                                             blockskip=blockskip)
    # also calculate some relative errors:
    try:
        rel_err = berr / abs(bavg[0])
        avg_rel_err = berr_avg / abs(bavg[0])
    except ZeroDivisionError:
        rel_err = float('inf')
        avg_rel_err = float('inf')
    # and correlation estimate:
    try:
        ncor = (berr / berr[0])**2
        avg_ncor = (berr_avg / berr[0])**2
    except ZeroDivisionError:
        ncor = float('inf')
        avg_ncor = float('inf')
    return blen, berr, berr_avg, rel_err, avg_rel_err, ncor, avg_ncor


def _get_path_distribution(path_ensemble, bins=1000):
    """
    This function will get the distribution of path lengths.

    Parameters
    ----------
    path_ensemble : object of type ``retis.core.path.PathEnsemble``.
        This is the path ensemble we will analyse.
    bins : int, optional
        The number of bins to use for the histograms for the distribution.

    Returns
    -------
    out[0] : list, [numpy.array, numpy.array, tuple]
        Result for accepted paths (distribution). out[0][0] is the histogram
        and out[0][1] are the mid points for bins. out[0][2] is a tuple with
        the average and standard deviation for the length.
    out[1] : list, [numpy.array, numpy.array, tuple]
        Result for all paths (distribution). out[1][0] is the histogram and
        out[1][1] are the mid points for bins. out[1][2] is a tuple with the
        average and standard deviation for the length.

    See Also
    --------
    _create_length_histograms
    """
    # first get lengths of accepted paths:
    length_acc = [path['length'] for path in path_ensemble.get_accepted()]
    length_acc = np.array(length_acc)
    length_all = []
    for path in path_ensemble.paths:
        length = _get_path_length(path)
        if length is not None:
            length_all.append(length)
    length_all = np.array(length_all)
    hist1, hist2 = _create_length_histograms(length_acc, length_all, bins)
    return hist1, hist2


def _get_path_length(path):
    """
    This is a helper function to return the path length for different
    moves.

    Parameters
    ----------
    path : dict
        This is the dict containing the information about the path, typically
        obtained by a ``for path in path_ensemble.get_paths():``.

    Returns
    -------
    out : int
        The path length
    """
    move = path['generated'][0]
    if move == 'tr':
        return 0
    elif move == 'sh':
        return path['length'] - 1
    else:
        msg = 'Ignored unknown mc move: {}'.format(move)
        warnings.warn(msg)
        return None


def _create_length_histograms(length_acc, length_all, bins):
    """
    This method will create the histograms which are the results
    from the length analysis.

    Parameters
    ----------
    length_acc : 1D numpy.array
         These are the lengths of the accepted paths
    length_all : 1D numpy.array
        These are the lengths of all paths
    bins : int
        The number of bins to use for the histograms.

    Returns
    -------
    out[0] : list, [numpy.array, numpy.array, tuple]
        Result for accepted paths (distribution). out[0][0] is the histogram
        and out[0][1] are the mid points for bins. out[0][2] is a tuple with
        the average and standard deviation for the length.
    out[1] : list, [numpy.array, numpy.array, tuple]
        Result for all paths (distribution). out[1][0] is the histogram and
        out[1][1] are the mid points for bins. out[1][2] is a tuple with the
        average and standard deviation for the length.

    See Also
    --------
    histogram in .histogram
    """
    hist1, _, bin_mid1 = histogram(length_acc, bins=bins,
                                   limits=(length_acc.min(), length_acc.max()),
                                   density=True)
    hist2, _, bin_mid2 = histogram(length_all, bins=bins,
                                   limits=(length_all.min(), length_all.max()),
                                   density=True)
    hist1 = [hist1, bin_mid1, (length_acc.mean(), length_acc.std())]
    hist2 = [hist2, bin_mid2, (length_all.mean(), length_all.std())]
    return hist1, hist2


def _shoot_analysis(path_ensemble, bins=1000):
    """
    This method will do a shoot analysis of the path ensemble.

    Parameters
    ----------
    path_ensemble : object of type ``retis.core.path.PathEnsemble``.
        This is the path ensemble we will analyse.
    bins : int, optional
        The number of bins to use for the histograms for the distribution.

    Returns
    -------
    out[0] : dict
        For each possible status ('ACC, 'BWI', etc) this dict will contain
        a histogram as returned by the histogram function.
        It will also contain a 'REJ' key which is the concatenation of all
        rejected and a 'ALL' key which is simply all the values.
    out[1] : dict
        For each possible status ('ACC, 'BWI', etc) this dict will contain
        the scale factors for the histograms. The scale factors are obtained
        by dividing with the 'ALL' value.

    See Also
    --------
    _create_shoot_histograms
    """
    shoot_stats = {'REJ': [], 'ALL': []}
    for path in path_ensemble.paths:
        _update_shoot_stats(shoot_stats, path)
    histograms, scale = _create_shoot_histograms(shoot_stats, bins)
    return histograms, scale


def _update_shoot_stats(shoot_stats, path):
    """
    This method will update the shoot_stats with the status of the
    given path.

    Parameters
    ----------
    shoot_stats : dict
        This dict contains the results from the shoot analysis, e.g.
        `shoot_stats[key]` contain the order parameters for the status
        `key` which can be the different statuses defined in
        ``retis.core.path._STATUS`` or 'REJ' (for rejected).
    path : dict
        This is the path information, represented as a dictionary.

    Returns
    -------
    N/A but it will update shoot_stats for shooting moves.
    """
    move = path['generated'][0]
    if move == 'sh':
        orderp = path['generated'][1]
        status = path['status']
        if not status in shoot_stats:
            shoot_stats[status] = []
        shoot_stats[status].append(orderp)
        if status != 'ACC':
            shoot_stats['REJ'].append(orderp)
        shoot_stats['ALL'].append(orderp)


def _create_shoot_histograms(shoot_stats, bins):
    """
    To create histograms and scale for the shoot analysis.

    Parameters
    ----------
    shoot_stats : dict
        This dict contains the results from the shoot analysis, e.g.
        `shoot_stats[key]` contain the order parameters for the status
        `key` which can be the different statuses defined in
        ``retis.core.path._STATUS`` or 'REJ' (for rejected).
    bins : int
        The number of bins to use for the histograms

    Returns
    -------
    out[0] : dict
        For each possible status ('ACC, 'BWI', etc) this dict will contain
        a histogram as returned by the histogram function.
        It will also contain a 'REJ' key which is the concatenation of all
        rejected and a 'ALL' key which is simply all the values.
    out[1] : dict
        For each possible status ('ACC, 'BWI', etc) this dict will contain
        the scale factors for the histograms. The scale factors are obtained
        by dividing with the 'ALL' value.

    See Also
    --------
    histogram in ``retis.analysis.histogram``.
    """
    histograms = {}
    scale = {}
    for key in shoot_stats:
        shoot_stats[key] = np.array(shoot_stats[key])
        mind = shoot_stats[key].min()
        maxd = shoot_stats[key].max()
        histograms[key] = histogram(shoot_stats[key], bins=bins,
                                    limits=(mind, maxd), density=True)
        scale[key] = (float(len(shoot_stats[key])) /
                      float(len(shoot_stats['ALL'])))
    return histograms, scale


def analyse_path_ensemble(path_ensemble, settings, idetect=None):
    """
    This method will make use of the different analysis functions and analyse
    a path ensemble. It will also output the results using the specified
    output object. This analysis function assumes that the given path ensemble
    is an object of type ``retis.core.path.PathEnsemble``.

    Parameters
    ----------
    path_ensemble : object of type ``retis.core.path.PathEnsemble``.
        The path ensemble to analyse.
    settings : dict
        This dictionary contains settings for the analysis.
    idetect : float, optional
        This is the interface used for detecting if a path is usccessfull
        or not. If no value is given, `path_ensemble.interfaces[-1]` will be
        assumed.

    Returns
    -------
    out : dict
        This dictionary contains the main results for the analysis which
        can be used for plotting or other kinds of output.

    See Also
    --------
    _pcross_lambda
    _running_pcross
    _pcross_error
    _get_path_distribution
    _shoot_analysis
    """
    result = {}
    if idetect is None:
        idetect = path_ensemble.interfaces[-1]
    # first analysis is pcross as a function of lambda:
    pcross, lamb = _pcross_lambda(path_ensemble,
                                  ngrid=settings['ngrid'])
    result['pcross'] = [lamb, pcross]
    # next get the running average of the crossing probability
    prun, pdata = _running_pcross(path_ensemble, idetect)
    result['prun'] = prun
    # next, the error analysis:
    error = _pcross_error(path_ensemble, idetect, data=pdata,
                          maxblock=settings['maxblock'],
                          blockskip=settings['blockskip'])
    result['blockerror'] = error
    # next length-analysis:
    hist1, hist2 = _get_path_distribution(path_ensemble,
                                          bins=settings['bins'])
    result['pathlength'] = [hist1, hist2]
    # next, shoots:
    # move so that the analysis returns histograms and scale...
    hist3, scale = _shoot_analysis(path_ensemble,
                                   bins=settings['bins'])
    result['shoots'] = [hist3, scale]
    # finally add some simple efficiency metrics:
    result['efficiency'] = [path_ensemble.get_acceptance_rate(),
                            path_ensemble.npath * hist2[2][0]]
    result['efficiency'].append(result['efficiency'][1] * error[4]**2)
    result['tis-cycles'] = path_ensemble.npath
    # retults['efficiency'] is [acceptance rate, totsim , tis-eff]
    return result


def analyse_path_ensemble_f(path_ensemble, settings,
                            idetect=None):
    """
    This method will make use of the different analysis functions and analyse
    a path ensemble. It will also output the results using the specified
    output object.

    Parameters
    ----------
    path_ensemble : object of type ``retis.core.path.PathEnsemble`` or
        ``retis.inout.txtinout.PathEnsembleFile``. This is the path ensemble
        to analyse.
    settings : dict
        This dictionary contains settings for the analysis.
    idetect : float, optional
        This is the interface used for detecting if a path is usccessfull
        or not. If no value is given, `path_ensemble.interfaces[-1]` will be
        use

    Returns
    -------
    out : dict
        This dictionary contains the main results for the analysis which
        can be used for plotting or other kinds of output.

    See Also
    --------
    _update_shoot_stats
    _pcross_lambda_cumulative
    _pcross_error
    _create_length_histograms
    _create_shoot_histograms

    References
    ----------
    .. [1] Wikipedia, "Moving Average",
           http://en.wikipedia.org/wiki/Moving_average
    """
    result = {'prun': []}
    if idetect is None:
        idetect = path_ensemble.interfaces[-1]
    orderparam = []  # list of all accepted order parameters
    weights = []
    success = 0  # determines if the current path is successfull or not
    pdata = []
    length_acc = []
    length_all = []
    shoot_stats = {'REJ': [], 'ALL': []}
    nacc = 0
    npath = 0
    for path in path_ensemble.get_paths():  # loop over all paths
        npath += 1
        if path['status'] == 'ACC':
            nacc += 1
            weights.append(1)
            orderparam.append(path['ordermax'][0])
            length_acc.append(path['length'])
            success = 1 if path['ordermax'][0] > idetect else 0
            pdata.append(success)  # Store data for block analysis
        else:  # just increase the weigths
            weights[-1] += 1
        # we also update the running average of the probability here:
        if len(result['prun']) == 0:
            result['prun'] = [success]
        else:  # update average
            result['prun'].append((success + result['prun'][-1] * (npath - 1))
                                  / float(npath))
        # get the length - note that this length depends on the type of move
        # see the _get_path_length function.
        length = _get_path_length(path)
        if length is not None:
            length_all.append(length)
        # update the shoot stats, this will only be done for shooting moves
        _update_shoot_stats(shoot_stats, path)
    # Perform the different analysis tasks:
    # 1) result['prun'] is already calculated.
    # 2) lambda pcross:
    orderparam = np.array(orderparam)
    ordermax = min(orderparam.max(), max(path_ensemble.interfaces))
    pcross, lamb = _pcross_lambda_cumulative(orderparam,
                                             path_ensemble.interfaces[1],
                                             ordermax,
                                             settings['ngrid'],
                                             weights=weights)

    result['pcross'] = [lamb, pcross]
    # 3) block error analysis:
    result['blockerror'] = _pcross_error(path_ensemble, idetect,
                                         data=np.repeat(pdata, weights),
                                         maxblock=settings['maxblock'],
                                         blockskip=settings['blockskip'])
    # 4) length analysis:
    hist1, hist2 = _create_length_histograms(np.repeat(length_acc, weights),
                                             np.array(length_all),
                                             settings['bins'])
    result['pathlength'] = [hist1, hist2]
    # 5) shoots analysis:
    hist3, scale = _create_shoot_histograms(shoot_stats,
                                            settings['bins'])
    result['shoots'] = [hist3, scale]
    # 6) Add some simple efficiency metrics:
    result['efficiency'] = [float(nacc) / float(npath),
                            float(npath) * hist2[2][0]]
    result['efficiency'].append(result['efficiency'][1] *
                                result['blockerror'][4]**2)
    result['tis-cycles'] = npath
    # retults['efficiency'] is [acceptance rate, totsim , tis-eff]
    return result


def match_probabilities(results, detect):
    """
    This method will match probabilities from several path ensembles.
    It will also calculate efficiencies and error for the matched probability.

    Parameters
    ----------
    results : list
        These are the results from the path analysis. `results[i]` is the
        output from ``analyse_path_ensemble`` when applied to ensemble i.
    detect : list of floats
        These are the detect interfaces used in the analysis.

    Returns
    -------
    out[0] : list of numpy.arrays
        out[0][i] is the matched probability for ensemble i
    out[1] : numpy.array
        Collected results, out[1][:,0] is the order parameter and
        out[1][:,1] is the probability.
    out[2] : dict
        These are results for the over-all probability and error
        and also some over-all TIS efficiencies.
    """
    accprob = 1.0
    accprob_err = 0.0
    prob_simtime = 0.0
    prob_opt_eff = 0.0
    all_prob = []
    matched_prob = [[], []]
    for idet, result in zip(detect, results):
        idx = np.where(result['pcross'][0] <= idet)[0]
        matched_prob[0].extend(result['pcross'][0][idx])
        matched_prob[1].extend(result['pcross'][1][idx] * accprob)
        all_prob.append(result['pcross'][1] * accprob)
        accprob *= result['prun'][-1]
        accprob_err += result['blockerror'][4]**2
        prob_simtime += result['efficiency'][1]
        prob_opt_eff += np.sqrt(result['efficiency'][2])
    matched_prob = np.transpose(np.array(matched_prob))
    prob_eff = accprob_err * prob_simtime
    accprob_err = np.sqrt(accprob_err)
    prob_opt_eff *= prob_opt_eff
    # gather the other results into one dict
    other = {'prob': accprob,  # over-all probability
             'relerror': accprob_err,  # error in probability
             'simtime': prob_simtime,  # simulation time: cycles * path-lenght
             'opteff': prob_opt_eff,  # optimized TIS efficiency
             'eff': prob_eff  # over-all TIS efficiency
            }
    return all_prob, matched_prob, other
