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
system.add_particle(name='X1', r=np.array([-0.7]))
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
maxcycles = 1e4
# Next, we will define the logic for the umbrella 
# simulation. A simulation object will have certain
# tasks to do, which may be dynamically changed.
# Here, all the umbrella simulations will do the same task,
# and we define these tasks here by defining two functions:
def record(system, traj_prop, ener_prop): 
    """Function to store positions and energy"""
    for ri in system.particles['r']:
        traj_prop.add(ri)
        ener_prop.add(system.v_pot)

randseed = 1 # set seed for random number generator
mc.seed_random_generator(randseed)
maxdx = 0.1 # maximum allowed displacement

def mc_task(system, maxdx):
    """
    Function to perform monte carlo moves.
    Will update positions and potential energy as needed.
    """
    accepted_r, v_pot, v_trial, status = mc.max_displace_step(system, maxdx=maxdx)
    if status:
        system.particles['r'] = accepted_r
        system.v_pot = v_trial

trajectory, energy = [], [] # to store all the trajectories and energies
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
    # Also create properties for storing data:
    traj = Property(desc='Position of the particle')
    ener = Property(desc='Energy of the particle')
    # let us add the two task we defined previously:
    task1 = {'func':mc_task, 'args':[system],
               'kwargs':{'maxdx':maxdx}}
    task2 = {'func':record, 'args':[system, traj, ener], 'kwargs':{}}
    simulation.task = [task1, task2]
    while not simulation.simulation_finished(system):
        simulation.step()
    traj.val = np.array(traj.val)
    traj.dump_to_file('pos-umbrella-{0:03d}.txt'.format(i))
    trajectory.append(traj)
    energy.append(ener)
    print("Umbrella no: {}, cycles: {}".format(i+1, simulation.cycle), 
          "Reached end point: {}".format(np.any(system.particles['r'] > over))) 

# We can now post-process the simulation output.
# Here, we make use of some of the analysis tools in retis:
from retis.analysis.histogram import histogram, match_all_histograms
bins = 100
limits = (-1.2, 1.2)
histograms = [histogram(traj.val, bins=bins, 
                        limits=limits) for traj in trajectory]
# We are going to match these histograms:
histograms_s, _, hist_avg = match_all_histograms(histograms, umbrellas)
# let's also do some very simple plotting
from matplotlib import pyplot as plt
x = histograms[0][2]
xv = np.linspace(-2, 2, 1000)
F = -np.log(hist_avg)/system.beta # free energy
V = np.array([forcefield.evaluate_potential(r=xi) for xi in xv]) # unbiased potetnial
F += (V.min()-F.min())
plt.plot(xv, V, 'b-', label='Unbiased potential')
plt.plot(x, F, lw=10, alpha=0.4, color='green', label='Free energy')
plt.legend()
plt.xlim((-1, 1))
plt.ylim((-0.3, 0.05))
plt.show()

# we can also create a animations:
from matplotlib import animation
fig = plt.figure()
ax = plt.axes(xlim=(-1.05, 1.05), ylim=(-0.3, 0.05))
line, = ax.plot(xv, V, lw=2)
linec = ax.axvline(x=None, lw=2, ls=':', color='black')
axvl = ax.axvspan(xmin=None, xmax=None, color="0.7", alpha=0.4)
axvr = ax.axvspan(xmin=None, xmax=None, color="0.7", alpha=0.4)
scat = ax.scatter(None, None, s=100, c='green')#, alpha=0.8)

umpos1 = umbrellas[0][0]
umpos2 = umbrellas[0][1]

traj_data = []
ener_data = []
umbr = [] # id of current umbrella
crossing = [] # position that must be crossed
for i, (traj, ener) in enumerate(zip(trajectory, energy)):
    r, e = traj.val[::50], ener.val[::50]
    traj_data.extend(r)
    ener_data.extend(e)
    umbr.extend([i]*len(r))
    if (i+1) == len(umbrellas):
        crossing.extend([1.5]*len(r))
    else:
        crossing.extend([umbrellas[i+1][0]]*len(r))

def init():
    # function to draw a clear frame
    line.set_ydata(V)
    return line, #, axv

def update(i):
    #global umpos1, umpos2
    p = np.array([traj_data[i], ener_data[i]])
    scat.set_offsets(p)
    linec.set_xdata(crossing[i])
    umpos1 = umbrellas[umbr[i]][0]
    umpos2 = umbrellas[umbr[i]][1]
    a = np.array([[-1.1, 0.0], [-1.1, 1.0],
                 [umpos1, 1.0], [umpos1, 0.0],
                 [-1.1, 0.0]])

    b = np.array([[umpos2, 0.0], [umpos2, 1.0],
                 [1.1, 1.0], [1.1, 0.0],
                 [umpos2, 0.0]])
    axvr.set_xy(b)
    axvl.set_xy(a)
    return scat, axvl, axvr, linec

anim = animation.FuncAnimation(fig, update, np.arange(len(traj_data)), 
        init_func=init,interval=25, blit=True)

plt.show()



