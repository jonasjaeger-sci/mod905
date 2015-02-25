# -*- coding: utf-8 -*-
from __future__ import print_function
"""
Example of running a MD NVE simulation
"""
from retis.core import Simulation, System, Box
from retis.core.particlefunctions import * 
from retis.core.integrators import VelocityVerlet
from retis.core.units import CONVERT
from retis.forcefield import ForceField, PairLennardJonesCutnp
from retis.io import WriteGromacs
from retis.tools import lattice_simple_cubic
import numpy as np 

# set up potential function(s) and force field:
lennard_jones = PairLennardJonesCutnp(dim=2)
lj_parameters = {'Ar': {'sigma': 1.0, 'epsilon': 1.0, 'rcut': 2.5},
              'mixing': 'geometric'}
forcefield = ForceField(potential=[lennard_jones], params=[lj_parameters])

target_temperature = 1.0
size = np.array([[0.0, 12.0/3.405], [0.0, 12.0/3.405]])
box = Box(size)
ljsystem = System(temperature=target_temperature, units='lj', box=box)
# generate some lattice points, this will give 9 points
lattice = lattice_simple_cubic(box.size, spacing=1)
for i,pos in enumerate(lattice):
    if i==4: continue
    ljsystem.add_particle(name='Ar', pos=pos, mass=1.0, ptype='Ar')
npart = ljsystem.particles.npart
print('Added {} particles to a simple square lattice'.format(npart))
npart = float(npart)
# generate velocities:
ljsystem.particles.vel = np.random.normal(loc=0.0,
                                        scale=np.sqrt(ljsystem.temperature['set']),
                                        size=(npart,2))
reset_momentum(ljsystem)
ljsystem.forcefield = forcefield
# also initiate forces:
ljsystem.potential_and_force()

# place N particles 
write_gro = WriteGromacs('test.gro', box, frame=0, units=ljsystem.units)

numberofsteps = 950
simulation_eq = Simulation(endcycle=numberofsteps)
timestep = 0.0025
integrator = VelocityVerlet(timestep)

task_integrate = {'func': integrator.integration_step,
                  'args': [ljsystem]}
simulation_eq.add_task(task_integrate)
outfmt = '{0:8d} {1:12.7f} {2:12.7f} {3:12.7f} {4:12.7f}'
step, v_pot, e_kin, e_tot, temperature = [], [], [], [], []
time = []
# we will animate on the fly:
from matplotlib import pyplot as plt
from matplotlib import animation
from matplotlib import rc
rc('axes', labelsize='large')
rc('font', family='serif')
fig = plt.figure(figsize=(12, 6))
dx = size[0][1]-size[0][0]
f = 0.12
dx = np.array([-dx*f, dx*f])
dy = size[1][1]-size[1][0]
dy = np.array([-dy*f*0.1, dy*f*0.1])
SIGMA = CONVERT['length']['lj', 'Å']
ECONV = CONVERT['energy']['lj', 'kcal/mol']
ax = fig.add_subplot(121)

ax.set_xlim((size[0]+dx)*SIGMA)
ax.set_ylim((size[1]+dy)*SIGMA)
ax.set_aspect('equal', 'datalim')
ax.set_xlabel('$x/\AA{}$')
ax.set_ylabel('$y/\AA{}$')
ax.set_xticks([size[0][0]*SIGMA, size[0][1]*SIGMA])
ax.set_yticks([size[1][0]*SIGMA, size[1][1]*SIGMA])
ax.xaxis.labelpad=-5
ax.yaxis.labelpad=-5
pos = box.pbc_wrap(ljsystem.particles.pos)
circles = [plt.Circle((p[0],p[1]), radius=SIGMA*0.5, alpha=.5) for p in pos]
force_arrow = plt.quiver(pos[:,0], pos[:,1], zorder=4)
plt.quiverkey(force_arrow,1,-4,6,'Forces',coordinates='data',color='black')
vel_arrow = plt.quiver(pos[:,0], pos[:,1], color='darkgreen',zorder=4)
plt.quiverkey(vel_arrow,4,-4,6,'Velocities',coordinates='data',color='darkgreen')

ax.axhline(y=size[1][0]*SIGMA, lw=2, ls=':', color='k')
ax.axhline(y=size[1][1]*SIGMA, lw=2, ls=':', color='k')
ax.axvline(x=size[0][0]*SIGMA, lw=2, ls=':', color='k')
ax.axvline(x=size[0][1]*SIGMA, lw=2, ls=':', color='k')

