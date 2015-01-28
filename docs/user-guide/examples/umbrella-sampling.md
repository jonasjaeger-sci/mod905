## Umbrella Sampling

This example will simply calculate the free energy profile
in a given, known, potential using umbrella sampling.

![Results](img/umbrella_sampling.png):

First, the retis library must be imported:
```python
from retis.core import UmbrellaSimulation, System
from retis.core import montecarlo as mc
from retis.forcefield import ForceField, DoubleWell, RectangularWell
import numpy as np
```
And the simulation and force field are created
by
```python
system = System(dim=1, temperature=500, units='eV/K') # create system
# Lets add a particle to this system
system.add_particle(name='X1', pos=np.array([-0.7])) 
potential_dw = DoubleWell(a=1, b=1, c=0.02)
potential_rw = RectangularWell()
forcefield = ForceField(desc='Double well', potential=[potential_dw])
forcefield_bias = ForceField(desc='Double well with rectangular bias',
                             potential=[potential_dw, potential_rw])
system.forcefield = forcefield_bias # attach biased force field to the system
```
