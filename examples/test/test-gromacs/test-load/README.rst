Testing of load for GROMACS
===========================

This directory contains tests for loading paths with GROMACS:

1. ``test-initialize``: This tests that we can initialize
   and run a RETIS simulation in two separate steps. This is
   compared to the outcome of just running the full simulation
   (i.e. in one step).

2. ``test-load``: This tests that we can run a RETIS simulation
   for a number of steps, stop it, relaunch it and that this gives
   the same result as running a longer RETIS simulation.

Instructions
------------

For these tests there is a ``run.sh`` script which contains the
commands used for executing them.

Note
----
The engines ``gromacs.py`` and ``gromacs_restart.py`` are used
here to create engines that draw predictable random numbers so
that the results can be compared. The ``gromacs`` engine of
PyRETIS will ask GROMACS to randomly select a seed for generating
velocities. Here, we explicitly set these seeds.
