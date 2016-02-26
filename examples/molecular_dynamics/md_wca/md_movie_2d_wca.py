# -*- coding: utf-8 -*-
"""
Example of running a MD NVE simulation
"""
# pylint: disable=C0103
from __future__ import print_function
import numpy as np
from pyretis.core import System, Box
from pyretis.inout.settings import create_simulation
from pyretis.core.units import CONVERT, create_conversion_factors
from pyretis.forcefield import ForceField
from pyretis.forcefield.potentials import PairLennardJonesCutnp, DoubleWellWCA
from pyretis.tools import generate_lattice
from pyretis.inout.plotting import COLORS, COLOR_SCHEME
from pyretis.inout import create_output
# imports for the plotting:
from matplotlib import pyplot as plt
from matplotlib import animation
import matplotlib as mpl
import matplotlib.gridspec as gridspec
# simulation settings:
settings = {'task': 'md-nve',
            'integrator': {'class': 'velocityverlet', 'timestep': 0.0025},
            'endcycle': 1100,
            'output-modify': [{'name': 'traj', 'when': {'every': 1}}],
            'generate-vel': {'seed': 0, 'momentum': True,
                             'distribution': 'maxwell'},
            'temperature': 2.0,
            'units': 'lj'}
create_conversion_factors(settings['units'])
# set up potential function(s) and force field:
wca = PairLennardJonesCutnp(dim=2)
wca_parameters = {0: {'sigma': 1.0, 'epsilon': 1.0, 'factor': 2.**(1./6.)},
                  1: {'sigma': 1.0, 'epsilon': 1.0, 'factor': 2.**(1./6.)},
                  'mixing': 'geometric'}

dwca = DoubleWellWCA(dim=2)
dwca_parameters = {'types': [(1, 1)], 'rzero': 1.0 * (2.0**(1.0/6.0)),
                   'height': 6.0, 'width': 0.25}

forcefield = ForceField(potential=[wca, dwca], params=[wca_parameters,
                                                       dwca_parameters])

PCOLOR = {'A': 'blue', 'B': 'magenta'}
# generate some lattice points, this will give 9 points
lattice, size = generate_lattice('sq', [3, 3], lcon=1.0)
# increase box slightly:
size = [[i[0], i[1]*1.1] for i in size]
box = Box(size)
# center lattice
lattice -= np.average(lattice, axis=0) - 0.5 * box.length
ljsystem = System(temperature=settings['temperature'],
                  units=settings['units'], box=box)
BIDX = [7, 8]
for i, lattice_pos in enumerate(lattice):
    if i in BIDX:
        ljsystem.add_particle(name='B', pos=lattice_pos, mass=1.0, ptype=1)
    else:
        ljsystem.add_particle(name='A', pos=lattice_pos, mass=1.0, ptype=0)
npart = ljsystem.particles.npart
print('Added {:d} particles to a simple square lattice'.format(npart))
npart = float(npart)
# generate velocities:
if 'generate-vel' in settings:
    ljsystem.generate_velocities(**settings['generate-vel'])
    msg = 'Generated temperatures with average: {}'
    print(msg.format(ljsystem.calculate_temperature()))
# attach force field:
ljsystem.forcefield = forcefield
# create the simulation :-)
simulationNVE = create_simulation(settings, ljsystem)
# create outputs for this simulation:
outputs = [task for task in create_output(settings)]
# some additional set-up for the animation
timeunit = (settings['integrator']['timestep'] *
            CONVERT['time'][settings['units'], 'fs'])
timeendfs = settings['endcycle'] * timeunit

time, step, v_pot, e_kin, e_tot, temperature = [], [], [], [], [], []
SIGMA = CONVERT['length'][settings['units'], 'A']
ECONV = CONVERT['energy'][settings['units'], 'kcal/mol']
# We will in this example animate on the fly. Here we do some additional
# set-up to be able to do just that :-)
mpl.rc('axes', labelsize='large')
mpl.rc('font', family='serif')
fig = plt.figure(figsize=(12, 6))
gs = gridspec.GridSpec(2, 2)
# This adds the first axis. Here we will plot the
# particles with velocity and force vectors.
ax = fig.add_subplot(gs[:, 0])
ax.set_xlim((size[0] + np.array([-0.5, 0.5])) * SIGMA)
ax.set_ylim((size[1] + np.array([-0.5, 0.5])) * SIGMA)
ax.set_aspect('equal', 'datalim')
ax.set_xlabel(u'x / Å')
ax.set_ylabel(u'y / Å')
ax.set_xticks([size[0][0] * SIGMA, size[0][1] * SIGMA])
ax.set_yticks([size[1][0] * SIGMA, size[1][1] * SIGMA])
ax.xaxis.labelpad = -5
ax.yaxis.labelpad = -10

