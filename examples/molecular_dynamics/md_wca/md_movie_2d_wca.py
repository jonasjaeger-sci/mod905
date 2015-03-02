# -*- coding: utf-8 -*-
"""
Example of running a MD NVE simulation
"""
# pylint: disable=C0103
from __future__ import print_function
from retis.core import (Simulation,
                        System,
                        Box,
                        random_normal,
                        seed_random_generator,
                        generate_maxwellian_velocities)
from retis.core.integrators import VelocityVerlet
from retis.core.units import CONVERT
from retis.forcefield import ForceField, PairWCAnp, DoubleWellWCA
from retis.io import WriteGromacs
from retis.tools import lattice_simple_cubic
from retis.core.particlefunctions import (calculate_kinetic_energy_tensor,
                                          calculate_kinetic_temperature,
                                          reset_momentum)
import numpy as np

# set up potential function(s) and force field:
wca = PairWCAnp(dim=2)
wca_parameters = {'A': {'sigma': 1.0, 'epsilon': 1.0},
                  'B': {'sigma': 1.0, 'epsilon': 1.0}}

dwca = DoubleWellWCA(dim=2)
dwca_parameters = {'types': [('B', 'B')], 'rzero': 1.0*(2.0**(1.0/6.0)),
                   'height': 6.0, 'width': 0.25}

forcefield = ForceField(potential=[wca, dwca], params=[wca_parameters,
                                                       dwca_parameters])

colors = {'A': 'blue', 'B': 'magenta'}
size = np.array([[0.0, 3.4], [0.0, 3.4]])
box = Box(size)
ljsystem = System(temperature=2.0, units='lj', box=box)
# generate some lattice points, this will give 9 points
lattice = lattice_simple_cubic(box.size, spacing=1.0)
for i, lattice_pos in enumerate(lattice):
    ljsystem.add_particle(name='A', pos=lattice_pos, mass=1.0, ptype='A')
# mutate two particles to be of type B
bidx = [7, 8]
for i in bidx:
    ljsystem.particles.ptype[i] = 'B'
npart = ljsystem.particles.npart
print('Added {} particles to a simple square lattice'.format(npart))
npart = float(npart)
# generate velocities:
seed_random_generator()
ljsystem.adjust_dof([1, 1]) # adjust DOF since we are in "NVEMG"
generate_maxwellian_velocities(ljsystem)
temp, avgtemp, _ = calculate_kinetic_temperature(ljsystem)
print('Generated temperatures with average: {}'.format(avgtemp))
ljsystem.forcefield = forcefield
# also initiate forces:
ljsystem.potential_and_force()

write_gro = WriteGromacs('test.gro', box, frame=0, units=ljsystem.units)

numberofsteps = 1100
simulationNVE = Simulation(endcycle=numberofsteps)
timestep = 0.0025
integrator = VelocityVerlet(timestep)
timeunit = timestep * CONVERT['time']['lj', 'fs']
timeendfs = numberofsteps * timeunit

task_integrate = {'func': integrator.integration_step,
                  'args': [ljsystem]}
simulationNVE.add_task(task_integrate)

outfmt = '{0:8d} {1:12.7f} {2:12.7f} {3:12.7f} {4:12.7f}'
step, v_pot, e_kin, e_tot, temperature = [], [], [], [], []
time = []

# We will in this example animate
# on the fly. We will then have to set up some matplotlib-specific
# stuff:
from matplotlib import pyplot as plt
from matplotlib import animation
from matplotlib import rc
import matplotlib.gridspec as gridspec
rc('axes', labelsize='large')
rc('font', family='serif')
fig = plt.figure(figsize=(12, 6))
gs = gridspec.GridSpec(2, 2)

# This will just set up some dimensions etc. for the plotting:
dx = size[0][1] - size[0][0]
f = 0.12
dx = np.array([-dx*f, dx*f])
dy = size[1][1] - size[1][0]
dy = np.array([-dy*f * 0.1, dy*f*0.1])
SIGMA = CONVERT['length']['lj', 'Å']
ECONV = CONVERT['energy']['lj', 'kcal/mol']

