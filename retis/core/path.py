# -*- coding: utf-8 -*-
"""
This file contain a class to represent paths.
"""
import numpy as np
import warnings
import copy
import itertools

__all__ = ['Path', 'paste_paths', 'reverse_path']

# the following defines a human-readable form of the possible path status:
_STATUS = {'ACC': 'The path has been accepted',
           'MCR': 'Momenta change rejection',
           'BWI': 'Backward trajectory end at wrong interface',
           'BTL': 'Backward trajectory too long (detailed balance condition)',
           'BTX': 'Backward trajectory too long (max-path exceeded)',
           'KOB': 'Kicked outside of boundaries',
           'FTL': 'Forward trajectory too long (detailed balance condition)',
           'FTX': 'Forward trajectory too long (max-path exceeded)',
           'NCR': 'No crossing with middle interface'}

def paste_paths(path1, path2, overlap=True):
    """
    Helper function to merge a backward and forward trajectory so that
    the paths will be stacked on top of each-other. The ordering is
    important here, paste_paths(path1, path2) != paste_paths(path2, path1).
    The code is very similar to Path.__add__ but we have to take care:
    - path1 must be iterated in reverse
    - we may have to remove one point in path2 (if the paths overlap)

    Parameters
    ----------
    path1 : object of type Path
        This is the backward trajectory
    path2 : object of type Path
        This is the forward trajectory
    overlap : boolean, default is True
        If true, path1 and path2 have a common starting-point, that is,
        the first point in path2 is identical to the first point in path1
        In time-space this means that the first point in path2 is equal to
        the last point in path1 (the backward and forward path started
        at the same location in space)
    """
    if path1.maxlen == path2.maxlen:
        # everything is ok, they have the same length
        maxlen = path1.maxlen
    else:
        # They are unequal and both is not None, just pick the largest.
        # In case one is None, the other will be picked.
        maxlen = max(path1.maxlen, path2.maxlen)
        msg = 'Unequal maxlen - setting equal to {}'.format(maxlen)
        warnings.warn(msg)
    time_origin = path1.time_origin - len(path1.path) + 1
    new_path = Path(maxlen=maxlen, time_origin=time_origin)
    iter_path1 = reversed(path1.path)  # we iterate in correct time direction
    if overlap:  # do not include the overlapping point:
        iter_path2 = path2.path[1:]
    else:
        iter_path2 = path2.path

    for phasepoint in itertools.chain(iter_path1, iter_path2):
        app = new_path.append(phasepoint[0],
                              phasepoint[1],
                              phasepoint[2])
        if not app:
            msg = 'Truncated path at: {}'.format(len(new_path.path))
            warnings.warn(msg)
            return new_path
    return new_path


