# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Methods for analysis of path ensembles.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

analyse_path_ensemble (:py:func:`.analyse_path_ensemble`)
    Method to analyse a path ensemble, it will calculate crossing
    probabilities and information about moves etc. This method
    can be applied to files as well as path ensemble objects.

analyse_path_ensemble_object (:py:func:`.analyse_path_ensemble_object`)
    Method to analyse a path ensemble, it will calculate crossing
    probabilities and information about moves etc. This method is
    intended to work directly on path ensemble objects.

match_probabilities (:py:func:`.match_probabilities`)
    Match probabilities from several path ensembles and calculate
    efficiencies and the error for the matched probability.

retis_flux (:py:func:`.retis_flux`)
    Calculate the initial flux with errors for a RETIS simulation.

retis_rate (:py:func:`.retis_rate`)
    Calculate the rate constant with errors for a RETIS simulation.
"""
from __future__ import absolute_import
import logging
import numpy as np
from pyretis.analysis.analysis import running_average, block_error_corr
from pyretis.analysis.histogram import histogram, histogram_and_avg
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['analyse_path_ensemble', 'analyse_path_ensemble_object',
           'match_probabilities', 'retis_flux', 'retis_rate']


def _get_successful(path_ensemble, idetect):
    """Build the data of accepted (successful) paths.

    In the `PathEnsemble` object all paths are stored, both accepted and
    rejected and the `PathEnsemble.get_accepted()` is used here to
    iterate over accepted paths. Successful paths are defined as paths
    which are able to reach the interface specified with `idetect`. For
    each accepted path, this function will give a value of `1` if the
    path was successful and `0` otherwise.

    Parameters
    ----------
    path_ensemble : object :py:class:`.PathEnsemble`
        This is the path ensemble we will analyse.
    idetect : float
        This is the interface used for detecting if a path is successful
        or not.

    Returns
    -------
    out : numpy.array
        ``out[i] = 1`` if path no. `i` is successful 0 otherwise.
    """
    data = []
    for path in path_ensemble.get_accepted():
        value = 1 if path['ordermax'][0] > idetect else 0
        data.append(value)
    data = np.array(data)
    return data


def _running_pcross(path_ensemble, idetect, data=None):
    """Create a running average of the crossing probability.

    The running average is created as a function of the cycle number.
    Note that the accepted paths are used to create an array which is
    then averaged. This could possibly be replaced by a simple
    'on-the-fly' calculation of the running average,
    as detailed in: http://en.wikipedia.org/wiki/Moving_average

    Parameters
    ----------
    path_ensemble : object like :py:class:`.PathEnsemble`
        This is the path ensemble we will analyse.
    idetect : float
        This is the interface used for detecting if a path is successful
        or not.
    data : numpy.array
        This is the data created by `_get_successful(path_ensemble)`
        If this function has been executed, the result can be re-used
        here by specifying data. If not, it will be generated.

    Returns
    -------
    out[0] : numpy.array
        The running average of the crossing probability
    out[1] : numpy.array
        The original data, can be further put to use in the other
        analysis functions.

    See Also
    --------
    `_get_successful`
    """
    if data is None:
        data = _get_successful(path_ensemble, idetect)
    return running_average(data), data


def _pcross_lambda(path_ensemble, ngrid=1000):
    """Calculate crossing probability for an ensemble.

    The crossing probability is here obtained as a function of the order
    parameter. The actual calculation is performed by
    `_pcross_lambda_cumulative` and this function is just a wrapper in
    order to handle input objects like :py:class:`.PathEnsemble`.

    Parameters
    ----------
    path_ensemble : object like :py:class:`.PathEnsemble`
        This is the path ensemble we will analyse.
    ngrid : int
        This is the number of grid points.

    Returns
    -------
    out[0] : numpy.array
        The crossing probability.
    out[1] : numpy.array
        The order parameters.

    See Also
    --------
    `_pcross_lambda_cumulative`

    Notes
    -----
    This routine could perhaps be made shorter by making use of
    `numpy.digitize` etc.
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
    """Obtain crossing probability as a function of the order parameter.

    It will do the actual calculation of the crossing probability as
    a function of order parameter. It is split off from `pcross_lambda`
    since the analysis is intended to be backwards compatible with the
    output/results from the old ``TISMOL FORTRAN`` program.

    Parameters
    ----------
    orderparam : numpy.array
        Array containing the order parameters.
    ordermin : float
        Minimum allowed order parameter.
    ordermax : float
        Maximum allowed order parameter.
    ngrid : int
        This is the number of grid points.
    weights : numpy.array, optional
        The weight of each order parameter. This is used in order to
        count a specific order parameter more than once. If not given,
        the values in `orderparam` will be weighted equally.
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


def _get_path_distribution(path_ensemble, bins=1000):
    """Calculate the distribution of path lengths.

    Parameters
    ----------
    path_ensemble : object like :py:class:`.PathEnsemble`
        This is the path ensemble we will analyse.
    bins : int, optional
        The number of bins to use for the histograms for the
        distribution.

    Returns
    -------
    out[0] : list, [numpy.array, numpy.array, tuple]
        Result for accepted paths (distribution). `out[0][0]` is the
        histogram and `out[0][1]` are the mid points for bins.
        `out[0][2]` is a tuple with the average and standard deviation
        for the length.
    out[1] : list, [numpy.array, numpy.array, tuple]
        Result for all paths (distribution). `out[1][0]` is the
        histogram and `out[1][1]` are the mid points for bins.
        `out[1][2]` is a tuple with the average and standard deviation
        for the length.
    out[2] : numpy.array
        The length of the accepted paths, in case we want to analyse it
        further.

    See Also
    --------
    `histogram_and_avg` in .histogram
    """
    # first get lengths of accepted paths:
    length_acc = [path['length'] for path in path_ensemble.get_accepted()]
    length_acc = np.array(length_acc)
    length_all = []
    for path in path_ensemble.paths:
        length = _get_path_length(path, path_ensemble.ensemble)
        if length is not None:
            length_all.append(length)
    length_all = np.array(length_all)
    hist_acc = histogram_and_avg(length_acc, bins, density=True)
    hist_all = histogram_and_avg(length_all, bins, density=True)
    return hist_acc, hist_all, length_acc


def _get_path_length(path, ensemble):
    """Return the path length for different moves.

    Different moves may have a different way of obtaining the path
    length. (Example: time-reversal vs. shooting move).

    Parameters
    ----------
    path : dict
        This is the dict containing the information about the path.
        It can typically be obtained by iterating over the path
        ensemble object, e.g. with a
        `for path in path_ensemble.get_paths():`.
    ensemble : int
        This integer identifies the ensemble. This is used for
        the swapping moves in [0^-] and [0^+].

    Returns
    -------
    out : int
        The path length
    """
    move = path['generated'][0]
    return_table = {'tr': 0, 's+': 0, 's-': 0, '00': 0}
    if move in return_table:
        if move == 's+' and ensemble == 0:
            return path['length'] - 2
        elif move == 's-' and ensemble == 1:
            return path['length'] - 2
        else:
            return return_table[move]
    else:
        if move == 'sh':
            return path['length'] - 1
        elif move == 'ki':
            msg = 'Skipped initial path: {}'.format(move)
            logger.info(msg)
            return None
        else:
            msg = 'Skipped unknown mc move: {}'.format(move)
            logger.warning(msg)
            return None


def _shoot_analysis(path_ensemble, bins=1000):
    """Analyse the shooting performed in the path ensemble.

    Parameters
    ----------
    path_ensemble : object like :py:class:`.PathEnsemble`
        This is the path ensemble we will analyse.
    bins : int, optional
        The number of bins to use for the histograms for the
        distribution.

    Returns
    -------
    out[0] : dict
        For each possible status ('ACC, 'BWI', etc) this dict will
        contain a histogram as returned by the histogram function.
        It will also contain a 'REJ' key which is the concatenation
        of all rejections and a 'ALL' key which is simply all the
        values.
    out[1] : dict
        For each possible status ('ACC, 'BWI', etc) this dict will
        contain the scale factors for the histograms. The scale
        factors are obtained by dividing with the 'ALL' value.

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
    """Update the shooting statistics with the status of the given path.

    Parameters
    ----------
    shoot_stats : dict
        This dict contains the results from the shoot analysis, e.g.
        `shoot_stats[key]` contain the order parameters for the status
        `key` which can be the different statuses defined in
        `pyretis.core.path._STATUS` or 'REJ' (for rejected).
    path : dict
        This is the path information, represented as a dictionary.

    Returns
    -------
    out : None
        Returns `None` but will update `shoot_stats` for shooting moves.
    """
    move = path['generated'][0]
    if move == 'sh':
        orderp = path['generated'][1]
        status = path['status']
        if status not in shoot_stats:
            shoot_stats[status] = []
        shoot_stats[status].append(orderp)
        if status != 'ACC':
            shoot_stats['REJ'].append(orderp)
        shoot_stats['ALL'].append(orderp)


def _create_shoot_histograms(shoot_stats, bins):
    """Create histograms and scale for the shoot analysis.

    Parameters
    ----------
    shoot_stats : dict
        This dict contains the results from the shoot analysis, e.g.
        `shoot_stats[key]` contain the order parameters for the status
        `key` which can be the different statuses defined in
        `pyretis.core.path._STATUS` or 'REJ' (for rejected).
    bins : int
        The number of bins to use for the histograms.

    Returns
    -------
    out[0] : dict
        For each possible status ('ACC, 'BWI', etc) this dict will
        contain a histogram as returned by the histogram function.
        It will also contain a 'REJ' key which is the concatenation of
        all rejections and a 'ALL' key which is simply all the values.
    out[1] : dict
        For each possible status ('ACC, 'BWI', etc) this dict will
        contain the scale factors for the histograms. The scale factors
        are obtained by dividing with the 'ALL' value.

    See Also
    --------
    `histogram` in `pyretis.analysis.histogram`.
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


def analyse_path_ensemble_object(path_ensemble, settings):
    """Analyse a path ensemble object.

    This function will make use of the different analysis functions and
    analyse a path ensemble. This analysis function assumes that the
    given path ensemble is an object like :py:class:`.PathEnsemble`
    and that this path ensemble contains all the paths that are needed.

    Parameters
    ----------
    path_ensemble : object like :py:class:`.PathEnsemble`
        The path ensemble to analyse.
    settings : dict
        This dictionary contains settings for the analysis.
        Here we make use of the following keys from the
        analysis section:

        * `ngrid`: The number of grid points for calculating the
          crossing probability as a function of the order parameter.
        * `maxblock`: The max length of the blocks for the block error
          analysis. Note that this will maximum be equal the half the
          length of the data, see `block_error` in `.analysis`.
        * `blockskip`: Can be used to skip certain block lengths.
          A `blockskip` equal to `n` will consider every n'th block up
          to `maxblock`, i.e. it will use block lengths equal to `1`,
          `1+n`, `1+2n`, etc.
        * `bins`: The number of bins to use for creating histograms.

    Returns
    -------
    out : dict
        This dictionary contains the main results for the analysis
        which can be used for plotting or other kinds of output.

    See Also
    --------
    `_pcross_lambda`, `_running_pcross`, `_get_path_distribution` and
    `_shoot_analysis`.
    """
    result = {}
    analysis = settings['analysis']
    if path_ensemble.nstats['npath'] != len(path_ensemble.paths):
        msg = ' '.join(['The number of paths stored in path ensemble does not',
                        'correspond to the number of paths seen by the path',
                        'ensemble! Consider re-running the analysis using',
                        'the path ensemble file!'])
        logger.warning(msg)
    # first analysis is pcross as a function of lambda:
    pcross, lamb = _pcross_lambda(path_ensemble,
                                  ngrid=analysis['ngrid'])
    result['pcross'] = [lamb, pcross]
    # next get the running average of the crossing probability
    prun, pdata = _running_pcross(path_ensemble, path_ensemble.detect)
    result['prun'] = prun
    try:
        result['cycle'] = np.array([path['cycle'] for path in path_ensemble])
    except KeyError:
        msg = 'Could not obtain cycle number! Will assume (1, 2, ..., len(p))'
        logger.warning(msg)
        result['cycle'] = np.arange(len(prun))
    # next, the error analysis:
    result['blockerror'] = block_error_corr(pdata,
                                            maxblock=analysis['maxblock'],
                                            blockskip=analysis['blockskip'])

    # next length-analysis:
    hist1, hist2, _ = _get_path_distribution(path_ensemble,
                                             bins=analysis['bins'])
    result['pathlength'] = (hist1, hist2)
    # next, shoots:
    # move so that the analysis returns histograms and scale...
    hist3, scale = _shoot_analysis(path_ensemble,
                                   bins=analysis['bins'])
    result['shoots'] = [hist3, scale]
    # finally add some simple efficiency metrics:
    result['efficiency'] = [path_ensemble.get_acceptance_rate(),
                            path_ensemble.nstats['npath'] * hist2[2][0]]
    result['efficiency'].append(result['efficiency'][1] *
                                result['blockerror'][4]**2)
    result['tis-cycles'] = path_ensemble.nstats['npath']
    # retults['efficiency'] is [acceptance rate, totsim , tis-eff]
    return result


def analyse_path_ensemble(path_ensemble, settings):
    """Analyse a path ensemble.

    This function will make use of the different analysis functions and
    analyse a path ensemble. This function is more general than the
    `analyse_path_ensemble_object` function in that it should work on
    both `PathEnsemble` and `PathEnsembleFile` objects. The running
    average is updated on-the-fly, see Wikipedia for
    details [wikimov]_.

    Parameters
    ----------
    path_ensemble : object like :py:class:`.PathEnsemble`
        This is the path ensemble to analyse.
    settings : dict
        This dictionary contains settings for the analysis.
        We make use of the following keys:

        * `ngrid`: The number of grid points for calculating the
          crossing probability as a function of the order parameter.
        * `maxblock`: The max length of the blocks for the block error
          analysis. Note that this will maximum be equal the half the
          length of the data, see `block_error` in `.analysis`.
        * `blockskip`: Can be used to skip certain block lengths.
          A `blockskip` equal to `n` will consider every n'th block up
          to `maxblock`, i.e. it will use block lengths equal to `1`,
          `1+n`, `1+2n`, etc.
        * `bins`: The number of bins to use for creating histograms.

    Returns
    -------
    out : dict
        This dictionary contains the main results for the analysis which
        can be used for plotting or other kinds of output.

    See Also
    --------
    `_update_shoot_stats`, `pcross_lambda_cumulative` and
    `_create_shoot_histograms`

    References
    ----------
    .. [wikimov] Wikipedia, "Moving Average",
       http://en.wikipedia.org/wiki/Moving_average
    """
    detect = path_ensemble.detect
    if path_ensemble.ensemble == 0:
        return analyse_path_ensemble0(path_ensemble, settings)
    ensemble = path_ensemble.ensemble
    result = {'prun': [],
              'cycle': [],
              'detect': detect,
              'ensemble': path_ensemble.ensemble_name,
              'ensembleid': ensemble,
              'interfaces': [i for i in path_ensemble.interfaces]}
    orderparam = []  # list of all accepted order parameters
    weights = []
    success = 0  # determines if the current path is successful or not
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
            success = 1 if path['ordermax'][0] > detect else 0
            pdata.append(success)  # Store data for block analysis
        else:  # just increase the weigths
            weights[-1] += 1
        # we also update the running average of the probability here:
        if len(result['prun']) == 0:
            result['prun'] = [success]
        else:  # update average
            result['prun'].append(float(success +
                                        result['prun'][-1] * (npath - 1)) /
                                  float(npath))
        result['cycle'].append(path['cycle'])
        # get the length - note that this length depends on the type of move
        # see the `_get_path_length` function.
        length = _get_path_length(path, ensemble)
        if length is not None:
            length_all.append(length)
        # update the shoot stats, this will only be done for shooting moves
        _update_shoot_stats(shoot_stats, path)
    # Perform the different analysis tasks:
    # 1) result['prun'] is already calculated.
    result['cycle'] = np.array(result['cycle'])
    result['prun'] = np.array(result['prun'])
    # 2) lambda pcross:
    analysis = settings['analysis']
    orderparam = np.array(orderparam)
    ordermax = min(orderparam.max(), max(path_ensemble.interfaces))
    pcross, lamb = _pcross_lambda_cumulative(orderparam,
                                             path_ensemble.interfaces[1],
                                             ordermax,
                                             analysis['ngrid'],
                                             weights=weights)

    result['pcross'] = [lamb, pcross]
    # 3) block error analysis:
    result['blockerror'] = block_error_corr(data=np.repeat(pdata, weights),
                                            maxblock=analysis['maxblock'],
                                            blockskip=analysis['blockskip'])
    # 4) length analysis:
    hist1 = histogram_and_avg(np.repeat(length_acc, weights),
                              analysis['bins'], density=True)
    hist2 = histogram_and_avg(np.array(length_all),
                              analysis['bins'], density=True)
    result['pathlength'] = (hist1, hist2)
    # 5) shoots analysis:
    result['shoots'] = _create_shoot_histograms(shoot_stats,
                                                analysis['bins'])
    # 6) Add some simple efficiency metrics:
    result['efficiency'] = [float(nacc) / float(npath),
                            float(npath) * hist2[2][0]]
    result['efficiency'].append(result['efficiency'][1] *
                                result['blockerror'][4]**2)
    result['tis-cycles'] = npath
    # extra analysis for the [0^+] ensemble in case we will determine
    # the initial flux:
    if ensemble == 1:
        lengtherr = block_error_corr(data=np.repeat(length_acc,
                                                    weights),
                                     maxblock=analysis['maxblock'],
                                     blockskip=analysis['blockskip'])
        result['lengtherror'] = lengtherr
        lenge2 = result['lengtherror'][4] * hist1[2][0] / (hist1[2][0]-2.)
        result['fluxlength'] = [hist1[2][0]-2.0, lenge2,
                                lenge2 * (hist1[2][0]-2.)]
        result['fluxlength'].append(result['efficiency'][1] * lenge2**2)
    # retults['efficiency'] is [acceptance rate, totsim , tis-eff]
    return result


def analyse_path_ensemble0(path_ensemble, settings):
    """Analyse the [0^-] ensemble.

    Parameters
    ----------
    path_ensemble : object like :py:class:`.PathEnsemble`
        This is the path ensemble to analyse.
    settings : dict
        This dictionary contains settings for the analysis.
        We make use of the following keys:

        * `ngrid`: The number of grid points for calculating the
          crossing probability as a function of the order parameter.
        * `maxblock`: The max length of the blocks for the block error
          analysis. Note that this will maximum be equal the half the
          length of the data, see `block_error` in `.analysis`.
        * `blockskip`: Can be used to skip certain block lengths.
          A `blockskip` equal to `n` will consider every n'th block up
          to `maxblock`, i.e. it will use block lengths equal to `1`,
          `1+n`, `1+2n`, etc.
        * `bins`: The number of bins to use for creating histograms.

    Returns
    -------
    result : dict
        The results from the analysis on this ensemble.
    """
    detect = path_ensemble.detect
    ensemble = path_ensemble.ensemble
    result = {'cycle': [],
              'detect': detect,
              'ensemble': path_ensemble.ensemble_name,
              'ensembleid': ensemble,
              'interfaces': [i for i in path_ensemble.interfaces]}
    length_acc, length_all, weights = [], [], []
    shoot_stats = {'REJ': [], 'ALL': []}
    nacc, npath = 0, 0
    for path in path_ensemble.get_paths():  # loop over all paths
        npath += 1
        if path['status'] == 'ACC':
            nacc += 1
            weights.append(1)
            length_acc.append(path['length'])
        else:  # just increase the weigths
            weights[-1] += 1
        result['cycle'].append(path['cycle'])
        length = _get_path_length(path, ensemble)
        if length is not None:
            length_all.append(length)
        # update the shoot stats, this will only be done for shooting moves
        _update_shoot_stats(shoot_stats, path)
    # Perform the different analysis tasks:
    analysis = settings['analysis']
    result['cycle'] = np.array(result['cycle'])
    # 1) length analysis:
    hist1 = histogram_and_avg(np.repeat(length_acc, weights),
                              analysis['bins'], density=True)
    hist2 = histogram_and_avg(np.array(length_all),
                              analysis['bins'], density=True)
    result['pathlength'] = (hist1, hist2)
    # 2) block error of lengths:
    result['lengtherror'] = block_error_corr(data=np.repeat(length_acc,
                                                            weights),
                                             maxblock=analysis['maxblock'],
                                             blockskip=analysis['blockskip'])
    # 3) shoots analysis:
    result['shoots'] = _create_shoot_histograms(shoot_stats,
                                                analysis['bins'])
    # 4) Add some simple efficiency metrics:
    result['efficiency'] = [float(nacc) / float(npath),
                            float(npath) * hist2[2][0]]
    result['efficiency'].append(result['efficiency'][1] *
                                result['lengtherror'][4]**2)
    lenge2 = result['lengtherror'][4] * hist1[2][0] / (hist1[2][0]-2.)
    result['fluxlength'] = [hist1[2][0]-2.0, lenge2, lenge2 * (hist1[2][0]-2.)]
    result['fluxlength'].append(result['efficiency'][1] * lenge2**2)
    result['tis-cycles'] = npath
    return result


def match_probabilities(path_results, detect):
    """Match probabilities from several path ensembles.

    It will also calculate efficiencies and error for the matched
    probability.

    Parameters
    ----------
    path_results : list
        These are the results from the path analysis. `path_results[i]`
        contains the output from `analyse_path_ensemble` applied to
        ensemble no. `i`. Here we make use of the following keys from
        `path_results[i]`:

        * `pcross`: The crossing probability.
        * `prun`: The running average of the crossing probability.
        * `blockerror`: The output from the block error analysis.
        * `efficiency`: The output from the efficiency analysis.
    detect : list of floats
        These are the detect interfaces used in the analysis.

    Returns
    -------
    results : dict
        These are results for the over-all probability and error
        and also some over-all TIS efficiencies.
    """
    results = {'matched-prob': [],
               'overall-prob': [[], []]}
    accprob = 1.0
    accprob_err = 0.0
    prob_simtime = 0.0
    prob_opt_eff = 0.0
    for idet, result in zip(detect, path_results):
        # do matching only in part left of idetect:
        idx = np.where(result['pcross'][0] <= idet)[0]
        results['overall-prob'][0].extend(result['pcross'][0][idx])
        results['overall-prob'][1].extend(result['pcross'][1][idx] * accprob)
        # update probabilities, error and efficiency:
        mat = np.column_stack((result['pcross'][0], result['pcross'][1]))
        mat[:, 1] *= accprob
        results['matched-prob'].append(mat)
        accprob *= result['prun'][-1]
        accprob_err += result['blockerror'][4]**2
        prob_simtime += result['efficiency'][1]
        prob_opt_eff += np.sqrt(result['efficiency'][2])
    results['overall-prob'] = np.transpose(results['overall-prob'])
    results['prob'] = accprob
    results['relerror'] = np.sqrt(accprob_err)
    results['simtime'] = prob_simtime  # simulation time: cycles * path-lenght
    results['opteff'] = prob_opt_eff**2  # optimized TIS efficiency
    results['eff'] = accprob_err * prob_simtime  # over-all TIS efficiency
    return results


def retis_flux(results0, results1, timestep):
    """Method to calculate the initial flux for RETIS.

    Parameters
    ----------
    results0 : dict
        Results from the analysis of ensemble [0^-]
    results1 : dict
        Results from the analysis of ensemble [0^+]

    Returns
    -------
    flux : float
        The initial flux.
    flux_error : float
        The relative error in the initial flux.
    """
    flux0 = results0['out']['fluxlength']
    flux1 = results1['out']['fluxlength']
    tsum = flux0[0] + flux1[0]
    flux = 1.0 / (tsum * timestep)
    flux_error = (np.sqrt((flux0[1]*flux0[0])**2 + (flux1[1]*flux1[0])**2) /
                  tsum)
    return flux, flux_error


def retis_rate(pcross, pcross_relerror, flux, flux_relerror):
    """Method to calculate the rate constant for RETIS.

    Parameters
    ----------
    pcross : float
        Estimated crossing probability
    pcross_relerror : float
        Relative error in crossing probability.
    flux : float
        The initial flux.
    flux_relerror : float
        Relative error in the initial flux.

    Returns
    -------
    rate : float
        The rate constant
    rate_error : float
        The relative error in the rate constant.
    """
    rate = pcross * flux
    rate_error = np.sqrt(pcross_relerror**2 + flux_relerror**2)
    return rate, rate_error