# This adds the first axis. Here we will plot the
# particles with velocity and force vectors.
ax = fig.add_subplot(gs[:, 0])
ax.set_xlim((size[0] + dx) * SIGMA)
ax.set_ylim((size[1] + dy) * SIGMA)
ax.set_aspect('equal', 'datalim')
ax.set_xlabel(r'$x/\AA{}$')
ax.set_ylabel(r'$y/\AA{}$')
ax.set_xticks([size[0][0] * SIGMA, size[0][1] * SIGMA])
ax.set_yticks([size[1][0] * SIGMA, size[1][1] * SIGMA])
ax.xaxis.labelpad = -5
ax.yaxis.labelpad = -10

pos0 = box.pbc_wrap(ljsystem.particles.pos)
# set up circles to represent the particles:
circles = []
for _ in range(int(npart)):
    circles.append(plt.Circle((0, 0), radius=SIGMA*0.5, alpha=0.5))
    circles[-1].set_visible(False)
    ax.add_patch(circles[-1])
# add arrows for the forces and velocities:
force_arrow = plt.quiver(pos0[:, 0], pos0[:, 1], zorder=4)
vel_arrow = plt.quiver(pos0[:, 0], pos0[:, 1], color='darkgreen', zorder=4)
# also add arrows for a "legend":
plt.quiverkey(force_arrow, 1, -3.5, 6, 'Forces', coordinates='data',
              color='black')
plt.quiverkey(vel_arrow, 4, -3.5, 6, 'Velocities', coordinates='data',
              color='darkgreen')
# also add a line representing the bond
linebond, = ax.plot(None, None, lw=2, ls='-', color='magenta', alpha=0.7)
# this will draw the lines representing the box boundaries:
ax.axhline(y=size[1][0]*SIGMA, lw=2, ls=':', color='k')
ax.axhline(y=size[1][1]*SIGMA, lw=2, ls=':', color='k')
ax.axvline(x=size[0][0]*SIGMA, lw=2, ls=':', color='k')
ax.axvline(x=size[0][1]*SIGMA, lw=2, ls=':', color='k')

ax2 = fig.add_subplot(gs[0, 1])
ax2.set_xlim(0, timeendfs)
ax2.set_ylim(-0.6, 0.6)
ax2.set_xlabel('Time/fs')
ax2.set_ylabel('Energy/kcal/mol')
time_text = ax2.text(0.02, 0.90, '', transform=ax2.transAxes)
linepot, = ax2.plot(None, None, lw=3, ls='-', color='blue', alpha=0.5,
                    label='Potential')
linekin, = ax2.plot(None, None, lw=3, ls='-', color='green', alpha=0.5,
                    label='Kinetic')
linetot, = ax2.plot(None, None, lw=3, ls='-', color='k', alpha=0.5,
                    label='Total')
ax2.legend(loc='lower left', ncol=2, frameon=False)


def plot_dwca_potential():
    """
    This is a helper function to plot the dwca potential.
    It is creating a fake system with a fake box and moves a
    particle relative to another one in order to obtain the potential.
    """
    rpos = np.linspace(0.1, 5, 500)
    potdwca = []
    fakesize = np.array([[0.0, 10.0], [0.0, 10.0]])
    fakebox = Box(fakesize)
    fakesys = System(units='lj', box=fakebox)
    fakesys.add_particle(name='B', pos=np.zeros(2), ptype='B')
    fakesys.add_particle(name='B', pos=np.zeros(2), ptype='B')
    for ri in rpos:
        fakesys.particles.pos[-1] = np.array([ri, 0.0])
        potdwca.append(dwca.potential(fakesys.particles, fakebox))
    return rpos, np.array(potdwca)

