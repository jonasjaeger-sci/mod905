TIS 1D example
==============

Simulation
----------
task = retis
steps = 1000
interfaces = [-2.9, -1.8, -0.7]

System
------
units = reduced
dimensions = 1
temperature = 0.7

Box
---
periodic = [False]

Engine
------
class = Langevin
timestep = 0.02
gamma = 0.3
high_friction = False
seed = 0

TIS
---
freq =  0.5
maxlength = 20000
aimless = True
allowmaxlength = False
zero_momentum = False
rescale_energy = False
sigma_v = -1
seed = 0

RETIS
-----
swapfreq = 0.5
relative_shoots = None
nullmoves = True
swapsimul = True

Initial-path
------------
method = load
load_folder = load-sparse

Particles
---------
position = {'file': 'load-sparse/initial.xyz'}
velocity = {'generate': 'maxwell',
            'momentum': False,
            'seed': 0}
mass = {'Ar': 1.0}
name = ['Ar']
type = [0]

Forcefield
----------
description = 1D double well

Potential
---------
class = DoubleWell
a = 1.0
b = 2.0
c = 0.0

Orderparameter
--------------
class = PositionVelocity
dim = x
index = 0
periodic = False

Output
------
energy-file = 100
order-file = 100
trajectory-file = 100

