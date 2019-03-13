Retis 1D example
================

Simulation
----------
task = retis
steps = 10
interfaces = [0.9, 0.95, 1, 1.3]

System
------
units = cp2k

Engine settings
---------------
class = cp2k
cp2k = cp2k
input_path = cp2k_input
timestep = 0.5
subcycles = 5

TIS settings
------------
freq = 0.5
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
load_folder = pippo

RETIS settings
--------------
swapfreq = 0.5
relative_shoots = None
nullmoves = True
swapsimul = True

Orderparameter
--------------
class = Distance
index = (0, 1)

Output settings
---------------
pathensemble-file = 1
screen = 10
order-file = 1
energy-file = 1
trajectory-file = 1
