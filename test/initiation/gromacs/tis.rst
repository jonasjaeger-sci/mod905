Retis 1D example
================

Simulation
----------
task = tis
steps = 10
interfaces = [-0.1, 0, 0.1]

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
ensemble_number = 23

Initial-path
------------
method = load
load_folder = load

Orderparameter
--------------
class = PositionVelocity
dim = x
index = 0
periodic = False


Output
------
order-file = 1
trajectory-file = 1
