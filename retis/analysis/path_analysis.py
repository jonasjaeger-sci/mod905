# -*- coding: utf-8 -*-
"""
This file contains methods for analysis of path ensembles as defined
in the object PathEnsemble in retis.core.path
"""
from __future__ import absolute_import
import numpy as np
from .analysis import running_average


__all__ = ['running_pcross', 'pcross_lambda']


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
    lamb = np.linspace(ordermin, ordermax, ngrid)
    pcross = np.zeros(ngrid)
    delta_l = lamb[1] - lamb[0]
    sumw = 0.0
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
