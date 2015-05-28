# -*- coding: utf-8 -*-
"""
This file contains some simple methods for numerical analysis.
"""

import numpy as np

__all__ = ['running_average']


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
