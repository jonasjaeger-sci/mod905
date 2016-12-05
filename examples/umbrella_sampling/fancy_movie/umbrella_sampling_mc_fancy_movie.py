# -*- coding: utf-8 -*-
"""
Example of running a simulation
"""
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from pyretis.core import System, RandomGenerator, Box
from pyretis.core.simulation.mc_simulation import UmbrellaWindowSimulation
from pyretis.forcefield import ForceField
from pyretis.forcefield.potentials import DoubleWell, RectangularWell
from pyretis.analysis.histogram import histogram, match_all_histograms


# Define system with a temperature in K
dummybox = Box(periodic=[False])
mysystem = System(temperature=500, units='eV/K', box=dummybox)
# We will only have one particle in the system:
mysystem.add_particle(name='X', pos=np.array([-0.7]))
# In this particular example, we are going to use
# a simple double well potential
potential_dw = DoubleWell(a=1, b=1, c=0.02)
# and a rectangular well potential
potential_rw = RectangularWell()
# do set up the unbiased force field
forcefield = ForceField('Double well', potential=[potential_dw])
# and the biased
forcefield_bias = ForceField('Double well with rectangular bias',
                             potential=[potential_dw, potential_rw])
# attach biased force field to the system:
mysystem.forcefield = forcefield_bias
umbrellas = [[-1.0, -0.4], [-0.5, -0.2], [-0.3, 0.0], [-0.1, 0.2],
             [0.1, 0.4], [0.3, 0.6], [0.5, 1.0]]
n_umb = len(umbrellas)
# and we initiate the random number generator we will use
RANDSEED = 1  # seed for random number generator:
RGEN = RandomGenerator(seed=RANDSEED)
# and define some common variables for the simulations
MINCYCLES = 1e4
MAXDX = 0.1  # maximum allowed displacement in the MC step(s).

trajectory, energy = [], []  # to store all trajectories & energies
# we run all the umbrella simulations by looping over
# the different umbrellas we defined:
print('Starting simulations:')
for i, umbrella in enumerate(umbrellas):
    print('Running umbrealla no: {} of {}. Location: {}'.format(i + 1, n_umb,
                                                                umbrella))
    params = {'left': umbrella[0], 'right': umbrella[1]}
    mysystem.forcefield.update_potential_parameters(potential_rw, params)
    mysystem.potential()  # recalculate potential energy
    over = umbrellas[min(i + 1, n_umb - 1)][0]  # position we must cross
    # Create the umbrella simulation :-)
    simulation = UmbrellaWindowSimulation(mysystem, umbrella, over,
                                          RGEN, MAXDX,
                                          mincycle=MINCYCLES)

    pos, trial, ener, ener_trial = [], [], [], []
    success = []
    for result in simulation.run():
        pos.append(mysystem.particles.pos)
        trial.append(result['displace_step'][2])
        success.append(result['displace_step'][3])
        ener.append(mysystem.v_pot)
    trajectory.append([np.array(pos), np.array(trial), success])
    energy.append(np.array(ener))

    print('Done. Cycles: {}'.format(simulation.cycle['step'] -
                                    simulation.cycle['start']))


# We can now post-process the simulation output.
# Here, we make use of some of the analysis tools in pyretis:

bins = 50
lim = (-1.2, 1.2)
histlim = (-1.2, 1.2)
potlim = (-0.35, 0.1)
XPOT = np.linspace(-2, 2, 1000)
VPOT = []
for xi in XPOT:
    mysystem.particles.pos = xi
    VPOT.append(forcefield.evaluate_potential(mysystem))
VPOT = np.array(VPOT)

# plotting for generating movie:
fig = plt.figure()
gs = gridspec.GridSpec(2, 2)
ax_pot = fig.add_subplot(gs[0, 0])
ax_hist = fig.add_subplot(gs[1, 0])
ax_all_hist = fig.add_subplot(gs[1, 1])
ax_all_hist.set_ylabel('probability density')
ax_all_hist.set_xlabel('$x$')
fig.subplots_adjust(left=0.1, bottom=0.2, right=0.90, top=0.90,
                    wspace=0.3, hspace=0.2)
figtext = plt.figtext(0.05, 0.05, '')
colors = ['blue', 'green', 'darkviolet', 'brown', 'gray', 'crimson', 'cyan']

ymax = 0.0