def reverse_path(path, order_func=None):
    """
    This method will reverse a path and return the reverse path as
    a new Path object.

    Parameters
    ----------
    path : object of type Path
        This is the path we wish to reverse
    order_func : function, optional
        In case the order parameter should be re-calculated for the reverse
        path, the function order_func can be specified to do this.
    """
    new_path = Path(maxlen=path.maxlen)
    for phasepoint in reversed(path.path):
        pos, vel = phasepoint[0], -1.0*phasepoint[1]
        if order_func:
            orderp = order_func(pos, vel)
        else:
            orderp = phasepoint[2]
        app = new_path.append(pos, vel, orderp)
        if not app:
            msg = 'Could not reverse path'
            warnings.warn(msg)
    return new_path


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
    ordermin : tuple
        This is the (current) minimum order parameter for the path.
        ordermin[0] is the value, ordermin[1] is the index in self.path.
    ordermax : tuple
        This is the (current) maximum order parameter for the path.
        ordermax[0] is the value, ordermax[1] is the index in self.path.
    time_origin : int
        This is the location of the phasepoint path[0] relative to it's
        parent. This might be usefull for plotting.
    status : str or None
        The status of the path. The possibilities are defined
        in the variable _STATUS
    """
    def __init__(self, maxlen=None, time_origin=0):
        """
        Initialize the Path object.

        Parameters
        ----------
        maxlen : int, optional
            This is the max-length of the path. The default value,
            None, is just a path of arbitrary length.
        time_origin : int, optional
            This can be used to store the shooting point of a parent
            trajectory.
        """
        self.maxlen = maxlen
        self.path = []
        self.ordermin = None
        self.ordermax = None
        self.time_origin = time_origin
        self.status = None

    def __iter__(self):
        """
        To iterate over the phase-space points

        Returns
        -------
        It will yield the phase-space points successively
        """
        for phasepoint in self.path:
            yield phasepoint

    def append(self, pos, vel, orderp):
        """
        Method to append a new phase point to the path. The phasepoint is
        assumed to be given by positions and velocities with
        a corresponding scalar order parameter.


        Parameters
        ----------
        pos : numpy.array
            The positions of the particles
        vel: numpy.array
            The velocities of the particles
        orderp : float
            This variable is the order parameter for the given point.
        """
        if self.maxlen is None or len(self.path) < self.maxlen:
            self.path.append([np.copy(pos), np.copy(vel), copy.copy(orderp)])
            self._update_orderp(orderp, len(self.path) - 1)
            return True
        else:
            msg = 'Path length exceeded! Could not append to path!'
            warnings.warn(msg)
            return False

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
            self.ordermax = (orderp, idx)
        if self.ordermin is None or orderp < self.ordermin[0]:
            self.ordermin = (orderp, idx)

    def get_min_max_orderp(self):
        """
        Function to check the order parameters. This will
        explicitly loop over the path and find the max/min order paramter.

        Returns
        -------
        out[0] : list
            This is the minimum order parameter, tuple with (value, index)
        out[1] : list
            This is the maximum order parameter, tuple with (value, index)
        """
        ordermin = None
        ordermax = None
        for i, phasepoint in enumerate(self.path):
            orderp = phasepoint[-1]
            if ordermin is None or ordermax is None:
                ordermin = (orderp, i)
                ordermax = (orderp, i)
            else:
                if orderp > ordermax[0]:
                    ordermax = (orderp, i)
                if orderp < ordermin[0]:
                    ordermin = (orderp, i)
        self.ordermin = ordermin
        self.ordermax = ordermax
        return ordermin, ordermax

    def check_interfaces(self, interfaces):
        """
        Method to get the current status of the path with respect
        to the given interfaces. This is indended to determine if we
        have crossed certain interfaces or not.

        Parameters
        ----------
        interfaces : list of floats
            This list is assumed to contain the three interface values
            left, middle and right

        Returns
        -------
        out[0] : str, 'L' or 'R' or None
            Start condition: did the trajectory start at the left ('L') or
            right (R) interface.
        out[1] : str, 'L' or 'R' or None
            Ending condition: did the trajectory end at the left ('L') or
            righ ('R') interface or None of them.
        out[2] : list of boolean
            out[2][i] = True if ordermin < interfaces[i] <= ordermax
        """
        start, end, cross = None, None, None
        if len(self.path) < 1:
            warnings.warn('Path is empty!')
            return start, end, cross
        ordermax, ordermin = self.ordermax[0], self.ordermin[0]
        cross = [ordermin < interpos <= ordermax for interpos in interfaces]
        left, right = min(interfaces), max(interfaces)
        # check end:
        if self.path[-1][-1] < left:
            end = 'L'
        elif self.path[-1][-1] > right:
            end = 'R'
        # and check start:
        if self.path[0][-1] <= left:
            start = 'L'
        elif self.path[0][-1] >= right:
            start = 'R'
        else:
            warnings.warn('Undefined starting point')
        return start, end, cross

    def __add__(self, other):
        """
        This functions defines how we add two paths,
        i.e. new_path = self + other

        Parameters
        ----------
        self, other : objects of type Path

        Returns
        -------
        out : object of type Path
        """
        if self.maxlen == other.maxlen:
            # everything is ok, they have the same length
            maxlen = self.maxlen
        else:
            # they are unequal and both is not none, just pick the largest
            maxlen = max(self.maxlen, other.maxlen)
            msg = 'Unequal maxlen - setting equal to {}'.format(maxlen)
            warnings.warn(msg)

        new_path = Path(maxlen=maxlen)

        for phasepoint in itertools.chain(self.path, other.path):
            app = new_path.append(np.copy(phasepoint[0]),
                                  np.copy(phasepoint[1]),
                                  copy.copy(phasepoint[2]))
            if not app:
                msg = 'Truncated path at: {}'.format(len(new_path.path))
                warnings.warn(msg)
                return new_path
        return new_path

    def __iadd__(self, other):
        for phasepoint in other.path:
            app = self.append(np.copy(phasepoint[0]),
                              np.copy(phasepoint[1]),
                              copy.copy(phasepoint[2]))
            if not app:
                msg = 'Truncated path at: {}'.format(len(self.path))
                warnings.warn(msg)
                return self
        return self

    def __str__(self):
        """
        Return a simple string representation of the Path.
        """
        msg = ['Path with length {} (max: {})'.format(len(self.path),
                                                      self.maxlen)]
        msg += ['\tOrder parameter max: {}'.format(self.ordermax)]
        msg += ['\tOrder parameter min: {}'.format(self.ordermin)]
        if len(self.path) > 0:
            msg += ['\tStart {}'.format(self.path[0][-1])]
            msg += ['\tEnd {}'.format(self.path[-1][-1])]
        if self.status:
            msg += ['\tStatus: {}'.format(_STATUS[self.status])]
        return '\n'.join(msg)
