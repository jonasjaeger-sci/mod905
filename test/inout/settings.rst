Molecular dynamics example settings
===================================
this is a simple test system to check the input statements are correct

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
position = {'input_file': 'initial.gro'}

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

Output
------
energy-file = 1
order-file = 1
cross-file = 1

Analysis
--------
txt-output = 'txt'
skipcross = 1
report = ['latex', 'rst', 'html', 'txt']
