MD flux simulation for the 2D WCA example
=========================================

Simulation settings
-------------------
task = md-flux
steps = 10000000
interfaces = [1.24]

System settings
---------------
units = lj
dimensions = 2
temperature = 1.0

Box
---
size = [5.9761430466719681, 5.9761430466719681]
periodic = [True, True]

Integrator
----------
class = VelocityVerlet
timestep = 0.002

Particles
---------

position = {'file': '../initial.xyz'}

velocity = {'scale': 25.0}

mass = {'A': 1.0, 'B': 1.0}
name = ['B', 'B', 'A']
type = [1, 1, 0]

Forcefield settings
-------------------
description = 2D Double Well + WCA

Potential
---------
class = PairLennardJonesCutnp
shift = True
dim = 2
mixing = geometric
parameter 0 = {'sigma': 1.0, 'epsilon': 1.0, 'factor': 1.122462048309373}
parameter 1 = {'sigma': 1.0, 'epsilon': 1.0, 'factor': 1.122462048309373}

Potential
---------
class = DoubleWellWCA
dim = 2
parameter rzero = 1.122462048309373
parameter height = 15.0
parameter width = 0.5
parameter types = [(1, 1)]

                         
Orderparameter
---------------
class = Distance
name = B-B distance
index = (0, 1)
periodic = True


Output
------
backup = False
energy-file = 10
order-file = 10
cross-file = 1
