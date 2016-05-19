# -*- coding: utf-8 -*-
"""
This is an example on how to perform a simple TIS simulation.
"""
# pylint: disable=C0103
from __future__ import print_function
import numpy as np
# pyretis imports:
from pyretis.core import Box, System
from pyretis.inout.settings import create_simulation
from pyretis.forcefield import ForceField
from pyretis.forcefield.potentials import DoubleWell
from pyretis.core.orderparameter import OrderParameterPosition
# imports for the plotting:
from pyretis.inout.plotting import COLORS, COLOR_SCHEME
import collections
from matplotlib import pyplot as plt
from matplotlib import animation
import matplotlib.transforms as transforms
import matplotlib.patches as mpatches
import matplotlib as mpl


simulation_settings = {'task': 'TIS',
                       'integrator': {'class': 'Langevin', 'timestep': 0.002,
                                      'gamma': 0.3, 'seed': 0,
                                      'high-friction': False},
                       'steps': 250,
                       'temperature': 0.07,
                       'interfaces': [-1.0, 0.0, 1.0],
                       'ensemble': '001',
                       'periodic_boundary': [False],
                       'units': 'lj',
                       'generate-vel': {'seed': 0, 'momentum': False,
                                        'distribution': 'maxwell'},
                       'orderparameter': {'class': 'OrderParameterPosition',
                                          'name': 'Position', 'index': 0,
                                          'dim': 'x', 'periodic': False},
                       'tis': {'start_cond': 'L',
                               'freq': 0.5,
                               'maxlength': 10000,
                               'aimless': True,
                               'allowmaxlength': False,
                               'sigma_v': -1,
                               'seed': 10,
                               'initial_path': 'kick'},
                       'output': [{'type': 'pathensemble', 'target': 'file',
                                   'when': {'every': 10}}]}

# set up simulation
box = Box(periodic=simulation_settings['periodic_boundary'])
print('\nCreated:', box)
system = System(temperature=simulation_settings['temperature'],
                units=simulation_settings['units'],
                box=box)

system.add_particle(name='A', pos=np.array([-1.0]))
msg = 'Added one particle {} at position: {}'
print(msg.format(system.particles.name, system.particles.pos))
if 'generate-vel' in simulation_settings:
    system.generate_velocities(**simulation_settings['generate-vel'])
    msg = 'Generated temperatures with average: {}'

# Set up force field:
double_well = DoubleWell(a=1.0, b=2.0, c=0.0)
forcefield = ForceField(potential=[double_well], desc='Double Well')
system.forcefield = forcefield
print('\nCreated:', system.forcefield)

simulation_tis = create_simulation(simulation_settings, system)
print('\nCreated:', simulation_tis)

# Simulation is now set up and ready to run.
# We will now add some plotting specific things:
mpl.rc('axes', labelsize='large')
mpl.rc('axes', edgecolor=COLORS['almost_black'])
mpl.rc('axes', labelcolor=COLORS['almost_black'])
mpl.rc('text', color=COLORS['almost_black'])
mpl.rc('xtick', color=COLORS['almost_black'])
mpl.rc('ytick', color=COLORS['almost_black'])
mpl.rc('font', family='serif')
fig = plt.figure(figsize=(12, 6))
# This adds the first axis. Here we will plot the paths.
ax = fig.add_subplot(111)
left, middle, right = simulation_settings['interfaces']
ax.axvline(x=left, lw=2, ls=':', color=COLORS['almost_black'])
ax.axvline(x=middle, lw=2, ls=':', color=COLORS['almost_black'])
ax.axvline(x=right, lw=2, ls=':', color=COLORS['almost_black'])

AXPAD = 0.2
ax.set_xlim(min(simulation_settings['interfaces']) - AXPAD,
            max(simulation_settings['interfaces']) + AXPAD)
trans = transforms.blended_transform_factory(ax.transData, ax.transAxes)
detect_text = ax.text(middle, 0.05, 'Detect', transform=trans,
                      horizontalalignment='center', backgroundcolor='w',
                      fontsize=14)
right_text = ax.text(right + 0.5*AXPAD, 0.05, 'Right', transform=trans,
                     horizontalalignment='center', fontsize=14)
left_text = ax.text(left - 0.5*AXPAD, 0.05, 'Left', transform=trans,
                    horizontalalignment='center', fontsize=14)
time_text = ax.text(0.01, 0.925, '', transform=ax.transAxes,
                    backgroundcolor='w', fontsize=14, color='darkgreen')
ax.set_ylim(-2, 2)
ax.set_xlabel('Order parameter')
ax.set_ylabel('Order parameter velocity')
# we will just store the n last paths
N = 10
last_paths = collections.deque()
last_start_points = collections.deque()
last_end_points = collections.deque()
for _ in range(N):
    linepath, = ax.plot([], [], lw=3.5, ls='-', color='blue',
                        alpha=0.0)
    scatter_start = ax.scatter([], [], alpha=0.5, color='blue',
                               marker='o', s=100, label='Path start')
    scatter_end = ax.scatter([], [], alpha=0.5, color='blue',
                             marker='^', s=100, label='Path end')
    last_paths.append(linepath)
    last_start_points.append(scatter_start)
    last_end_points.append(scatter_end)
