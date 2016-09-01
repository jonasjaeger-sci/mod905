Molecular dynamics example settings
===================================

Simulation settings
-------------------
task = md-nve
steps = 1000

Integrator settings
-------------------
class = velocityverlet
timestep = 0.002

System settings
---------------
temperature = 2.0
units = lj

Particles
---------
position = {'file': 'initial.gro'}

velocity = {'generate': 'maxwell',
            'set-temperature': 2.0,
            'momentum': True,
            'seed': 0}

mass = {'Ar': 1.0}
name = ['Ar']
type = [0]

Force field settings
--------------------

description = Lennard Jones test

Potential
---------
class = PairLennardJonesCutnp
shift = True
parameter 0 = {'sigma': 1.0, 'epsilon': 1.0, 'rcut': 2.5}
