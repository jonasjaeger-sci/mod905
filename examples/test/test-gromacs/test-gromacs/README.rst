Testing integration with GROMACS
================================

This will run GROMACS forward and backward and compare the results.
We are here doing the following:

1) Start from a given configuration.
2) Integrate forward in time for n steps.
3) Reverse the velocities of the configuration output from 2)
4) Integrate backward in time for n steps.

The trajectories from 2) and 4) should match for short simulations.
A complicating factor is here that we can use two formats for GROMACS,
.gro and .g96, with different precision. You can compare the outcome for
these two cases by modifying the ``engines.rst`` file and adding a .gro
file.

In the example, we perform the integration in different ways:

1) Step-stop-step, (i.e. starting and stopping GROMACS
after doing a specified number of subcycles) by using the
PyRETIS GROMACS engine.

2) Running the full simulation with GROMACS (without starting and stopping),
by using the PyRETIS GROMACS2 engine.

The first approach can be used by executing:

python test_gromacs.py 1

which will use the GROMACS engine from PyRETIS.

The second approach can be used by executing:

python test_gromacs.py 2

which will use the GROMACS2 engine from PyRETIS,

Note that additional settings can be set for the engine using
the ``engine.rst`` file and that you can also set the subcycles,
timestep, and the number of steps to perform here.
