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
        blockskip = n will consider every n'th block up to maxblock. That
        is it will use block lengths equal to 1, 1+n, 1+n+n, etc.

    Returns
    -------
    blockid : numpy.array
        These contains the block lengths consideres
    block_avg : numpy.array
        The averages as function of block length
    block_std : numpy.array
        The standard deviation as function of block length
    block_std_avg : float
        The average standard deviation for block with length
        > maxblock//2
    """
    if maxblock is None:
        maxblock = len(data) // 2
    else:
        maxblock = min(maxblock, len(data) // 2)
    # define helper variables:
    blockid = np.arange(0, maxblock, blockskip, dtype=np.int_) + 1
    # blockid contains in reality the lengths of the blocks one should
    # consider
    block = np.zeros(len(blockid))  # to accumulate values for a block
    nblock = np.zeros(len(blockid))  # to count number of whole blocks
    block_avg = np.zeros(len(blockid))  # to store averages in block
    block_var = np.zeros(len(blockid))  # to store variance in block
    block_std = np.zeros(len(blockid))  # to store standard deviation
    for i, datai in enumerate(data):
        block += datai  # accumulate the value to all blocks
        # next pick out blocks which are full:
        k = np.where((i + 1) % blockid == 0)[0]
        block_avg[k] = block_avg[k] + block[k]
        block_var[k] = block_var[k] + block[k]**2
        block[k] = 0.0
        nblock[k] += 1
        #if i%1000==0: print i
    # remaining of blocks is thrown away
    # Next, calculate average and variance.
    # here we also accumulate values for block where the length
    # is larger then half the maxblock length in order to calculate
    # an average relative error and average correlation length
    block_std_avg = []
    for i, j in enumerate(blockid):
        block_avg[i] /= float(j + 1) * nblock[i]
        block_var[i] /= float(j + 1)**2 * nblock[i]
        denom = nblock[i] - 1.0
        if denom > 0:
            block_var[i] = (block_var[i] - block_avg[i]**2) / denom
        else:
            block_var[i] = 0.0
        block_std[i] = np.sqrt(block_var[i])
        if j > (maxblock // 2):
            block_std_avg.append(block_std[i])
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
    return blockid, block_avg, block_std, block_std_avg
