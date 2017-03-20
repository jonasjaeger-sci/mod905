Retis 1D example
================

Simulation
----------
task = retis
steps = 10
interfaces = [-0.26, -0.24, -0.22, -0.20, -0.19, -0.18, -0.17,
              -0.16, -0.15, -0.14, -0.13, -0.12, -0.11, -0.10,
              -0.09, -0.08, -0.07, -0.06, -0.05, -0.04, -0.02,
               0.00,  0.02,  0.20]

System
------
units = gromacs

Engine settings
---------------
class = gromacs
gmx = gmx_5.1.4
mdrun = gmx_5.1.4 mdrun
input_path = ext_input
timestep = 0.002
subcycles = 5

TIS settings
------------
freq =  0.5
maxlength = 20000
aimless = True
allowmaxlength = False
zero_momentum = False
rescale_energy = False
sigma_v =  -1
seed = 0

RETIS settings
--------------
swapfreq = 0.5
relative_shoots = None
nullmoves = True
swapsimul = True

Initial-path
------------
method = kick
kick-from previous

Orderparameter
--------------
class = RingDiffusion
module = orderp.py
