Molecular dynamics example settings
===================================

Simulation settings
-------------------
task = md-nve
steps = 33

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
position = {'input_file': 'input_data/one.txt'}

Forcefield settings
-------------------
description = 'Lennard Jones test, one component'

Potential
---------
class = 'PairLennardJonesCutnp'
shift = False
parameter 0 = {'epsilon': 1.0, 'rcut': 2.5, 'sigma': 1.0}
