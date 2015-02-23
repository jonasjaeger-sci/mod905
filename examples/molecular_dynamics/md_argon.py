# -*- coding: utf-8 -*-
from __future__ import print_function
"""
Example of running a MD NVE simulation
"""
from retis.core import Simulation, System, Box
from retis.core.particlefunctions import * 
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

ljsystem = System(temperature=target_temperature, units='lj', box=box)
for pos in lattice:
    ljsystem.add_particle(name='Ar', pos=pos, mass=1.0, ptype='Ar')
npart = ljsystem.particles.npart
print('Created fcc grid with {} atoms.'.format(npart))

# generate velocities:
ljsystem.particles.vel = np.random.normal(loc=0.0, 
                                        scale=np.sqrt(ljsystem.temperature['set']),
                                        size=(npart,3))
reset_momentum(ljsystem)
calculate_linear_momentum(ljsystem)
ljsystem.adjust_dof([1,1,1])
temp, avgtemp, _ = calculate_kinetic_temperature(ljsystem)
print('Generated temperatures with average: {}'.format(avgtemp))
ljsystem.forcefield = forcefield
# also initiate forces:
ljsystem.potential_and_force()

write_gro = WriteGromacs('test.gro', box, frame=0, units=ljsystem.units)
# finished with initialization


# first set up a simulation where we equilibriate the system
# and scale the temperature:
numberofsteps = 100
simulation_eq = Simulation(endcycle=numberofsteps)
integrator = VelocityVerlet(0.0025)

task_integrate = {'func': integrator.integration_step,
                  'args': [ljsystem]}

def rescale_velocity(system):
    temp, avgtemp, _ = calculate_kinetic_temperature(ljsystem)
    scale_factor = np.sqrt(system.temperature['set']/avgtemp)
    system.particles.vel *= scale_factor

task_rescale = {'func': rescale_velocity, 'args': [ljsystem]}

def reset_momentum_task(system):
    print('Resetting momentum')
    reset_momentum(system)

task_reset_momentum = {'func': reset_momentum_task, 'args': [ljsystem],
                       'extra': {'every': 10}}

simulation_eq.add_task(task_integrate)
simulation_eq.add_task(task_rescale)
simulation_eq.add_task(task_reset_momentum)

def common_calculations(system):
    kin_tens = calculate_kinetic_energy_tensor(system)
    press_tens = calculate_pressure_tensor(system, 
                                           kin_tensor=kin_tens)
    temp, avgtemp, _ = calculate_kinetic_temperature(system, 
                                                     kin_tensor=kin_tens)
    ekin = kin_tens.trace()
    press =  calculate_scalar_pressure(system, press_tensor=press_tens, 
                                       kin_tensor=kin_tens)
    pxx = press_tens.diagonal()
    vpot = system.v_pot
    etot = ekin+vpot
    return vpot, ekin, etot, avgtemp, press, pxx

temps = []
kinetic_e = []
potential_e = []
total_e = []
pressure = []

while not simulation_eq.is_finished():
    # let us also calculate some stuff:
    vpot, ekin, etot, avgtemp, press, pxx = common_calculations(ljsystem)
    temps.append(avgtemp)
    kinetic_e.append(ekin)
    potential_e.append(vpot)
    total_e.append(etot)
    pressure.append(pxx)
    print('Step: {}, Temp: {}, E-tot:{}'.format(simulation_eq.cycle['step'], avgtemp, etot))
    write_gro.write_frame(ljsystem.particles.pos)
    simulation_eq.step()

simulation_nve = Simulation(endcycle=numberofsteps)
task_reset_momentum = {'func': reset_momentum_task, 'args': [ljsystem],
                       'extra': {'every': 100}}
simulation_nve.add_tasks(task_integrate, task_reset_momentum)

while not simulation_nve.is_finished():
    vpot, ekin, etot, avgtemp, press, pxx = common_calculations(ljsystem)
    temps.append(avgtemp)
    kinetic_e.append(ekin)
    potential_e.append(vpot)
    total_e.append(etot)
    pressure.append(pxx)
    print('Step: {}, Temp: {}, E-tot:{}'.format(simulation_nve.cycle['step'], avgtemp, etot))
    write_gro.write_frame(ljsystem.particles.pos)
    simulation_nve.step()


from matplotlib import pyplot as plt
plt.figure()
plt.plot(temps)
plt.show()
plt.figure()
plt.plot(kinetic_e-kinetic_e[numberofsteps])
plt.plot(potential_e-potential_e[numberofsteps])
plt.plot(total_e-total_e[numberofsteps])
plt.figure()
pressure = np.array(pressure)
for pxx in pressure.T:
    plt.plot(pxx)
plt.show()

