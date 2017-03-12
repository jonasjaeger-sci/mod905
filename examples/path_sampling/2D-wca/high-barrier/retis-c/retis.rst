2D WCA RETIS simulation
=======================

Simulation
----------
task = retis
steps = 1000000
interfaces = [1.24, 1.34, 1.40, 1.46, 1.52, 1.54, 1.64, 1.74]

System
------
units = reduced
dimensions = 2
temperature = 1.0

Box
---
size = [5.9761430466719681, 5.9761430466719681]
periodic = [True, True]

Engine
------
class = VelocityVerlet
timestep = 0.002

TIS settings
------------
freq = 0.5
maxlength = 20000
aimless = True
allowmaxlength = False
zero_momentum = True
rescale_energy = 25
sigma_v = -1
seed = 0

RETIS settings
--------------
swapfreq = 0.5
relative_shoots = None
nullmoves = True
swapsimul = True

Initial-path
------------
method = kick

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
class = WCAPotential
module = ../c-for-python3/wcafunctions.py
shift = True
dim = 2
parameter sigma = 1.0
parameter epsilon = 1.0
parameter rcut = 1.122462048309373
parameter idxi = 0
parameter idxj = 1
parameter rzero = 1.122462048309373
parameter height = 15.0
parameter width = 0.5

Orderparameter
---------------
class = WCAOrderParameter
index = (0, 1)
module = ../c-for-python3/wcafunctions.py

Output
------
backup = overwrite
energy-file = 100
order-file = 100
path-file = 1
trajectory-file = 0
