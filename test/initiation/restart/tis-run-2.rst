TIS 1D example
==============

Simulation settings
-------------------
interfaces = [-0.9, -0.9, 1.0]
steps = 2
task = tis

System settings
---------------
dimensions = 1
temperature = 0.07
units = reduced

Engine settings
---------------
timestep = 0.002
class = Langevin
seed = 0
gamma = 0.3
high_friction = False

Box settings
------------
periodic = [False]

Particles settings
------------------
name = ['Ar']
position = {'file': 'initial.xyz'}
mass = {'Ar': 1.0}
velocity = {'generate': 'maxwell', 'momentum': False, 'seed': 0}
type = [0]

Forcefield settings
-------------------
description = '1D double well'

Potential
---------
c = 0.0
b = 2.0
a = 1.0
class = DoubleWell

Orderparameter settings
-----------------------
periodic = False
dim = 'x'
index = 0
class = Position

Output settings
---------------
directory = '001'
trajectory-file = 1
screen = 10
backup = 'overwrite'
pathensemble-file = 1
order-file = 1
energy-file = 1
cross-file = 1
restart-file = 1

TIS settings
------------
detect = -0.8
ensemble_number = 1
rescale_energy = False
zero_momentum = False
maxlength = 20000
aimless = True
freq = 0.5
sigma_v = -1
allowmaxlength = False
seed = 0

Initial-path settings
---------------------
method = kick
