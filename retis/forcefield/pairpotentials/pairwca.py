# -*- coding: utf-8 -*-
"""
This file contains a WCA pair potential
"""
from __future__ import absolute_import
from .pairlennardjones import PairLennardJonesCutnp

__all__ = ['PairWCAnp']

class PairWCAnp(PairLennardJonesCutnp):
    """
    A simple WCA potential, based on the PairLennardJonesCutnp class.
    It is equal to the LJ potential with a shift of the energy and
    a cut-off set at sigma*2.**(1./6.)
    """
    def __init__(self, dim=3, mixing='geometric',
                 desc='WCA potential'):
        super(PairWCAnp, self).__init__(dim=dim, desc=desc, shift=True,
                                        factor=2.**(1./6.))
