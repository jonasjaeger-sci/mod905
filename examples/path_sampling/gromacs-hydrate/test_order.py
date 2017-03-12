# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""This file tests the Python implementation of the order parameter."""
import logging
import numpy as np
from pyretis.engines.gromacs import read_gromos96_file
from pyretis.core import System, Particles
from orderp import RingDiffusion
from ordermod import ordermod
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


if __name__ == '__main__':
    testo = RingDiffusion()
    print('Idx1', testo.idx1)
    print('Idx2', testo.idx2)
    _, pos, _ = read_gromos96_file('ext_input/conf.g96')
    system = System()
    system.particles = Particles(dim=3)
    system.particles.pos = pos
    print(testo.calculate(system))
    print(ordermod.calculate(pos))
