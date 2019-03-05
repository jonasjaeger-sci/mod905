MD flux simulation 2D WCA, low barrier
======================================

Simulation
----------
task = md-flux
steps = 1000000
interfaces = [1.2]

System
------
units = reduced
dimensions = 2
temperature = 1.0

Box
---
cell = [3.872983346207417, 3.872983346207417]
periodic = [True, True]

Engine
------
class = VelocityVerlet
timestep = 0.002

Particles
---------
position = {'file': '../initial.xyz'}
velocity = {'scale': 9.0}
mass = {'A': 1.0, 'B': 1.0}
name = ['A', 'A', 'A', 'A', 'A', 'A', 'A', 'B', 'B']
type = [0, 0, 0, 0, 0, 0, 0, 1, 1]

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
parameter height = 6.0
parameter width = 0.25
parameter types = [(1, 1)]

Orderparameter
--------------
class = OrderParameterWCAJCP1
module = ../orderp.py
index = (7, 8)
periodic = True

Output
------
backup = overwrite
energy-file = 10
order-file = 10
cross-file = 1
