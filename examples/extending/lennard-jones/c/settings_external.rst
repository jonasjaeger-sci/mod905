Molecular dynamics example settings
===================================

Simulation settings
-------------------
task = md-nve
steps = 1000

Engine settings
---------------
class = velocityverlet
timestep = 0.002

System settings
---------------
temperature = 2.0
units = lj

Particles
---------
position = {'generate': 'fcc',
            'repeat': [3, 3, 3],
            'density': 0.9}

velocity = {'generate': 'maxwell',
            'set-temperature': 2.0,
            'momentum': True,
            'seed': 0}

mass = {'Ar': 1.0}
name = ['Ar']
type = [0]

Forcefield settings
--------------------

description = Lennard Jones test

Potential
---------
class = PairLennardJonesCutC
module = ljpotentialc.py
shift = True
parameter 0 = {'sigma': 1.0, 'epsilon': 1.0, 'rcut': 2.5}
mixing = geometric

Output
------
backup = False # True, False, Append
energy-file = 1
order-file = 10
cross-file = 1
trajectory-file = 10
write_vel = True
