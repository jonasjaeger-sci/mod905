# -*- coding: utf-8 -*-
"""
Example of running a simulation
"""
from __future__ import print_function
# first we need to import the retis simulation library
# here, we only import the functions we need
from retis.core import UmbrellaSimulation, System
from retis.core import montecarlo as mc
from retis.forcefield import ForceField, DoubleWell, RectangularWell
# we will also use the numpy library for positions, velocities etc...
import numpy as np 

# Let's set up the simulation.
# We begin by defining the system we will simulate.
system = System(dim=1, temperature=500, units='eV/K') 
# Lets add a particle to this system
system.add_particle(name='X1', pos=np.array([-0.7]))
# We also need to set up the force field.
# We do this by combining two potential functions:
# 1) A double well potential
potential_dw = DoubleWell(a=1, b=1, c=0.02)
# 2) A rectangular well
potential_rw = RectangularWell()
forcefield = ForceField(desc='Double well', potential=[potential_dw])

forcefield_bias = ForceField(desc='Double well with rectangular bias',
                             potential=[potential_dw, potential_rw])

system.forcefield = forcefield_bias # attach biased force field to the system

# Now we need to define the simulation. Here we define several
# small umbrella simulations, which we will link together with this script.
# We select the placement of the umbrellas:
umbrellas = [[-1.0, -0.4], [-0.5, -0.2], [-0.3, 0.0], [-0.1, 0.2], 
             [0.1, 0.4], [0.3, 0.6], [0.5, 1.0]]
n_umb = len(umbrellas)
# and just define some parameters for the simulation
maxcycles = 1e4
randseed = 1 # seed for random number generator:
mc.seed_random_generator(randseed)
maxdx = 0.1 # maximum allowed displacement

# Next, we will define some tasks we want
# do to during the simulation. 
# We need to perform the actual umbrella sampling
def mc_task(system, maxdx):
    """
    Function to perform monte carlo moves.
    Will update positions and potential energy as needed.
    """
    accepted_r, v_pot, r_trial, v_trial, status = mc.max_displace_step(system, maxdx=maxdx)
    if status:
        system.particles.pos = accepted_r
        system.v_pot = v_trial

# and we need to record the positions for later analysis:  
def record(system, traj_prop, ener_prop): 
    """
    Function to store positions and energy
    Here, in case we use more than one particle, we will
    simply replicate the energy of the system correspondingly.
    """
    for ri in system.particles.pos:
        traj_prop.append(ri)
        ener_prop.append(system.v_pot)


trajectory, energy = [], [] # to store all  trajectories/energies
# we run all the umbrella simulations by looping over 
# the different umbrellas we defined:
print('Starting simulations:')
for i, umbrella in enumerate(umbrellas):
    print('Running umbrealla no: {} of {}. Location: {}'.format(i+1, n_umb, umbrella))
    # Update parameters for the rectangular potential:
    params = {'left': umbrella[0], 'right': umbrella[1]}
    system.forcefield.update_potential_parameters(potential_rw, params)
    system.potential() # recalculate potential energy
    over = umbrellas[min(i+1, n_umb-1)][0] # position we must cross
    # Initiate the umbrella simulation:
    simulation = UmbrellaSimulation(umbrella=umbrella, overlap=over, 
                                    maxcycle=maxcycles)
    # Also create empy list for storing some data:
    traj = []
    ener = []
    # let us add the two task we defined previously:
    task1 = {'func':mc_task, 'args':[system],
               'kwargs':{'maxdx':maxdx}}
    task2 = {'func':record, 'args':[system, traj, ener], 'kwargs':{}}
    simulation.task = [task1, task2]

    while not simulation.is_finished(system):
        simulation.step()
    #traj.dump_to_file('pos-umbrella-{0:03d}.txt'.format(i))
    trajectory.append(np.array(traj))
    energy.append(np.array(ener))
    print('Done. Cycles: {}'.format(simulation.cycle)) 

# We can now post-process the simulation output.
# Here, we make use of some of the analysis tools in retis:
from retis.analysis.histogram import histogram, match_all_histograms
bins = 100
lim = (-1.2, 1.2)
histograms = [histogram(traj, bins=bins, limits=lim) for traj in trajectory]
# We are going to match these histograms:
histograms_s, _, hist_avg = match_all_histograms(histograms, umbrellas)

# let's also create a simple plot of the
# potential and the free energy.
from matplotlib import pyplot as plt
x = histograms[0][2]
xv = np.linspace(-2, 2, 1000)
F = -np.log(hist_avg)/system.beta # free energy
V = np.array([forcefield.evaluate_potential(pos=xi) for xi in xv]) # unbiased potetnial
F += (V.min()-F.min())
plt.plot(xv, V, 'b-', label='Unbiased potential')
plt.plot(x, F, lw=10, alpha=0.4, color='green', label='Free energy')
plt.legend()
plt.xlim((-1, 1))
plt.ylim((-0.3, 0.05))
plt.show()

