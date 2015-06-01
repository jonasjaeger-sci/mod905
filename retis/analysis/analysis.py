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
    half of the length of the input data.

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
        blockskip = n will consider every n'th block up to maxblock.
    """
    if maxblock is None:
        maxblock = len(data) // 2
    else:
        maxblock = min(maxblock, len(data) // 2)
    # define helper variables:
    block = np.zeros(maxblock)  # to accumulate values for a block
    nblock = np.zeros(maxblock)  # to count number of whole blocks processed
    block_avg = np.zeros(maxblock)  # to store averages in block
    block_var = np.zeros(maxblock)  # to store variance in block
    block_std = np.zeros(maxblock)  # to store standard deviation
    for i, datai in enumerate(data):
        block += datai  # accumulate the value to all blocks
        for j in xrange(0, maxblock, blockskip):
            if (i + 1) % (j + 1) == 0:
                avg = block[j] / float(j + 1)
                block_avg[j] += avg
                block_var[j] += avg**2
                block[j] = 0.0
                nblock[j] += 1.0
    # remaining of blocks is thrown away
    # Next, calculate average and variance.
    # here we also accumulate values for block where the length
    # is larger then half the maxblock length in order to calculate
    # an average relative error and average correlation length
    block_std_avg = []
    for j in xrange(0, maxblock, blockskip):
        block_avg[j] /= nblock[j]
        block_var[j] /= nblock[j]
        denom = nblock[j] - 1.0
        if denom > 0:
            block_var[j] = (block_var[j] - block_avg[j]**2) / denom
        else:
            block_var[j] = 0.0
        block_std[j] = np.sqrt(block_var[j])
        if j > (maxblock // 2):
            block_std_avg.append(block_std[j])
    block_std_avg = np.average(block_std_avg)
    # calculate relative errors
    #try:
    #    rel_err = block_std / abs(block_avg[0])
    #    avg_rel_err = avg_abs_err / abs(block_avg[0])
    #except ZeroDivisionError:
    #    rel_err = float('inf') * block_std
    #    avg_rel_err = float('inf')
    # and correlation
    #try:
    #    ncor = (block_std / block_std[0])**2
    #    avg_ncor = (avg_abs_err / block_std[0])**2
    #except ZeroDivisionError:
    #    ncor = float('inf') * block_std
    #    avg_ncor = float('inf')
    return block_avg, block_std, block_std_avg#, rel_err, avg_rel_err
