DUMMY example
=============

Simulation
----------
task = tis
steps = 1
interfaces = [-0.9, -0.8, 1.0]
rgen = 'rgen-borg'
seed = 0
umbrella = 'test'
overlap = 1
maxdx = 10
mincycle = 1

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
timestep = 0.05
gamma = 0.3
high_friction = False
rgen = 'rgen-borg'
seed = 0

TIS settings
------------
freq = 0.5
maxlength = 50000
aimless = True
allowmaxlength = False
zero_momentum = False
rescale_energy = False
sigma_v = -1
rgen = 'rgen-borg'
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
position = {'generate': '1d'}
mass = {'Ar': 1.0}
name = ['Ar']
ptype = [0]

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
class = Position
dim = x
index = 0
periodic = False

Output
------
backup = overwrite
order-file = -1
trajectory-file = -1
energy-file = -1
pathensemble-file = -1

Analysis
--------
report = ['latex', 'rst', 'html', 'txt']