ax2 = fig.add_subplot(122)
ax2.set_xlim(0,5000)
ax2.set_ylim(-0.6, 0.6)
ax2.set_xlabel('Time/fs')
ax2.set_ylabel('Energy/kcal/mol')
time_text = ax2.text(0.02, 0.95, '', transform=ax2.transAxes)
linepot, = ax2.plot(None, None, lw=2, ls='-', color='blue', label='Potential')
linekin, = ax2.plot(None, None, lw=2, ls='-', color='green', label='Kinetic')
linetot, = ax2.plot(None, None, lw=2, ls='-', color='k', label='Total')
ax2.legend(loc='lower left', ncol=2, frameon=False)
plt.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.15)

def init():
    # function to draw a clear frame
    patches = []
    for ci in circles:
        ci.set_visible(False)
        ax.add_patch(ci)
        patches.append(ci)
    linepot.set_data(None, None)
    patches.append(linepot)
    linekin.set_data(None, None)
    patches.append(linekin)
    linetot.set_data(None, None)
    patches.append(linetot)
    force_arrow.set_visible(False)
    patches.append(force_arrow)
    vel_arrow.set_visible(False)
    patches.append(vel_arrow)
    time_text.set_text('')
    patches.append(time_text)
    return patches #line1, line2, line3, line4

def update(i):
    pos = box.pbc_wrap(ljsystem.particles.pos)
    vel = ljsystem.particles.vel
    force = ljsystem.particles.force
    patches = []
    for ci, pi in zip(circles, pos):
        ci.center = np.array([pi[0],pi[1]])*SIGMA
        ci.set_visible(True)
        patches.append(ci)
    fmax = None
    for fi in force:
        fs = np.sqrt(np.dot(fi,fi))
        if fs>fmax or fmax is None: fmax=fs
    vmax = None
    for vi in vel:
        vs = np.sqrt(np.dot(vi,vi))
        if vs>vmax or vmax is None: vmax = vs
    XY, FU, FV, VU, VV = [], [], [], [], []
    for pi, fi, vi in zip(pos, force, vel):
        pj = pi*SIGMA
        fj = 10.0*fi/fmax
        vj = 10.0*vi/vmax
        XY.append([pj[0], pj[1]])
        FU.append(fj[0])
        FV.append(fj[1])
        VU.append(vj[0])
        VV.append(vj[1])
    force_arrow.set_offsets(XY)
    force_arrow.set_UVC(FU, FV)
    force_arrow.set_visible(True)
    patches.append(force_arrow)
    vel_arrow.set_offsets(XY)
    vel_arrow.set_UVC(VU, VV)
    vel_arrow.set_visible(True)
    patches.append(vel_arrow)
    if simulation_eq.is_finished():
        print('Simulation is done')
        return patches
    else:
        write_gro.write_frame(pos)
        step.append(simulation_eq.cycle['step'])
        time.append(simulation_eq.cycle['step']*timestep*CONVERT['time']['lj', 'fs'])
        kin_tens = calculate_kinetic_energy_tensor(ljsystem)
        temp, avgtemp, _ = calculate_kinetic_temperature(ljsystem, kin_tensor=kin_tens)
        v_pot.append(ljsystem.v_pot/npart)
        temperature.append(avgtemp)
        e_kin.append(kin_tens.trace()/npart)
        e_tot.append(e_kin[-1]+v_pot[-1])
        linepot.set_data(time, (v_pot-v_pot[0])*ECONV)
        patches.append(linepot)
        linekin.set_data(time, (e_kin-e_kin[0])*ECONV)
        patches.append(linekin)
        linetot.set_data(time, (e_tot-e_tot[0])*ECONV)
        patches.append(linetot)
        time_text.set_text('Time: {0:6.2f} fs'.format(time[-1]))
        patches.append(time_text)
        print(outfmt.format(step[-1], temperature[-1], v_pot[-1], e_kin[-1], e_tot[-1]))
        simulation_eq.step()
        return patches

anim = animation.FuncAnimation(fig, update, frames=numberofsteps, repeat=False,
                               interval=2, blit=True, init_func=init)
#anim.save('particles.mp4', fps=30, extra_args=['-vcodec', 'libx264']) # for making movie file
plt.show()
