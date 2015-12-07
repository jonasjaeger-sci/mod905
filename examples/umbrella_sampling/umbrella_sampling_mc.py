# -*- coding: utf-8 -*-
"""
This is a simple example of how pyretis can be used
for running an umbrella simulation.

In this simulation, we study a particle moving in a one-dimensional
potential energy landscape and the goal is to determine this
landscape by performing umbrella simulations.
"""
from __future__ import print_function
from pyretis.core import System, RandomGenerator, Box
from pyretis.inout.settings import create_simulation
from pyretis.forcefield import ForceField
from pyretis.forcefield.potentials import DoubleWell, RectangularWell
from pyretis.analysis import histogram, match_all_histograms
import numpy as np
from matplotlib import pyplot as plt

# Define system with a temperature in K
dummybox = Box(periodic=[False])
mysystem = System(temperature=500, units='eV/K', box=dummybox)
# We will only have one particle in the system:
mysystem.add_particle(name='X', pos=np.array([-0.7]))
# In this particular example, we are going to use
# a simple double well potential
potential_dw = DoubleWell()
# and a rectangular well potential
potential_rw = RectangularWell()
# do set up the unbiased force field
forcefield = ForceField(desc='Double well', potential=[potential_dw])
# and the biased
forcefield_bias = ForceField(desc='Double well with rectangular bias',
                             potential=[potential_dw, potential_rw],
                             params=[{'a': 1.0, 'b': 1.0, 'c': 0.02}, None])
mysystem.forcefield = forcefield_bias

# Next we create a list containing the location of the
# different umbrellas:
umbrellas = [[-1.0, -0.4], [-0.5, -0.2], [-0.3, 0.0], [-0.1, 0.2], [0.1, 0.4],
             [0.3, 0.6], [0.5, 1.0]]
n_umb = len(umbrellas)
# and we initiate the random number generator we will use
RANDSEED = 1  # seed for random number generator:
settings = {'type': 'umbrellawindow'}
settings['rgen'] = RandomGenerator(seed=RANDSEED)
settings['mincycle'] = 10000
settings['maxdx'] = 0.1

trajectory, energy = [], []  # to store all trajectories & energies
# we run all the umbrella simulations by looping over
# the different umbrellas we defined:
print('Starting simulations:')
msg = '\nRunning umbrella no: {} of {}. Location: {}'
for i, umbrella in enumerate(umbrellas):
    print(msg.format(i + 1, n_umb, umbrella))
    # Move rectangular potential to correct place:
    potential_rw.params = {'left': umbrella[0], 'right': umbrella[1]}
    mysystem.potential()  # recalculate potential energy
    settings['umbrella'] = umbrella
    #calculate position we must cross for this window:
    settings['over'] = umbrellas[min(i + 1, n_umb - 1)][0]
    # Create the umbrella simulation :-)
    simulation = create_simulation(settings, mysystem)
    print(simulation)
    # Also create empy list for storing some data:
    traj, ener = [], []
    for result in simulation.run():
        for pos in mysystem.particles.pos:
            traj.append(pos)
            ener.append(mysystem.v_pot)
    trajectory.append(np.array(traj))
    energy.append(np.array(ener))
    print('Done. Cycles: {}'.format(simulation.cycle['step'] -
                                    simulation.cycle['start']))

# We can now post-process the simulation output.
BINS = 100
LIM = (-1.1, 1.1)
histograms = [histogram(traj, bins=BINS, limits=LIM) for traj in trajectory]
# extract the bins (the midpoints) and the bin-width:
bin_x = histograms[0][-1]
dbin = bin_x[1] - bin_x[0]
# We are going to match these histograms:
print('Matching histograms...')
histograms_s, _, hist_avg = match_all_histograms(histograms, umbrellas)

# let us create some simple plots using matplotlib:
# first, let us plot the matched histograms on a log-scale:
print('Plotting matched histograms')
fig = plt.figure()
axs = fig.add_subplot(111)
axs.set_yscale('log')
axs.set_xlabel('Position ($x$)', fontsize='large')
axs.set_ylabel('Matched histograms', fontsize='large')
colors = ['blue', 'green', 'darkviolet', 'brown', 'gray', 'crimson', 'cyan']
for i, histo in enumerate(histograms_s):
    axs.bar(bin_x - 0.5 * dbin, histo, dbin, color=colors[i],
            alpha=0.6, log=True)
axs.plot(bin_x, hist_avg, lw=7, color='orangered', alpha=0.6,
         label='Average after matching')
axs.legend()
axs.set_xlim((-1.1, 1.1))
axs.set_ylim((0.1, 1200))
fig.tight_layout()

print('Plotting the free energy')
fig2 = plt.figure()
ax2 = fig2.add_subplot(111)
XPOT = np.linspace(-2, 2, 1000)
free = -np.log(hist_avg) / mysystem.temperature['beta']  # free energy
# set up unbiased potential
VPOT = np.array([forcefield.evaluate_potential(pos=xi) for xi in XPOT])
free += (VPOT.min() - free.min())
ax2.plot(XPOT, VPOT, 'blue', lw=3, label='Unbiased potential', alpha=0.5)
ax2.plot(bin_x, free, lw=7, alpha=0.5, color='green', label='Free energy')
ax2.set_xlabel('Position ($x$)', fontsize='large')
ax2.set_ylabel('Potential energy ($V(x)$) / eV', fontsize='large')
ax2.legend()
ax2.set_xlim((-1.1, 1.1))
ax2.set_ylim((-0.3, 0.05))
fig2.tight_layout()

plt.show()
