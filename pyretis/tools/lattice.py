# -*- coding: utf-8 -*-
"""Some convenient methods for generating initial structures.

This module defines a function which may be useful for generating
initial structures on a lattice.

Examples
--------
>>> from pyretis.tools.lattice import generate_lattice

>>> xyz = generate_lattice('diamond', [1, 1, 1], lcon=1)
"""
import itertools
import numpy as np


__all__ = ['generate_lattice']


UNIT_CELL = {'sc': np.array([[0.0, 0.0, 0.0]]),
             'sq': np.array([[0.0, 0.0]]),
             'sq2': np.array([[0.0, 0.0], [0.5, 0.5]]),
             'bcc': np.array([[0.0, 0.0, 0.0], [0.5, 0.5, 0.5]]),
             'fcc': np.array([[0.0, 0.0, 0.0], [0.5, 0.5, 0.0],
                              [0.0, 0.5, 0.5], [0.5, 0.0, 0.5]]),
             'hcp': np.array([[0.0, 0.0, 0.0], [0.5, 0.5, 0.0],
                              [0.5, 5.0/6.0, 0.5], [0.0, 1.0/3.0, 0.5]]),
             'diamond': np.array([[0.0, 0.0, 0.0], [0.0, 0.5, 0.5],
                                  [0.5, 0.0, 0.5], [0.5, 0.5, 0.0],
                                  [0.25, 0.25, 0.25], [0.25, 0.75, 0.75],
                                  [0.75, 0.25, 0.75], [0.75, 0.75, 0.25]])}


def generate_lattice(lattice, repeat, lcon=None, density=None):
    """Generate points on a simple lattice.

    The lattice is one of the defined keys in the global variable
    `UNIT_CELL`. This lattive will be reapeaded a number of times.
    The lattice spacing can be given explicitly, or it can be given
    implicitly by the number density.

    Parameters
    ----------
    lattice : string
        Select the kind of lattice. The following options are currently
        defined in `UNIT_CELL`:

        * sc : simple cubic lattice
        * sq : square lattice (2D) with one atom in the unit cell.
        * sq2 : square lattice with two atoms in the unit cell.
        * bcc : body-centered cubic lattice
        * fcc : face-centered cubic lattice
        * hcp : hexagonal close-packed lattice
        * diamond : a diamond structure
    lcon : float
        The lattice constant.
    density : float, optional
        A desired density. If this is given, `lcon` is calculated.
    repeat : list of ints
        `repead[i]` is the number of repetitions in the `i` direction.

    Returns
    -------
    positions : numpy.array
        The lattice positions.
    size : list of floats
        The corresponding size(s), can be used to define a simulation box.
    """
    try:
        unit_cell = UNIT_CELL[lattice.lower()]
    except KeyError:
        msg = 'Unknown lattice "{}" requested!'.format(lattice)
        raise ValueError(msg)
    ndim = len(unit_cell[0])
    npart = len(unit_cell)
    if density is not None:
        lcon = (npart / density)**(1.0 / float(ndim))
    if lcon is None:
        msg = 'Could not determine lattice constant!'
        raise ValueError(msg)
    positions = []
    if ndim == 2:
        nrx = repeat[0]
        nry = repeat[1]
        for i in itertools.product(range(nrx), range(nry)):
            pos = lcon * (np.array(i) + unit_cell)
            positions.extend(pos)
        size = [[0.0, i * lcon] for i in (nrx, nry)]
    elif ndim == 3:
        nrx = repeat[0]
        nry = repeat[1]
        nrz = repeat[2]
        for i in itertools.product(range(nrx), range(nry), range(nrz)):
            pos = lcon * (np.array(i) + unit_cell)
            positions.extend(pos)
        size = [[0.0, i * lcon] for i in (nrx, nry, nrz)]
    else:
        msg = 'Can not create lattices with dimensionality "{}".'
        raise ValueError(msg.format(ndim))
    positions = np.array(positions)
    return positions, size