all_histograms = []  # for storing all histograms
all_normed_histograms = []  # for storing all histograms
for i, (traj, ener) in enumerate(zip(trajectory, energy)):
    pos, trial, success = traj[0], traj[1], traj[2]
    ax_pot.cla()  # clear axis
    ax_pot.set_ylabel('$V(x)$')
    ax_pot.set_xlabel('$x$')
    ax_pot.plot(XPOT, VPOT, color='blue', lw=3, alpha=0.5)
    ax_pot.axvspan(xmin=umbrellas[i][0], xmax=umbrellas[i][1],
                   color='blue', alpha=0.1)
    ax_pot.set_xlim(lim)
    ax_pot.set_ylim(potlim)
    scatter = ax_pot.scatter(None, None, s=150, c='green', alpha=0.6)
    scatter_last = []  # to store n last points:
    npoint = 0  # setting npoint > 0 will draw the npoint last points
    for j in range(npoint):
        alphamax = 0.5
        alphamin = 0.1
        alphaj = (alphamax - alphamin) * j / (npoint - 1.) + alphamin
        scatter_last.append(ax_pot.scatter(None, None, s=150, c='green',
                                           alpha=alphaj))
    scatter2 = ax_pot.scatter(None, None, s=150, c='black', alpha=0.6,
                              marker='x')

    ax_hist.cla()
    ax_hist.set_xlabel('$x$')
    ax_hist.set_ylabel('# counts')
    ax_hist.set_xlim(lim)
    ax_hist.set_ylim(0.0, 1.0)
    # create empty histogram to get bins etc.:
    hist, bins, bin_mid = histogram([0], bins=bins, limits=histlim)
    db = bin_mid[1] - bin_mid[0]
    rects = ax_hist.bar(bin_mid - 0.5 * db, hist, db, color=colors[i],
                        alpha=0.5)

    ax_all_hist.set_xlim(lim)
    rects2 = ax_all_hist.bar(bin_mid - 0.5 * db, hist, db,
                             color=colors[i], alpha=0.5)

    pos_so_far = []  # store all positions
    pos_last = []  # store the most recent npoint positions
    for j, (posj, enerj) in enumerate(zip(pos, ener)):
        print(j)
        figtext.set_text('Total number of MC cycles: {}'.format(j))
        pos_ener = np.array([posj, enerj])
        scatter.set_offsets(pos_ener)  # update plot
        pos_so_far.append(posj)
        for k, sk in enumerate(scatter_last):
            if k < len(pos_last):
                sk.set_offsets(pos_last[k])
            else:
                sk.set_offsets([None, None])
        pos_last.append([posj, enerj])
        if len(pos_last) > npoint:
            pos_last.pop(0)
        if success[j]:
            scatter2.set_offsets([None, None])
        else:
            mysystem.particles.pos = trial[j]
            pott = forcefield.evaluate_potential(mysystem)
            scatter2.set_offsets([trial[j], pott])
        hist, bins, bin_mid = histogram(pos_so_far, bins=bins, limits=histlim)
        hist2, bins2, bin_mid2 = histogram(pos_so_far, bins=bins,
                                           limits=histlim, density=True)
        ax_hist.set_ylim(0.0, hist.max() * 1.05)
        ymax = max([histi[0].max() for histi in all_normed_histograms] +
                   [hist2.max()])
        ax_all_hist.set_ylim(0.0, ymax * 1.05)
        # update histograms
        for rect, rect2, h, h2 in zip(rects, rects2, hist, hist2):
            rect.set_height(h)
            rect2.set_height(h2)
        if j % 1 == 0:
            filename = 'frame-{0:03d}-{1:05d}.png'.format(i, j)
            print('Writing file: {}'.format(filename))
            fig.savefig(filename)
    # add final histogram:
    all_histograms.append([hist, bins, bin_mid])
    all_normed_histograms.append([hist2, bins2, bin_mid2])
    ax_all_hist.set_xlim(lim)
# do the rescaling:
figtext.set_text('Rescaling...')
ax_pot.cla()
ax_pot.set_ylabel('$V(x)$')
ax_pot.set_xlabel('$x$')
ax_pot.plot(XPOT, VPOT, color='blue', lw=3, alpha=0.5)
ax_pot.set_xlim(lim)
ax_pot.set_ylim(potlim)
# We are going to match these histograms:
histograms_s, scale_factors, hist_avg = match_all_histograms(all_histograms,
                                                             umbrellas)
ax_hist_log = fig.add_subplot(gs[0, 1])
ax_hist.cla()
ax_hist.set_xlabel('$x$')
ax_hist.set_ylabel('matching histograms')
ax_hist.set_xlim(lim)
ax_hist_log.set_xlim(lim)
ax_hist_log.set_yscale('log')
ax_hist_log.set_xlabel('$x$')
ax_hist_log.set_ylabel('logscale')

logmin = None
for x in hist_avg:
    if logmin is None and x > 0.0:
        logmin = x
    if 0 < x < logmin:
        logmin = x

for i, (histo, scale) in enumerate(zip(all_histograms, scale_factors)):
    hist, bind, bin_mid = histo
    if i == 0:
        ax_hist.bar(bin_mid - 0.5 * db, hist, db, color=colors[i], alpha=0.5)
        ax_hist_log.bar(bin_mid - 0.5 * db, hist, db, color=colors[i],
                        alpha=0.5, log=True)
        ax_hist.set_ylim(0.0, hist.max() * 1.05)
        ax_hist_log.set_ylim(logmin / 10, hist.max() * 10)
    else:
        s = np.linspace(1, scale, 12)  # do scaling in 12 steps
        rects = ax_hist.bar(bin_mid - 0.5 * db, hist, db, color=colors[i],
                            alpha=0.5)
        rects2 = ax_hist_log.bar(bin_mid - 0.5 * db, hist, db,
                                 color=colors[i], alpha=0.5, log=True)
        for j, si in enumerate(s):
            for rect, rect2, h in zip(rects, rects2, hist):
                rect.set_height(h * si)
                rect2.set_height(h * si)
            if j % 1 == 0:
                filename = 'scale-{0:03d}-{1:05d}.png'.format(i, j)
                print('Writing file: {}'.format(filename))
                fig.savefig(filename)
figtext.set_text('Calculating free energy')
ax_hist.plot(bin_mid, hist_avg, lw=6, color='orangered', alpha=0.65)
ax_hist_log.plot(bin_mid, hist_avg, lw=6, color='orangered', alpha=0.65)
free = -np.log(hist_avg) / mysystem.temperature['beta']  # free energy
free += (VPOT.min() - free.min())
ax_pot.plot(bin_mid, free, lw=6, color='orangered', alpha=0.65)
fig.savefig('final.png')
