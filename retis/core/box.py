# -*- coding: utf-8 -*-
"""Definition of a class for a simulation box"""

import numpy as np

__all__ = ['Box']


class Box(object):
    """
    Box(object) defines a simple simulation box. The box will handle
    periodic boundaries if needed.
    A non-periodic dummy-box can be created using Box(periodic=[False, ...])
    which may be usefull for setting the dimensionality.
    Otherwise, a box will typically be created with a size, Box(size=[...]).
    Periodocity can be explicity set (default is assumed periodic in all
    dimensions).

    Attributes
    ----------
    size : list
        size[i] = [low, high] are the box boundaries in dimension i
    length : list
        length[i] = length of box in dimension i, equals
        size[i][1] - size[i][0]
    periodic : list
        periodic[i] = True if periodic boundaries are to be used in
        dimension i, False otherwise.
    dim : int
        the number of dimensions the box is made up of.
    """

    def __init__(self, size=None, periodic=None):
        """
        Initialize the box

        Parameters
        ----------
        size : list.
            The size of the box, can be given with size[i] = length_i
            which defines the box-length in dimension i. The box will then be
            assumed to have size[i] = [0, length_i]. Alternatively the
            boundaries can be defined explicitly: size[i] = [low, high].
        periodic : list, optional.
            periodic[i] is True if periodic boundaries will be applied in
            dimension i. Default is True for each dimension in size.
        """
        self.length = []
        self.periodic = []
        self.low = []
        self.high = []
        if size is None:
            if periodic is None:  # Assume 1D non-periodic box
                size = [[-float('inf'), float('inf')]]
                periodic = [False]
            else:
                size = [[-float('inf'), float('inf')] for i in periodic]
        self.size = size
        for i, dim in enumerate(size):
            ldim = len(dim)
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
        self.dim = len(self.length)

    def calculate_volume(self):
        """
        Calculates the volume of the box.

        Returns
        -------
        out : float
            The volume of the box.
        """
        return np.product(self.length)

    def pbc_coordinate_dim(self, pos, dim):
        """
        This function applies the periodic boundaries to the selected
        dimension only. This can be usefull for instance in connection
        with order parameters.

        Parameters
        ----------
        pos : float
            Coordinate to wrap around
        dim : int
            This selects the dimension to consider
        """
        if self.periodic[dim]:
            low, length = self.low[dim], self.length[dim]
            relpos = pos - low
            delta = relpos
            if relpos < 0.0 or relpos >= length:
                delta = relpos - np.floor(relpos/length) * length
            return delta + low
        else:
            return pos
        #while x < self.low[dim]:
        #    x = x + self.length[dim]
        #while x > self.high[dim]:
        #    x = x - self.length[dim]
        #return x

    #def pbc_slow2(self, allpos):
    #    """
    #    This implementation of applying the pbc coordinate
    #    are included here just for testing. It will probably be
    #    removed in the future.
    #    """
    #    dpos = np.zeros(allpos.shape)
    #    for i, periodic in enumerate(self.periodic):
    #        if periodic:
    #            coord = [self.pbc_coordinate2(x, i) for x in allpos[:, i]]
    #            dpos[:, i] = np.array(coord)
    #        else:
    #            dpos[:, i] = np.array([x for x in allpos[:, i]])
    #    return dpos

    #def pbc_coordinate(self, x, low, high, length):
    #    """
    #    This implementation of applying the pbc coordinate
    #    are included here just for testing. It will probably be
    #    removed or modified in the future.
    #    """
    #    if x < low or x > high:
    #        return x - np.floor(x/length)*length
    #    else:
    #        return x

    #def pbc_slow(self, allpos):
    #    """
    #    This implementation of applying the pbc coordinate
    #    are included here just for testing. It will probably be
    #    removed or modified in the future.
    #    """
    #    dpos = np.zeros(allpos.shape)
    #    for i, periodic in enumerate(self.periodic):
    #        if periodic:
    #            low = self.low[i]
    #            high = self.high[i]
    #            length = self.length[i]
    #            pos = [self.pbc_coordinate(xi, low, high, length)
    #                                      for xi in allpos[:, i]]
    #            dpos[:, i] = np.array(pos)
    #        else:
    #            dpos[:, i] = allpos[:, i]
    #    return dpos

    def pbc_wrap(self, pos):
        """
        This method applies periodic boundaries to the
        given position

        Paramters
        ---------
        pos : nump.array
            Positions to apply periodic boundaries to.

        Returns
        -------
        out : numpy.array, same shape as parameter `pos`
            The pbc-wrapped positions.
        """
        pbcpos = np.zeros(pos.shape)
        for i, periodic in enumerate(self.periodic):
            if periodic:
                low = self.low[i]
                length = self.length[i]
                relpos = pos[:, i] - low
                delta = np.where(np.logical_or(relpos < 0.0, relpos >= length),
                                 relpos - np.floor(relpos/length) * length,
                                 relpos)
                pbcpos[:, i] = delta + low
            else:
                pbcpos[:, i] = pos[:, i]
        return pbcpos

    def pbc_dist_matrix(self, distance):
        """
        This method applies periodic boundaries to a distance
        matrix/vector.

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
        for i, (periodic, length) in enumerate(zip(self.periodic,
                                                   self.length)):
            if periodic:
                dist = pbcdist[:, i]
                high = 0.5 * length
                k = np.where(np.abs(dist) >= high)[0]
                dist[k] -= np.rint(dist[k]/length) * length
        return pbcdist

    def pbc_dist_coordinate(self, distance):
        """
        This function applies periodic boundaries to a distance.
        The distance can be a vector, but not a matrix of several
        distance vectors.

        Parameters
        ----------
        distance : numpy.array, shape (self.dim,)
            A distance vector.

        Returns
        -------
        out : numpy.array, same shape as parameter `distance`
            The pbc-wrapped distance vector.
        """
        pbcdist = np.zeros(distance.shape)
        for i, (periodic, length) in enumerate(zip(self.periodic,
                                                   self.length)):
            if periodic and np.abs(distance[i]) > 0.5*length:
                pbcdist[i] = distance[i] - np.rint(distance[i]/length)*length
            else:
                pbcdist[i] = distance[i]
        return pbcdist

    def __str__(self):
        """
        This method returns a string describing the box

        Returns
        -------
        out : string,
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
