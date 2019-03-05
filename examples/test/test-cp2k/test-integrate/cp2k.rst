Molecular dynamics example settings
===================================

Simulation
----------
task = md-flux
steps = 10
interfaces = [2.0]

Engine
------
class = cp2k
cp2k = cp2k
input_path = cp2k_input
timestep = 0.5
subcycles = 5

System settings
---------------
units = cp2k

Orderparameter
--------------
class = PositionVelocity
dim = x
index = 0
periodic = False

Output
------
energy-file = 1
order-file = 1
trajectory-file = -1
screen = 1
