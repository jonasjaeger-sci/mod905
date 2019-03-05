Molecular dynamics example settings
===================================

Simulation settings
-------------------
task = md-nve
steps = 1000

Engine settings
---------------
class = Langevin
timestep = 0.002
gamma = 0.3 
seed = 0
high_friction = False

System settings
---------------
temperature = 2.0
units = lj

Particles
---------
position = {'generate': 'fcc',
            'repeat': [3, 3, 3],
            'density': 0.9}

velocity = {'generate': 'maxwell',
            'temperature': 2.0,
            'momentum': True,
            'seed': 0}

mass = {'Ar': 1.0}
name = ['Ar']
type = [0]

Forcefield settings
-------------------
description = Lennard Jones test

Potential
---------
class = PairLennardJonesCutnp
shift = True
parameter 0 = {'sigma': 1.0, 'epsilon': 1.0, 'rcut': 2.5}

Output
------
prefix = md-full-
backup = overwrite
energy-file = 1
order-file = 10
cross-file = 1
trajectory-file = 10
restart-file = 10
