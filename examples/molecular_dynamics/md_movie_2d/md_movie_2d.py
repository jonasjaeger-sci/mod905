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
from retis.tools import lattice_simple_cubic
import numpy as np 

# set up potential function(s) and force field:
lennard_jones = PairLennardJonesCut()
lj_parameters = {'Ar': {'sigma': 1.0, 'epsilon': 1.0, 'rcut': 2.5},
              'mixing': 'geometric'}
forcefield = ForceField(potential=[lennard_jones], params=[lj_parameters])

target_temperature = 1.0
size = [[0.0, 12.0/3.405], [0.0,12.0/3.405]]
box = Box(size)
ljsystem = System(temperature=target_temperature, units='lj', box=box)
# generate some lattice points, this will give 9 points
lattice = lattice_simple_cubic(box.size, spacing=1)
for i,pos in enumerate(lattice):
    if i==4: continue
    ljsystem.add_particle(name='Ar', pos=pos, mass=1.0, ptype='Ar')
npart = ljsystem.particles.npart
print('Added {} particles to a simple square lattice'.format(npart))
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

numberofsteps = 1000
simulation_eq = Simulation(endcycle=numberofsteps)
integrator = VelocityVerlet(0.0025)

task_integrate = {'func': integrator.integration_step,
                  'args': [ljsystem]}
simulation_eq.add_task(task_integrate)
while not simulation_eq.is_finished():
    write_gro.write_frame(box.pbc_wrap(ljsystem.particles.pos))
    simulation_eq.step()

