RETIS simulation 2D WCA, low barrier
====================================

Simulation
----------
task = retis
steps = 1000000
interfaces = [1.2, 1.24, 1.26, 1.32, 1.58]

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

TIS settings
------------
freq =  0.5
maxlength = 20000
aimless = True
allowmaxlength = False
zero_momentum = True
rescale_energy = 9.0
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
velocity = {'scale': 9.0}
mass = {'A': 1.0, 'B': 1.0}
name = ['A', 'A', 'A', 'A', 'A', 'A', 'A', 'B', 'B']
type = [0, 0, 0, 0, 0, 0, 0, 1, 1]

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
parameter idxi = 7
parameter idxj = 8
parameter rzero = 1.122462048309373
parameter height = 6.0
parameter width = 0.25

Orderparameter
--------------
class = OrderParameterWCAJCP1
module = ../c-for-python3/orderp.py
index = (7,8)
periodic = True

Output
------
backup = overwrite
