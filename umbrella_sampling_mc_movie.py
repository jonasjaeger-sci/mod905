#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
"""
Example of running a simulation
"""
from retis.core.simulation import Simulation
from retis.core.system import System
from retis.forcefield.forcefield import ForceField
from retis.forcefield.onedimpot import DoubleWell, RectangularWell
import retis.core.montecarlo as mc
import numpy as np # use numpy array for positions, velocities etc...

from matplotlib import pyplot as plt

# set up the system we are going to simulate "on"
system = System(dim=1, temperature=500, units='eV/K') # Create system

# create two force fields by combining potential functions:
potential = DoubleWell(a=1, b=1, c=0.02)

forcefield = ForceField(desc='Unbiased force field', potential=[potential])
bias_potential = RectangularWell()
forcefield_bias = ForceField(desc='Biased potential',
                  potential=[potential, bias_potential])

r = np.linspace(-1,1,100)
V = forcefield.evaluate_potential(r)
fig = plt.figure()
plt.plot(r,V)
#plt.plot(r,V2)
plt.show()
system.forcefield = forcefield
# Next we create particles, here it's hard coded:
system.n = 1
system.r = np.array([-0.7])
system.v = np.zeros(system.n)
system.f = np.zeros(system.n)
system.p = ['X'] # named particle type
# set up the simulation we will run on the system:
simulation = Simulation() # create a new simulation
# add properties relevant for the umbrella simulation:
simulation.umbrellas = [[-0.5, -0.2], 
                        [-0.3, 0.0], 
                        [-0.1, 0.2], 
                        [0.1, 0.4], 
                        [0.3, 0.6], 
                        [0.5, 1.0]]
simulation.randseed = 1 # set seed for random number generator
mc.seed_random_generator(simulation.randseed)
simulation.maxcycles = 1000

system.forcefield = forcefield_bias
system.potential()
print(system.v_pot)
# for the umbrella simulation, we are going
# to simulate over all umbrellas
# for each umbrella, we run the monte carlo
# procedure until we are past it
simulation.task = []
while simulation.umbrellas:
    simulation.cycle = 0 # set current step
    umbrella = simulation.umbrellas.pop(0)
    print(umbrella)
    bias_potential.update_left_right(*umbrella) # update bias potential
    system.potential()
    print(system.v_pot)
    if len(simulation.umbrellas) == 0: break
    while simulation.cycle < simulation.maxcycles and system.r<simulation.umbrellas[0][0]:
        simulation.cycle += 1
        r, v_pot, v_trial, status = mc.max_displace_step(system, maxdx=0.1)
        if status:
            system.r = r
            system.v_pot = v_trial
        print(system.r)
    print("Done", system.r, simulation.umbrellas[0][0], simulation.cycle)




#system.r = np.zeros((system.n, system.dim))
#system.v = np.zeros((system.n, system.dim))
#system.f = np.zeros((system.n, system.dim))

#system.force() # evaluate the force
#system.potential() # evaluate the potential
#print(system.epot)
#print(system.r)


#print(system.r)

