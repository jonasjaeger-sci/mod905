# -*- coding: utf-8 -*-
"""
This is a simple example of how pyretis can be used
for running an umbrella simulation.

In this simulation, we study a particle moving in a one-dimensional
potential energy landscape and the goal is to determine this
landscape by performing umbrella simulations.
"""
from __future__ import print_function
from retis.core import UmbrellaWindowSimulation, System
from retis.core import montecarlo as mc
from retis.forcefield import ForceField, DoubleWell, RectangularWell
import numpy as np 

# Define system with a temperature in K
system = System(temperature=500, units='eV/K') 
# We will only have one particle in the system:
system.add_particle(name='X', pos=np.array([-0.7]))
# In this particular example, we are going to use
# a simple double well potential
potential_dw = DoubleWell(a=1, b=1, c=0.02)
# and a rectangular well potential
potential_rw = RectangularWell()
# do set up the unbiased force field
forcefield = ForceField(desc='Double well', potential=[potential_dw])
# and the biased
forcefield_bias = ForceField(desc='Double well with rectangular bias',
                             potential=[potential_dw, potential_rw])
system.forcefield = forcefield_bias 

# Next we create a list containing the location of the
# different umbrellas:
umbrellas = [[-1.0, -0.4], [-0.5, -0.2], [-0.3, 0.0], [-0.1, 0.2], [0.1, 0.4],
             [0.3, 0.6], [0.5, 1.0]]
n_umb = len(umbrellas)
# and we initiate the random number generator we will use
randseed = 1 # seed for random number generator:
mc.seed_random_generator(randseed)
# and define some common variables for the simulations
mincycles = 1e4
maxdx = 0.1 # maximum allowed displacement in the MC step(s).

# In pyretis, a simulation is defined by defining certain tasks
# the simulation will perform. Here we need to create a task
# to perform Monte Carlo moves to sample the potential energy.
# Let's make use of the predefined method `max_displace_step`
# defined in the `retis.core.montecarlo` module which we 
# have imported as `mc`.
def mc_task(system, maxdx):
    """
    Function to perform monte carlo moves.
    Will update positions and potential energy as needed.
    """
    accepted_r, v_pot, r_trial, v_trial, status = mc.max_displace_step(system, maxdx=maxdx)
    if status:
        system.particles.pos = accepted_r
        system.v_pot = v_trial

# For convenience, we also create a function to
# store all accepted positions and energies
def record(system, traj_prop, ener_prop): 
    """
    Function to store positions and energy
    Here, in case we use more than one particle, we will
    simply replicate the energy of the system correspondingly.
    """
    for ri in system.particles.pos:
        traj_prop.append(ri)
        ener_prop.append(system.v_pot)


trajectory, energy = [], [] # to store all trajectories & energies
# we run all the umbrella simulations by looping over 
# the different umbrellas we defined:
print('Starting simulations:')
for i, umbrella in enumerate(umbrellas):
    print('Running umbrealla no: {} of {}. Location: {}'.format(i+1, n_umb, umbrella))
    # Move rectangular potential to correct place:
    params = {'left': umbrella[0], 'right': umbrella[1]}
    system.forcefield.update_potential_parameters(potential_rw, params)
    system.potential() # recalculate potential energy
    over = umbrellas[min(i+1, n_umb-1)][0] # position we must cross
    # Initiate the umbrella simulation:
    simulation = UmbrellaWindowSimulation(umbrella=umbrella, overlap=over, 
                                          mincycle=mincycles)
    # Also create empy list for storing some data:
    traj, ener = [], []
    # let us add the two task we defined previously:
    task_monte_carlo = {'func':mc_task, 'args':[system],
                        'kwargs':{'maxdx':maxdx}}
    task_record = {'func':record, 'args':[system, traj, ener]}
    simulation.task = [task_monte_carlo, task_record]

    while not simulation.is_finished(system):
        simulation.step()
    trajectory.append(np.array(traj))
    energy.append(np.array(ener))
    print('Done. Cycles: {}'.format(simulation.cycle['step']-simulation.cycle['start'])) 

# We can now post-process the simulation output.
from retis.analysis.histogram import histogram, match_all_histograms
bins = 100
lim = (-1.1, 1.1)
histograms = [histogram(traj, bins=bins, limits=lim) for traj in trajectory]
# extract the bins (the midpoints) and the bin-width:
bin_x = histograms[0][-1]
dbin = bin_x[1]-bin_x[0]
# We are going to match these histograms:
print('Matching histograms...')
histograms_s, _, hist_avg = match_all_histograms(histograms, umbrellas)

# let us create some simple plots using matplotlib:
from matplotlib import pyplot as plt
# first, let us plot the matched histograms on a log-scale:
print('Plotting matched histograms')
fig = plt.figure()
ax = fig.add_subplot(111)
ax.set_yscale('log')
ax.set_xlabel('Position ($x$)', fontsize='large')
ax.set_ylabel('Matched histograms', fontsize='large')
colors = ['blue', 'green', 'darkviolet', 'brown', 'gray', 'crimson', 'cyan']
for i, histo in enumerate(histograms_s):
    ax.bar(bin_x-0.5*dbin, histo, dbin, color=colors[i], alpha=0.6, log=True)
ax.plot(bin_x, hist_avg, lw=7, color='orangered', alpha=0.6, label='Average after matching')
ax.legend()
plt.xlim((-1.1, 1.1))

print('Plotting the free energy')
fig2 = plt.figure()
ax2 = fig2.add_subplot(111)
xv = np.linspace(-2, 2, 1000)
F = -np.log(hist_avg)/system.temperature['beta'] # free energy
V = np.array([forcefield.evaluate_potential(pos=xi) for xi in xv]) # unbiased potetnial
F += (V.min()-F.min())
ax2.plot(xv, V, 'blue', lw=3, label='Unbiased potential', alpha=0.5)
ax2.plot(bin_x, F, lw=7, alpha=0.5, color='green', label='Free energy')
ax2.set_xlabel('Position ($x$)', fontsize='large')
ax2.set_ylabel('Potential energy ($V(x)$) / eV', fontsize='large')
ax2.legend()
plt.xlim((-1.1, 1.1))
plt.ylim((-0.3, 0.05))
plt.show()

