# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Additional classes for paths.

This module defines different types of paths.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ReservoirPath (:py:class:`.ReservoirPath`)
    A path where only a subset of points are stored in memory.
"""
import logging
import numpy as np
from pyretis.core.path import Path
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['ReservoirPath']


class ReservoirPath(Path):
    """A path where only a subset of points are stored in memory.

    This class represents a path. A path consist of a series of
    consecutive snapshots (the trajectory) with the corresponding order
    parameter. Here we store phase points for only a small subset of the
    points in the path and maintain a reservoir of shooting points that
    are picked with the correct probability.
    """

    def __init__(self, rgen, maxlen=None, time_origin=0, res_length=10):
        """Initialize the Path object.

        Parameters
        ----------
        rgen : object like :py:class:`.RandomGenerator`
            This is the random generator that will be used.
        maxlen : int, optional
            This is the max-length of the path. The default value,
            None, is just a path of arbitrary length.
        time_origin : int, optional
            This can be used to store the shooting point of a parent
            trajectory.
        res_length : int, optional
            This is the number of shooting-point candidates to store.
        """
        super().__init__(rgen, maxlen=maxlen, time_origin=time_origin)
        self.res_length = res_length
        self.reservoir = []

    def trajectory(self, reverse=False):
        """Iterate over the phase-space points in the path.

        Parameters
        ----------
        reverse : boolean
            If this is True, we iterate in the reverse direction.

        Yields
        ------
        out : tuple
            The phase-space points in the path.
        """
        if reverse:
            for i in range(self.length - 1, -1, -1):
                yield self.phasepoint(i)
        else:
            for i in range(self.length):
                yield self.phasepoint(i)

    def phasepoint(self, idx):
        """Return a specific phase point.

        Parameters
        ----------
        idx : int
            Index for phase-space point to return.

        Returns
        -------
        out : tuple
            A phase-space point in the path.
        """
        phasepoint = {'order': self.order[idx], 'pos': None, 'vel': None,
                      'vpot': self.vpot[idx], 'ekin': self.ekin[idx]}
        return phasepoint

    def _append_posvel(self, pos, vel):
        """Append positions and velocities to the path."""
        if pos is not None and vel is not None:
            self.add_to_reservoir(self.length + 1, self.length, pos, vel)

    def get_shooting_point(self):
        """Return a shooting point from the path.

        This will simply draw a shooting point from the path at
        random. All points can be selected with equal probability with
        the exception of the end points which are not considered.

        Parameters
        ----------

        Returns
        -------
        out[0] : tuple
            The order parameter(s).
        out[1] : dict
            The phase point.
        out[2] : int
            The shooting point index.
        """
        if len(self.reservoir) < 1:
            logger.critical('Reservoir empty, need to regenerate path!')
            return None
        else:
            item = self.reservoir.pop()
            idx = item[0]
            phasepoint = {'order': self.order[idx],
                          'pos': item[1], 'vel': item[2],
                          'vpot': self.vpot[idx], 'ekin': self.ekin[idx]}
            return phasepoint, idx

    def add_to_reservoir(self, items, idx, pos, vel):
        """Try to add a point to the reservoir.

        Parameters
        ----------
        items : int
            The number of items seen by the reservoir.
        idx : int
            This is the index along the path for the `pos` and `vel`.
        pos : numpy.array
            The positions to store.
        vel : numpy.array
            The velocities to store.
        """
        if items == 1:
            for i in range(self.res_length):
                self.reservoir.append((idx, np.copy(pos), np.copy(vel)))
        else:
            factor = 1.0 / float(items)
            for i in range(self.res_length):
                if self.rgen.rand() < factor:
                    self.reservoir[i] = (idx, np.copy(pos), np.copy(vel))

    def empty_path(self, **kwargs):
        """Return an empty path of same class as the current one.

        For this empty path, the reservoir is not populated.

        Returns
        -------
        out : object like :py:class:`.PathBase`
            A new empty path.
        """
        maxlen = kwargs.get('maxlen', None)
        time_origin = kwargs.get('time_origin', 0)
        res_length = kwargs.get('res_length', self.res_length)
        return self.__class__(self.rgen, maxlen=maxlen,
                              time_origin=time_origin,
                              res_length=res_length)

    def reverse(self):
        """Reverse the path with addinional handling for the reservoir.

        This method will call `PathBase.reverse()` but will also do
        some extra reverse handling since we here have to reverse
        indices in the reservoir of shooting points.

        Returns
        -------
        path : object like :py:class:`.PathBase`
            This is basically a copy of `self`, just reversed.
        """
        path = self.reverse_trajectory()
        path.reservoir = []
        for point in self.reservoir:
            idx = self.length - 1 - point[0]
            path.reservoir.append((idx, np.copy(point[1]), np.copy(point[2])))
        return path
