# -*- coding: utf-8 -*-
"""
This file contain a class to represent paths.
"""
import numpy as np
import warnings
import copy

__all__ = ['Path']

class Path(object):
    """
    Path(object)

    This class represents a path. A path consist of a series of consecutive
    snapshots (the trajectory) with the corresponding order parameter.
    We assume here that the order parameter is a scalar value.

    Attributes
    ----------
    maxlen : int
        This is the maximum path length. Some algorithms requires this to
        be set. Others don't, which is indicated by setting maxlen equal to
        None.
    path : list
        This is the trajectory/series of snapshots, stored as a list of tuples.
        Each tuple stores the position, velocities, order parameter.
    ordermin : list
        This is the (current) minimum order parameter for the path.
        ordermin[0] is the value, ordermin[1] is the index in self.path.
    ordermax : list
        This is the (current) maximum order parameter for the path.
        ordermax[0] is the value, ordermax[1] is the index in self.path.
    """
    def __init__(self, maxlen=None):
        """
        Initialize the Path object.

        Parameters
        ----------
        maxlen : int, optional
            This is the max-length of the path. The default value,
            None, is just a path of arbitrary length.
        """
        self.maxlen = maxlen
        self.path = []
        self.ordermin = None
        self.ordermax = None

    def __iter__(self):
        """
        To iterate over the phase-space points

        Returns
        -------
        It will yield the phase-space points successively
        """
        for phasepoint in self.path:
            yield phasepoint

    def append(self, particles, orderp):
        """
        Method to append a new time-splice to the path

        Parameters
        ----------
        particles : object of particlelist type
            This object represents the snapshot which will be stored.
            Note that we here copies the positions and velocities and
            store these.
        orderp : float
            This variable is the order parameter for the given point.
        """
        if self.maxlen is None or len(self.path) < self.maxlen:
            pos = np.copy(particles.pos)
            vel = np.copy(particles.vel)
            self.path.append([pos, vel, copy.copy(orderp)])
            self._update_orderp(orderp, len(self.path)-1)
        else:
            msg = 'Could not add time slice to path!'
            warnings.warn(msg)

    def _update_orderp(self, orderp, idx):
        """
        Function to update the max/min order parameter given a new
        order parameter.

        Paramters
        ---------
        orderp : float
            This is the new order parameter
        idx : integer
            This is the index of the new order parameter in self.path
        """
        if self.ordermax is None or orderp > self.ordermax[0]:
            self.ordermax = [orderp, idx]
        if self.ordermin is None or orderp < self.ordermin[0]:
            self.ordermin = [orderp, idx]

    def get_min_max_orderp(self):
        """
        Function to check the order parameters. This will
        explicitly loop over the path and find the max/min order paramter.

        Returns
        -------
        out[0] : list
            This is the minimum order parameter, tuple with [value, index]
        out[1] : list
            This is the maximum order parameter, tuple with [value, index]
        """
        ordermin = None
        ordermax = None
        for i, phasepoint in enumerate(self.path):
            orderp = phasepoint[-1]
            if ordermin is None or ordermax is None:
                ordermin = [orderp, i]
                ordermax = [orderp, i]
            else:
                if orderp > ordermax[0]:
                    ordermax = [orderp, i]
                if orderp < ordermin[0]:
                    ordermin = [orderp, i]
        self.ordermin = ordermin
        self.ordermax = ordermax
        return ordermin, ordermax
