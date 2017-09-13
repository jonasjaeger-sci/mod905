# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Definition of a class for a simulation box.

The simulation box handles the periodic boundaries if needed.
It is typically referenced via the :py:class:`.System` class,
i.e. as ``System.box``.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

BoxBase (:py:class:`.BoxBase`)
    Class for a simulation box.

RectangularBox (:py:class:`.RectangularBox`)
    Class representing a rectangular simulation box.

TriclinicBox (:py:class:`.TriclinicBox`)
    Class representing a triclinic simulation box.

Examples
~~~~~~~~
>>> from pyretis.core.box import create_box

>>> box = create_box(length=[10, 10, 10], periodic=[True, False, True])
"""
from abc import ABCMeta, abstractmethod
import logging
import numpy as np
from numpy.linalg import det
from numpy import product
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['create_box']


def create_box(low=None, high=None, length=None, periodic=None):
    """Helper method to select a box.

    Parameters
    ----------
    low : numpy.array
        1D array containing the lower bounds of the cell.
    high : numpy.array
        1D array containing the higher bounds of the cell.
    length : numpy.array
        1D array containing the size lengths of the cell.
    periodic : list of boolean
        If `periodic[i]` then we should apply periodic boundaries
        to dimension `i`.

    Returns
    -------
    out : object like :py:class:`.BoxBase`
        The object representing the simulation box.
    """
    obj = TriclinicBox
    if length is None or len(length) <= 3:
        obj = RectangularBox
    return obj(low=low, high=high, length=length, periodic=periodic)


def array_to_box_matrix(length):
    """Method to convert an array to a box matrix.

    Parameters
    ----------
    length : list or numpy.array
        An (1D) array containing 1, 2, 3, 6 or 9 items. These are
        the xx, yy, zz, xy, xz, yx, yz, zx, zy elements. Setting
        x = 0, y = 1 and z = 2 will give the indices in the matrix,
        e.g. yx -> (1, 0) will correspond to the item in row 1 and
        column 0.

    Returns
    -------
    box : numpy.array (2D)
        The box vector on matrix form.
    """
    if len(length) == 1:
        return 1.0 * np.array([length[0]])
    elif len(length) == 2:
        return 1.0 * np.array([[length[0], 0.0],
                               [0.0, length[1]]])
    elif len(length) == 3:
        return 1.0 * np.array([[length[0], 0.0, 0.0],
                               [0.0, length[1], 0.0],
                               [0.0, 0.0, length[2]]])
    elif len(length) == 6:
        return 1.0 * np.array([[length[0], length[3], length[4]],
                               [0.0, length[1], length[5]],
                               [0.0, 0.0, length[2]]])
    elif len(length) == 9:
        return 1.0 * np.array([[length[0], length[3], length[4]],
                               [length[5], length[1], length[6]],
                               [length[7], length[8], length[2]]])
    else:
        logger.error('%d box parameters given, need 1, 2 3, 6, or 9.',
                     len(length))
        raise ValueError('Incorrect number of box-parameters!')


def box_matrix_to_list(matrix):
    """Return a list representation of the box matrix.

    This method ensures correct ordering of the elements for PyRETIS.

    Parameters
    ----------
    matrix : numpy.array
        A matrix (2D) representing the box.

    Returns
    -------
    out : list
        A list with the box-parametres.
    """
    if matrix is None:
        return None
    if np.count_nonzero(matrix) <= 3:
        return np.diag(matrix)
    return [matrix[0, 0], matrix[1, 1], matrix[2, 2],
            matrix[0, 1], matrix[0, 2], matrix[1, 0],
            matrix[1, 2], matrix[2, 0], matrix[2, 1]]


def _cos(angle):
    """Return cosine of an angle.

    Here, we also check if the angle is close to 90.0 and
    if so, we return just a zero.

    Parameters
    ----------
    angle : float
        The angle in degrees.

    Returns
    -------
    out : float
        The cosine of the angle.
    """
    if np.isclose(angle, 90.):
        return 0.
    return np.cos(np.radians(angle))  # pylint: disable=no-member


def box_vector_angles(length, alpha, beta, gamma):
    """Return the box matrix from lengths ang angles.

    Parameters
    ----------
    length : numpy.array
        1D array, the box-lengths on form ``[a, b, c]``
    alpha : float
        The alpha angle.
    beta : float
        The beta angle.
    gamma : float
        The gamma angle.

    Returns
    -------
    out : np.array
        The box matrix (2D).
    """
    box_matrix = np.zeros((3, 3))
    cos_alpha = _cos(alpha)
    cos_beta = _cos(beta)
    cos_gamma = _cos(gamma)
    box_matrix[0, 0] = length[0]
    box_matrix[0, 1] = length[1] * cos_gamma
    box_matrix[0, 2] = length[2] * cos_beta
    box_matrix[1, 1] = np.sqrt(length[1]**2 - box_matrix[0, 1]**2)
    box_matrix[1, 2] = (length[1] * length[2] * cos_alpha -
                        box_matrix[0, 1] * box_matrix[0, 2]) / box_matrix[1, 1]
    box_matrix[2, 2] = np.sqrt(length[2]**2 - box_matrix[0, 2]**2 -
                               box_matrix[1, 2]**2)
    return box_matrix


class BoxBase(metaclass=ABCMeta):
    """Class for a generic simulation box.

    This class defines a generic simulation box.

    Attributes
    ----------
    low : numpy.array
        1D array containing the lower bounds of the cell.
    high : numpy.array
        1D array containing the higher bounds of the cell.
    length : numpy.array
        1D array containing the length of the sides of the
        simulation box.
    ilength : numpy.array
        1D array containing the inverse box lengths for the
        simulation box.
    periodic : list of boolean
        If `periodic[i]` then we should apply periodic boundaries
        to dimension `i`.
    box_matrix : numpy.array
        2D matrix, representing the simulation cell.
    cell : numpy.array
        1D array representing the simulation cell (flattened
        version of the 2D box matrix).
    """

    def __init__(self, low=None, high=None, length=None, periodic=None):
        """Initialise the BoxBase class."""

        case = (length is not None, low is not None, high is not None)

        self.length = None
        self.ilength = None
        self.low = None
        self.high = None
        self.periodic = None
        self.box_matrix = np.zeros((3, 3))
        self.cell = None
        self.dim = 0

        if length is not None:
            self.cell = [float(i) for i in length]
            self._update_length(length)
        if low is not None:
            self.low = np.array([float(i) for i in low])
        if high is not None:
            self.high = np.array([float(i) for i in high])

        self._set_low_high_length_cell(case, periodic)

        # Here: low, high and length should have been set.
        if self.periodic is None:
            if periodic is None:
                self.periodic = [True for _ in self.length]
            else:
                self.periodic = [i for i in periodic]
        if len(self.periodic) < len(self.length):
            for _ in range(len(self.length) - len(self.periodic)):
                self.periodic.append(True)

        self.dim = len(self.length)
        self.box_matrix = array_to_box_matrix(self.cell)
        self._check_consistency()
        self.ilength = 1.0 / self.length

    def _update_length(self, new_length):
        """Update the box lengths."""
        if len(new_length) <= 3:
            self.length = np.array([float(i) for i in new_length])
        else:
            self.length = np.array([float(i) for i in new_length[:3]])

    def _set_low_high_length_cell(self, case, periodic):
        """Determine low, high and length."""
        if case == (True, True, True):
            # We have given length, low and high.
            pass
        elif case == (True, False, True):
            # Length & high has been given, just determine low.
            self.low = self.high - self.length
        elif case == (True, True, False):
            # Length and low was given, determine high.
            self.high = self.low + self.length
        elif case == (True, False, False):
            # Length is given, set low to 0 and high to low + length
            self.low = np.zeros_like(self.length)
            self.high = self.low + self.length
        elif case == (False, True, True):
            # Low and high is given, determine length
            self.length = self.high - self.low
        elif case == (False, False, True):
            # High is given, assume low and determine length.
            self.low = np.zeros_like(self.high)
            self.length = self.high - self.low
        elif case == (False, True, False):
            # Low given. High and length to be determined.
            # This is not enough info really...
            self.length = float('inf') * np.ones_like(self.low)
            self.high = float('inf') * np.ones_like(self.low)
        elif case == (False, False, False):
            # Not much info is given. We let things be determined by
            # the periodic settings.
            if periodic is None:
                self.periodic = [False]
            else:
                self.periodic = periodic
            self.low = np.array([-float('inf') for _ in self.periodic])
            self.high = float('inf') * np.ones_like(self.low)
            self.length = float('inf') * np.ones_like(self.low)
        if self.cell is None:
            self.cell = [i for i in self.length]

    def _check_consistency(self):
        """Do some simple check for consistency of cell parameters."""
        length = self.high - self.low
        if any(i < 0 for i in length):
            logger.error('Check box settings! Found high < low!')
            raise ValueError('Incorrect box: high < low!')
        if not all(np.isclose(self.length, length)):
            logger.error('Check box settings length != high - low')
            raise ValueError('Check box: length != high - low')
        if any(self.length == 0):
            logger.error('Cannot have a length of 0')
            raise ValueError('Check box: Found length == 0')

    def update_size(self, new_size):
        """Update the box size.

        Parameters
        ----------
        new_size : list, tuple, numpy.array, or other iterable.
            The new box size.
        """
        if new_size is None:
            logger.warning(
                'Box update ignored: Tried to update with empty size!'
            )
        else:
            try:
                size = new_size.size
            except AttributeError:
                size = len(new_size)
            if size <= 3:
                if size == len(self.cell):
                    for i in range(self.dim):
                        self.length[i] = new_size[i]
                        self.high[i] = self.low[i] + new_size[i]
                        self.cell[i] = new_size[i]
                    self.ilength = 1.0 / self.length
            else:
                try:
                    self.box_matrix = array_to_box_matrix(new_size)
                    self.cell = [i for i in new_size]
                    self._update_length(new_size)
                    self.high = self.low + self.length
                    self.ilength = 1.0 / self.length
                except ValueError:
                    logger.critical('Box update failed!')

    def bounds(self):
        """Return the bounds (low, high) as an array."""
        bounds = []
        for i, j in zip(self.low, self.high):
            bounds.append([i, j])
        return bounds

    @abstractmethod
    def calculate_volume(self):
        """Return the volume of the box."""
        return

    @abstractmethod
    def pbc_coordinate_dim(self, pos, dim):
        """Apply periodic boundaries to a selected dimension only.

        For the given positions, this function will apply periodic
        boundary conditions to one dimension only. This can be useful
        for instance in connection with order parameters.

        Parameters
        ----------
        pos : float
            Coordinate to wrap.
        dim : int
            This selects the dimension to consider.
        """
        return

    @abstractmethod
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
        return

    @abstractmethod
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
        return

    @abstractmethod
    def pbc_dist_coordinate(self, distance):
        """Apply periodic boundaries to a distance.

        This will apply periodic boundaries to a distance. Note that the
        distance can be a vector, but not a matrix of several distance
        vectors.

        Parameters
        ----------
        distance : numpy.array with shape `(self.dim,)`
            A distance vector.

        Returns
        -------
        out : numpy.array, same shape as parameter `distance`
            The periodic-boundary wrapped distance vector.
        """
        return

    def print_length(self, fmt=None):
        """Return a string with box lengths. Can be used for output."""
        if fmt is None:
            return ' '.join(('{}'.format(i) for i in self.cell))
        return ' '.join((fmt.format(i) for i in self.cell))

    def restart_info(self):
        """Return a dictionary with restart information."""
        info = {
            'length': self.cell,
            'periodic': self.periodic,
            'low': self.low,
            'high': self.high,
        }
        return info

    def __str__(self):
        """Return a string describing the box.

        Returns
        -------
        out : string
            String with type of box, extent of the box and
            information about the periodicity.
        """
        boxstr = []
        if len(self.cell) <= 3:
            boxstr.append('Orthogonal box:')
        else:
            boxstr.append('Triclinic box:')
        for i, periodic in enumerate(self.periodic):
            low = self.low[i]
            high = self.high[i]
            msg = 'Dim: {}, Low: {}, high: {}, periodic: {}'
            boxstr.append(msg.format(i, low, high, periodic))
        cell = self.print_length()
        boxstr.append('Cell: {}'.format(cell))
        return '\n'.join(boxstr)


class RectangularBox(BoxBase):
    """An orthogonal box."""

    def __init__(self, low=None, high=None, length=None, periodic=None):
        super().__init__(low=low, high=high, length=length, periodic=periodic)

    def calculate_volume(self):
        """Calculate the volume of the box.

        Returns
        -------
        out : float
            The volume of the box.
        """
        return product(self.length)

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
                delta = np.where(
                    np.logical_or(relpos < 0.0, relpos >= length),
                    relpos - np.floor(relpos * ilength) * length,
                    relpos
                )
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

        Note
        ----
        This will modify the given input matrix inplace. This can be
        changed by setting ``pbcdist = np.copy(distance)``.
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
        distance : numpy.array with shape `(self.dim,)`
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


class TriclinicBox(BoxBase):
    """An triclinic box."""

    def __init__(self, low=None, high=None, length=None, periodic=None):
        super().__init__(low=low, high=high, length=length, periodic=periodic)

    def calculate_volume(self):
        """Calculate the volume of the box.

        Returns
        -------
        out : float
            The volume of the box.
        """
        return det(self.box_matrix)

    def pbc_coordinate_dim(self, pos, dim):
        """Apply periodic boundaries to a selected dimension only."""
        raise NotImplementedError

    def pbc_wrap(self, pos):
        """Apply periodic boundaries to the given position."""
        raise NotImplementedError

    def pbc_dist_matrix(self, distance):
        """Apply periodic boundaries to a distance matrix/vector."""
        raise NotImplementedError

    def pbc_dist_coordinate(self, distance):
        """Apply periodic boundaries to a distance."""
        raise NotImplementedError
