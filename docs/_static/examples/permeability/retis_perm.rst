TIS 1D example
==============

Simulation
----------
task = retis
steps = 50
interfaces = [-0.1, 0., 0.1]
zero_left = -0.2
permeability = True
swap_attributes = ['order_function']

System
------
units = reduced
dimensions = 1
temperature = 1.

Box
---
periodic = [True]
low = [-0.5]
high = [0.5]

Engine
------
class = Langevin
timestep = 0.0002
gamma = 5.
high_friction = True
seed = 0

TIS
---
freq =  0.5
maxlength = 200000  
aimless = True
allowmaxlength = False
zero_momentum = False
rescale_energy = False
sigma_v = -1
seed = 42
mirror_freq = 0.1
target_freq = 0.1 
target_indices = [0, 1, 2]

RETIS settings
--------------
swapfreq = 0.1
relative_shoots = None
nullmoves = True
swapsimul = True

Initial-path
------------
method = kick
kick-from = previous

Particles
---------
position = {'input_file': 'initial.xyz'}
velocity = {'generate': 'maxwell',
            'momentum': False,
            'seed': 0}
mass = {'Ar': 1.0}
name = ['Ar1', 'Ar2', 'Ar3']
type = [0, 0, 0]

Forcefield
----------
description = 1D flat with walls, no force

Orderparameter
--------------
class = Permeability
dim = x
index = 0
offset = 0
relative = False
mirror_pos = -0.15

Collective-variable
-------------------
class = PermeabilityMinusOffset
dim = x
index = 0
offset = 0
relative = False
mirror_pos = -0.15

Collective-variable
-------------------
class = Permeability
dim = x
index = 1
offset = 0
relative = False
mirror_pos = -0.15

Collective-variable
-------------------
class = Permeability
dim = x
index = 1
offset = 0
relative = False
mirror_pos = -0.15

Collective-variable
-------------------
class = Permeability
dim = x
index = 2
offset = 0
relative = False
mirror_pos = -0.15

Collective-variable
-------------------
class = Position
dim = x
index = 0

Collective-variable
-------------------
class = Position
dim = x
index = 1

Collective-variable
-------------------
class = Position
dim = x
index = 2


Potential
---------
class = FlatWall1D
module = flat_potential.py

Output
------
screen = 1000
energy-file = 1000
order-file = 1

Analysis
--------
tau_ref_bin = [-0.175, -0.125]
