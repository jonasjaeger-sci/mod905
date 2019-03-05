Retis 1D example
================

Simulation
----------
task = retis
steps = 10
interfaces = [2.78, 2.88, 3.01, 3.80, 4.00]

System
------
units = gromacs

Engine settings
---------------
class = gromacs
gmx = GMX
mdrun = GMX
input_path = gmx_input
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

RETIS settings
--------------
swapfreq = 0.5
relative_shoots = None
nullmoves = True
swapsimul = True

Initial-path
------------
method = load
load_folder = load
top_file = gmx_input/conf.gro

Orderparameter
--------------
class = Distance
module = orderp.py
idx1 = 0
idx2 = 3

Output
------
order-file = 1
trajectory-file = 1
