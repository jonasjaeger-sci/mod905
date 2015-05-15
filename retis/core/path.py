# -*- coding: utf-8 -*-
"""
This file contain a class to represent paths.
"""
import numpy as np
import warnings
import copy
import itertools

__all__ = ['Path', 'PathEnsemble', 'paste_paths', 'reverse_path']

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

_GENERATED = {'sh': 'Path was generated with a shooting move',
              'tr': 'Path was generated with a time-reversal move',
              's+': 'Swapping move +',
              's-': 'Swapping move -'}


def paste_paths(path_back, path_forw, overlap=True, maxlen=None):
    """
    This function will merge two paths - one is in the backward time
    direction and the other is in the forward direction. The resulting
    path is equal to the two paths stacked on top of each-other in correct
    time. Note that the ordering is important here:
    paste_paths(path1, path2) != paste_paths(path2, path1).

    The code is very similar to Path.__add__ but we have to take care:
    - path_back must be iterated in reverse (it is assumed to be a
      backward trajectory)
    - we may have to remove one point in path2 (if the paths overlap)

    Parameters
    ----------
    path_back : object of type Path
        This is the backward trajectory
    path_forw : object of type Path
        This is the forward trajectory
    overlap : boolean, default is True
        If true, path_back and path_forw have a common starting-point,
        that is, the first point in path_forw is identical to the first point
        in path_back. In time-space this means that the first point in
        path_forw is identical to the last point in path_back (the backward
        and forward path started at the same location in space).
    maxlen : float, optional
        This is the maximum length for the new path. If it's not given, it will
        just be set to the largest of the maxlen of the two given paths.
    """
    if maxlen is None:
        if path_back.maxlen == path_forw.maxlen:
            # everything is ok, they have the same maximum length
            maxlen = path_back.maxlen
        else:
            # They are unequal and both is not None, just pick the largest.
            # In case one is None, the other will be picked.
            # Note that now there is a chance of truncating the path while
            # pasting!
            maxlen = max(path_back.maxlen, path_forw.maxlen)
            msg = 'Unequal maxlen - setting equal to {}'.format(maxlen)
            warnings.warn(msg)
    time_origin = path_back.time_origin - len(path_back.path) + 1
    new_path = Path(maxlen=maxlen, time_origin=time_origin)
    iter_path_back = reversed(path_back.path)  # iterate in correct time dir
    if overlap:  # do not include the overlapping point:
        iter_path_forw = path_forw.path[1:]
    else:
        iter_path_forw = path_forw.path

    for phasepoint in itertools.chain(iter_path_back, iter_path_forw):
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
        Each tuple stores (positions, velocities, order parameter).
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
        self.generated = None

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
        to the given interfaces. This is intended to determine if we
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
        # check end & start:
        end = self.get_end_point(left, right)
        start = self.get_start_point(left, right)
        return start, end, cross

    def get_end_point(self, left, right):
        """
        This function just returns the end point of the path as
        a string.

        Parameters
        ----------
        left : float
            The left interface
        right : float
            The right interface

        Returns
        -------
        out : string
            String representing where the end point is ('L' - left,
            'R' - right or None).
        """
        if self.path[-1][-1] < left:
            end = 'L'
        elif self.path[-1][-1] > right:
            end = 'R'
        else:
            end = None
        return end

    def get_start_point(self, left, right):
        """
        This function just returns the start point of the path as
        a string.

        Parameters
        ----------
        left : float
            The left interface
        right : float
            The right interface

        Returns
        -------
        out : string
            String representing where the start point is ('L' - left,
            'R' - right or None).
        """
        if self.path[0][-1] <= left:
            start = 'L'
        elif self.path[0][-1] >= right:
            start = 'R'
        else:
            start = None
            warnings.warn('Undefined starting point')
        return start

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
        if self.generated:
            msg += ['\tGenerated: {}'.format(_GENERATED[self.generated])]
        return '\n'.join(msg)


