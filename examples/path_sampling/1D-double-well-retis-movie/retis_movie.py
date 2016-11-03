# -*- coding: utf-8 -*-
# Copyright (c) 2016, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""This is a simple RETIS example animating the algorithm.

You can play with the interfaces, the potential parameters,
the temperature, the ratio of the different RETIS moves etc.

Have fun!
"""
from pyretis.core import System, Box
from pyretis.core.properties import Property
from pyretis.inout.settings import (create_force_field,
                                    create_orderparameter, create_simulation)
from pyretis.analysis.path_analysis import _pcross_lambda_cumulative
import numpy as np
import matplotlib as mpl
from matplotlib import pylab as plt
from matplotlib import animation
from matplotlib import gridspec as gridspec

INTERFACES = [-0.9, -0.8, -0.7, -0.6, -0.5, -0.4, -0.3, 1.0]
PCROSS_LOG = True
PCROSS_LOG = False
# Let us define the simulation:
SETTINGS = {}
# Basic settings for the simulation:
SETTINGS['simulation'] = {'task': 'retis',
                          'steps': 150,
                          'interfaces': INTERFACES}
# Basic settings for the system:
SETTINGS['system'] = {'units': 'lj', 'temperature': 0.07}
# Basic settings for the Langevin integrator:
SETTINGS['integrator'] = {'class': 'Langevin',
                          'gamma': 0.3,
                          'high_friction': False,
                          'seed': 0,
                          'timestep': 0.002}
# Potential parameters:
# The potential is: `V_\text{pot} = a x^4 - b (x - c)^2`
SETTINGS['potential'] = [{'a': 1.0, 'b': 2.0, 'c': 0.0,
                          'class': 'DoubleWell'}]
# Settings for the order parameter:
SETTINGS['orderparameter'] = {'class': 'OrderParameterPosition',
                              'dim': 'x', 'index': 0, 'name': 'Position',
                              'periodic': False}
# TIS specific settings:
SETTINGS['tis'] = {'freq': 0.5,
                   'maxlength': 20000,
                   'aimless': True,
                   'allowmaxlength': False,
                   'sigma_v': -1,
                   'seed': 0,
                   'zero_momentum': False,
                   'rescale_energy': False,
                   'initial_path': 'kick'}
# RETIS specific settings:
SETTINGS['retis'] = {'swapfreq': 0.5,
                     'relative_shoots': None,
                     'nullmoves': True,
                     'swapsimul': True}

# For convenience:
TIMESTEP = SETTINGS['integrator']['timestep']
ANALYSIS = {'ngrid': 100}

# Set up for plotting:
mpl.rc('font', size=14, family='serif')
mpl.rc('lines', color='#262626')
mpl.rc('savefig', directory=None)
NINT = len(INTERFACES)
CMAP = plt.get_cmap('Set1')
COLORS = [CMAP(float(i)/float(NINT)) for i in range(NINT)]
TXTCOLOR = {'SW': '#006BA4', 'NU': '#FF800E',
            'TR': '#ABABAB', 'SH': '#595959'}


def set_up_system(settings):
    """Just a method to help set up the system.

    Parameters
    ----------
    settings : dict
        The settings required to set up the system.

    Returns
    -------
    sys : object like System from pyretis.core
        A system object we can use in a simulation.
    """
    box = Box(periodic=[False])
    sys = System(temperature=settings['system']['temperature'],
                 units=settings['system']['units'], box=box)
    sys.forcefield = create_force_field(settings)
    sys.order_function = create_orderparameter(settings)
    sys.add_particle(np.array([-1.0]), mass=1, name='Ar', ptype=0)
    return sys


def get_path(path):
    """Get points on a trajectory, useful for plotting.

    Parameters
    ----------
    path : object like Path from pyretis.core
        The path/trajectory we are collecting points from.

    Returns
    -------
    out[0] : numpy.array
        The order parameter(s) as a function of time.
    out[1] : numpy.array
        The positions as a function of time.
    out[2] : numpy.array
        The velocities as a function of time.
    """
    order = []
    pos = []
    vel = []
    leng = path.length
    if leng <= 50:
        freq = 1
    elif 50 < leng <= 600:
        freq = 6
    elif 600 < leng < 2000:
        freq = 10
    else:
        freq = 20
    for i, point in enumerate(path.trajectory()):
        if i == 0 or i == leng-1 or i % freq == 0:
            order.append(point[0])
            pos.append(point[1][0])
            vel.append(point[2][0])
    return np.array(order), np.array(pos), np.array(vel)


def matplotlib_setup():
    """A method to do some MPL set up & animation preparation."""
    new_fig = plt.figure(figsize=(12, 6))
    grid = gridspec.GridSpec(3, 4)
    ax1 = new_fig.add_subplot(grid[:, :2])
    ax2 = new_fig.add_subplot(grid[0, 2:])
    ax3 = new_fig.add_subplot(grid[1:, 2:])
    if not PCROSS_LOG:
        axp = ax3.twinx()
    axes = (ax1, ax2, ax3)
    plot_patches = {'paths': [],
                    'prob': [],
                    'prob2': [],
                    'matched': None,
                    'fluxline': None,
                    'txtmove': [],
                    'txtcycle': None,
                    'start': [],
                    'end': []}
    k = 0
    for i, pos in enumerate(INTERFACES):
        ax1.axvline(x=pos, lw=2, ls=':', color='#262626')
        ax3.axvline(x=pos, lw=2, ls=':', color='#262626')
        newline, = ax1.plot([], [], lw=3, ls='-', color=COLORS[i])
        plot_patches['paths'].append(newline)
        if PCROSS_LOG:
            newlinep2, = ax3.plot([], [], lw=3, ls='-',
                                  color=newline.get_color())
            plot_patches['prob2'].append(newlinep2)
        else:
            newlinep, = ax3.plot([], [], lw=3, ls='-',
                                 color=newline.get_color())
            plot_patches['prob'].append(newlinep)

        newscat = ax1.scatter(None, None, s=75, marker='o',
                              color=newline.get_color())
        plot_patches['start'].append(newscat)
        newscat = ax1.scatter(None, None, s=75, marker='s',
                              color=newline.get_color())
        plot_patches['end'].append(newscat)
        # Note, we also add a line for [0^-], this is just to get
        # the colors right, plines[0] is not used for anything else...
        if i == 0:
            txt_x = pos-0.4
            txt_y = 1.8
        else:
            txt_x = INTERFACES[i-1]
            txt_y = 1.8 - (k-1) * 0.2
        txtbox = ax1.text(txt_x, txt_y, '', transform=ax1.transData,
                          backgroundcolor='w', fontsize=12)
        plot_patches['txtmove'].append(txtbox)
        if k % 3 == 0 and k > 0:
            k = 0
        k += 1
    plot_patches['txtcycle'] = ax1.text(-1.4, -1.8, '',
                                        transform=ax1.transData,
                                        backgroundcolor='w', fontsize=14)
    ax1.set_xlabel(r'Order parameter ($\lambda$)')
    ax1.set_ylabel(r'Velocity ($\dot{\lambda}$)')
    if PCROSS_LOG:
        ax3.set_yscale('log')
        plot_patches['matched'] = ax3.plot([], [], lw=6, ls='-',
                                           color='#262626',
                                           zorder=0, alpha=0.7)[0]
        ax3.set_xlim(-1, 1.05)
        ax3.set_ylim(1e-7, 1)
    else:
        axp.set_yscale('log')
        plot_patches['matched'] = axp.plot([], [], lw=6, ls='-',
                                           color='#262626',
                                           zorder=0, alpha=0.7)[0]
        ax3.set_xlim(-1, 1.05)
        axp.set_ylim(1e-7, 1)
        ax3.set_ylim(0, 1)
    ax3.set_xlabel(r'$\lambda$')
    ax3.set_ylabel(r'Probability')

    ax1.set_ylim(-2, 2)
    ax1.set_xlim(-1.5, 1.5)

    plot_patches['fluxline'] = ax2.plot([0], [0], lw=3, ls='-',
                                        color='#4C72B0')[0]
    ax2.set_ylim(0, 1)
    ax2.set_xlim(0, 1)
    ax2.set_ylabel('Flux')
    ax2.set_xlabel('Cycles completed')
    ax2.locator_params(axis='y', nbins=4)
    if PCROSS_LOG:
        new_fig.subplots_adjust(left=0.1, bottom=0.15, right=0.95, top=0.95,
                                wspace=0.5, hspace=0.5)
    else:
        new_fig.set_tight_layout(True)
    return new_fig, plot_patches, axes


def analyse_prob(ensemble, props, idx, step):
    """Update running estimates for probability.

    Parameters
    ----------
    ensemble : object
        The ensemble to analyse.
    props : dict
        A dictionary for storing properties we calculate.
    idx : int
        An index for the path ensemble.
    step : int
        The current simulation step.
    """
    orderp = ensemble.last_path.ordermax[0]
    success = 1 if orderp > ensemble.detect else 0
    prun = props['prun'][idx]
    if len(prun) == 0:
        prun.append(success)
    else:
        npath = step + 1
        prun.append(float(success + prun[-1] * (npath-1)) / float(npath))
    props['orderp'][idx].append(orderp)
    orderparam = np.array(props['orderp'][idx])
    ordermax = min(orderparam.max(), max(ensemble.interfaces))
    ordermin = ensemble.interfaces[1]
    pcross, lamb = _pcross_lambda_cumulative(orderparam, ordermin, ordermax,
                                             ANALYSIS['ngrid'])
    props['pcross'][idx] = (lamb, pcross)


def update(frame, simulation, plot_patches, prop, axes):
    """Method to run the simulation and update plots.

    Parameters
    ----------
    frame : int
        The current frame number, supplied by animation.FuncAnimation
    simulation : object
        The simulation we are running.
    plot_patches : dict of objects
        This dict contains the lines, text boxes etc. from matplotlib
        which we will use to display our data.
    prop : dict of objects
        A dict with results from the simulation.
    axes : tuple
        This tuple contains the axes used for plotting.

    Returns
    -------
    out : list
        list of the patches to be drawn.
    """
    patches = []
    if not simulation.is_finished():
        result = simulation.step()
        step = result['cycle']['step']
        print('\n# Current cycle: {}'.format(step))
        for i, ensemble in enumerate(simulation.path_ensembles):
            _, pos, vel = get_path(ensemble.last_path)
            plot_patches['paths'][i].set_data(pos, vel)
            patches.append(plot_patches['paths'][i])
            plot_patches['start'][i].set_offsets((pos[0], vel[0]))
            plot_patches['start'][i].set_visible(True)
            patches.append(plot_patches['start'][i])
            plot_patches['end'][i].set_offsets((pos[-1], vel[-1]))
            plot_patches['end'][i].set_visible(True)
            patches.append(plot_patches['end'][i])
            if i == 0:
                prop['length0-'].add(ensemble.last_path.length)
            elif i == 1:
                prop['length0+'].add(ensemble.last_path.length)
            if i > 0:
                analyse_prob(ensemble, prop, i, step)
                if not PCROSS_LOG:
                    plot_patches['prob'][i].set_data(prop['pcross'][i][0],
                                                     prop['pcross'][i][1])
                    patches.append(plot_patches['prob'][i])

        flux = 1.0 / ((prop['length0-'].mean + prop['length0+'].mean - 4.0) *
                      TIMESTEP)
        fluxx, fluxy = plot_patches['fluxline'].get_data()
        fluxx = np.append(fluxx, fluxx[-1] + 1)
        fluxy = np.append(fluxy, flux)
        plot_patches['fluxline'].set_data(fluxx, fluxy)
        axes[1].set_xlim(0, step+1)
        axes[1].set_ylim(0, 1.1*fluxy.max())
        patches.append(plot_patches['fluxline'])
        if 'retis' in result:
            for i, move in enumerate(result['retis']):
                if move[0] == 'tis':
                    trial = move[2]
                    txtmove = trial.generated[0].upper()
                else:
                    txtmove = move[0][:2].upper()
                plot_patches['txtmove'][i].set_text(txtmove)
                plot_patches['txtmove'][i].set_color(TXTCOLOR[txtmove])
                patches.append(plot_patches['txtmove'][i])
        plot_patches['txtcycle'].set_text('Cycle: {}'.format(step))
        patches.append(plot_patches['txtcycle'])

        # match probabilities:
        matched_lamb = []
        matched_prob = []
        accprob = 1.0
        for i, ensemble in enumerate(simulation.path_ensembles):
            if i == 0:
                continue
            lamb, pcross = prop['pcross'][i]
            idx = np.where(lamb <= ensemble.detect)[0]
            matched_lamb.extend(lamb[idx])
            matched_prob.extend(pcross[idx] * accprob)
            if PCROSS_LOG:
                prob2 = prop['pcross'][i][1]*accprob
                plot_patches['prob2'][i].set_data(prop['pcross'][i][0], prob2)
                patches.append(plot_patches['prob2'][i])
            accprob *= prop['prun'][i][-1]
        plot_patches['matched'].set_data(matched_lamb, matched_prob)
        patches.append(plot_patches['matched'])
        print('# Current flux estimate: {}'.format(flux))
        if matched_lamb[-1] < INTERFACES[-1]:
            pcr = 0.0
        else:
            pcr = matched_prob[-1]
        kab = flux * pcr
        print('# Current P_cross estimate: {}'.format(pcr))
        print('# Current rate constant estimate: {}'.format(kab))
        return patches
    else:
        print('# Simulation is done (frame = {})'.format(frame))
        return patches


def main():
    """Just run the simulation :-)"""
    print('# CREATING SYSTEM')
    system = set_up_system(SETTINGS)
    print('# CREATING SIMULATION:')
    simulation = create_simulation(SETTINGS, system)
    print(simulation)
    print('# GENERATING INITIAL PATHS')
    fig, plot_patches, axes = matplotlib_setup()
    prop = {}
    prop['length0-'] = Property(desc='Average path length for [0^-]')
    prop['length0+'] = Property(desc='Average path length for [0^+]')
    prop['orderp'] = [[] for _ in INTERFACES]
    prop['prun'] = [[] for _ in INTERFACES]
    prop['pcross'] = [[] for _ in INTERFACES]
    _ = animation.FuncAnimation(fig, update,
                                frames=SETTINGS['simulation']['steps']+1,
                                fargs=[simulation, plot_patches, prop,
                                       axes],
                                repeat=False,
                                interval=10,
                                blit=False)
    plt.show()

if __name__ == '__main__':
    main()
