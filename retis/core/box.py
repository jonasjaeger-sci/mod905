# -*- coding: utf-8 -*-
"""
Class for a simulation box
"""

import numpy as np

__all__ = ['Box']

class Box(object):
    """
    Box(object) defines a simple simulation box.

    Attributes
    ----------
    boundary : list, boundary[i] = [low, high] are the box boundaries in
        dimension i
    length : list, length[i] = length of box in dimension i, equals
        boundary[i][1] - boundary[i][0]
    periodic : list, periodic[i] = True if periodic boundaries are to be
        used in dimension i, False otherwise.
    """

    def __init__(self, size, periodic=None):
        """
        Initialize the box
        
        Parameters
        ----------
        size : list with the size of the box, can be given as 
            size[i] = length_i which defines the box-length in
            dimension i, the box will the be assumed to have 
            boundary[i] = [0, length_i]. Alternatively the boundaries
            can be defined explicitly: size[i] = [low, high]
        periodic : optional list, periodic[i] is True if periodic 
            boundaries will be applied in dimension i. Default
            is True for each dimension in size.
        """
        self.length = []
        self.periodic = []
        self.low = []
        self.high = []
        for dim in size:
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
            length = self.high[-1]-self.low[-1]
            if length <= 0:
                msg = 'Error for dim: {}, box length <= 0'.format(dim)
                raise ValueError(msg)
            self.length.append(length)
            if periodic is None:
                self.periodic.append(True)
            else:
                try:
                    self.periodic.append(periodic[dim])
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
        float equal to the volume of the box.
        """
        volume = None
        for length in self.length:
            if volume is None:
                volume = length
            else:
                volume *= length
        return volume

    def pbc_coordinate2(self, x, dim):
        while x<self.low[dim]:
            x = x + self.length[dim]
        while x>self.high[dim]:
            x = x - self.length[dim]
        return x

    def pbc_slow2(self, allpos):
        dpos = np.zeros(allpos.shape)
        for i, periodic in enumerate(self.periodic):
            if periodic:
                coord = [self.pbc_coordinate2(x, i) for x in allpos[:,i]]
                dpos[:,i] = np.array(coord)
            else:
                dpos[:,i] = np.array([x for x in allpos[:,i]])
        return dpos

    def pbc_coordinate(self, x, low, high, length):
        if x < low or x > high:
            return x - np.floor(x/length)*length
        else:
            return x

    def pbc_slow(self, allpos):
        dpos = np.zeros(allpos.shape)
        for i, periodic in enumerate(self.periodic):
            if periodic:
                low = self.low[i]
                high = self.high[i]
                length = self.length[i]
                pos = [self.pbc_coordinate(xi, low, high, length) for xi in allpos[:,i]]
                dpos[:,i] = np.array(pos)
            else:
                dpos[:,i] = allpos[:,i]
        return dpos

    def pbc_wrap(self, pos):
        """
        This method applies periodic boundaries to the 
        given position

        Paramters
        ---------
        pos : nump.array, the positions to consider

        Returns
        -------
        The pbc-wrapped positions
        """
        pbcpos = np.zeros(pos.shape)
        for i, periodic in enumerate(self.periodic):
            if periodic:
                low = self.low[i]
                length = self.length[i]
                relpos = pos[:,i] - low
                delta = np.where(np.logical_or(relpos < 0.0, relpos>=length), 
                             relpos-np.floor(relpos/length)*length, relpos)
                pbcpos[:,i] = delta + low
            else:
                pbcpos[:,i] = pos[:,i]
        return pbcpos
    

    def pbc_dist_matrix(self, distance):
        """
        This method applies periodic boundaries to a distance
        matrix/vector
        
        Parameters
        ----------
        distance : numpy.array, the distance vectors
    
        Returns
        -------
        The pbc-wrapped distances
        """
        pbcdist = distance 
        for i, (periodic, length) in enumerate(zip(self.periodic, self.length)):
            if periodic:
                dist = pbcdist[:,i]
                high = 0.5*length
                k = np.where(np.abs(dist)>=high)[0]
                dist[k] -= np.rint(dist[k]/length)*length
        return pbcdist

    def pbc_dist_coordinate(self, distance):
        pbcdist = np.zeros(distance.shape)
        for i, (periodic, length) in enumerate(zip(self.periodic, self.length)):
            if periodic and np.abs(distance[i])>0.5*length:
                pbcdist[i] = distance[i]-np.rint(distance[i]/length)*length
            else:
                pbcdist[i] = distance[i]
        return pbcdist

    def __str__(self):
        """
        This method returns a string describing the box
        
        Returns
        -------
        String with type of box, extent of the box and
        information about the periodicity.
        """
        boxstr = ['Simple rectangular cuboid box:']
        for i, periodic in enumerate(self.periodic):
            low = self.low[i]
            high = self.high[i]
            boxstr.append('Low: {}, high: {}, periodic: {}'.format(low, high, periodic))
        return '\n'.join(boxstr)
        
