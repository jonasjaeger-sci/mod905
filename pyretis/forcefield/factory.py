# -*- coding: utf-8 -*-
"""Define a factory for potentials.

Note: This module will probably be deleted and replace with a true
factory method. That is, a class method for the potential function
class. For now, this is a transition module. Don't count on it
being present in the future!
"""
import logging
from pyretis.forcefield.potentials import (PairLennardJonesCut,
                                           PairLennardJonesCutnp,
                                           DoubleWellWCA,
                                           DoubleWell,
                                           RectangularWell)
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['potential_factory']


_CLASS_MAP = {'pairlennardjonescut': PairLennardJonesCut,
              'doublewell': DoubleWell,
              'rectangularwell': RectangularWell,
              'pairlennardjonescutnp': PairLennardJonesCutnp,
              'doublewellwca': DoubleWellWCA}


def potential_factory(settings):
    """Return a potential based in input settings."""
    klass_name = settings['class'].lower()
    klass = _CLASS_MAP[klass_name]
    args = {}
    for key in settings:
        if key == 'class':
            pass
        else:
            args[key] = settings[key]
    potential = klass(**args)
    return potential