pos0 = box.pbc_wrap(ljsystem.particles.pos)
# set up circles to represent the particles:
circles = []
for _ in range(int(npart)):
    circles.append(plt.Circle((0, 0), radius=SIGMA * 0.5, alpha=0.5))
    circles[-1].set_visible(False)
    ax.add_patch(circles[-1])
# add arrows for the forces and velocities:
force_arrow = plt.quiver(pos0[:, 0], pos0[:, 1],
                         color=COLORS['almost_black'], zorder=4)
vel_arrow = plt.quiver(pos0[:, 0], pos0[:, 1],
                       color=COLOR_SCHEME['colorblind_10'][1], zorder=4)
# also add arrows for a "legend":
plt.quiverkey(force_arrow, 3, -3.5, 9, 'Forces', coordinates='data',
              color=COLORS['almost_black'], fontproperties={'size': 'large'})
plt.quiverkey(vel_arrow, 9, -3.5, 9, 'Velocities', coordinates='data',
              color=COLOR_SCHEME['colorblind_10'][1],
              fontproperties={'size': 'large'})
# also add a line representing the bond
linebond, = ax.plot([], [], lw=3, ls='-', color=PCOLOR['B'], alpha=0.8)
# draw lines representing the box boundaries:
ax.axhline(y=size[1][0] * SIGMA, lw=2, ls=':', color=COLORS['almost_black'])
ax.axhline(y=size[1][1] * SIGMA, lw=2, ls=':', color=COLORS['almost_black'])
ax.axvline(x=size[0][0] * SIGMA, lw=2, ls=':', color=COLORS['almost_black'])
ax.axvline(x=size[0][1] * SIGMA, lw=2, ls=':', color=COLORS['almost_black'])
# add second axis for displaying energies:
ax2 = fig.add_subplot(gs[0, 1])
ax2.set_xlim(0, timeendfs)
ax2.set_ylim(-0.55, 0.55)
ax2.set_xlabel('Time / fs')
ax2.set_ylabel('Energy / (kcal/mol)')
time_text = ax2.text(0.02, 0.90, '', transform=ax2.transAxes)
linepot, = ax2.plot([], [], lw=4, ls='-', color=COLOR_SCHEME['deep'][0],
                    alpha=0.8, label='Potential')
linekin, = ax2.plot([], [], lw=4, ls='-', color=COLOR_SCHEME['deep'][1],
                    alpha=0.8, label='Kinetic')
linetot, = ax2.plot([], [], lw=4, ls='-', color=COLORS['almost_black'],
                    alpha=0.8, label='Total')
ax2.legend(loc='lower left', ncol=3, frameon=False,
           columnspacing=1, labelspacing=1)


def plot_dwca_potential():
    """Plot the double well WCA potential.

    This is a helper function to plot the dwca potential.
    It is creating a fake system with a fake box and moves a
    particle relative to another one in order to obtain the potential.

    Returns
    -------
    out[0] : numpy.array
        Positions, can be used as an x-coordinate in a plot.
    out[1] : numpy.array
        The potential energy as a function of `out[0]`, can be used as the
        y-coordinate in a plot.
    """
    rpos = np.linspace(0.1, 5, 500)
    potdwca = []
    fakesize = np.array([[0.0, 10.0], [0.0, 10.0]])
    fakebox = Box(fakesize)
    fakesys = System(units='lj', box=fakebox)
    fakesys.add_particle(name='B', pos=np.zeros(2), ptype=1)
    fakesys.add_particle(name='B', pos=np.zeros(2), ptype=1)
    for ri in rpos:
        fakesys.particles.pos[-1] = np.array([ri, 0.0])
        potdwca.append(dwca.potential(fakesys.particles, fakebox))
    return rpos, np.array(potdwca)


# add third axis for plotting the potential and order parameter:
ax3 = fig.add_subplot(gs[1, 1])
rbond, pot_dwca = plot_dwca_potential()
linedwpot, = ax3.plot(rbond, pot_dwca, lw=3, ls='-',
                      color=COLORS['almost_black'])
ax3.set_ylim(0, dwca.params['height'] + 1)
min_max = dwca.min_max()
ax3.set_xlim(min_max[0] - 0.2, min_max[1] + 0.2)
ax3.set_ylabel('Double well potential')
ax3.set_xlabel('Bond length (circle)')
orderscatter = ax3.scatter([], [], alpha=0.5, color=PCOLOR['B'],
                           marker='o', s=200)
plt.subplots_adjust(left=0.08, top=0.95, bottom=0.15, right=0.95, hspace=0.3)


def init():
    """Declare what to re-draw when clearing the animation frame.

    Returns
    -------
    out : list
        list of the patches to be drawn
    """
    patches = []
    for ci in circles:
        ci.set_visible(False)
        patches.append(ci)
    linebond.set_data([], [])
    patches.append(linebond)
    force_arrow.set_visible(False)
    patches.append(force_arrow)
    vel_arrow.set_visible(False)
    patches.append(vel_arrow)
    time_text.set_text('')
    patches.append(time_text)
    orderscatter.set_offsets(([], []))
    patches.append(orderscatter)
    return patches


