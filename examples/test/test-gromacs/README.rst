Test GROMACS
============

This folder contains some tests for using GROMACS as an
external integrator. The different tests are described below.

test-gromacs
------------
This test will check that the core functionality of the
GROMACS engines are in place and that they give comparable results
to running just plain MD simulations with GROMACS.

test-gromacs-gromacs2
---------------------
This test will compare the two engines ``GROMACS``
and ``GROMACS2`` by running two short RETIS simulations.

test-integrate
--------------
Test that the integrate method of the engine work as intended.

test-load
---------
Test that we can load already existing GROMACS trajectories and
use these with PyRETIS.

test-restart
------------
Test that the restart method works with GROMACS.

test-retis
----------
Test that the RETIS simulation works with GROMACS.
