Testing restart/load for internal trajectories
==============================================

This example will test that restart using internal trajectories
work as expected.

The example consist of the following simulations/directories:

1. ``retis-full``: This is a RETIS simulation of 20 cycles,
   using the ``initial.xyz`` as the initial configuration.

2. ``retis-10``: This is a RETIS simulation of 10 cycles,
   otherwise equal to ``retis-full``.

3. ``retis-10-20``: A RETIS simulation of 10 cycles,
   staring from the last cycle sof ``retis-10``.

The trajectories from these simulations can be compared
by using ``python compare.py``.

Instructions for running the test
---------------------------------

1. Run the full RETIS simulation, in ``retis-full``:
   ``pyretisrun -i retis.rst -p``

2. Run the 10-cycles RETIS simulation, in ``retis-10``:
   ``pyretisrun -i retis.rst -p``

3. Run the 10-cycles RETIS simulation, in ``retis-10-20``:

   3.1 Copy input files for the simulation from ``retis-10``.
       Start by creating a new directory ``restart`` in
       ``retis-10-20``. For each path ensemble you will now have to
       copy the ``energy.txt``, ``order.txt`` and ``traj.txt`` and
       modify the copies so that they only contain the last accepted
       trajectory. Let's take ``000`` and an example.
       
       a. Create a new directory: ``000`` in ``retis-10-20/restart/``.
       b. Check ``pathensemble.txt`` in ``retis-10/000`` and note the
          index for the last accepted path.
       c. Copy the files ``energy.txt``, ``order.txt`` and ``traj.txt``
          from ``retis-10/000`` to ``retis-10-20/restart/000``.
       d. In each of the copies you have made, keep only the trajectory
          with the index found in cycles. Remove the others.

       There is a script, ``copy_restart_files.py``, which automates this
       process for all ensembles. It can be used using:

       ``python copy_restart_files.py``

       if you prefer to not manually copy the input files.

   3.2 Run the simulation:
       ``pyretisrun -i retis.rst -p``

4. Comparing the simulations: ``python compare.py``.

Commands for executing all these cycles can be found in ``run.sh``.
