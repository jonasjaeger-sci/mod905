# -*- coding: utf-8 -*-
from __future__ import print_function
"""
Example of running a MD NVE simulation
"""
from retis.core import Simulation, System, Box
from retis.core.particlefunctions import kinetic_energy, kinetic_temperature, reset_momentum, evaluate_press
from retis.core.integrators import VelocityVerlet
from retis.forcefield import ForceField, PairLennardJonesCut
from retis.io import WriteGromacs
from retis.tools import latticefcc
import numpy as np 

# set up potential function(s) and force field:
lennard_jones = PairLennardJonesCut()
lj_parameters = {'Ar': {'sigma': 1.0, 'epsilon': 1.0, 'rcut': 2.5},
              'mixing': 'geometric'}
forcefield = ForceField(potential=[lennard_jones], params=[lj_parameters])

target_temperature = 1.0
target_density = 0.9
lattice, size = latticefcc(density=target_density, nx=3, ny=3, nz=3)
box = Box(size)

ljsystem = System(temperature=target_temperature, units='lj', dim=3, box=box)
for pos in lattice:
    ljsystem.add_particle(name='Ar', pos=pos, mass=1.0, ptype='Ar')
npart = ljsystem.particles.npart
print('Created fcc grid with {} atoms.'.format(npart))

# generate velocities:
ljsystem.particles.vel = np.random.normal(loc=0.0, 
                                        scale=np.sqrt(ljsystem.temperature),
                                        size=(npart,3))
reset_momentum(ljsystem.particles)
temp, avgtemp = kinetic_temperature(ljsystem.particles)
print('Generated temperatures with average: {}'.format(avgtemp))
ljsystem.forcefield = forcefield





write_gro = WriteGromacs('test.gro', box, frame=0, units=ljsystem.units)

# first set up a simulation where we equilibriate the system
# and scale the temperature:
simulation_eq = Simulation(maxcycle=1000)
integrator = VelocityVerlet(0.0025)

task_integrate = {'func': integrator.integration_step,
                  'args': [ljsystem]}

def rescale_velocity(system):
    temp, avgtemp = kinetic_temperature(system.particles, dof=[1,1,1])
    scale_factor =  np.sqrt(system.temperature/avgtemp)
    system.particles.vel *= scale_factor

task_rescale = {'func': rescale_velocity, 'args': [ljsystem]}

task_reset_momentum = {'func': reset_momentum, 'args': [ljsystem.particles]}

simulation_eq.task = [task_integrate, task_rescale, task_reset_momentum]

# we also define some computations
def compute_energies(system):
    ekin = np.sum(kinetic_energy(system.particles))
    vpot = system.v_pot
    temp, avgtemp = kinetic_temperature(system.particles, 
                                        dof=[1., 1., 1.])
    return avgtemp, vpot, ekin, ekin+vpot

temps = []
kinetic_e = []
potential_e = []
total_e = []
pressure = []
while not simulation_eq.is_finished():
    simulation_eq.step()
    # let us also calculate some things:
    avgtemp, vpot, ekin, etot = compute_energies(ljsystem)
    temps.append(avgtemp)
    kinetic_e.append(ekin)
    potential_e.append(vpot)
    total_e.append(etot)
    pV, press = evaluate_press(ljsystem.particles, ljsystem, temperature=avgtemp)
    pressure.append(press)
    print('Step: {}, Temp: {}, E-tot:{}'.format(simulation_eq.cycle, avgtemp, etot))
    write_gro.write_frame(ljsystem.particles.pos)

simulation_nve = Simulation(maxcycle=1000)
simulation_nve.task = [task_integrate, task_reset_momentum]

while not simulation_nve.is_finished():
    simulation_nve.step()
    avgtemp, vpot, ekin, etot = compute_energies(ljsystem)
    temps.append(avgtemp)
    kinetic_e.append(ekin)
    potential_e.append(vpot)
    total_e.append(etot)
    pV, press = evaluate_press(ljsystem.particles, ljsystem, temperature=avgtemp)
    pressure.append(press)
    print('Step: {}, Temp: {}, E-tot:{}'.format(simulation_eq.cycle, avgtemp, etot))
    write_gro.write_frame(ljsystem.particles.pos)


from matplotlib import pyplot as plt
plt.figure()
plt.plot(temps)
plt.show()
plt.figure()
plt.plot(kinetic_e)
plt.plot(potential_e)
plt.plot(total_e)
plt.figure()
plt.plot(pressure)
plt.show()

