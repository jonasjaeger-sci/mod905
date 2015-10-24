# -*- coding: utf-8 -*-
"""This file contains a class for a generic property."""
import numpy as np

__all__ = ['Property']


class Property(object):
    """
    Property(object).

    A generic object to store values obtained during a simulation.
    It will maintain the mean and variance as values are added using
    Property.add(val)

    Attributes
    ----------
    desc : string
        Description of the property.
    n : integer
        Number values stored.
    mean : float
        The current mean.
    delta2 : float
        Helper variable used for calculating the variance.
    variance : float
        The current variance
    val : list
        Store all values.

    Parameters
    ----------
    desc : string, optional.
        Used to set the attribute desc.

    Examples
    --------
    >>> from pyretis.core.properties import Property
    >>> ener = Property(desc='Energy of the particle(s)')
    >>> ener.add(42.0)
    >>> ener.add(12.220)
    >>> ener.add(99.22)
    >>> ener.mean
    """

    def __init__(self, desc=''):
        """
        Initialize the property.

        Parameters
        ----------
        desc : string, optional
            Text description of the object

        Returns
        -------
        N/A
        """
        self.desc = desc
        self.n = 0
        self.mean = 0.0
        self.delta2 = 0.0
        self.variance = 0.0
        self.val = []

    def add(self, val):
        """
        Add a value to the property and updated the mean and variance.

        Parameters
        ----------
        val : float or another type (list, numpy.array)
            The value to add.

        Returns
        -------
        None, but updates the mean and variance
        """
        self.n += 1
        self.val.append(val)
        self.update_mean_and_variance()

    def update_mean_and_variance(self):
        """
        Calculate the mean and variance on the fly.

        Source:
        http://en.wikipedia.org/wiki/Algorithms_for_calculating_variance

        Returns
        -------
        N/A, however, the mean and variance is updated.

        Note
        ----
        Consider if this should be moved/deleted and just
        replaced with a function from the analysis method.
        """
        val = self.val[-1]  # most recent value
        delta = val - self.mean
        self.mean += delta/float(self.n)
        self.delta2 += delta * (val - self.mean)
        if self.n < 2:
            self.variance = float('inf')
        else:
            self.variance = self.delta2/float(self.n - 1)

    def dump_to_file(self, filename):
        """
        Dump the contents in `self.val` to a file.

        Parameters
        ----------
        filename : string
            Name/path of file to write.

        Note
        ----
        Consider if this should be moved/deleted and just
        replaced with a function from a more general input-output
        module
        """
        np.savetxt(filename, self.val)

    def __str__(self):
        """Simply return the string description of the property."""
        return self.desc
