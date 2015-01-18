# -*- coding: utf-8 -*-
"""
Class for a simulation box
"""

import numpy as np

__all__ = ["Box"]

class Box(object):
    """
    Box(object) defines a simple simulation box.

    Attributes
    ----------
    boundary : list, boundary[i] = [low, high] are the box boundaries in
        dimension i
    length : list, length[i] = length of box in dimension i, equals
        boundary[i][1] - boundary[i][0]
    """
    def __init__(self, size, periodic=None):
        """
        Initialize the box
        
        Parameters
        ----------
        self : 
        size : list with the size of the box, can be given as 
            size[i] = length_i which defines the box-length in
            dimension i, the box will the be assumed to have 
            boundary[i] = [0, length_i]. Alternatively the boundaries
            can be defined explicitly: size[i] = [low, high]
        periodic : optional list, periodic[i] is True if periodic 
            boundaries will be applied in dimension i. Default
            is true for each dimension in size
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
                msg = "Did not understand dimension in box: {}".format(dim)
                raise ValueError(msg)
            length = self.high[-1]-self.low[-1]
            if length <= 0:
                msg = "Error for dim: {}, box length <= 0!".format(dim)
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


    def pbc_slow(self, allpos):
        dpos = []
        for pos in allpos:
            npos = []
            for i, posi in enumerate(pos):
                if self.periodic[i]:
                    rpos = posi - self.low[i]
                    if rpos < 0.0 or rpos > self.length[i]:
                        rpos = rpos - np.floor(rpos / self.length[i]) * self.length[i]
                    rpos += self.low[i]
                    npos.append(rpos)
                else:
                    npos.append(posi)
            dpos.append(npos)
        return np.array(dpos)
    def pbc_wrap(self, pos):
        """
        This method applied periodic boundaries to the 
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
            if not periodic:
                continue
            low = self.low[i]
            length = self.length[i]
            relpos = pos[:,i] - low
            delta = np.where(np.logical_or(relpos < 0.0, relpos>length), relpos-np.floor(relpos/length)*length, relpos)
            pbcpos[:,i] = delta + low
        return pbcpos
    

    def __str__(self):
        boxstr = ["Simple rectangular cuboid box:"]
        for i, periodic in enumerate(self.periodic):
            low = self.low[i]
            high = self.high[i]
            boxstr.append('Low: {}, high: {}, periodic: {}'.format(low, high, periodic))
        return '\n'.join(boxstr)
        
