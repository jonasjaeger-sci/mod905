Testing of load for GROMACS
===========================

This directory contains tests for loading paths with GROMACS:

1. ``test-initialise``: In this test, we first run a simulation
   for initialising a RETIS simulation, which is then continued
   using the ``load`` method. This is compared to the outcome of
   just running the full simulation.

2. ``test-load``: This test is similar to the first test. However,
   here, we run the RETIS simulation for a number of steps before
   stopping it and relaunching it. This is compared to running
   a longer RETIS simulation.

3. ``test-load-sparse``: This test uses the load tool to
   construct an artificial load trajectory. Frames or trajectories
   are copied from the load folder to the destination directory, the
   frames sorted such that, if possible, the [0-] and the [i+]
   ensembles are satisfied. The simulations are then performed until the
   simulation performed removing the memory of the initial artificial path.
  

Instructions
------------

For these tests, there is a ``run.sh`` script which contains the
commands used for executing them.

Further, these tests should be executed using a double precision
version of GROMACS.

Note
----
The engines ``gromacs.py`` and ``gromacs_restart.py`` are used
here to create engines that draw predictable random numbers so
that the results can be compared. The ``gromacs`` engine of
PyRETIS will ask GROMACS to randomly select a seed for generating
velocities. Here, we explicitly set these seeds.
