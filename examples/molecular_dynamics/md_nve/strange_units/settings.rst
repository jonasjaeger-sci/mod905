Molecular dynamics example settings
===================================

Simulation settings
-------------------
task = md-nve
steps = 1000

Integrator settings
-------------------
class = velocityverlet
timestep = 0.08821552861273872

System settings
---------------
temperature = 239.6000017707801
units = real

Particles
---------
position = {'generate': 'fcc', 'density': 0.02279770663050494,
            'repeat': [3, 3, 3]}

velocity = {'generate': 'maxwell',
            'set-temperature': 239.6000017707801,
            'momentum': True,
            'seed': 0}

mass = {'Ar': 39.948}
name = ['Ar']
type = [0]

Forcefield settings
--------------------

description = Lennard Jones test

Potential
---------
class = PairLennardJonesCutnp
shift = True
parameter 0 = {'sigma': 3.405, 'epsilon': 0.238066991253, 'factor': 2.5}

Output
------
backup = False # True, False, Append
energy-file = 1
order-file = 1
cross-file = 1
trajectory-file = 1
write_vel = False