scatter_test = ax.scatter([], [], alpha=0.5, color='blue',
                          marker='o', s=100, label='Path start/end')
alpha = np.linspace(0.05, 1.0, N)
MAP = 'husl_10'
status_color = {'ACC': COLOR_SCHEME[MAP][7],
                'MCR': COLOR_SCHEME[MAP][1],
                'BWI': COLOR_SCHEME[MAP][0],
                'BTL': COLOR_SCHEME[MAP][3],
                'BTX': COLOR_SCHEME[MAP][4],
                'KOB': COLOR_SCHEME[MAP][5],
                'FTL': COLOR_SCHEME[MAP][6],
                'FTX': COLOR_SCHEME[MAP][2],
                'NCR': COLOR_SCHEME[MAP][8]}
MYORDER = ['ACC', 'NCR', 'BWI', 'FTL', 'BTL', 'MCR',
           'FTX', 'BTX', 'KOB']
for key in status_color:
    assert key in MYORDER, 'Missing {} in MYORDER'.format(key)
# make legend:
patches = []
labels = []
for key in MYORDER:
    leg = mpatches.Patch(color=status_color[key])
    patches.append(leg)
    labels.append(key)
legend1 = plt.legend(patches, labels, ncol=3, bbox_to_anchor=(1.0, 1.1))
ax.add_artist(legend1)
legend2 = plt.legend((scatter_start, scatter_end), ('Start', 'End'),
                     scatterpoints=1, ncol=2, frameon=False,
                     columnspacing=1,
                     handletextpad=0, prop={'size': 12},
                     bbox_to_anchor=(0.275, 1.1))


def init():
    """
    This function declears what to re-draw when clearing the frame:

    Returns
    -------
    out : list
        list of the patches to be drawn
    """
    patches = []
    for line in last_paths:
        line.set_data([], [])
        patches.append(line)
    for point in last_start_points:
        point.set_offsets([])
        patches.append(point)
    for point in last_end_points:
        point.set_offsets([])
        patches.append(point)
    time_text.set_text('')
    patches.append(time_text)
    return patches


def update_scatter(scatter_queue, orderp, ordervel, status):
    """
    To update the scatter points. Used by `update` defined below.

    Parameters
    ----------
    scatter_queue : collections.deque
        The list of scatter points
    orderp : float
        The order parameter
    ordervel : float
        The velocity of the order parameter
    status : string
        Status for the path
    """
    patches = []
    new_point = scatter_queue.popleft()
    new_point.set_offsets([orderp, ordervel])
    new_point.set_color(status_color[status])
    scatter_queue.append(new_point)
    for i, point in enumerate(scatter_queue):
        point.set_alpha(alpha[i])
        patches.append(point)
    return patches


def update(frame, simulation):
    """
    This function will be running the simulation and updating the plots.
    It is called one time per step, and we choose to update the simulation
    inside this function

    Parameters
    ----------
    frame : int
        The current frame number, supplied by animation.FuncAnimation
    simulation : object
        The simulation we are running.

    Returns
    -------
    out : list
        list of the patches to be drawn
    """
    patches = []
    if not simulation.is_finished():
        result = simulation.step()
        trial = result['trialpath']
        status = result['status']
        if trial is None:
            initial = True
            path = result['pathensemble'].last_path
        else:
            initial = False
            path = trial

        orderp = [p[0] for p in path.order[::6]]
        orderp.append(path.order[-1][0])  # force adding of the last point
        orderp = np.array(orderp)
        ordervel = [p[1] for p in path.order[::6]]
        ordervel.append(path.order[-1][1])  # force adding of the last point
        ordervel = np.array(ordervel)


        new_line = last_paths.popleft()
        new_line.set_data(orderp, ordervel)
        if initial:
            new_line.set_color(COLORS['almost_black'])
        else:
            new_line.set_color(status_color[status])
        last_paths.append(new_line)
        for i, line in enumerate(last_paths):
            line.set_alpha(alpha[i])
            patches.append(line)

        pscatter = update_scatter(last_start_points, orderp[0], ordervel[0],
                                  status)
        patches += pscatter
        pscatter = update_scatter(last_end_points, orderp[-1], ordervel[-1],
                                  status)
        patches += pscatter
        time_text.set_text('Cycle: {:d}'.format(frame))
        patches.append(time_text)
        return patches
    else:
        print('Simulation is done')
        return patches


anim = animation.FuncAnimation(fig, update,
                               frames=simulation_settings['steps']+1,
                               fargs=[simulation_tis],
                               repeat=False,
                               interval=2,
                               blit=True, init_func=init)
# for making a movie:
# anim.save('tis.mpeg', fps=30)
plt.show()
