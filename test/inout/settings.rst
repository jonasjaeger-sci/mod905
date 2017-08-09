Molecular dynamics example settings
===================================
Here i can write some text to remind me 
what this simulation is doing.

Simulation settings
-------------------
task = 'md-nve'
steps = 100


Engine settings
---------------
class = velocityverlet
timestep = 0.002

System settings
---------------
units = 'lj'
units = lj
units='lj'
units= 'lj'
units     = 'lj'
temperature = 2.0

Particles
---------
position = {'file': 'initial.gro'}

velocity = {'generate': 'maxwell',
            'temperature': 2.0,
            'momentum': True,
            'seed': 0}

mass = {'Ar': 1.0}


Forcefield settings
-------------------
description = Lennard Jones test

potential
---------
class  = PairLennardJonesCutnp
shift = True
