TIS 1D example
==============

Simulation
----------
task = tis
steps = 20000
interfaces = [-0.9, -0.8, -0.7, -0.6, -0.5, -0.4, -0.3, 1.0]

System
------
units = lj
dimensions = 1
temperature = 0.07

Box
---
periodic = [False]

Integrator
----------
class = Langevin
timestep = 0.002
gamma = 0.3
high_friction = False
seed = 10

TIS settings
------------
freq =  0.5
maxlength = 20000
aimless = True
allowmaxlength = False
zero_momentum = False
rescale_energy = False
sigma_v = -1
seed = 1
initial_path = kick

Particles
---------
position = {'file': 'initial.xyz'}
velocity = {'generate': 'maxwell',
            'momentum': False,
            'seed': 10}
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
name = Position
periodic = False