ax3 = fig.add_subplot(gs[1, 1])
rbond, pot_dwca = plot_dwca_potential()
linedwpot, = ax3.plot(rbond, pot_dwca, lw=3, ls='-', color='black')
ax3.set_ylim(0, dwca.height + 1)
min_max = dwca.min_max()
ax3.set_xlim(min_max[0] - 0.2, min_max[1] + 0.2)
ax3.set_ylabel('Potential')
ax3.set_xlabel('Bond length')
orderscatter = ax3.scatter(None, None, alpha=0.5, color='magenta',
                           marker='o', s=200)
plt.subplots_adjust(left=0.1, top=0.95, bottom=0.15, right=0.95, hspace=0.3)


def energy_calculation(system):
    """
    This is a helper function to calculate energies for the system.

    Parameters
    ----------
    system : object
        The system object, with a particle list, which we can use to compute
        the energies.
    """
    kin_tens = calculate_kinetic_energy_tensor(system)
    _, avgtemp, _ = calculate_kinetic_temperature(system,
                                                  kin_tensor=kin_tens)
    kini = kin_tens.trace()
    return avgtemp, system.v_pot, kini


def init():
    """
    This function declears what to re-draw when clearing the frame:

    Returns
    -------
    out : list
        list of the patches to be drawn
    """
    patches = []
    for ci in circles:
        ci.set_visible(False)
        patches.append(ci)
    linebond.set_data(None, None)
    patches.append(linebond)
    force_arrow.set_visible(False)
    patches.append(force_arrow)
    vel_arrow.set_visible(False)
    patches.append(vel_arrow)
    time_text.set_text('')
    patches.append(time_text)
    return patches


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
    ptypes = ljsystem.particles.ptype
    for ci, pi, itype in zip(circles, pos, ptypes):
        ci.center = np.array([pi[0], pi[1]])*SIGMA
        ci.set_color(colors[itype])
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
        # reaction coordinate:
        delta = box.pbc_dist_coordinate(ljsystem.particles.pos[bidx[0]] -
                                        ljsystem.particles.pos[bidx[1]])
        dr = np.sqrt(np.dot(delta, delta))
        points = [dr, dwca.potential(ljsystem.particles, box)]
        orderscatter.set_offsets(points)
        patches.append(orderscatter)
        # draw the bond:
        xpos = np.array([pos[bidx[1], 0], pos[bidx[1], 0] + delta[0]]) * SIGMA
        ypos = np.array([pos[bidx[1], 1], pos[bidx[1], 1] + delta[1]]) * SIGMA
        linebond.set_data(xpos, ypos)
        patches.append(linebond)
        # here we calculate some energies and updates the energy plots:
        step.append(simulationNVE.cycle['step'])
        time.append(step[-1] * timeunit)
        temp, vpot, ekin = energy_calculation(system)
        temperature.append(temp)
        v_pot.append(ECONV * vpot / npart)
        e_kin.append(ECONV * ekin / npart)
        e_tot.append(e_kin[-1] + v_pot[-1])
        # update plots with energies:
        linepot.set_data(time, (np.array(v_pot) - v_pot[0]))
        patches.append(linepot)
        linekin.set_data(time, (np.array(e_kin) - e_kin[0]))
        patches.append(linekin)
        linetot.set_data(time, (np.array(e_tot) - e_tot[0]))
        patches.append(linetot)
        # also display current simulation time;
        time_text.set_text('Time: {0:6.2f} fs'.format(time[-1]))
        patches.append(time_text)
        # output energies to the screen:
        print(outfmt.format(step[-1], temperature[-1], v_pot[-1],
                            e_kin[-1], e_tot[-1]))
        # store the trajectory to a .gro file:
        write_gro.write_frame(pos, atomname=ljsystem.particles.ptype)
        # finally, do the simultion step:
        simulationNVE.step()
        return patches
    else:
        print('Simulation is done')
        return patches


# This will run the animation/simulation:
anim = animation.FuncAnimation(fig, update, frames=numberofsteps,
                               fargs=[ljsystem], repeat=False, interval=2,
                               blit=True, init_func=init)
# for making a movie:
#anim.save('particles.mp4', fps=30, extra_args=['-vcodec', 'libx264'])
plt.show()
