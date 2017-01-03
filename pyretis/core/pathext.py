# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Classes and functions for paths.

The classes and functions defined in this module are useful for
representing paths.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PathExt
    Class for a external paths. In external paths, the trajectories
    are stored in external files and the object will only contain the
    file names so that the external snapshots can be accessed.
"""
import logging
from pyretis.core.path import Path
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['PathExt']


class PathExt(Path):
    """A path where snapshots are not stored in memory.

    This class represents a path where the snapshots are stored
    on disk and not in memory. This is useful when we are using
    external engines and do not have to read entire trajectories
    into memory.

    Attributes
    ----------
    pos : list of strings
        Positions as function of time
    """

    def __init__(self, rgen, maxlen=None, time_origin=0):
        """Initialize the Path object.

        Parameters
        ----------
        rgen : object like :py:class:`.random_gen.RandomGenerator`
            This is the random generator that will be used.
        maxlen : int, optional
            This is the max-length of the path. The default value,
            None, is just a path of arbitrary length.
        time_origin : int, optional
            This can be used to store the shooting point of a parent
            trajectory.
        """
        super().__init__(rgen, maxlen=maxlen,
                         time_origin=time_origin)

    def _append_posvel(self, pos, vel):
        """Add positions and velocities to the path."""
        self.pos.append(pos)
        self.vel.append(vel)

    @staticmethod
    def reverse_velocities(vel):
        """Reverse the velocities.

        Parameters
        ----------
        vel : boolean
            The velocities to reverse.

        Returns
        -------
        out : boolean
            The reversed velocities.
        """
        return not vel
