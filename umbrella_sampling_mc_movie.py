#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
"""
Example of running a simulation
"""
from retis.core.simulation import Simulation
from retis.core.system import System
from retis.forcefield.onedimpot import DoubleWell

import numpy as np # use numpy array for positions, velocities etc...

# set up the simulation:
simulation = Simulation() # create a new simulation

# set up the system we are going to simulate "on"
system = System(dim=1) # new empty system
system.forcefield = DoubleWell(a=1, b=1, c=0.02) # select force field
# Next we create particles,
# here it's hard coded:
system.n = 1
system.r = np.zeros(system.n)
system.v = np.zeros(system.n)
system.f = np.zeros(system.n)
system.p = ['X'] # named particle type
system.force() # evaluate the force

