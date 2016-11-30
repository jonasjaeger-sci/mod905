# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""Example of running a MD simulation using the pyretis library.

The system considered is a simple Lennard-Jones fluid.
"""
# pylint: disable=C0103
import numpy as np
from pyretis.core import Box, Particles, System
from pyretis.core.simulation import SimulationNVE
from pyretis.integrators import VelocityVerlet
from pyretis.tools import generate_lattice
from pyretis.forcefield import ForceField
from pyretis.forcefield.potentials import PairLennardJonesCutnp
from matplotlib import pyplot as plt


# If you have a recent version of matplotlib you can make
# the plot nicer by loading a style, e.g.:
plt.style.use('bmh')


print('Creating box:')
xyz, size = generate_lattice('fcc', [3, 3, 3], density=0.9)
box = Box(size=size)
print(box)

print('Creating system:')
system = System(units='lj', box=box, temperature=2.0)
system.particles = Particles(dim=3)
for i, pos in enumerate(xyz):
    system.add_particle(pos, vel=np.zeros_like(pos), force=np.zeros_like(pos),
                        mass=1.0, name='Ar', ptype=0)
gen_settings = {'distribution': 'maxwell', 'momentum': True}
system.generate_velocities(**gen_settings)
print(system.particles)

print('Creating force field:')
potentials = [PairLennardJonesCutnp(dim=3, shift=True, mixing='geometric')]
parameters = [{0: {'sigma': 1, 'epsilon': 1, 'rcut': 2.5}}]
ffield = ForceField(desc='Lennard Jones',
                    potential=potentials, params=parameters)
system.forcefield = ffield
print(system.forcefield)

print('Creating simulation:')
integrator = VelocityVerlet(0.002)
simulation = SimulationNVE(system, integrator, steps=100)

ekin = []
vpot = []
etot = []
step = []
for result in simulation.run():
    print('Step:', result['cycle']['step'])
    step.append(result['cycle']['step'])
    ekin.append(result['thermo']['ekin'])
    vpot.append(result['thermo']['vpot'])
    etot.append(result['thermo']['etot'])
# Do some plotting:
fig1 = plt.figure()
ax1 = fig1.add_subplot(111)
ax1.plot(step, ekin, label='Kinetic energy')
ax1.plot(step, etot, label='Total energy')
ax1.plot(step, vpot, label='Potential energy')
ax1.set_xlabel('Step no.')
ax1.set_ylabel('Energy / reduced units')
fig1.savefig('out.png')
plt.show()
