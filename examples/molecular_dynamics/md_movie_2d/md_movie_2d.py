# -*- coding: utf-8 -*-
"""
Example of running a MD NVE simulation.
In this example we animate the output.
"""
# pylint: disable=C0103
from __future__ import print_function
# retis imports:
from retis.core import System, Box
from retis.core.simulation import create_simulation
from retis.core.units import CONVERT
from retis.forcefield import ForceField
from retis.forcefield.pairpotentials import PairLennardJonesCutnp
from retis.tools import lattice_simple_cubic
from retis.inout.plotting import _COLORS, _COLOR_SCHEME
# imports for the plotting:
from matplotlib import pyplot as plt
from matplotlib import animation
import matplotlib as mpl
# other imports:
import numpy as np


# set up simulation settings:
settings = {'type': 'NVE',
            'integrator': {'name': 'velocityverlet', 'timestep': 0.0025},
            'endcycle': 950,
            'output': [{'target': 'file', 'type': 'traj', 'every': 1,
                        'format': 'gro'}],
            'units': 'lj',
            'temperature': 1.0,
            'generate-vel': {'seed': 0, 'momentum': True,
                             'distribution': 'maxwell'}}
# set up potential function(s) and force field:
ljpot = PairLennardJonesCutnp(dim=2, shift=True)
ljparams = {'Ar': {'sigma': 1.0, 'epsilon': 1.0, 'rcut': 2.5},
            'mixing': 'geometric'}
forcefield = ForceField(potential=[ljpot], params=[ljparams])

# create a box:
size = np.array([[0.0, 12.0 / 3.405], [0.0, 12.0 / 3.405]])
box = Box(size)

# create a system:
ljsystem = System(temperature=settings['temperature'],
                  units=settings['units'], box=box)

# generate some lattice points, this will give 9 points
# also add particles at (some of) the lattice locations
lattice = lattice_simple_cubic(box.size, spacing=1.0)
for i, lattice_pos in enumerate(lattice):
    if i == 4:
        continue
    ljsystem.add_particle(name='Ar', pos=lattice_pos, mass=1.0, ptype='Ar')

npart = ljsystem.particles.npart
msg = 'Added {:d} particles to a simple square lattice'
print(msg.format(npart))
npart = float(npart)

# generate velocities:
if 'generate-vel' in settings:
    ljsystem.generate_velocities(**settings['generate-vel'])
    msg = 'Generated temperatures with average: {}'
    print(msg.format(ljsystem.calculate_temperature()))

# attach the force field:
ljsystem.forcefield = forcefield

# create simulation :-)
simulation_nve = create_simulation(settings, ljsystem)

# We will in this example animate on the flym then we will have to do some
# extra set up. The actual simulation is carried out by calling
# `simulation_nve.step()` in the `update` function which is executed by
# the animation.FuncAnimation() call. In effect animation.FuncAnimation will
# run the simulation one step, update the plot and display it and continue
# this loop until the simulation is done.
timeunit = (settings['integrator']['timestep'] *
            CONVERT['time'][ljsystem.units, 'fs'])
timeendfs = settings['endcycle'] * timeunit
time, step, v_pot, e_kin, e_tot, temperature = [], [], [], [], [], []
SIGMA = CONVERT['length']['lj', 'Å']
ECONV = CONVERT['energy']['lj', 'kcal/mol']

mpl.rc('axes', labelsize='large')
mpl.rc('font', family='serif')
fig = plt.figure(figsize=(12, 6))
# This adds the first axis. Here we will plot the
# particles with velocity and force vectors.
ax = fig.add_subplot(121)
ax.set_xlim((size[0] + np.array([-0.5, 0.5])) * SIGMA)
ax.set_ylim((size[1] + np.array([-0.5, 0.5])) * SIGMA)
ax.set_aspect('equal', 'datalim')
ax.set_xlabel(u'x / Å')
ax.set_ylabel(u'y / Å')
ax.set_xticks([size[0][0] * SIGMA, size[0][1] * SIGMA])
ax.set_yticks([size[1][0] * SIGMA, size[1][1] * SIGMA])
ax.xaxis.labelpad = -5
ax.yaxis.labelpad = -5

pos0 = box.pbc_wrap(ljsystem.particles.pos)
# set up circles to represent the particles:
circles = []
for _ in range(int(npart)):
    circles.append(plt.Circle((0, 0), radius=SIGMA * 0.5, alpha=0.5,
                              color='blue'))
    circles[-1].set_visible(False)
    ax.add_patch(circles[-1])
# add arrows for the forces and velocities:
force_arrow = plt.quiver(pos0[:, 0], pos0[:, 1],
                         color=_COLORS['almost_black'], zorder=4)
vel_arrow = plt.quiver(pos0[:, 0], pos0[:, 1],
                       color=_COLOR_SCHEME['colorblind_10'][1], zorder=4)
# also add arrows for a "legend":
plt.quiverkey(force_arrow, 3, -3.5, 9, 'Forces', coordinates='data',
              color=_COLORS['almost_black'], fontproperties={'size': 'large'})
plt.quiverkey(vel_arrow, 9, -3.5, 9, 'Velocities', coordinates='data',
              color=_COLOR_SCHEME['colorblind_10'][1],
              fontproperties={'size': 'large'})
