# -*- coding: utf-8 -*-
# Copyright (c) 2023, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""This file defines the order parameter used for the GROMACS example."""
import os
import logging
from pyretis.orderparameter import Distance
from itertools import combinations
from pyretis.orderparameter import OrderParameter
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
logger.addHandler(logging.NullHandler())


class DistanceL(Distance):
    """Distance(OrderParameter).

    This class computes the distance between the O of water using internal
    function.

    Attributes
    ----------
    name : string
        A human-readable name for the order parameter.

    """

    def __init__(self, idx1, idx2):
        """Set up the order parameter."""
        self.index = (idx1, idx2)
        self.periodic = True
