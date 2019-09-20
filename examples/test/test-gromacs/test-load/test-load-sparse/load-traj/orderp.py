# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""This file defines the order parameter used for the GROMACS example."""
import os
import logging
from itertools import combinations
import mdtraj as md
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

    def __init__(self, idx1, idx2):
        """Set up the order parameter.

        Parameters
        ----------
        index : tuple of ints
            This is the indices of the atom we will use the position of.

        """
        super().__init__(description='Water molecule distance')
        self.idx1 = idx1
        self.idx2 = idx2

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
        # mdtraj doesn't support .g96
        file_gro = system.particles.config[0]
        file_top = system.particles.top
        if file_gro[-4:] == '.g96':
            file_g96 = system.particles.config[0]
            file_gro = '{}.gro'.format(file_g96[:-4])
            os.system('gmx', 'editconf', '-f', file_g96, '-o', file_gro)

        if file_gro[-4:] in ['.trr', '.xtc']:
            idx_frame = system.particles.config[1]
            trj = md.load_frame(file_gro, idx_frame, top=file_top)
        else:
            trj = md.load(file_gro)
        atom_pair = combinations([self.idx1, self.idx2], 2)
        orderp = md.compute_distances(trj, atom_pair, periodic=True)
        return orderp[0]
