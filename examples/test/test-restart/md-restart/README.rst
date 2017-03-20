This is a test of the restart capabilities
==========================================

Here we run a MD simulation in two ways:

1) 1000 steps from a generated starting configuration.

2) 100 steps, identical to 1). Then the simulation
   is stopped, restarted and extended for 900 more steps.

This gives two simulations of 1000 steps each which can be compared.

The sub-directories are as follows:

* ``run-full``: For running 1000 MD steps.

* ``run-100``: For running 100 MD steps.

* ``run-100-1000``: For extending the 100 step MD simulation.

Instructions
------------

The two directories contain MD simulations with different
integrators. The tests can be run in the same way:

1. Run the full simulation, in ``run-full``:
   ``pyretisrun -i md-full.rst -p``

2. Run the 100 step simulation, in ``run-100``:
   ``pyretisrun -i md-100.rst -p``

3. Run the 900 remaining steps, in ``run-100-1000``:

   3.1 Cut-and-paste the last snapshot from ``run-100/md-100-traj.txt`` and
       save it as ``run-100-1000/initial.txt``

   3.2 Run the simulation: ``pyretisrun -i md-100-1000.rst -p``

4. Compare the output: ``python compare.py``
   
