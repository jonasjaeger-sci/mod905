Retis 1D example
================

Simulation
----------
task = repptis
steps = 100000
interfaces = [0.20, 0.325, 0.55, 0.69] 
zero_left =  0.10
permeability = True
#restart = pyretis.restart

System
------
units = reduced
dimensions = 2
temperature = 0.07

Box
---
periodic = [False, False]

Engine
------
class = Langevin
timestep = 0.01
gamma = 25.0
high_friction = False
seed = 0

TIS settings
------------
freq = 0.0
maxlength = 100000
aimless = True
allowmaxlength = False
zero_momentum = False
rescale_energy = False
sigma_v =  -1
seed = 0

Initial-path
------------
#method = restart
method = load
load_folder = load

RETIS settings
--------------
swapfreq = 0.1
relative_shoots = None
nullmoves = True
swapsimul = True

Particles
---------
position = {'input_file': 'initial.xyz'}
velocity = {'generate': 'maxwell',
            'momentum': False,
            'seed': 0}
mass = {'Ar': 1.0}
name = ['Ar']
ptype = [0]

Forcefield settings
-------------------
description = Maze Potential 

Potential
---------
class = Maze2D_color
module = mazepotential_mixed.py
mazefig = color_aperture_beta.png
gauss_a = 500.0
gauss_b = 0.0
gauss_c = 1.0
dw = 0.5
gauss_a2 = 25.0
gauss_b2 = 0.
gauss_c2 = 1.0
dw2 = 0.5
global_pot = "global_slope"
global_pot_params = [0., 0.5]
D = 4
slope_exit = 0.20

Orderparameter
--------------
class = OrderX
module = order.py


Output settings
---------------
trajectory-file = -1
order-file = 1
energy-file = -1
backup = 'append'

Analysis settings
-----------------
tau_ref_bin = [0.1, 0.2]
