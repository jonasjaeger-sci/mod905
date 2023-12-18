Testing integration with CP2K
=============================

This will run CP2K forward and backward and compare the results.
We are here doing the following:

1) Start from a given configuration.
2) Integrate forward in time for n steps.
3) Reverse the velocities of the configuration output from 2)
4) Integrate forward in time for n steps.

The trajectories from 2) and 4) should match for short simulations. 

In this example, we perform the integration in different ways:

1) Step-stop-step and so on using the PyRETIS CP2K engine.

2) Running the full simulation with CP2K (without starting and stopping).

The test can be run by executing:

python test_cp2k.py

and

python test_cp2k_step.py

Note 1: additional settings can be set for the engine using
the engine.rst file and that you can also set the subcycles,
timestep, and the number of steps to perform here.

Note 2: test_cp2k.py will also invoke a test to compare the simulations results 
between the forward and backward path.


Important
---------

Before running this test, you will have to supply the two files

* GTH_BASIS_SETS which can be downloaded from:
  https://github.com/misteliy/cp2k/blob/master/tests/QS/GTH_BASIS_SETS

* GTH_POTENTIALS, which can be downloaded from:
  https://github.com/misteliy/cp2k/blob/master/tests/QS/GTH_POTENTIALS

and copy them into the ``cp2k_input`` folder.
