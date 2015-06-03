# -*- coding: utf-8 -*-
"""
This file contains some simple methods for numerical analysis.
"""

import numpy as np

__all__ = ['running_average', 'block_error']


def running_average(data):
    """
    Function to create a running average of the given data.
    The running average will be calculated over the rows.

    Parameters
    ----------
    data : numpy.array
        This is the data we will average

    Returns
    -------
    out : numpy.array
        The running average
    """
    one = np.ones(np.shape(data))
    return data.cumsum(axis=0) / one.cumsum(axis=0)


def _chunks(itera, size):
    """
    Yield successive size-sized chunks from itera.

    Parameters
    ----------
    itera : iterabel
        This is the iterabel we will return chunks of
    size : int
        The size of the chunks

    Returns
    -------
    This is an iterator and will yield the chunks

    Notes
    -----
    Source: http://stackoverflow.com/a/312464
    """
    for i in xrange(0, len(itera), size):
        yield itera[i:i+size]


def block_error(data, maxblock=None, blockskip=1):
    """
    This method will estimate the standard deviation in the input
    data by performing a block analysis. The number of blocks
    to consider can be specified or it will be taken as the
    half of the length of the input data. Averages and variance is calculated
    using the on-the-fly algorithm presented here:
    http://en.wikipedia.org/wiki/Algorithms_for_calculating_variance

    Parameters
    ----------
    data : numpy.array (or iterable with data points)
        The data to analyse
    maxblock : int
        Can be used to set the max length of the blocks to consider.
        Note that the maxbloc will never be set longer than half
        the length in data.
    blockskip : int
        This can be used to skip certain block lengths, i.e.
        blockskip = 1 will consider all blocks up to maxblock, while
        blockskip = n will consider every n'th block up to maxblock. That
        is it will use block lengths equal to 1, 1+n, 1+n+n, etc.

    Returns
    -------
    blocklen : numpy.array
        These contains the block lengths considered
    block_avg : numpy.array
        The averages as function of block length
    block_err : numpy.array
        Estimate of errors as function of block length
    block_err_avg : float
        Average of the error estimate for blocks with length > maxblock//2
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
        block_avg[k] = block_avg[k] + deltas/nblock[k]
        block_var[k] = block_var[k] + deltas*(block[k] - block_avg[k])
        # reset these blocks
        block[k] = 0.0
        if i % 1000 == 0:
            print i
    block_var = block_var / (nblock - 1)
    block_err = np.sqrt(block_var/nblock)  # estimate of error
    k = np.where(blocklen > maxblock // 2)[0]
    block_err_avg = np.average(block_err[k])
    return blocklen, block_avg, block_err, block_err_avg

def _block_error_relative(block_avg, block_err, block_err_avg):
    """
    This is a helper function to estimate the correlation length
    and relative errors from a block analysis.

    Parameters
    ----------
    block_avg : numpy.array
        These are the block averages, as obtained from the
        block_error function.
    block_err : numpy.array
        These are the error estimates, as obtained from the
        block_error function.
    block_err_avg : float
        The average block error, as obtained from the block_error function.

    Returns
    -------
    rel_err : numpy.array
        Relative errors (wrt. the overall average) as function of block size.
    avg_rel_err : float
        Average relative errors (wrt. the overall average) as function of
        block-size. Note that block_err_avg are calculated from block_err in
        the block_error function by considering a subset of the blocks.
    ncor : numpy.array
        Estimated correlation length as function of block size.
    avg_ncor : float
        Average correlation length based on block_err_avg
    """
    # calculate relative errors
    try:
        rel_err = block_err / abs(block_avg[0])
        avg_rel_err = block_err_avg / abs(block_avg[0])
    except ZeroDivisionError:
        rel_err = float('inf')
        avg_rel_err = float('inf')
    # and correlation
    try:
        ncor = (block_err / block_err[0])**2
        avg_ncor = (block_err_avg / block_err[0])**2
    except ZeroDivisionError:
        ncor = float('inf')
        avg_ncor = float('inf')
    return rel_err, avg_rel_err, ncor, avg_ncor
