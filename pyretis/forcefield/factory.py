# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""Define a factory for potentials.

Note: This module will probably be deleted and replace with a true
factory method. That is, a class method for the potential function
class. For now, this is a transition module. Don't count on it
being present in the future!
"""
import logging
from pyretis.core.common import generic_factory
from pyretis.forcefield.potentials import (PairLennardJonesCut,
                                           PairLennardJonesCutnp,
                                           DoubleWellWCA,
                                           DoubleWell,
                                           RectangularWell)
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['potential_factory']


def potential_factory(settings):
    """Create a potential according to the given settings.

    This function is included as a convenient way of setting up and
    selecting a potential function.

    Parameters
    ----------
    settings : dict
        This defines how we set up and select the potential.

    Returns
    -------
    out[0] : object like `PotentialFunction`.
        This object represents the potential.
    """
    potential_map = {'doublewell': {'cls': DoubleWell},
                     'rectangularwell': {'cls': RectangularWell},
                     'pairlennardjonescut': {'cls': PairLennardJonesCut},
                     'pairlennardjonescutnp': {'cls': PairLennardJonesCutnp},
                     'doublewellwca': {'cls': DoubleWellWCA}}
    return generic_factory(settings, potential_map, name='potential')
