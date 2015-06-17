# -*- coding: utf-8 -*-
"""
Example of running a MD NVE simulation.
In this example we animate the output.
"""
# pylint: disable=C0103
from __future__ import print_function
from retis.core import Simulation, System, Box, RandomGenerator
from retis.core.integrators import VelocityVerlet
from retis.core.units import CONVERT
from retis.forcefield import ForceField, PairLennardJonesCutnp
from retis.inout import WriteGromacs
from retis.tools import lattice_simple_cubic
from retis.core.particlefunctions import (calculate_kinetic_energy_tensor,
                                          calculate_kinetic_temperature)
import numpy as np

# set up potential function(s) and force field:
ljpot = PairLennardJonesCutnp(dim=2, shift=True)
ljparams = {'Ar': {'sigma': 1.0, 'epsilon': 1.0, 'rcut': 2.5},
            'mixing': 'geometric'}
forcefield = ForceField(potential=[ljpot], params=[ljparams])

size = np.array([[0.0, 12.0/3.405], [0.0, 12.0/3.405]])
box = Box(size)
ljsystem = System(temperature=1.0, units='lj', box=box)
# generate some lattice points, this will give approx 9 points
lattice = lattice_simple_cubic(box.size, spacing=1.0)
for i, lattice_pos in enumerate(lattice):
    if i == 4:
        continue
    ljsystem.add_particle(name='Ar', pos=lattice_pos, mass=1.0, ptype='Ar')
npart = ljsystem.particles.npart
print('Added {} particles to a simple square lattice'.format(npart))
npart = float(npart)
# generate velocities:
ljsystem.adjust_dof([1, 1]) # adjust DOF since we are in "NVEMG"
DOF = ljsystem.temperature['dof']
rgen = RandomGenerator(seed=0)
ljsystem.generate_velocities(rgen, momentum=False)
temp, avgtemp, _ = calculate_kinetic_temperature(ljsystem.particles, dof=DOF)
print('Generated temperatures with average: {}'.format(avgtemp))

ljsystem.forcefield = forcefield
# also initiate forces:
ljsystem.potential_and_force()

write_gro = WriteGromacs('test.gro', box, frame=0, units=ljsystem.units)

numberofsteps = 950
simulationNVE = Simulation(endcycle=numberofsteps)
timestep = 0.0025
timeunit = timestep * CONVERT['time']['lj', 'fs']
integrator = VelocityVerlet(timestep)
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
rc('axes', labelsize='large')
rc('font', family='serif')
fig = plt.figure(figsize=(12, 6))

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
ax = fig.add_subplot(121)
ax.set_xlim((size[0] + dx) * SIGMA)
ax.set_ylim((size[1] + dy) * SIGMA)
ax.set_aspect('equal', 'datalim')
ax.set_xlabel(r'$x/\AA{}$')
ax.set_ylabel(r'$y/\AA{}$')
ax.set_xticks([size[0][0] * SIGMA, size[0][1] * SIGMA])
ax.set_yticks([size[1][0] * SIGMA, size[1][1] * SIGMA])
ax.xaxis.labelpad = -5
ax.yaxis.labelpad = -5

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
plt.quiverkey(force_arrow, 1, -4, 6, 'Forces', coordinates='data',
              color='black')
plt.quiverkey(vel_arrow, 4, -4, 6, 'Velocities', coordinates='data',
              color='darkgreen')
# this will draw the lines representing the box boundaries:
ax.axhline(y=size[1][0]*SIGMA, lw=2, ls=':', color='k')
ax.axhline(y=size[1][1]*SIGMA, lw=2, ls=':', color='k')
ax.axvline(x=size[0][0]*SIGMA, lw=2, ls=':', color='k')
ax.axvline(x=size[0][1]*SIGMA, lw=2, ls=':', color='k')

ax2 = fig.add_subplot(122)
ax2.set_xlim(0, timeendfs)
ax2.set_ylim(-0.6, 0.6)
ax2.set_xlabel('Time/fs')
ax2.set_ylabel('Energy/kcal/mol')
time_text = ax2.text(0.02, 0.95, '', transform=ax2.transAxes)
linepot, = ax2.plot(None, None, lw=3, ls='-', color='blue', alpha=0.5,
                    label='Potential')
linekin, = ax2.plot(None, None, lw=3, ls='-', color='green', alpha=0.5,
                    label='Kinetic')
linetot, = ax2.plot(None, None, lw=3, ls='-', color='k', alpha=0.5,
                    label='Total')
ax2.legend(loc='lower left', ncol=2, frameon=False)
plt.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.15)


def energy_calculation(system):
    """
    This is a helper function to calculate energies for the system.

    Parameters
    ----------
    system : object
        The system object, with a particle list, which we can use to compute
        the energies.
    """
    particles = system.particles
    dof = system.temperature['dof']
    kin_tens = calculate_kinetic_energy_tensor(particles)
    _, avgtemp, _ = calculate_kinetic_temperature(particles, dof=dof,
                                                  kin_tensor=kin_tens)
    kini = kin_tens.trace()
    return avgtemp, system.v_pot, kini


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

    if not simulationNVE.is_finished():
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
        write_gro.write_frame(pos)
        # finally, do the simultion step:
        simulationNVE.step()
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
    return patches


# This will run the animation/simulation:
anim = animation.FuncAnimation(fig, update, frames=numberofsteps,
                               fargs=[ljsystem], repeat=False, interval=2,
                               blit=True, init_func=init)
# for making a movie:
#anim.save('particles.mp4', fps=30, extra_args=['-vcodec', 'libx264'])
plt.show()
