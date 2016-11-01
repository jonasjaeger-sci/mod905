# -*- coding: utf-8 -*-
# Copyright (c) 2016, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""This is a simple RETIS example.

Here we will show the moves attempted in a RETIS simulation.

Have fun!
"""
from pyretis.core import System, Box
from pyretis.inout.settings import (create_force_field,
                                    create_orderparameter, create_simulation)
from pyretis.inout.plotting import mpl_set_style
import numpy as np
from matplotlib import pylab as plt
from matplotlib import animation
from matplotlib import gridspec as gridspec
# Let us define the simulation:
SETTINGS = {}
# Basic settings for the simulation:
SETTINGS['simulation'] = {'task': 'retis',
                          'steps': 100,
                          'interfaces': [-0.9, -0.8, -0.7,
                                         -0.6, -0.5, -0.4,
                                         -0.3, 1.0]}
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

mpl_set_style()
INTERFACES = SETTINGS['simulation']['interfaces']
NINT = len(INTERFACES)
CMAP = plt.get_cmap('Set1')
COLORS = [CMAP(float(i)/float(NINT)) for i in range(NINT)]


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


def print_step_results(ensembles, retis_result):
    """A function to print out RETIS results.

    Parameters
    ----------
    ensembles : list of enemble objects
        The different path ensembles we are simulating.
    retis_result : list of lists
        The results from a RETIS simulation step
    """
    for i, result in enumerate(retis_result):
        name = ensembles[i].ensemble_name
        print('Move in {}'.format(name))
        name_of_move = result[0]
        accepted = result[1]
        print('\tType: {}'.format(name_of_move))
        if name_of_move == 'swap':
            name2 = ensembles[result[2]].ensemble_name
            print('\tSwapping: {} -> {}'.format(name2, name))
        elif name_of_move == 'tis':
            trial_path = result[2]
            if trial_path.generated[0] == 'sh':
                tis_move = 'shooting'
            elif trial_path.generated[0] == 'tr':
                tis_move = 'time-reversal'
            else:
                tis_move = 'unknown'
            print('\tTIS move: {}'.format(tis_move))
        print('\tResult: {}'.format(accepted))


def matplotlib_setup():
    """A method to do some MPL set up."""
    new_fig = plt.figure()
    ax1 = new_fig.add_subplot(111)
    # Draw lines for interfaces:
    path_lines = []
    for i, pos in enumerate(INTERFACES):
        ax1.axvline(x=pos, lw=2, ls=':', color='#262626',
                    alpha=0.8)
        pathline1, = ax1.plot([], [], lw=3, ls='-', color=COLORS[i])
        pathline2, = ax1.plot([], [], lw=3, ls='-')
        path_lines.append(pathline1)
        path_lines.append(pathline2)
    txtbox = ax1.text(0.1, 0.8, '', transform=ax1.transAxes,
                      backgroundcolor='w', fontsize=16)
    def init_func():
        """Method to define what MPL needs to re-draw when clearing the frame.

        Returns
        -------
        out : list
            list of the patches to be re-drawn
        """
        patches = []
        for line in path_lines:
            line.set_data([], [])
            patches.append(line)
        txtbox.set_text('')
        patches.append(txtbox)
        return patches
    plot_patches = {'path': path_lines,
                    'textbox': txtbox}
    return new_fig, plot_patches, init_func


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
    for i, point in enumerate(path.trajectory()):
        if i == 0 or i == leng-1:
            order.append(point[0])
            pos.append(point[1][0])
            vel.append(point[2][0])
    return np.array(order), np.array(pos), np.array(vel)


def update(frame, simulation, plot_patches):
    """Method to run the simulation and update plots.

    Parameters
    ----------
    frame : int
        The current frame number, supplied by animation.FuncAnimation
    simulation : object
        The simulation we are running.
    plot_patches : dict of lists/objects
        This list contains stuff we can use for plotting.

    Returns
    -------
    out : list
        list of the patches to be drawn
    """
    patches = []
    path_lines = plot_patches['path']
    ensembles = simulation.path_ensembles
    if frame == 0:
        for i, ensemble in enumerate(ensembles):
            name = ensemble.ensemble_name
            _, pos, vel = get_path(ensemble.last_path)
            line = path_lines[2*i]
            line.set_data(pos, vel)
            patches.append(line)
            txtbox = plot_patches['textbox']
            txtbox.set_text(r'Initial path in ${}$'.format(name))
    else:
        if not simulation.is_finished():
            result = simulation.step()
    return patches


def main():
    """Just run the simulation :-)"""
    print('# CREATING SYSTEM...')
    system = set_up_system(SETTINGS)
    print('# CREATING SIMULATION...')
    simulation = create_simulation(SETTINGS, system)
    print(simulation)
    print('# INITIATING TRAJECTORIES...')
    simulation.step()  # Run the first step of the simulation:
    # Let us look at the resulting path ensembles and paths:
    fig, patches, init = matplotlib_setup()
    anim = animation.FuncAnimation(fig, update,
                                   frames=SETTINGS['simulation']['steps']+1,
                                   fargs=[simulation, patches],
                                   repeat=False,
                                   interval=10,
                                   blit=False,  # True, here might be faster
                                   init_func=init)
    plt.show()

if __name__ == '__main__':
    main()
