# -*- coding: utf-8 -*-
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
    """Create a potential according to the given integrator settings.

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
    potential_map = {'doublewell': {'cls': DoubleWell,
                                    'kwargs': {'a', 'b', 'c', 'desc'}},
                     'rectangularwell': {'cls': RectangularWell,
                                         'kwargs': {'left', 'right', 'desc'}},
                     'pairlennardjonescut': {'cls': PairLennardJonesCut,
                                             'kwargs': {'dim', 'shift',
                                                        'desc'}},
                     'pairlennardjonescutnp': {'cls': PairLennardJonesCutnp,
                                               'kwargs': {'dim', 'shift',
                                                          'desc'}},
                     'doublewellwca': {'cls': DoubleWellWCA,
                                       'kwargs': {'dim', 'desc'}}}
    return generic_factory(settings, potential_map, name='potential')
