.. _examples-mc:

Monte Carlo examples
====================

.. _examples-mc-umbrella-sampling:

Umbrella Sampling
-----------------

This example will simply calculate the free energy profile in a given,
known, potential using umbrella sampling. The results we will obtain are
shown in the figure below: the potential energy :math:`V(x)` and the probability 
density.

.. image:: ../img/umbrella_sampling.png
   :scale: 75 %
   :alt: Result from the umbrella sampling
   :align: center

We begin by importing the pytismol library:

.. code-block:: python

  from retis.core import UmbrellaSimulation, System 
  from retis.core import montecarlo as mc 
  from retis.forcefield import ForceField, DoubleWell, RectangularWell 
  import numpy as np

We then set up the simulation and force field by:

.. code-block:: python

  system = System(dim=1, temperature=500, units='eV/K') # create system 
  # Lets add a particle to this system 
  system.add_particle(name='X1', pos=np.array([-0.7]))
  potential_dw = DoubleWell(a=1, b=1, c=0.02) 
  potential_rw = RectangularWell() 
  forcefield = ForceField(desc='Double well', potential=[potential_dw]) 
  forcefield_bias = ForceField(desc='Double well with rectangular bias',
                               potential=[potential_dw, potential_rw]) 
  system.forcefield = forcefield_bias # attach biased force field to the system

