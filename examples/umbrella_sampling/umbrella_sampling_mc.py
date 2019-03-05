# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Example showing a simple umbrella simulation with PyRETIS.

In this simulation, we study a particle moving in a one-dimensional
potential energy landscape and the goal is to determine this
landscape by performing umbrella simulations.

"""

import sys
import colorama
from tqdm import tqdm
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.cm import get_cmap
from pyretis.core import System, RandomGenerator, create_box, Particles
from pyretis.inout.setup import create_simulation
from pyretis.inout import print_to_screen
from pyretis.forcefield import ForceField
from pyretis.forcefield.potentials import DoubleWell, RectangularWell
from pyretis.analysis import histogram, match_all_histograms


UMBRELLA_WINDOWS = [
    [-1.0, -0.4],
    [-0.5, -0.2],
    [-0.3, 0.0],
    [-0.1, 0.2],
    [0.1, 0.4],
    [0.3, 0.6],
    [0.5, 1.0]
]


plt.style.use('seaborn')


def set_up_system(pos=np.array([-0.7])):
    """Set up the initial system."""
    # Define system with a temperature in K:
    dummybox = create_box(periodic=[False])
    mysystem = System(temperature=500, units='eV/K', box=dummybox)
    mysystem.particles = Particles(dim=mysystem.get_dim())
    # We will only have one particle in the system:
    mysystem.add_particle(name='X', pos=pos)
    # In this particular example, we are going to use
    # a simple double well potential:
    potential_dw = DoubleWell(a=1, b=1, c=0.02)
    # And a rectangular well potential:
    potential_rw = RectangularWell()
    # Set up the force field:
    forcefield_bias = ForceField(
        'Double well with rectangular bias',
        potential=[potential_dw, potential_rw],
        params=[{'a': 1.0, 'b': 1.0, 'c': 0.02}, None]
    )
    mysystem.forcefield = forcefield_bias
    return mysystem


def set_up_simulation(system, umbrella, over, seed):
    """Set up a single umbrella window simulation.

    Parameters
    ----------
    system : object like :py:class:`.System`
        The system we are investigating.
    umbrella : list of floats
        The umbrella window we are investigating.
    over : float
        The coordinate we need to cross for the
        current window.
    seed : integer
        A seed for the random number generator.

    """
    settings = {}
    settings['simulation'] = {
        'task': 'umbrellawindow',
        'rgen': RandomGenerator(seed=seed),
        'mincycle': 10000,
        'maxdx': 0.1,
        'over': over,
        'umbrella': umbrella,
    }
    # Update the parameters for the rectangular bias window:
    potential_rw = system.forcefield.potential[1]
    potential_rw.set_parameters({'left': umbrella[0], 'right': umbrella[1]})
    system.potential()  # recalculate potential energy
    # Create the umbrella simulation:
    simulation = create_simulation(settings, {'system': system})
    return simulation


def run_umbrellas(windows):
    """Run the sampling for the given set of windows.

    Parameters
    ----------
    windows : list of floats
        The umbrella windows to investigate.

    """
    system = set_up_system()
    msg = '\nRunning umbrella no: {} of {}. Location: {}'
    n_umb = len(windows)
    print_to_screen('Starting simulations:', level='info')
    trajectories = []
    energies = []
    for i, window in enumerate(windows):
        print_to_screen(msg.format(i + 1, n_umb, window))
        over = windows[min(i + 1, n_umb - 1)][0]
        simulation = set_up_simulation(system, window, over, 1)
        traj, ener = [], []
        for _ in tqdm(simulation.run()):
            for pos in system.particles.pos:
                traj.append(pos)
                ener.append(system.particles.vpot)
        trajectories.append(traj)
        energies.append(ener)
        nstep = simulation.cycle['step'] - simulation.cycle['start']
        print_to_screen('Done. Cycles: {}'.format(nstep), level='success')
    return system, trajectories, energies


def analysis_and_plot(system, trajectory, windows):
    """Plot some results from the simulation."""
    # We can now post-process the simulation output.
    bins = 100
    lim = (-1.0, 1.0)
    histograms = [histogram(trj, bins=bins, limits=lim) for trj in trajectory]
    # Extract the bins (the midpoints) and the bin-width:
    bin_x = histograms[0][-1]
    dbin = bin_x[1] - bin_x[0]
    # We are going to match these histograms:
    print_to_screen('Matching histograms...', level='info')
    histograms_s, _, hist_avg = match_all_histograms(histograms, windows)
    # Let us create some simple plots using matplotlib:
    plot_histograms(histograms_s, hist_avg, bin_x, dbin)
    plot_free_energy(hist_avg, bin_x, system)


def plot_histograms(histograms_s, hist_avg, bin_x, dbin):
    """Plot matched histograms.

    Parameters
    ----------
    histograms_s : list of numpy.arrays
        The scaled histograms.
    hist_avg : numpy.array
        The average histogram.
    bin_x : numpy.array
        The midpoints for the histograms.
    dbin : float
        The histogram width.

    """
    print_to_screen('Plotting matched histograms', level='info')
    fig = plt.figure()
    axs = fig.add_subplot(111)
    axs.set_yscale('log')
    axs.set_xlabel('Position ($x$)', fontsize='large')
    axs.set_ylabel('Matched histograms', fontsize='large')
    colors = []
    for maps in ('viridis', 'Spectral', None):
        try:
            cmap = get_cmap(name=maps)
            colors = cmap(np.linspace(0, 1, len(histograms_s)))
            break
        except ValueError:
            continue

    for i, histo in enumerate(histograms_s):
        axs.bar(bin_x - 0.5 * dbin, histo, dbin, color=colors[i],
                alpha=0.8, log=True, edgecolor='#262626')
    axs.plot(bin_x, hist_avg, lw=7, color='orangered', alpha=0.8,
             label='Average after matching')
    axs.legend()
    axs.set_xlim((-1.1, 1.1))
    axs.set_ylim((0.1, hist_avg.max() * 1.25))
    fig.tight_layout()


def plot_unbiased_potential(system, xpos):
    """Plot the unbiased potential for the given locations."""
    # Set up and plot the unbiased potential:
    forcefield = ForceField(
        'Double well',
        potential=[system.forcefield.potential[0]]
    )
    vpot = []
    for i in xpos:
        system.particles.pos = i
        vpot.append(forcefield.evaluate_potential(system))
    return np.array(vpot)


def plot_free_energy(hist_avg, bin_x, system):
    """Plot the free energy obtained.

    Parameters
    ----------
    hist_avg : numpy.array
        The average histogram.
    bin_x : numpy.array
        Midpoints for the bins.
    system : object like :py:class:`.System`
        The system we have been investigating, we are here
        using it to plot the unbiased potential we have been
        sampling.

    """
    print_to_screen('Plotting the free energy', level='info')
    fig = plt.figure()
    axi = fig.add_subplot(111)
    xpos = np.linspace(-2, 2, 1000)
    free = -np.log(hist_avg) / system.temperature['beta']  # Free energy.
    vpot = plot_unbiased_potential(system, xpos)
    free += (vpot.min() - free.min())

    axi.plot(xpos, vpot, lw=3, label='Unbiased potential', alpha=0.5)
    axi.plot(bin_x, free, lw=7, alpha=0.5,
             label='Free energy from umbrella simulations')
    axi.set_xlabel('Position ($x$)', fontsize='large')
    axi.set_ylabel('Potential energy ($V(x)$) / eV', fontsize='large')
    axi.legend()
    axi.set_xlim((-1.1, 1.1))
    axi.set_ylim((-0.3, 0.05))
    fig.tight_layout()


if __name__ == '__main__':
    colorama.init(autoreset=True)
    SYS, TRAJ, _ = run_umbrellas(UMBRELLA_WINDOWS)
    analysis_and_plot(SYS, TRAJ, UMBRELLA_WINDOWS)
    if 'noplot' not in sys.argv[1:]:
        plt.show()