def get_max_vector(vectors):
    """Determine the longest vector in a list of vectors.

    Parameters
    ----------
    vectors : numpy.array
        Numpy array of vectors to analyse, using `numpy.dot`.

    Returns
    -------
    vmax : float
        The length of the largest vector.
    """
    vmax = None
    for vi in vectors:
        vs = np.sqrt(np.dot(vi, vi))
        if vmax is None or vs > vmax:
            vmax = vs
    return vmax


def get_velocity_force_arrows(forces, vels):
    """Obtain the force and velocity vectors.

    Parameters
    ----------
    forces : numpy.array
        The forces on the particles.
    vels : numpy.array
        The velocity of the particles.

    Returns
    -------
    out[0] : numpy.array
        The x-component of the forces, normalized.
    out[1] : numpy.array
        The y-component of the forces, normalized.
    out[2] : numpy.array
        The x-component of the velocities, normalized.
    out[3] : numpy.array
        The y-component of the velocities, normalized.
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


def spring_bond(delta, dr, part1, part2):
    """Create positions for a zig-zag line.

    This is a function that will create positions which can be used to
    create a zig-zag bond. It is used here to illustrate a spring bond
    between two atoms

    Parameters
    ----------
    delta : numpy.array
        Distance vector between `part1` and `part2`, subjected to periodic
        boundary conditions.
    dr : float
        Length of `delta` vector.
    part1 : numpy.array
        Particle 1 position. Bond is drawn from `part1`.
    part2 : numpy.array
        Particle 2 position. Bond is drawn to `part2`.

    Returns
    -------
    out[0] : numpy.array
        X-coordinates for the line.
    out[1] : numpy.array
        Y-coordinates for the line.
    """
    delta_u = delta / dr
    xpos = [part1[0]]
    ypos = [part1[1]]
    for pidx, add in enumerate(np.linspace(0.0, dr-1, 11)):
        point = part1 + (add + 0.5) * delta_u
        if pidx in [2, 4, 6, 8]:
            try:
                dperp = np.array([-delta_u[1] / delta_u[0], 1.0])
                dperp = dperp / np.sqrt(np.dot(dperp, dperp))
            except ZeroDivisionError:
                dperp = 0.0
            sig = 1 if delta_u[0] > 0.0 else -1.0
            if pidx in [2, 6]:
                dvec = sig*0.2*dperp
            else:
                dvec = -sig*0.2*dperp
            point = point + dvec
        xpos.append(point[0])
        ypos.append(point[1])
    xpos.append(part2[0])
    ypos.append(part2[1])
    xpos = np.array(xpos) * SIGMA
    ypos = np.array(ypos) * SIGMA
    return xpos, ypos


def update(frame, system, output_tasks):
    """Update plots for the animation.

    This function will be running the simulation and updating the plots.
    It is called one time per step, and we choose to update the simulation
    inside this function

    Parameters
    ----------
    frame : int
        The current frame number, supplied by `animation.FuncAnimation`.
    system : object
        The system object we are simulating
    output_tasks : list of objects like `OutputTask`
        This list defines the outputs to do for this simulation.

    Returns
    -------
    out : list
        List of the patches to be drawn.
    """
    pos = box.pbc_wrap(system.particles.pos)
    patches = []
    for ci, pi, itype in zip(circles, pos, system.particles.name):
        ci.center = np.array([pi[0], pi[1]]) * SIGMA
        ci.set_color(PCOLOR[itype])
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

    if not simulationNVE.is_finished():
        result = simulationNVE.step()
        for tsk in output_tasks:
            tsk.output(result)
        # reaction coordinate:
        delta = box.pbc_dist_coordinate(system.particles.pos[BIDX[1]] -
                                        system.particles.pos[BIDX[0]])
        dr = np.sqrt(np.dot(delta, delta))
        points = [dr, dwca.potential(system.particles, box)]
        orderscatter.set_offsets(points)
        patches.append(orderscatter)
        # draw the bond:
        xpos, ypos = spring_bond(delta, dr,
                                 system.particles.pos[BIDX[0]],
                                 system.particles.pos[BIDX[1]])
        linebond.set_data(xpos, ypos)
        patches.append(linebond)
        # here we calculate some energies and updates the energy plots:
        step.append(result['cycle']['step'])
        time.append(result['cycle']['step'] * timeunit)
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
        print('Simulation is done')
        return patches


# This will run the animation/simulation:
anim = animation.FuncAnimation(fig, update, frames=settings['endcycle']+1,
                               fargs=[ljsystem, outputs], repeat=False,
                               interval=2, blit=True, init_func=init)
# for making a movie:
# anim.save('particles.mp4', fps=30, extra_args=['-vcodec', 'libx264'])
plt.show()
