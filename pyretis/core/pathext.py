# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Classes and functions for paths.

The classes and functions defined in this module are useful for
representing paths.


Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PathExt
    Class for a generic path that stores all possible information.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

paste_paths
    Function for joining two paths, one is in a backward time
    direction and the other is in the forward time direction.
"""
import logging
from pyretis.core.path import Path
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['PathExt']


class PathExt(Path):
    """A path where the full trajectory is stored in memory.

    This class represents a path. A path consist of a series of
    consecutive snapshots (the trajectory) with the corresponding
    order parameter. Here we store all information for all phase points
    on the path.

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

    def append(self, phasepoint):
        """Append a new phase point to the path.

        We will here append a new phase-space point to the path.
        The phase point is assumed to be given by positions and
        velocities with a corresponding order parameter and energy.

        Parameters
        ----------
        orderp : list of floats
            This variable is the order parameter for the given point.
            `orderp[0]` is the actual order parameter used in path
            sampling methods while `orderp[1:]` can represent other
            order parameters for instance is `orderp[1]` typically the
            velocity of `orderp[0]`.
        pos : tuple
            The file with the positions.
        vel: boolean
            If True, then this is for a time-reversed configuration.
            I.e. the velocities should be reversed before they are used.
        vpot : float
            The potential energy of the configuration.
        ekin : float
            The kinetic energy of the configuration.
        """
        if self.maxlen is None or self.length < self.maxlen:
            orderp = phasepoint['order']
            self.order.append(orderp)
            self._update_orderp(orderp[0], self.length)
            self.pos.append(phasepoint['pos'])
            self.vel.append(phasepoint['vel'])
            self.vpot.append(phasepoint['vpot'])
            self.ekin.append(phasepoint['ekin'])
            self.length += 1
            return True
        else:
            msg = 'Max length exceeded! Could not append to path!'
            logger.debug(msg)
            return False

    def reverse(self):
        """Return a reversed version of the path.

        This will simply reverse a path and return the reversed path as
        a new `Path` object. Note that currently, recalculating
        order parameters have not been implemented!  Typically, reversing
        will not change the order parameter, but it might change the
        velocity for the order parameter and so on.

        Returns
        -------
        new_path : object like :py:class:`PathBase`
            This is basically a copy of `self`, just reversed.
        """
        new_path = self.empty_path()
        for phasepoint in self.trajectory(reverse=True):
            new_point = {key: val for key, val in phasepoint.items()}
            new_point['vel'] = not new_point['vel']
            app = new_path.append(phasepoint)
            if not app:
                msg = 'Could not reverse path'
                logger.error(msg)
                return None
        return new_path
