# -*- coding: utf-8 -*-
"""
This file contains methods for analysis of path ensembles as defined
in the object PathEnsemble in retis.core.path
"""
from __future__ import absolute_import
import numpy as np
from .analysis import running_average, block_error


__all__ = ['running_pcross', 'pcross_lambda', 'pcross_error',
           'get_path_distribution']


def _get_successfull(pathensemble):
    """
    This is a helper function to build the data of accepted paths.
    In the PathEmsemble object, accepted paths are store as a list of
    lists: [[path_id, accepted_number_of_times], ...] which just stores
    the id of the path and how many times it was accepted. This function
    will create a flattened version with 1 if the path is successfull and
    0 if it's not. This is then repeated accepted_number_of_times.

    Parameters
    ----------
    pathensemble : object of type retis.core.path.PathEnsemble
        This is the PathEnsemble we will analyse

    Returns
    -------
    out : numpy.array
        These are the values giving if paths are successfull or not.
    """
    data = []
    for (pathid, reps) in pathensemble.accepted:
        value = 1 if pathensemble.path_data['success'][pathid] else 0
        data += reps * [value]
    return np.array(data)


def running_pcross(pathensemble, data=None):
    """
    Function to create a running average of the crossing probability
    as function of the cycle number. Note that the accepted paths are used
    to create an array which is then averaged. This could possibly
    be replaced by a simple on-the-fly calculation of the running average,
    as detailed in: http://en.wikipedia.org/wiki/Moving_average

    Parameters
    ----------
    pathensemble : object of type retis.core.path.PathEnsemble
        This is the PathEnsemble we will analyse
    data : numpy.array
        This is the data created by _get_successfull(pathensemble)
        If this function has been executed, the result can be re-used here
        by specifying data. If not, it will be generated

    Returns
    -------
    out : numpy.array
        The running average of the crossing probability
    """
    if data is None:
        data = _get_successfull(pathensemble)
    return running_average(data)


def pcross_lambda(pathensemble, ngrid=1000):
    """
    This function will calculate the crossing probability for an ensemble as
    a function of the value of the order parameter.

    Parameters
    ----------
    pathensemble : object of type retis.core.path.PathEnsemble
        This is the PathEnsemble we will analyse
    ngrid : int
        This is the number of grid points

    Returns
    -------
    out[0] : numpy.array
        The crossing probability
    out[1] : numpy.array
        The order parameters

    Note
    ----
    This routine could perhaps be made shorter by making use of
    numpy.digitize etc.
    """
    # first, get the boundaries and order parameters of the
    # accepted paths
    orderparam = []
    weights = []
    ordermax = None
    for (pathid, reps) in pathensemble.accepted:
        orderp = pathensemble.path_data['ordermax'][pathid][0]
        if ordermax is None or orderp > ordermax:
            ordermax = orderp
        orderparam.append(orderp)
        weights.append(reps)
    # next create the ``cumulative histogram'':
    ordermax = min(ordermax, max(pathensemble.interfaces))
    ordermin = pathensemble.interfaces[1]
    pcross, lamb = _pcross_lambda_cumulative(orderparam, ordermin, ordermax,
                                             ngrid, weights=weights)
    return pcross, lamb


def _pcross_lambda_cumulative(orderparam, ordermin, ordermax, ngrid,
                              weights=None):
    """
    This is a helper function for pcross_lambda, it will do the actual
    calculation of the crossing probability as a function of order parameter.

    It is split of from pcross_lambda in case the same analysis is to
    be done for something different from a path ensemble, for instance
    the results from the old tismol program.

    Parameters
    ----------
    orderparam : numpy.array
        Array with the order parameters
    ordermin : float
        Minimum allowed order parameter
    ordermax : float
        Maximum allowed order parameter
    ngrid : int
        This is the number of grid points
    weights : numpy.array, optional
        The weight of each order parameter. This is used in order to
        count a specific order parameter more than once.
        If it's not given, then all order parameters will be weights equally.
    """
    lamb = np.linspace(ordermin, ordermax, ngrid)
    pcross = np.zeros(ngrid)
    delta_l = lamb[1] - lamb[0]
    sumw = 0.0
    if weights is None:
        weights = np.ones(orderparam.shape)
    for orderp, weight in zip(orderparam, weights):
        idx = int((orderp - ordermin) / delta_l)
        if idx >= ngrid:
            idx = ngrid
        sumw += weight
        if idx >= ngrid:
            idx = ngrid - 1
        if 0 <= idx < ngrid:
            pcross[:idx+1] += weight
    pcross /= sumw  # normalization
    return pcross, lamb


def pcross_error(pathensemble, maxblock=5000, blockskip=1, data=None):
    """
    This function will run the block error analysis for the
    path ensemble.

    Parameters
    ----------
    pathensemble : object of type retis.core.path.PathEnsemble
        This is the PathEnsemble we will analyse
    maxblock : int
        The maximum block length to consider
    blockskip = int
        Intervall between blocks. Blocks are created as 1, 1+blockskip, ...
        up to maxblock.
    data : numpy.array
        This is the data created by _get_successfull(pathensemble)
        If this function has been executed, the result can be re-used here
        by specifying data. If not, it will be generated
    """
    if data is None:
        data = _get_successfull(pathensemble)

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


def get_path_distribution(pathensemble):
    """
    This function will get the distribution of path-lengths for the
    successful paths
    """
    # first get lengths of successfull:
    lengths = []
    for (pathid, reps) in pathensemble.accepted:
        length = pathensemble.path_data['length'][pathid]
        lengths.extend([length]*reps)

    lengths2 = []
    for mc_move, length in zip(pathensemble.path_data['generated'],
                               pathensemble.path_data['length']):
        if mc_move == 'tr':
            lengths2.append(0)
        elif mc_move == 'sh':
            lengths2.append(length-1)
        else:
            raise ValueError('Unknown mc move')
    print len(lengths), len(lengths2)
    return np.array(lengths), np.array(lengths2)
