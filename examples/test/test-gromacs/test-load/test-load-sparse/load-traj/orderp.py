# -*- coding: utf-8 -*-
# Copyright (c) 2023, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""
This file defines the order parameter used for the GROMACS example.

NOTE: This file is NOT being used, it is kept as an example on how to use
      mdtraj.
      To test this file, add module = orderp.py in the Orderparameter section
      of retis-load-rc.rst file.
      Also add the import mdtraj import to the list above.

"""
import logging
import mdtraj as md
from itertools import combinations
from pyretis.orderparameter import OrderParameter
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
logger.addHandler(logging.NullHandler())


class Distance(OrderParameter):
    """Distance(OrderParameter).

    This class computes the distance between the O of water using mdtraj.

    Attributes
    ----------
    name : string
        A human-readable name for the order parameter.

    """

    def __init__(self, index):
        """Set up the order parameter.

        Parameters
        ----------
        index : tuple of ints
            This is the indices of the atom we will use the position of.

        """
        super().__init__(description='Water molecule distance')
        self.idx1 = index[0]
        self.idx2 = index[1]
        self.top = 'gromacs_input/conf.gro'

    def calculate(self, system):
        """Calculate the order parameter.

        Here, the order parameter is just the distance between two
        particles.

        Parameters
        ----------
        system : object like `System` from `pyretis.core.system`
            This object is used to import the file names required
            for mdtraj.

        Returns
        -------
        out : float
            The order parameter.

        """
        file_gro = system.particles.config[0]
        trj = md.load(file_gro, top=self.top)
        atom_pair = combinations([self.idx1, self.idx2], 2)
        orderp = md.compute_distances(trj, atom_pair, periodic=True)
        return orderp[0]
