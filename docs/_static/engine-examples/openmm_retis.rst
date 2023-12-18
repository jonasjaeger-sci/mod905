Retis 1D example
================

Simulation
----------
task = retis
steps = 10
interfaces = [3.0, 3.2, 3.4, 3.6, 3.8, 4.0]

System
------
units = gromacs

Engine
------
type = openmm
class = openmm
openmm_simulation = simulation
openmm_module = openmm_sim.py
subcycles = 10

TIS settings
------------
freq = 0.5
maxlength = 20000
aimless = True
allowmaxlength = False
zero_momentum = False
seed = 0

RETIS settings
--------------
swapfreq = 0.5
relative_shoots = None
nullmoves = True
swapsimul = True

Orderparameter
--------------
class = Distance
index = (0, 3)
periodic = False

Initial-path
------------
method = kick
kick-from = previous

Output
------
pathensemble-file = 1
order-file = 5
cross-file = 5
trajectory-file = 5