class PathEnsemble(object):
    """
    PathEnsemble(object)

    This class represents a collection of Paths or a Path ensemble.
    The Path ensemble will not save the phase-space points of the paths
    but it will store other information about the paths.
    The PathEnsemble implements a dict ``path_data`` which contains important
    data for the paths.

    Attributes
    ----------
    ensemble : str
        This is a string representation of the path ensemble. Typically
        something like '0-', '0+', '1', '2', ...
    interfaces : list of ints
        These are the interfaces specified with the values
        for the order parameters: [left, middle, right]
    path_data : dict
        This dict contains information about the paths. The possible keys are:
        status : list of strings
            This is the status of the path. The possibilities are defined in
            the variable _STATUS.
        length : list of ints
            This is the path lengths.
        ordermin : list of tuples. ordermin[i][0] = minimum order parameter of
            the path, ordermin[i][1] = index in the path where this occurs.
        ordermax : list of tuples. ordermax[i][0] = maximum order parameter of
            the path, ordermax[i][1] = index in the path where this occurs.
        generated :  list of strings
            The strings indicate how the paths were generated. The
            possibilities are defined in _GENERATED
        interface : list of typles
            interface[i] = (start, middle, end) for path i. start/end can
            be 'L'/'R'/'*' and middle can be 'M' or '*'. This is a string
            representation on where the path started, where it ended and
            if it crossed the middle interface.
        cycle :  list of ints
            This is the cycle number where the path was generated.
    npath : int
        The number of paths stored.
    maxpath : int
        The maximum number of paths to store.
    stats : dict
        This dict just contain some numbers which can be used
        for statistics during the simulation.
    """
    def __init__(self, ensemble, interfaces, maxpath=100000):
        """
        Initialize the Path object.

        Parameters
        ----------
        ensemble : string
            The string representation of the path ensemble.
        interfaces : list of ints
            These are the interfaces specified with the values
            for the order parameters: [left, middle, right]
        """
        self.ensemble = ensemble
        self.interfaces = tuple(interfaces)  # Should not change interfaces
        self.path_data = {'status': [],
                          'length': [],
                          'ordermin': [],
                          'ordermax': [],
                          'generated': [],
                          'interface': [],
                          'cycle': []}
        self.npath = 0
        self.maxpath = maxpath
        self.stats = {}
        for key in _STATUS:
            self.stats[key] = 0
        self.stats['RX'] = 0

    def reset_data(self):
        """
        This method will just erase the stored data in path_data.
        It can be used in combination with flushing the data to a
        file in order to periodically write and empty the amount of data
        stored in memory.
        """
        for key in self.path_data:
            self.path_data[key] = []
        for key in self.stats:
            self.stats[key] = 0
        self.npath = 0

    def append(self, path, cycle=0):
        """
        This will append the data from the given path object to
        self.path_data

        Parameters
        ----------
        path : object of type Path
            This is the path to store data from.
        cycle : int, optional
            The current cycle number
        """
        if self.npath >= self.maxpath:
            pass
        self.path_data['generated'].append(path.generated)
        self.path_data['status'].append(path.status)
        self.path_data['length'].append(len(path.path))
        self.path_data['ordermax'].append(tuple(path.ordermax))
        self.path_data['ordermin'].append(tuple(path.ordermin))
        left, right, cross = path.check_interfaces(self.interfaces)
        if cross[1]:
            middle = 'M'
        else:
            middle = '*'
        self.path_data['interface'].append((left, middle, right))
        self.path_data['cycle'].append(cycle)
        self.npath += 1
        self.stats[path.status] += 1
        if left == 'L' and right == 'R' and cross[1]:
            self.stats['RX'] += 1

    def __str__(self):
        """
        Return a string with some info about this object
        """
        msg = ['Path ensemble: {}'.format(self.ensemble)]
        msg += ['\tNumber of paths stored: {}'.format(self.npath)]
        msg += ['\tNumber of paths accepted: {}'.format(self.stats['ACC'])]
        msg += ['\tNumber of reactive paths: {}'.format(self.stats['RX'])]
        return '\n'.join(msg)
