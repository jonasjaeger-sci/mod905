Retis 1D example
================

Simulation
----------
task = retis
steps = 5000
interfaces = [0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.8]

Box
---
size = [10, 10, 10]
periodic = [True, True, True]

System
------
units = reduced

Engine settings
---------------
class = VASPEngine
module = vasp.py
vasp = mpirun -np 8 vasp_std
input_path = vasp_input
timestep = 1
subcycles = 2


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

Initial-path
------------
method = kick

RETIS settings
--------------
swapfreq = 0.5
relative_shoots = None
nullmoves = True
swapsimul = True

Orderparameter
--------------
name = H-H distane
class = distance
index = (0, 1)
periodic = True

Collective-Variable 1
--------------
class = MaxDist
name = MaxDistance
pairs_index_list = ((0, 1), (1, 2))
periodic = True


Output settings
---------------
write_vel = False
pathensemble-file = 1
pathensemble-screen = 10
backup = False
energy-screen = 0
cross-file = 0
order-file = 1
energy-file = 1
trajectory-file = 1

