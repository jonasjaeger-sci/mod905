Molecular dynamics example settings
===================================

Simulation settings
-------------------
task = md-nve
steps = 1000

System settings
---------------
temperature = 2.0
units = lj
dimensions = 3

Box
---
periodic = [True, True, True]
low = [0.0, 0.0, 0.0]
high = [8.39798, 8.39798, 8.39798]

Engine settings
---------------
class = velocityverlet
timestep = 0.0025

Particles settings
------------------
position = {'file': 'input_data/mix.txt'}
mass = {'A': 1.0, 'B': 1.0, 'C': 1.5}

Forcefield settings
-------------------
description = 'Lennard Jones 3 species.'

Potential
---------
class = 'PairLennardJonesCutnp'
shift = True
mixing = geometric
parameter 0 = {'epsilon': 1.1, 'rcut': 2.5, 'sigma': 1.2}
parameter 1 = {'epsilon': 0.9, 'rcut': 2.5, 'sigma': 1.4}
parameter 2 = {'epsilon': 1.0, 'rcut': 2.5, 'sigma': 1.0}
