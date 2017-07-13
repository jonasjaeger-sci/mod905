RETIS EXAMPLE FOR TESTING
=========================
This is an example which we can use for testing.

Simulation
----------
task = retis
steps = 20000
interfaces = [-0.9, -0.8, -0.7, -0.6, -0.5, -0.4, -0.3, 1.0]

System
------
units = reduced
dimensions = 1
temperature = 0.07

Box
---
periodic = [False]

Engine
------
class = Langevin
timestep = 0.002
gamma = 0.3
high_friction = False
seed = 0

TIS settings
------------
freq =  0.5
maxlength = 20000
aimless = True
allowmaxlength = False
zero_momentum = False
rescale_energy = False
sigma_v =  -1
seed = 0

RETIS settings
--------------
swapfreq = 0.5
relative_shoots = None
nullmoves = True
swapsimul = True

Initial-path settings
---------------------
method = kick
kick-from = initial

Particles
---------
position = {'file': 'initial.xyz'}
velocity = {'generate': 'maxwell',
            'momentum': False,
            'seed': 0}
mass = {'Ar': 1.0}
name = ['Ar']
type = [0]

Forcefield settings
-------------------
description = 1D double well

Potential
---------
class = DoubleWell
a = 1.0
b = 2.0
c = 0.0

Orderparameter
--------------
class = OrderParameterPosition
dim = x
index = 0
periodic = False

Collective-variable
-------------------
class = OrderParameterPosition2
dim = y
index = 5
periodic = False

Collective-variable
-------------------
class = OrderParameterPosition3
dim = z
index = 10
periodic = False

Output
------
trajectory-file = 100
energy-file = 100
order-file = 100
