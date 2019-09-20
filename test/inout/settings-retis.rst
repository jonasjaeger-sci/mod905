RETIS EXAMPLE FOR TESTING
=========================
This is an example which we can use for testing.

Simulation
----------
task = retis
steps = 20000
interfaces = [-0.9, -0.8, -0.7, -0.6, -0.5, -0.4, -0.3, 1.0]
zero_left = -99

System
------
units = reduced
dimensions = 1
temperature = 0.07

Box
---
periodic = [False]

Engine
------
class = Langevin
timestep = 0.002
gamma = 0.3
high_friction = False
seed = 0

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

Initial-path settings
---------------------
method = kick
kick-from = initial

Particles
---------
position = {'file': 'initial.xyz'}
velocity = {'generate': 'maxwell',
            'momentum': False,
            'seed': 0}
mass = {'Ar': 1.0}
name = ['Ar']
type = [0]

Forcefield settings
-------------------
description = 1D double well

Potential
---------
class = DoubleWell
a = 1.0
b = 2.0
c = 0.0

Orderparameter
--------------
class = Position
dim = x
index = 0
periodic = False

Collective-variable
-------------------
class = Position2
dim = y
index = 5
periodic = False

Collective-variable
-------------------
class = Position3
dim = z
index = 10
periodic = False

Collective-variable
-------------------
class = one_more_class
something = expected
dim = z
index = 10
periodic = False

Output
------
trajectory-file = 100
energy-file = 100
order-file = 100

Ensemble
--------
interface = -0.4
output order-file = 16
collective-variable01 name = 'Gianni'
particles velocity generate = 'Priapo'
particles velocity fantasy = 'game'
particles position madeup = {'Italian': job'}
particles position = {'input_file': 'just_kidding.xyz'}

Ensemble
--------
interface = -0.8
output order-file = 1600000
collective-variable5 name = 'Bugno'
particles velocity = {'generate': 'maxwell'}
particles position madeup = 'Food_job'
potential03 hit the test = True
collective-variable3 something unexpected = [1, 2, 3]
collective-variable1 position nonsense = 'pineapple_on_pizza'
collective-variable02 position nonsense = 'pineapple_on_pizza'
engine class = premium


