# Copyright (c) 2023, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""This file contains classes to represent order parameters.

The order parameters are assumed to all be completely determined
by the system properties and they will all return at least one
value - the order parameter itself. The order parameters can also
return several order parameters which can be used for further analysis.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Position (:py:class:`.Position`)
    An order parameter equal to the position of a particle.

AreaAndVolume (:py:class:`.AreaAndVolume`)
    An order parameter equal to the Area or Volume of a group of a particles.

"""
import logging
import numpy as np
from scipy.spatial import ConvexHull
from pyretis.orderparameter import OrderParameter
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
logger.addHandler(logging.NullHandler())


class AreaAndVolume(OrderParameter):
    """AreaAndVolume(OrderParameter).

    This order parameter calculates the area of the six-membered ring
    which the methane molecule jumps through when performing the L6L jump,
    and the volume of the starting cage.

    Attributes:
    ----------
    periodic : boolean
        This determines if periodic boundaries should be applied to
        the position or not.

    """

    def __init__(self, periodic=True):
        """Initialize the class."""
        super().__init__(description="Area of ring and volume "
                                     "of starting cage")
        self.periodic = periodic
        self.idx1 = np.array([220, 252, 412, 444, 796], dtype='i4')
        self.idx2 = np.array([220, 252, 284, 316, 412, 444, 540, 604,
                              668, 700, 796, 828, 924, 988, 1052, 1084,
                              1180, 1212, 1308, 1340, 1372, 1404, 1436, 1468],
                             dtype='i4')

    def calculate(self, system):
        """Calculate area and volume."""
        pos = system.particles.pos
        ar_ring = ConvexHull(pos[self.idx1]).area
        vol_cage = ConvexHull(pos[self.idx2]).volume
        return [ar_ring, vol_cage]


class Position(OrderParameter):
    """A positional order parameter.

    This class defines a very simple order parameter which is just
    the position of a given particle.

    Attributes
    ----------
    index : integer
        This is the index of the atom which will be used, i.e.
        ``system.particles.pos[index]`` will be used.
    dim : integer
        This is the dimension of the coordinate to use.
        0, 1 or 2 for 'x', 'y' or 'z'.
    periodic : boolean
        This determines if periodic boundaries should be applied to
        the position or not.

    """

    def __init__(self, index, dim='x', periodic=False):
        """Initialise the order parameter.

        Parameters
        ----------
        index : int
            This is the index of the atom we will use the position of.
        dim : string
            This select what dimension we should consider,
            it should equal 'x', 'y' or 'z'.
        periodic : boolean, optional
            This determines if periodic boundary conditions should be
            applied to the position.

        """
        txt = 'Position of particle {} (dim: {})'.format(index, dim)
        super().__init__(description=txt, velocity=False)
        self.periodic = periodic
        self.index = index
        self.dim = {'x': 0, 'y': 1, 'z': 2}.get(dim, None)
        if self.dim is None:
            msg = 'Unknown dimension {} requested'.format(dim)
            raise ValueError(msg)

    def calculate(self, system):
        """Calculate the position order parameter.

        Parameters
        ----------
        system : object like :py:class:`.System`
            The object containing the positions.

        Returns
        -------
        out : list of floats
            The position order parameter.

        """
        particles = system.particles
        pos = particles.pos[self.index]
        lamb = pos[self.dim]
        if self.periodic:
            lamb = system.box.pbc_coordinate_dim(lamb, self.dim)
        return [lamb]
