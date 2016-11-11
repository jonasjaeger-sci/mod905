# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""Module defining functions useful in analysis of simulation data.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

running_average
    Method to calculate a running average.

block_error
    Perform block error analysis.

block_error_corr
    Method to run a block error analysis and calculate relative
    errors and correlation length.
"""
import numpy as np
from pyretis.analysis.histogram import histogram_and_avg

__all__ = ['running_average', 'block_error',
           'block_error_corr']


def running_average(data):
    """Function to create a running average of the given data.

    The running average will be calculated over the rows.

    Parameters
    ----------
    data : numpy.array
        This is the data we will average.

    Returns
    -------
    out : numpy.array
        The running average.
    """
    one = np.ones(np.shape(data))
    return data.cumsum(axis=0) / one.cumsum(axis=0)


def _chunks(itera, size):
    """Yield successive same-sized chunks from `itera`.

    Parameters
    ----------
    itera : iterable
        This is the iterable we will return chunks of.
    size : int
        The size of the chunks.

    Yields
    ------
    out : object like `itera`
        The successive same-sized chunks from `itera`-

    Notes
    -----
    We are here using `range` rather than `xrange`. This is just to ease
    the transition from python2 to python3. Note that this will probably
    lead to some inefficiencies for python2 execution. The code is based
    on one question at Stackoverflow [chunks]_.

    References
    ----------
    .. [chunks] Stackoverflow, "How do you split ...",
       http://stackoverflow.com/a/312464
    """
    for i in range(0, len(itera), size):
        yield itera[i:i+size]


def block_error(data, maxblock=None, blockskip=1):
    """Perform block error analysis.

    This function will estimate the standard deviation in the input
    data by performing a block analysis. The number of blocks
    to consider can be specified or it will be taken as the
    half of the length of the input data. Averages and variance are
    calculated using a on-the-fly algorithm [1]_.

    Parameters
    ----------
    data : numpy.array (or iterable with data points)
        The data to analyse.
    maxblock : int, optional
        Can be used to set the maximum length of the blocks to
        consider. Note that the `maxbloc` will never be set longer
        than half the length in data.
    blockskip : int, optional
        This can be used to skip certain block lengths, i.e.
        `blockskip = 1` will consider all blocks up to `maxblock`, while
        `blockskip = n` will consider every n'th block up to `maxblock`,
        i.e. it will use block lengths equal to `1`, `1 + n`, `1 + 2*n`,
        and so on.

    Returns
    -------
    blocklen : numpy.array
        These contains the block lengths considered.
    block_avg : numpy.array
        The averages as function of block length.
    block_err : numpy.array
        Estimate of errors as function of block length.
    block_err_avg : float
        Average of the error estimate using blocks where
        ``length > maxblock//2``.

    References
    ----------

    .. [1] Wikipedia, "Algorithms for calculating variance",
       http://en.wikipedia.org/wiki/Algorithms_for_calculating_variance
    """
    if maxblock is None:
        maxblock = len(data) // 2
    else:
        maxblock = min(maxblock, len(data) // 2)
    # define helper variables:
    blocklen = np.arange(0, maxblock, blockskip, dtype=np.int_)
    # blocklen contains the lengths of the blocks
    blocklen += 1
    # +1 to make blocklen[i] = length of block no i where numbering
    # starts at 0 -> blocklen[0] = 1 and so on. Note that arange does
    # create [0, ..., maxblock).
    block = np.zeros(len(blocklen))  # to accumulate values for a block
    nblock = np.zeros(block.shape)  # to count number of whole blocks
    block_avg = np.zeros(block.shape)  # to store averages in block
    block_var = np.zeros(block.shape)  # estimator of variance

    for i, datai in enumerate(data):
        block += datai  # accumulate the value to all blocks
        # next pick out blocks which are "full":
        k = np.where((i + 1) % blocklen == 0)[0]
        # update estimate of average and variance
        block[k] = block[k] / blocklen[k]
        nblock[k] += 1
        deltas = block[k] - block_avg[k]
        block_avg[k] = block_avg[k] + deltas / nblock[k]
        block_var[k] = block_var[k] + deltas * (block[k] - block_avg[k])
        # reset these blocks
        block[k] = 0.0
    block_var = block_var / (nblock - 1)
    block_err = np.sqrt(block_var / nblock)  # estimate of error
    k = np.where(blocklen > maxblock // 2)[0]
    block_err_avg = np.average(block_err[k])
    return blocklen, block_avg, block_err, block_err_avg


def block_error_corr(data, maxblock=None, blockskip=1):
    """Run block error analysis on the given data.

    This will run the block error analysis and return relative
    errors and the correlation length.

    Parameters
    ----------
    data : numpy.array
        Data to analyse.
    maxblock : int, optional
        The maximum block length to consider.
    blockskip : int, optional
        This can be used to skip certain block lengths, i.e.
        `blockskip = 1` will consider all blocks up to `maxblock`, while
        `blockskip = n` will consider every n'th block up to `maxblock`,
        i.e. it will use block lengths equal to `1`, `1 + n`, `1 + 2*n`,
        and so on.

    Returns
    -------
    out[0] : numpy.array, `blen`.
        These contains the block lengths considered.
    out[1] : numpy.array, `berr`.
        Estimate of errors as function of block length.
    out[2] : float, `berr_avg`.
        Average of the error estimate for blocks
        with ``length > maxblock // 2``.
    out[3] : numpy.array, `rel_err`.
        Estimate of relative errors (normalised by the overall average)
        as a function of block length.
    out[4] : float, `avg_rel_err`.
        The average relative error, for blocks
        with ``length > maxblock // 2``.
    out[5] : numpy.array, `ncor`.
        The estimated correlation length as a function of block length.
    out[6] : float, `avg_ncor`.
        The average (for blocks with length > maxblock // 2) estimated
        correlation length.
    """
    blen, bavg, berr, berr_avg = block_error(data, maxblock=maxblock,
                                             blockskip=blockskip)
    # also calculate some relative errors:
    rel_err = np.divide(berr, abs(bavg[0]))
    avg_rel_err = np.divide(berr_avg, abs(bavg[0]))
    ncor = np.divide(berr**2, berr[0]**2)
    avg_ncor = np.divide(berr_avg**2, berr[0]**2)
    return blen, berr, berr_avg, rel_err, avg_rel_err, ncor, avg_ncor


def mean_square_displacement(data, ndt=None):
    """Calculate the mean square displacement for the given data.

    Parameters
    ----------
    data : numpy.array, 1D
        This numpy.array contain the data as a function of time.
    ndt : int, optional
        This parameter is the number of time origins. I.e. points up to
        ndt will be used as time origins. If not specified the value of
        the input ``data.size // 5`` will be used.

    Returns
    -------
    msd : numpy.array, 2D
        First column is the mean squared displacement and the second
        column is the corresponding standard deviation.
    """
    length = data.size
    if ndt is None:
        ndt = length // 5
    msd = []
    for i in range(1, ndt):
        delta = (data[i:] - data[:-i])**2
        msd.append((delta.mean(), delta.std()))
    return np.array(msd)


def analyse_data(data, settings):
    """Analyse the given data and run some common analysis procedures.

    Specifically it will:

    1) Calculate a running average.

    2) Obtain a histogram.

    3) Run a block error analysis.


    Parameters
    ----------
    data : numpy.array, 1D
        This numpy.array contain the data as a function of time.
    settings : dict
        This dictionary contains settings for the analysis.

    Returns
    -------
    result : dict
        This dict contains the results.
    """
    result = {}
    # 1) Do the running average
    result['running'] = running_average(data)
    # 2) Obtain distributions:
    result['distribution'] = histogram_and_avg(data, settings['bins'],
                                               density=True)
    # 3) Do the block error analysis:
    result['blockerror'] = block_error_corr(data,
                                            maxblock=settings['maxblock'],
                                            blockskip=settings['blockskip'])
    return result
