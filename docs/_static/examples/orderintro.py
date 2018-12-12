# -*- coding: utf-8 -*-
# Copyright (c) 2018, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Example of interaction with a OrderParameter"""
import numpy as np
from pyretis.core import System, Particles
from pyretis.orderparameter import OrderParameterPosition

system = System(temperature=1, units='reduced')
system.particles = Particles(dim=3)
system.add_particle([1.0, 2.0, 3.0], mass=1.0, name='Ar', ptype=0)

position = OrderParameterPosition(0, dim='x')
print('Order =', position.calculate(system))
print('Order =', position.calculate_all(system))


# Let's define additional collective variables:
def collective_y(syst):
    """Position along y-axis."""
    return [syst.particles.pos[0][1]]


def collective_2(syst):
    """Additional collective variable."""
    return [np.cos(np.pi * syst.particles.pos[0][2])]


position.add_orderparameter(collective_y)
position.add_orderparameter(collective_2)
print('Order =', position.calculate(system))
print('Order =', position.calculate_all(system))
