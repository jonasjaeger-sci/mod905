#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
"""
Example of running a simulation
"""
# first we need to import the retis simulation library
# here, we only import the functions we need
from retis.core.simulation import Simulation, UmbrellaSimulation
from retis.core.system import System
from retis.core.properties import Property
from retis.forcefield.forcefield import ForceField
from retis.forcefield.onedimpot import DoubleWell, RectangularWell
import retis.core.montecarlo as mc
# we will also use the numpy library for positions, velocities etc...
import numpy as np 

# Now, set up the simulation
# first we just select some potential functions
# to use in the force field:
potential_dw = DoubleWell(a=1, b=1, c=0.02)
potential_rw = RectangularWell()
forcefield = ForceField(desc='Unbiased double well', 
                        potential=[potential_dw])
forcefield_bias = ForceField(desc='Double well with rectangular bias',
                             potential=[potential_dw, potential_rw])

# Then we create the system we will simulate "on":
system = System(dim=1, temperature=500, units='eV/K') 
system.forcefield = forcefield_bias # attach force field
# Next we create particles, here it's hard coded:
system.n = 1
system.r = np.array([-0.7])
system.v = np.zeros(system.n)
system.f = np.zeros(system.n)
system.p = ['X']*system.n # named particle type

# Now we need to define the simulation
# The simulation will act on the system
# and it may consist of several steps
# or "sub-simulations"
# Here we create a overall simulation that
# will run several small simulations.
# each of the small simulations are in fact a
# umbrella simulation.

# set up the simulation we will run on the system:
simulation = Simulation() # create a new simulation
# add properties relevant for the umbrella simulation:
umbrellas = [[-1.0, -0.4],
             [-0.5, -0.2], 
             [-0.3, 0.0], 
             [-0.1, 0.2], 
             [0.1, 0.4], 
             [0.3, 0.6], 
             [0.5, 1.0]]

simulation.randseed = 1 # set seed for random number generator
# initialize random 
mc.seed_random_generator(simulation.randseed)

simulation.maxcycles = 10000
system.forcefield = forcefield_bias
trajectory = [] # to store trajectories

for i, umbrella in enumerate(umbrellas):
    potential_rw.update_left_right(*umbrella) # update bias potential
    system.potential() # recalculate potential energy with new potential
    try:
        over = umbrellas[i+1]
    except:
        over = umbrellas[i]

    u_simulation = UmbrellaSimulation(umbrella=umbrella, 
                                      overlap=over,
                                      maxcycle=simulation.maxcycles)
    traj = Property(desc='Position of the particle') # to record the trajectory

    # let us define a monte carlo task:
    def mc_task(system, maxdx=0.1):
        r, v_pot, v_trial, status = mc.max_displace_step(system, maxdx=maxdx)
        if status:
            system.r = r
            system.v_pot = v_trial
    # add another task to store the positions:
    def record_positions(system, traj):
        traj.add(system.r)

    task1 = {'func':mc_task, 'args':[system],
               'kwargs':{'maxdx':0.1}}
    task2 = {'func':record_positions, 'args':[system, traj], 'kwargs':{}}

    u_simulation.task = [task1, task2]
    # run umbrella simulation
    while u_simulation.step(system):
        #print(u_simulation.cycle)
        pass
    print(u_simulation.cycle)
    #traj.dump_to_file('pos-umbrella-{0:03d}.txt'.format(i))
    trajectory.append(traj)
    print("Done", system.r, umbrellas[i][0], simulation.cycle)

# now, we need to do some post processing
# of the trajectories we have obtained
# we need to get the histograms:
from retis.analysis.histogram import histogram, match_histograms
bins = 48
#bins = 75
limits = (-1.2, 1.2)
histograms = [histogram(traj.val, bins=bins, 
                        limits=limits) for traj in trajectory]
# we need to rescale them to match
histograms_s, scale_factor = [histograms[0][0]], [1.0]
x = histograms[0][2]
for i in range(len(umbrellas)-1):
    limits = (umbrellas[i+1][0], umbrellas[i][1])
    matched, s = match_histograms(histograms_s[-1], 
                                  histograms[i+1][0], x, limits)
    histograms_s.append(matched)
    scale_factor.append(s)
print(scale_factor)

hist_avg = []
for i,xi in enumerate(x):
    h = 0.0
    n = 0.0
    for k,u in enumerate(umbrellas):
        if u[0]<= xi <u[1]:
            h += histograms_s[k][i]
            n += 1.0
    if n > 0.0:
        h /= n
    hist_avg.append(h)

# let's also do some very simple plotting
from matplotlib import pyplot as plt
for h in histograms_s:
    plt.plot(x,h)
plt.plot(x, hist_avg, lw=10, alpha=0.4)
#plt.semilogy()
#for h in histograms:
#    plt.plot(x,h[0])
plt.show()

# plot the unbiased potential:
r = np.linspace(-1,1,100)
V = forcefield.evaluate_potential(r)
plt.plot(r,V,'b-')
plt.show()

