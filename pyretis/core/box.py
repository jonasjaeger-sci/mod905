# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""Definition of a class for a simulation box.

The simulation box handles the periodic boundaries if needed.
It is typically referenced via the `system`, i.e. as `system.box`.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Box (:py:class:`pyretis.core.box.Box`)
    Class for a simulation box.

Examples
~~~~~~~~
>>> from pyretis.core.box import Box

>>> box = Box(size=[10, 10, 10], periodic=[True, False, True])
"""
import logging
import numpy as np
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['Box']


class Box(object):
    """Box(object).

    This class defines a simple simulation box. The box will handle
    periodic boundaries if needed. A non-periodic dummy-box can be
    created using `Box(periodic=[False, ...])` which may be useful for
    setting the dimensionality for a simulation. Otherwise, a box will
    typically be created with a size, `Box(size=[...])`.
    Periodicity can be explicitly set and the default behavior is for
    the box is to be periodic in all dimensions.

    Attributes
    ----------
    size : list
        `size[i] = [low, high]` are the box boundaries in dimension `i`.
    length : numpy array (1D)
        `length[i]` = length of box in dimension `i`, equals
        `size[i][1] - size[i][0]`.
    ilength : numpy array (1D)
        This is just the inverse box lengths, equal to `1.0/length`.
        This variable is just used for convenience.
    periodic : list
        `periodic[i] = True` if periodic boundaries are to be used in
        dimension `i`, `False` otherwise.
    dim : int
        The number of dimensions the box is made up of.
    """

    def __init__(self, size=None, periodic=None):
        """Initialize the box.

        Parameters
        ----------
        size : list.
            The size of the box, can be given with `size[i] = length_i`
            which defines the box-length in dimension `i`. The box will
            then be assumed to have `size[i] = [0, length_i]`.
            Alternatively the boundaries can be defined explicitly:
            `size[i] = [low, high]`.
        periodic : list, optional.
            `periodic[i]` is `True` if periodic boundaries will be
            applied in dimension `i`. Default is `True` for each
            dimension in `size`.
        """
        self.length = []
        self.periodic = []
        self.low = []
        self.high = []
        if size is None:
            if periodic is None:  # Assume 1D non-periodic box
                size = [[-float('inf'), float('inf')]]
                periodic = [False]
                logger.warning('Assuming a 1D non-periodic box!')
            else:
                # this might seem strange, but it's probably something
                # that is done if we just need a dummy box.
                size = [[-float('inf'), float('inf')] for _ in periodic]
        self.size = size
        for i, dim in enumerate(size):
            try:
                ldim = len(dim)
            except TypeError:
                ldim = 1
            if ldim == 1:
                self.low.append(0.0)
                self.high.append(dim)
            elif ldim == 2:
                self.low.append(dim[0])
                self.high.append(dim[1])
            else:
                msg = 'Did not understand dimension in box: {}'.format(dim)
                raise ValueError(msg)
            length = self.high[-1] - self.low[-1]
            if length <= 0:
                msg = 'Error for dim: {}, box length <= 0'.format(dim)
                raise ValueError(msg)
            self.length.append(length)
            if periodic is None:
                self.periodic.append(True)
            else:
                try:
                    self.periodic.append(periodic[i])
                except IndexError:
                    self.periodic.append(True)
        self.low = np.array(self.low)
        self.high = np.array(self.high)
        self.length = np.array(self.length)
        self.ilength = 1.0 / self.length
        self.dim = len(self.length)

    def calculate_volume(self):
        """Calculate the volume of the box.

        Returns
        -------
        out : float
            The volume of the box.
        """
        return np.product(self.length)

    def pbc_coordinate_dim(self, pos, dim):
        """Apply periodic boundaries to a selected dimension only.

        For the given positions, this function will apply periodic
        boundary conditions to one dimension only. This can be useful
        for instance in connection with order parameters.

        Parameters
        ----------
        pos : float
            Coordinate to wrap around.
        dim : int
            This selects the dimension to consider.
        """
        if self.periodic[dim]:
            low, length = self.low[dim], self.length[dim]
            ilength = self.ilength[dim]
            relpos = pos - low
            delta = relpos
            if relpos < 0.0 or relpos >= length:
                delta = relpos - np.floor(relpos * ilength) * length
            return delta + low
        else:
            return pos

    def pbc_wrap(self, pos):
        """Apply periodic boundaries to the given position.

        Parameters
        ----------
        pos : nump.array
            Positions to apply periodic boundaries to.

        Returns
        -------
        out : numpy.array, same shape as parameter `pos`
            The periodic-boundary wrapped positions.
        """
        pbcpos = np.zeros(pos.shape)
        for i, periodic in enumerate(self.periodic):
            if periodic:
                low = self.low[i]
                length = self.length[i]
                ilength = self.ilength[i]
                relpos = pos[:, i] - low
                delta = np.where(np.logical_or(relpos < 0.0, relpos >= length),
                                 relpos - np.floor(relpos * ilength) * length,
                                 relpos)
                pbcpos[:, i] = delta + low
            else:
                pbcpos[:, i] = pos[:, i]
        return pbcpos

    def pbc_dist_matrix(self, distance):
        """Apply periodic boundaries to a distance matrix/vector.

        Parameters
        ----------
        distance : numpy.array
            The distance vectors.

        Returns
        -------
        out : numpy.array, same shape as parameter `distance`
            The pbc-wrapped distances.
        """
        pbcdist = distance
        for i, (periodic, length, ilength) in enumerate(zip(self.periodic,
                                                            self.length,
                                                            self.ilength)):
            if periodic:
                dist = pbcdist[:, i]
                high = 0.5 * length
                k = np.where(np.abs(dist) >= high)[0]
                dist[k] -= np.rint(dist[k] * ilength) * length
        return pbcdist

    def pbc_dist_coordinate(self, distance):
        """Apply periodic boundaries to a distance.

        This will apply periodic boundaries to a distance. Note that the
        distance can be a vector, but not a matrix of several distance
        vectors.

        Parameters
        ----------
        distance : numpy.array with shape `(self.dim,)`.
            A distance vector.

        Returns
        -------
        out : numpy.array, same shape as parameter `distance`
            The periodic-boundary wrapped distance vector.
        """
        pbcdist = np.zeros(distance.shape)
        for i, (periodic, length, ilength) in enumerate(zip(self.periodic,
                                                            self.length,
                                                            self.ilength)):
            if periodic and np.abs(distance[i]) > 0.5*length:
                pbcdist[i] = (distance[i] -
                              np.rint(distance[i] * ilength) * length)
            else:
                pbcdist[i] = distance[i]
        return pbcdist

    def __str__(self):
        """Return a string describing the box.

        Returns
        -------
        out : string
            String with type of box, extent of the box and
            information about the periodicity.
        """
        boxstr = ['Simple rectangular cuboid box:']
        for i, periodic in enumerate(self.periodic):
            low = self.low[i]
            high = self.high[i]
            msg = 'Dim: {}, Low: {}, high: {}, periodic: {}'
            boxstr.append(msg.format(i, low, high, periodic))
        return '\n'.join(boxstr)
