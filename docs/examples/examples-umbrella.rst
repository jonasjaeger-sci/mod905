.. _examples-mc:

.. _examples-mc-umbrella-sampling:

Umbrella Sampling
=================

This example will simply calculate the free energy profile in a given,
known, potential using umbrella sampling. The results we will obtain are
shown in the figure below: the potential energy :math:`V(x)`
and the probability density.

.. figure:: /_static/img/umbrella_sampling.png
   :class: img-responsive center-block
   :alt: Result from the umbrella sampling
   :align: center

   Sample results for the potential energy and the probability density.

We begin by importing the pyretis library:

.. literalinclude:: /_static/examples/examples-mc.py
   :lines: 1-5

And we import `numpy <http://www.numpy.org/>`_
and `matplotlib <http://matplotlib.org/>`_
which we will use for some additional numerical methods and for plotting.

.. literalinclude::  /_static/examples/examples-mc.py
   :lines: 7-8

First, we set up the system by defining the units we will
use and adding a particle (labelled as 'X') at a specified position.

.. literalinclude::  /_static/examples/examples-mc.py
   :lines: 10-12


Next we define the force field in terms of potential functions.
Here, we create the unbiased potential - a
:ref:`double well potential <user-section-potential-doublewell>` -
and a biased version of the potential where a
:ref:`rectangular well <user-section-potential-rectangularwell>` is used.
Finally, the biased potential is attached to the system.

.. literalinclude::  /_static/examples/examples-mc.py
   :lines: 14-19

In order to run the actual simulation, we need to specify some additional
settings, like where the umbrella windows should be placed and how many
cycles we need to perform:

.. literalinclude::  /_static/examples/examples-mc.py
   :lines: 21-25

and we create a random number generator for use in the umbrella simulation:

.. literalinclude::  /_static/examples/examples-mc.py
   :lines: 27-28

We are now ready to run the simulation. We will do this by looping over
the umbrella windows we defined,

.. literalinclude::  /_static/examples/examples-mc.py
   :lines: 30-50

The simulation is now done, and we can do the analysis and plot the results.
For the analysis we match the histograms:

.. literalinclude::  /_static/examples/examples-mc.py
   :lines: 52-61

And we finally plot the results:

.. literalinclude::  /_static/examples/examples-mc.py
   :lines: 63-97
