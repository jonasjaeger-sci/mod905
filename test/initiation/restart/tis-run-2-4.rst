TIS 1D example
==============

Simulation settings
-------------------
interfaces = [-0.9, -0.9, -0.8]
steps = 9
task = tis
restart = ../run-2/pyretis.restart
seed = 2

System settings
---------------
dimensions = 1
temperature = 0.7
units = reduced

Engine settings
---------------
timestep = 0.02
class = Langevin
seed = 1
gamma = 0.3
high_friction = False

Box settings
------------
periodic = [False]

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
backup = 'append'
pathensemble-file = 1
order-file = 1
energy-file = 1
cross-file = 1
restart-file = 1

TIS settings
------------
ensemble_number = 1
detect = -0.8
rescale_energy = False
zero_momentum = False
maxlength = 20000
aimless = True
freq = 0.5
sigma_v = -1
allowmaxlength = False
seed = 3

Initial-path settings
---------------------
method = restart
