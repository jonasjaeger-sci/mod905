Testing of restart for GROMACS
==============================

This directory contains tests for restarting with GROMACS:

1. ``test-continue``: This will test that we can continue
   a RETIS simulation. The continuation is done by making
   use of the ``restart`` method. The outcome of this is
   compared with a continuous simulation.

2. ``test-initialise``: This test is similar to the previous test,
   however, here the continuation is done immediately after creating
   an initial path. This is compared to the outcome of just running
   without the restart.

2. ``test-restart``: This tests that we can run a RETIS simulation
   for a number of steps, stop it, relaunch it and that this gives
   the same result as running a longer RETIS simulation. This is
   similar to ``test-continue``, however, we here test that we
   can run the restart in a new folder.

Instructions
------------

For these tests, there is a ``run.sh`` script which contains the
commands used for executing them.

Note
----
The engines ``gromacs.py`` and ``gromacs_restart.py`` are used
here to create engines that draw predictable random numbers so
that the results can be compared. The ``gromacs`` engine of
PyRETIS will ask GROMACS to randomly select a seed for generating
velocities. Here, we explicitly set these seeds.
