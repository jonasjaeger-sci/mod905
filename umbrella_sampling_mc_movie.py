#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
"""
Example of running a simulation
"""
# first we need to import the retis simulation library
# here, we only import the functions we need
from retis.core import UmbrellaSimulation, System, Property
from retis.core import montecarlo as mc
from retis.forcefield import ForceField
from retis.forcefield.potentials import DoubleWell, RectangularWell
# we will also use the numpy library for positions, velocities etc...
import numpy as np 

# Let's set up the simulation.
# We begin by defining the system we will simulation "on":
system = System(dim=1, temperature=500, units='eV/K') 
# Lets add a particle to this system
system.add_particle(name='X', r=np.array([-0.7]))
# We also need to set up the force field.
# We do this by combining potential functions.
# Here, we select two pre-defined potential functions,
# a duoble well potential and a rectangular well potential.
# The rectangular well will be used as a bias potential.
potential_dw = DoubleWell(a=1, b=1, c=0.02)
potential_rw = RectangularWell()
forcefield = ForceField(desc='Double well', potential=[potential_dw])
forcefield_bias = ForceField(desc='Double well with rectangular bias',
                             potential=[potential_dw, potential_rw])

system.forcefield = forcefield_bias # attach force field to the system

# Now we need to define the simulation. Here we define several
# small umbrella simulations, which we will link together with this script.
# We select the placement of the umbrellas
umbrellas = [[-1.0, -0.4], [-0.5, -0.2], [-0.3, 0.0], [-0.1, 0.2], 
             [0.1, 0.4], [0.3, 0.6], [0.5, 1.0]]
# and just define some parameters for the simulation:
maxcycles = 100000
# Next, we will define the logic for the umbrella 
# simulation. A simulation object will have certain
# tasks to do, which may be dynamically changed.
# Here, all the umbrella simulations will do the same task,
# and we define these tasks here by defining two functions:
def record_positions(system, traj): 
    """Function to store positions"""
    traj.add(system.r)
randseed = 1 # set seed for random number generator
mc.seed_random_generator(randseed)
maxdx = 0.1 # maximum allowed displacement
def mc_task(system, maxdx):
    """
    Function to perform monte carlo moves.
    Will update positions and potential energy as needed.
    """
    r, v_pot, v_trial, status = mc.max_displace_step(system, maxdx=maxdx)
    if status:
        system.r = r
        system.v_pot = v_trial

trajectory = [] # to store all the trajectories

# we run all the umbrella simulations by looping over the different
# umbrellas we defined:
for i, umbrella in enumerate(umbrellas):
    # we need to update the position of the bias potential and recalculate:
    potential_rw.update_left_right(*umbrella) 
    system.potential()
    # this defines the point we must cross in the simulation:
    if (i+1)==len(umbrellas):
        over = umbrellas[i][0]
    else:
        over = umbrellas[i+1][0]
    # Now, we can define the actual simulation:
    simulation = UmbrellaSimulation(umbrella=umbrella, overlap=over, 
                                    maxcycle=maxcycles)
    # we also create a new property, which we use to record the trajectory:
    traj = Property(desc='Position of the particle')
    # let us add the two task we defined previously:
    task1 = {'func':mc_task, 'args':[system],
               'kwargs':{'maxdx':maxdx}}
    task2 = {'func':record_positions, 'args':[system, traj], 'kwargs':{}}
    simulation.task = [task1, task2]
    while simulation.step(system):
        pass
    traj.dump_to_file('pos-umbrella-{0:03d}.txt'.format(i))
    trajectory.append(traj)
    print("Umbrella no: {}, cycles: {}".format(i+1, simulation.cycle), 
          "Reached end point: {}".format(system.r[0]>over)) 

# We can now post-process the simulation output.
# Here, we make use of some of the analysis tools in retis:
from retis.analysis.histogram import histogram, match_all_histograms
bins = 101
limits = (-1.2, 1.2)
histograms = [histogram(traj.val, bins=bins, 
                        limits=limits) for traj in trajectory]
# We are going to match these histograms:
histograms_s, scale_factor, hist_avg = match_all_histograms(histograms, umbrellas)
# let's also do some very simple plotting
from matplotlib import pyplot as plt
x = histograms[0][2]
F = -np.log(hist_avg)/system.beta
r = np.linspace(-1,1,100)
V = forcefield.evaluate_potential(r)
shift = V.min()-F.min()
F += shift
# Plot unbiased potential and free energy::
plt.plot(r,V,'b-', label='Unbiased potential')
plt.plot(x, F, lw=10, alpha=0.4, color='green', label='Free energy')
plt.legend()
plt.show()

#for h in histograms_s:
#    plt.plot(x,h)
#plt.plot(x, hist_avg, lw=10, alpha=0.4)
#plt.show()