# this will draw the lines representing the box boundaries:
ax.axhline(y=size[1][0] * SIGMA, lw=2, ls=':', color=_COLORS['almost_black'])
ax.axhline(y=size[1][1] * SIGMA, lw=2, ls=':', color=_COLORS['almost_black'])
ax.axvline(x=size[0][0] * SIGMA, lw=2, ls=':', color=_COLORS['almost_black'])
ax.axvline(x=size[0][1] * SIGMA, lw=2, ls=':', color=_COLORS['almost_black'])
# add second axis for plotting the energies
ax2 = fig.add_subplot(122)
ax2.set_xlim(0, timeendfs)
ax2.set_ylim(-0.6, 0.6)
ax2.set_xlabel('Time / fs')
ax2.set_ylabel('Energy / (kcal/mol)')
time_text = ax2.text(0.02, 0.95, '', transform=ax2.transAxes)
linepot, = ax2.plot(None, None, lw=4, ls='-', color=_COLOR_SCHEME['deep'][0],
                    alpha=0.8, label='Potential')
linekin, = ax2.plot(None, None, lw=4, ls='-', color=_COLOR_SCHEME['deep'][1],
                    alpha=0.8, label='Kinetic')
linetot, = ax2.plot(None, None, lw=4, ls='-', color=_COLORS['almost_black'],
                    alpha=0.8, label='Total')
ax2.legend(loc='lower left', ncol=2, frameon=False)
plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.15)


def get_max_vector(vectors):
    """
    Helper function that determines the "largest vector" given a set
    of vectors

    Parameters
    ----------
    vectors : numpy.array
        Numpy array of vectors to analyse, using np.dot
    """
    vmax = None
    for vi in vectors:
        vs = np.sqrt(np.dot(vi, vi))
        if vmax is None or vs > vmax:
            vmax = vs
    return vmax


def get_velocity_force_arrows(forces, vels):
    """
    This is a helper function to obtain the force and
    velocity vectors

    Paramters
    ---------
    pos : numpy.array
        The positions of the particles
    force : numpy.array
        The forces on the particles
    vel : numpy.array
        The velocity of the particles
    """
    fmax, vmax = get_max_vector(forces), get_max_vector(vels)
    FU, FV, VU, VV = [], [], [], []
    for fi, vi in zip(forces, vels):
        fj = 10.0 * fi / fmax
        vj = 10.0 * vi / vmax
        FU.append(fj[0])
        FV.append(fj[1])
        VU.append(vj[0])
        VV.append(vj[1])
    return FU, FV, VU, VV


def update(frame, system):
    """
    This function will be running the simulation and updating the plots.
    It is called one time per step, and we choose to update the simulation
    inside this function

    Parameters
    ----------
    frame : int
        The current frame number, supplied by animation.FuncAnimation
    system : object
        The system object we are simulating

    Returns
    -------
    out : list
        list of the patches to be drawn
    """
    pos = box.pbc_wrap(system.particles.pos)
    patches = []
    # update positions of the circles according to the particles:
    for ci, pi in zip(circles, pos):
        ci.center = np.array([pi[0], pi[1]]) * SIGMA
        ci.set_visible(True)
        patches.append(ci)
    # update the force and velocity vectors:
    FU, FV, VU, VV = get_velocity_force_arrows(system.particles.force,
                                               system.particles.vel)
    force_arrow.set_offsets(pos * SIGMA)
    force_arrow.set_UVC(FU, FV)
    force_arrow.set_visible(True)
    patches.append(force_arrow)
    vel_arrow.set_offsets(pos * SIGMA)
    vel_arrow.set_UVC(VU, VV)
    vel_arrow.set_visible(True)
    patches.append(vel_arrow)

    if not simulation_nve.is_finished():
        result = simulation_nve.step()
        # here we calculate some energies and updates the energy plots:
        step.append(result['cycle']['step'])
        time.append(step[-1] * timeunit)
        temperature.append(result['thermo']['temp'])
        v_pot.append(ECONV * result['thermo']['vpot'])
        e_kin.append(ECONV * result['thermo']['ekin'])
        e_tot.append(e_kin[-1] + v_pot[-1])
        # update plots with energies:
        linepot.set_data(time, (np.array(v_pot) - v_pot[0]))
        patches.append(linepot)
        linekin.set_data(time, (np.array(e_kin) - e_kin[0]))
        patches.append(linekin)
        linetot.set_data(time, (np.array(e_tot) - e_tot[0]))
        patches.append(linetot)
        # also display current simulation time;
        time_text.set_text('Time: {0:6.2f} fs (frame: {1})'.format(time[-1],
                                                                   frame))
        patches.append(time_text)
        return patches
    else:
        print('Simulation is done.')
        return patches


def init():
    """
    This function declears what to re-draw when clearing the frame:

    Returns
    -------
    out : list
        list of the patches to be drawn
    """
    patches = []
    force_arrow.set_visible(False)
    patches.append(force_arrow)
    vel_arrow.set_visible(False)
    patches.append(vel_arrow)
    time_text.set_text('')
    patches.append(time_text)
    for ci in circles:
        ci.set_visible(False)
        patches.append(ci)
    return patches


# This will run the animation/simulation:
anim = animation.FuncAnimation(fig, update, frames=settings['endcycle']+1,
                               fargs=[ljsystem], repeat=False, interval=2,
                               blit=True, init_func=init)
# for making a movie:
# anim.save('particles.mp4', fps=30, extra_args=['-vcodec', 'libx264'])
plt.show()
