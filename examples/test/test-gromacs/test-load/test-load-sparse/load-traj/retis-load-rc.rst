Retis 1D example
================

Simulation
----------
task = retis
steps = 5
interfaces = [2.19, 2.20, 2.21, 2.22, 4.33]

System
------
units = gromacs

Engine settings
---------------
class = gromacs2
gmx = GMXCOMMAND
mdrun = GMXCOMMAND mdrun
input_path = gromacs_input
timestep = 0.002
subcycles = 5
gmx_format = gro

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
module = orderp.py
idx1 = 0
idx2 = 3

Output settings
---------------
pathensemble-file = 1
screen = 10
order-file = 1
energy-file = 1
trajectory-file = 1
