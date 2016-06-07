MD flux simulation
==================

units = lj
task = md-flux
steps = 100000
interfaces = [1.24]

integrator = {'class': 'velocityverlet', 'timestep': 0.002}

box = {'size': [3.872983346207417, 3.872983346207417]}

System settings
---------------

dimensions = 2
temperature = 1.0

Particles
---------

particles-position = {'file': 'initial.xyz'}

particles-velocity = {'scale': 9.0}

particles-mass = {'A': 1.0, 'B': 1.0}

Force field settings
--------------------

forcefield = {'desc': '2D double well + wca'}
potentials = [{'class': 'PairLennardJonesCutnp', 'shift': True, 'dim': 2},
              {'class': 'DoubleWellWCA', 'dim': 2}]

potential-parameters = [{'mixing': 'geometric',
                         0: {'sigma': 1.0, 'epsilon': 1.0, 'factor': 1.122462048309373},
                         1: {'sigma': 1.0, 'epsilon': 1.0, 'factor': 1.122462048309373}},
                        {'types': [(1,1)], 'rzero': 1.122462048309373, 'height': 6.0, 'width':0.25}]
                         
Order parameter
---------------

#orderparameter = {'class': 'OrderParameterDist',
#                  'index': (0,1),
#                  'name': 'Position',
#                  'periodic': True}

orderparameter = {'class': 'OrderParameterDist',
                  'args': ['Position', (7,8)],
                  'kwargs': {'periodic': True},
                  'module': 'orderp.py'}

Output settings
---------------

output-modify = [{'name': 'traj', 'when': {'every': 10}},
                 {'name': 'orderp', 'when': {'every': 100}}]
