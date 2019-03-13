Test LAMMPS
===========

This folder contains a few tests for checking the PyRETIS - LAMMPS
interaction:

* `test-dump-phasepoint`: Which will test that we can dump points from
  LAMMPS trajectories correctly.

* `test-integrate`: Which will test that we can integrate the equations
  of motion with LAMMPS from PyRETIS.

* `test-modify-velocities`: Which will check that PyRETIS can use LAMMPS
  to draw randomized velocities.

* `test-propagate`: Which will check that the PyRETIS propagate method
  works as intended with LAMMPS. This method is the central method
  used when PyRETIS requests the generation of new trajectories
  using LAMMPS.


The folder `lammps_testing` includes a common script which is used
for plotting some of the results from the tests.

In each folder, there is a `README.rst` which describes how to run the
test.
