# -*- coding: utf-8 -*-
"""Some convenient methods for generating initial structures.

This module is defining some tools which may be useful for generating
initial structures: ``latticefcc`` will return a fcc lattice and
``lattice_simple_cubic`` will return a simple cubic lattice.
"""
import itertools
import numpy as np


__all__ = ['latticefcc', 'lattice_simple_cubic']


def latticefcc(lcon=None, density=None, nrx=1, nry=1, nrz=1):
    """Generate points on a simple fcc lattice.

    Parameters
    ----------
    lcon : float
        The lattice constant.
    density : float, optional
        A desired density. If this is given, `lcon` is calculated.
    nrx : int
        Number of repetitions of the lattice in the x-direction.
    nry : int
        Number of repetitions of the lattice in the y-direction.
    nrz : int
        Number of repetitions of the lattice in the z-direction.

    Returns
    -------
    positions : numpy.array
        The lattice positions.
    size : list of floats
        The corresponding size(s), can be used to define a simulation box.

    Note
    ----
    Current implementation will only work for a 3D system.
    """
    unit_cell = np.array([[0.0, 0.0, 0.0], [0.5, 0.5, 0.0],
                          [0.0, 0.5, 0.5], [0.5, 0.0, 0.5]])
    npart = 4.0
    if density is not None:
        lcon = (npart/density)**(1.0/3.0)
    if lcon is None:
        raise ValueError
    positions = np.zeros((4 * nrx * nry * nrz, 3))
    j = 0
    for i in itertools.product(range(nrx), range(nry), range(nrz)):
        positions[j:j+4, :] = lcon * (np.array(i) + unit_cell)
        j = j + 4
    size = [[0.0, i * lcon] for i in (nrx, nry, nrz)]
    return positions, size


def lattice_simple_cubic(box, spacing=1.0):
    """Create a simple cubic lattice with the given spacing.

    Parameters
    ----------
    box : list of lists/tuples
        `box[i] = [low, high]` gives the box bounds in dimension `i`
    spacing : float
        the lattice spacing

    Returns
    -------
    positions : numpy.array
        The lattice positions.
    """
    npart = [int(np.floor((boxi[1] - boxi[0]) / spacing)) for boxi in box]
    ranges = [range(i) for i in npart]
    origin = np.array([boxi[0] for boxi in box])
    pos = [origin + spacing * np.array(i) for i in itertools.product(*ranges)]
    positions = np.array(pos)
    avgp = np.average(positions, axis=0)
    newavg = np.array([boxi[0] + 0.5*(boxi[1] - boxi[0]) for boxi in box])
    return positions + (newavg - avgp)
