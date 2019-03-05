TIS 1D example
==============

Simulation
----------
task = tis
steps = 1000
interfaces = [-0.9, -0.8, -0.7]

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

Initial-path
------------
method = load
load_folder = load

Particles
---------
position = {'file': 'initial.xyz'}
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
class = Position
dim = x
index = 0
periodic = False

Output
------
energy-file = 100
order-file = 100
trajectory-file = 100

