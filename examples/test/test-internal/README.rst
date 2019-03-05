Test internal
=============

This folder contains some tests for using PyRETIS with the
internal engines. The different tests are described below.

compare-internal-with-lammps
----------------------------
Check that the Velocity Verlet engine give comparable
results to independent simulations performed with LAMMPS.

mdflux-restart
--------------
Check the restart capabilities for the MD Flux simulation.

md-restart
----------
Check the restart capabilities of internal engines when performing
MD simulations.

retis
-----
Check correctness of a RETIS simulation in the current version
of PyRETIS. The correctness is tested against old results.

retis-restart
-------------
Check the restart capabilities of internal RETIS simulations.

tis-multiple
------------
Check the correctness of a TIS simulation. The results are
tested against a previous version of PyRETIS.

tis-restart
-----------
Check the restart capabilities of internal TIS simulations.

retis-load-sparse
-----------------
Check the ability to initiate a simulation from a terrible initial set up.
The inputs can be either frames, trajectories, or mixed.
